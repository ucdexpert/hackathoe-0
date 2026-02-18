#!/usr/bin/env python3
"""
Gmail Send Skill - Send real emails via SMTP

Usage:
    python send_email.py --to recipient@example.com --subject "Subject" --body "Message"
    python send_email.py --to user@example.com --subject "Test" --body "Hello" --cc other@example.com
    python send_email.py --to user@example.com --subject "Report" --body "See attached" --attachments file.pdf,file2.txt
"""

import os
import sys
import smtplib
import argparse
import re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime

# Load .env file automatically
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv not installed, rely on system env variables


def validate_email(email: str) -> bool:
    """Validate email address format."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email.strip()))


def send_email(to: str, subject: str, body: str, 
               cc: str = None, attachments: list = None) -> dict:
    """
    Send email via Gmail SMTP.
    
    Args:
        to: Recipient email address
        subject: Email subject
        body: Email body text
        cc: Optional CC recipient
        attachments: Optional list of file paths
    
    Returns:
        dict: {'success': bool, 'message': str, 'message_id': str or None}
    """
    # Get credentials from environment
    email_address = os.environ.get('EMAIL_ADDRESS')
    email_password = os.environ.get('EMAIL_PASSWORD')
    smtp_server = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
    smtp_port = int(os.environ.get('SMTP_PORT', '587'))
    
    # Validate credentials
    if not email_address or not email_password:
        return {
            'success': False,
            'message': 'ERROR: EMAIL_ADDRESS and EMAIL_PASSWORD environment variables required',
            'message_id': None
        }
    
    # Validate recipient
    if not to or not validate_email(to):
        return {
            'success': False,
            'message': f'ERROR: Invalid email address: {to}',
            'message_id': None
        }
    
    # Validate subject
    if not subject or len(subject.strip()) == 0:
        return {
            'success': False,
            'message': 'ERROR: Email subject is required',
            'message_id': None
        }
    
    # Validate body
    if not body or len(body.strip()) == 0:
        return {
            'success': False,
            'message': 'ERROR: Email body is required',
            'message_id': None
        }
    
    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = email_address
        msg['To'] = to
        msg['Subject'] = subject
        msg['Date'] = datetime.now().strftime('%a, %d %b %Y %H:%M:%S %z')
        
        # Add CC if provided
        recipients = [to.strip()]
        if cc:
            cc_list = [c.strip() for c in cc.split(',')]
            valid_cc = [c for c in cc_list if validate_email(c)]
            if valid_cc:
                msg['Cc'] = ', '.join(valid_cc)
                recipients.extend(valid_cc)
        
        # Add body
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        # Add attachments if provided
        if attachments:
            for file_path in attachments:
                file_path = file_path.strip()
                if os.path.exists(file_path):
                    try:
                        with open(file_path, 'rb') as f:
                            part = MIMEBase('application', 'octet-stream')
                            part.set_payload(f.read())
                            encoders.encode_base64(part)
                            part.add_header(
                                'Content-Disposition',
                                f'attachment; filename="{os.path.basename(file_path)}"'
                            )
                            msg.attach(part)
                    except Exception as e:
                        pass  # Skip attachment on error
        
        # Connect and send
        with smtplib.SMTP(smtp_server, smtp_port, timeout=30) as server:
            server.starttls()
            server.login(email_address, email_password)
            server.send_message(msg, to_addrs=recipients)
            message_id = msg.get('Message-ID', 'N/A')
        
        return {
            'success': True,
            'message': f'SUCCESS: Email sent to {to}',
            'message_id': message_id
        }
        
    except smtplib.SMTPAuthenticationError:
        return {
            'success': False,
            'message': 'ERROR: SMTP authentication failed. Check EMAIL_ADDRESS and EMAIL_PASSWORD',
            'message_id': None
        }
    except smtplib.SMTPConnectError:
        return {
            'success': False,
            'message': f'ERROR: Failed to connect to SMTP server {smtp_server}:{smtp_port}',
            'message_id': None
        }
    except smtplib.SMTPException as e:
        return {
            'success': False,
            'message': f'ERROR: SMTP error: {str(e)}',
            'message_id': None
        }
    except Exception as e:
        return {
            'success': False,
            'message': f'ERROR: {str(e)}',
            'message_id': None
        }


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Send emails via Gmail SMTP',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Environment Variables:
    EMAIL_ADDRESS     Your Gmail address
    EMAIL_PASSWORD    Your Gmail app password
    SMTP_SERVER       SMTP server (default: smtp.gmail.com)
    SMTP_PORT         SMTP port (default: 587)

Examples:
    python send_email.py --to user@example.com --subject "Hello" --body "Test message"
    python send_email.py --to user@example.com --subject "Report" --body "See attached" --attachments report.pdf
        '''
    )
    
    parser.add_argument('--to', '-t', required=True, help='Recipient email address')
    parser.add_argument('--subject', '-s', required=True, help='Email subject')
    parser.add_argument('--body', '-b', required=True, help='Email body text')
    parser.add_argument('--cc', help='CC recipient(s), comma-separated')
    parser.add_argument('--attachments', '-a', help='Attachment file paths, comma-separated')
    parser.add_argument('--json', action='store_true', help='Output as JSON')
    
    args = parser.parse_args()
    
    # Parse attachments
    attachments = None
    if args.attachments:
        attachments = [a.strip() for a in args.attachments.split(',')]
    
    # Send email
    result = send_email(
        to=args.to,
        subject=args.subject,
        body=args.body,
        cc=args.cc,
        attachments=attachments
    )
    
    # Output result
    if args.json:
        import json
        print(json.dumps(result, indent=2))
    else:
        print(result['message'])
        if result['success'] and result['message_id']:
            print(f"Message-ID: {result['message_id']}")
    
    sys.exit(0 if result['success'] else 1)


if __name__ == '__main__':
    main()
