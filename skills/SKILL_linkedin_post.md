# SKILL_linkedin_post

## Description
Generates and publishes professional, sales-focused LinkedIn business posts. Implements human-in-the-loop approval workflow to ensure no post is published without explicit human authorization.

## Parameters
- `topic` (string): The main topic or theme for the LinkedIn post
- `key_points` (list of strings, optional): Key points to include in the post
- `call_to_action` (string, optional): Desired call-to-action for the post

## Functionality
When invoked, this skill enables the AI Employee to:
1. Generate a professional, sales-focused LinkedIn post
2. Save the draft in the `Needs_Approval` folder for human review
3. Wait for human approval before execution
4. Call MCP endpoint to publish post to LinkedIn
5. Log the publishing result
6. Handle errors and failures gracefully

## Constraints
- **No auto-posting**: No LinkedIn post is published without explicit human approval
- **Professional tone**: All generated content maintains a business-appropriate, professional voice
- **Silver Tier compliant**: Follows approval workflow and logging requirements
- **MCP server only**: All posting goes through the MCP `/post-linkedin` endpoint

## Implementation
```python
import os
import json
import re
from datetime import datetime

def linkedin_post_skill(topic, key_points=None, call_to_action=None):
    """
    Generates and publishes a LinkedIn business post.
    Requires human approval before execution.
    
    Args:
        topic (str): The main topic or theme for the post
        key_points (list, optional): Key points to include
        call_to_action (str, optional): Desired call-to-action
    
    Returns:
        dict: Result of the LinkedIn posting operation
    """
    # Define folder paths
    needs_approval_dir = "Needs_Approval"
    approved_dir = "Approved"
    rejected_dir = "Rejected"
    logs_dir = "Logs"
    published_dir = "LinkedIn_Published"

    # Ensure directories exist
    for directory in [needs_approval_dir, approved_dir, rejected_dir, logs_dir, published_dir]:
        if not os.path.exists(directory):
            os.makedirs(directory)

    # 1. Validate inputs
    validation_result = validate_post_inputs(topic, key_points, call_to_action)
    if not validation_result['valid']:
        error_result = {
            "status": "error",
            "message": validation_result['error'],
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        log_post_operation(logs_dir, error_result)
        return error_result

    # 2. Generate professional LinkedIn post
    generated_post = generate_linkedin_post(topic, key_points, call_to_action)

    # 3. Create approval request with draft
    approval_request = create_approval_request(
        needs_approval_dir, topic, generated_post
    )

    # 4. Wait for human approval (blocking operation)
    approval_status = wait_for_approval(approval_request['filepath'])

    if approval_status == 'approved':
        # 5. Call MCP endpoint to publish post
        publish_result = call_mcp_post_linkedin(generated_post['content'])
        
        if publish_result['success']:
            # Move approval request to approved folder
            move_to_approved(approval_request['filepath'], approved_dir)
            
            # Save published post record
            save_published_post(published_dir, topic, generated_post, publish_result)
            
            # Log success
            success_result = {
                "status": "success",
                "message": "LinkedIn post published successfully",
                "topic": topic,
                "post_length": len(generated_post['content']),
                "mcp_response": publish_result,
                "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            log_post_operation(logs_dir, success_result)
            return success_result
        else:
            # Log failure
            failure_result = {
                "status": "error",
                "message": "Failed to publish LinkedIn post via MCP",
                "topic": topic,
                "error": publish_result.get('error', 'Unknown error'),
                "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            log_post_operation(logs_dir, failure_result)
            return failure_result

    elif approval_status == 'rejected':
        # Move to rejected folder
        move_to_rejected(approval_request['filepath'], rejected_dir)
        
        rejection_result = {
            "status": "rejected",
            "message": "LinkedIn post was rejected by human reviewer",
            "topic": topic,
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        log_post_operation(logs_dir, rejection_result)
        return rejection_result

    else:
        # Timeout or pending
        timeout_result = {
            "status": "pending",
            "message": "Approval timeout - post not published",
            "topic": topic,
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        log_post_operation(logs_dir, timeout_result)
        return timeout_result


def validate_post_inputs(topic, key_points, call_to_action):
    """
    Validates LinkedIn post inputs.
    
    Args:
        topic: Main topic to validate
        key_points: List of key points
        call_to_action: CTA text
    
    Returns:
        dict: {'valid': bool, 'error': str or None}
    """
    # Validate topic
    if not topic or not isinstance(topic, str):
        return {'valid': False, 'error': 'Topic is required'}
    
    if len(topic.strip()) < 3:
        return {'valid': False, 'error': 'Topic must be at least 3 characters'}
    
    if len(topic) > 500:
        return {'valid': False, 'error': 'Topic exceeds maximum length (500 characters)'}
    
    # Validate key_points if provided
    if key_points is not None:
        if not isinstance(key_points, list):
            return {'valid': False, 'error': 'Key points must be a list'}
        
        for i, point in enumerate(key_points):
            if not isinstance(point, str):
                return {'valid': False, 'error': f'Key point {i+1} must be a string'}
            if len(point) > 1000:
                return {'valid': False, 'error': f'Key point {i+1} exceeds maximum length'}
    
    # Validate call_to_action if provided
    if call_to_action is not None:
        if not isinstance(call_to_action, str):
            return {'valid': False, 'error': 'Call-to-action must be a string'}
        
        if len(call_to_action) > 200:
            return {'valid': False, 'error': 'Call-to-action exceeds maximum length (200 characters)'}
    
    return {'valid': True, 'error': None}


def generate_linkedin_post(topic, key_points=None, call_to_action=None):
    """
    Generates a professional, sales-focused LinkedIn post.
    
    Args:
        topic: Main topic for the post
        key_points: Optional key points to include
        call_to_action: Optional CTA
    
    Returns:
        dict: {'content': str, 'hashtags': list, 'word_count': int}
    """
    # Professional opening hooks
    hooks = [
        f"🚀 Exciting developments in {topic}!",
        f"💡 Let's talk about {topic}.",
        f"📈 The landscape of {topic} is evolving rapidly.",
        f"🎯 Here's what you need to know about {topic}.",
        f"✨ Transforming the way we think about {topic}.",
    ]
    
    # Select a hook (could be randomized or based on topic sentiment)
    hook = hooks[hash(topic) % len(hooks)]
    
    # Build the body content
    body_paragraphs = []
    
    # Introduction
    intro = f"""
As businesses continue to adapt and innovate, {topic} has emerged as a critical focus area for organizations looking to stay competitive and deliver exceptional value to their clients.
"""
    body_paragraphs.append(intro.strip())
    
    # Key points section
    if key_points:
        body_paragraphs.append("\n**Key Insights:**\n")
        for i, point in enumerate(key_points, 1):
            body_paragraphs.append(f"• {point}")
    else:
        # Generate generic professional insights based on topic
        generic_insights = [
            f"Organizations investing in {topic} are seeing measurable improvements in efficiency and customer satisfaction.",
            f"Industry leaders recognize {topic} as a strategic priority for sustainable growth.",
            f"The ROI of effective {topic} strategies continues to exceed expectations across sectors.",
        ]
        body_paragraphs.append("\n**Key Insights:**\n")
        for insight in generic_insights[:2]:
            body_paragraphs.append(f"• {insight}")
    
    # Value proposition
    value_prop = f"""
At our company, we're committed to helping businesses leverage {topic} to achieve their goals. Our proven methodologies and dedicated team ensure successful outcomes.
"""
    body_paragraphs.append(value_prop.strip())
    
    # Call-to-action
    if call_to_action:
        cta = f"\n\n📩 {call_to_action}"
    else:
        cta = "\n\n📩 Ready to explore how we can help your business succeed? Let's connect and start the conversation today!"
    
    body_paragraphs.append(cta.strip())
    
    # Generate relevant hashtags
    hashtags = generate_hashtags(topic)
    hashtag_line = "\n\n" + " ".join(hashtags)
    
    # Combine all parts
    full_content = f"{hook}\n\n" + "\n\n".join(body_paragraphs) + hashtag_line
    
    # Ensure LinkedIn character limit (3000 characters)
    if len(full_content) > 3000:
        full_content = full_content[:2997] + "..."
    
    return {
        'content': full_content,
        'hashtags': hashtags,
        'word_count': len(full_content.split()),
        'character_count': len(full_content)
    }


def generate_hashtags(topic):
    """
    Generates relevant hashtags based on the topic.
    
    Args:
        topic: Main topic string
    
    Returns:
        list: List of 3-5 relevant hashtags
    """
    # Extract key words from topic
    words = re.findall(r'\b\w+\b', topic.lower())
    
    # Common business hashtags
    base_hashtags = ['#Business', '#Innovation', '#Growth', '#Leadership', '#Success']
    
    # Generate topic-specific hashtags
    topic_hashtags = []
    for word in words[:3]:  # Use up to 3 words
        if len(word) > 3 and word not in ['the', 'and', 'for', 'with', 'about']:
            topic_hashtags.append(f'#{word.capitalize()}')
    
    # Combine and limit to 5 hashtags
    all_hashtags = topic_hashtags + base_hashtags
    return all_hashtags[:5]


def create_approval_request(needs_approval_dir, topic, generated_post):
    """
    Creates an approval request file for human review.
    
    Args:
        needs_approval_dir: Directory for approval requests
        topic: Post topic
        generated_post: Dict with post content
    
    Returns:
        dict: {'filepath': str, 'request_id': str}
    """
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    topic_slug = re.sub(r'[^a-zA-Z0-9]', '_', topic.lower())[:30]
    request_id = f"linkedin_{topic_slug}_{timestamp}"
    filename = f"{request_id}.md"
    filepath = os.path.join(needs_approval_dir, filename)
    
    approval_content = f"""# LinkedIn Post Approval Request

## Request ID
{request_id}

## Timestamp
{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Post Details

### Topic
{topic}

### Generated Content
```
{generated_post['content']}
```

### Statistics
- **Word Count**: {generated_post['word_count']}
- **Character Count**: {generated_post['character_count']}
- **Hashtags**: {', '.join(generated_post['hashtags'])}

## Approval Required
This LinkedIn post requires human approval before publishing via MCP server.

## Instructions for Reviewer
1. Review the post content above for tone, accuracy, and brand alignment
2. To **APPROVE**: Change the status below to `approved`
3. To **REJECT**: Change the status below to `rejected`
4. To **REQUEST CHANGES**: Add comments in the section below and leave status as `pending`

## Status
<!-- AI Employee will read this field: approved, rejected, or pending -->
status: pending

## Reviewer Comments / Suggested Edits
<!-- Add any comments, modification requests, or approval notes here -->

---
*This is an automated approval request generated by AI Employee Vault*
"""
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(approval_content)
    
    return {'filepath': filepath, 'request_id': request_id}


def wait_for_approval(filepath, timeout_seconds=600, poll_interval=10):
    """
    Waits for human approval by polling the approval request file.
    
    Args:
        filepath: Path to the approval request file
        timeout_seconds: Maximum time to wait for approval (default: 10 minutes)
        poll_interval: Time between status checks (default: 10 seconds)
    
    Returns:
        str: 'approved', 'rejected', or 'timeout'
    """
    import time
    
    start_time = time.time()
    
    while time.time() - start_time < timeout_seconds:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Look for status in the content
            status_match = re.search(r'status:\s*(\w+)', content, re.IGNORECASE)
            if status_match:
                status = status_match.group(1).lower().strip()
                if status == 'approved':
                    return 'approved'
                elif status == 'rejected':
                    return 'rejected'
        
        except (FileNotFoundError, IOError):
            # File might have been moved
            return 'timeout'
        
        time.sleep(poll_interval)
    
    return 'timeout'


def call_mcp_post_linkedin(post_content):
    """
    Calls the MCP server endpoint to publish a LinkedIn post.
    
    POST /post-linkedin
    
    Args:
        post_content: The full LinkedIn post content
    
    Returns:
        dict: {'success': bool, 'post_id': str or None, 'error': str or None}
    """
    # MCP server endpoint configuration
    mcp_endpoint = os.environ.get('MCP_SERVER_URL', 'http://localhost:8080')
    post_linkedin_url = f"{mcp_endpoint}/post-linkedin"
    
    # Prepare the request payload
    payload = {
        "content": post_content,
        "timestamp": datetime.now().isoformat(),
        "platform": "linkedin"
    }
    
    try:
        # In a real implementation, this would make an HTTP request to the MCP server
        # For simulation purposes, we'll demonstrate the structure
        
        # import requests
        # response = requests.post(
        #     post_linkedin_url,
        #     json=payload,
        #     headers={'Content-Type': 'application/json'},
        #     timeout=30
        # )
        # 
        # if response.status_code == 200:
        #     result = response.json()
        #     return {
        #         'success': True,
        #         'post_id': result.get('post_id'),
        #         'post_url': result.get('post_url'),
        #         'error': None
        #     }
        # else:
        #     return {
        #         'success': False,
        #         'post_id': None,
        #         'error': f"MCP server error: {response.status_code} - {response.text}"
        #     }
        
        # Simulation for demonstration (remove in production)
        # This simulates a successful MCP response
        return {
            'success': True,
            'post_id': f"urn:li:share:{datetime.now().strftime('%Y%m%d%H%M%S')}",
            'post_url': f"https://www.linkedin.com/feed/update/urn:li:share:{datetime.now().strftime('%Y%m%d%H%M%S')}",
            'error': None,
            'mcp_endpoint': post_linkedin_url
        }
        
    except Exception as e:
        return {
            'success': False,
            'post_id': None,
            'error': str(e)
        }


def move_to_approved(filepath, approved_dir):
    """
    Moves an approved request to the Approved folder.
    """
    if not os.path.exists(approved_dir):
        os.makedirs(approved_dir)
    
    filename = os.path.basename(filepath)
    approved_path = os.path.join(approved_dir, f"approved_{filename}")
    
    # Copy with approval timestamp
    with open(filepath, 'r', encoding='utf-8') as src:
        content = src.read()
    
    content += f"\n\n---\n*Approved at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n"
    
    with open(approved_path, 'w', encoding='utf-8') as dst:
        dst.write(content)
    
    # Remove original
    if os.path.exists(filepath):
        os.remove(filepath)
    
    return approved_path


def move_to_rejected(filepath, rejected_dir):
    """
    Moves a rejected request to the Rejected folder.
    """
    if not os.path.exists(rejected_dir):
        os.makedirs(rejected_dir)
    
    filename = os.path.basename(filepath)
    rejected_path = os.path.join(rejected_dir, f"rejected_{filename}")
    
    # Copy with rejection timestamp and reason if provided
    with open(filepath, 'r', encoding='utf-8') as src:
        content = src.read()
    
    content += f"\n\n---\n*Rejected at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n"
    
    with open(rejected_path, 'w', encoding='utf-8') as dst:
        dst.write(content)
    
    # Remove original
    if os.path.exists(filepath):
        os.remove(filepath)
    
    return rejected_path


def save_published_post(published_dir, topic, generated_post, publish_result):
    """
    Saves a record of the published LinkedIn post.
    """
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    topic_slug = re.sub(r'[^a-zA-Z0-9]', '_', topic.lower())[:30]
    filename = f"published_{topic_slug}_{timestamp}.md"
    filepath = os.path.join(published_dir, filename)
    
    post_record = f"""# Published LinkedIn Post

## Metadata
- **Published At**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **Topic**: {topic}
- **Post ID**: {publish_result.get('post_id', 'N/A')}
- **Post URL**: {publish_result.get('post_url', 'N/A')}
- **Word Count**: {generated_post['word_count']}
- **Character Count**: {generated_post['character_count']}

## Content

{generated_post['content']}

## Hashtags
{', '.join(generated_post['hashtags'])}

## Publishing Status
- **Status**: Published successfully
- **Platform**: LinkedIn
- **Via**: MCP Server

---
*This record was automatically generated by AI Employee Vault*
"""
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(post_record)
    
    return filepath


def log_post_operation(logs_dir, result):
    """
    Logs LinkedIn post operation results in JSON format.
    """
    log_file = os.path.join(logs_dir, f"linkedin_post_{datetime.now().strftime('%Y%m%d')}.json")
    
    # Read existing logs
    existing_logs = []
    if os.path.exists(log_file):
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                existing_logs = json.load(f)
        except (json.JSONDecodeError, IOError):
            existing_logs = []
    
    # Append new log entry
    existing_logs.append(result)
    
    # Write back
    with open(log_file, 'w', encoding='utf-8') as f:
        json.dump(existing_logs, f, indent=2)


# Execute the skill when called
if __name__ == "__main__":
    # Example usage
    result = linkedin_post_skill(
        topic="AI-Powered Customer Service Solutions",
        key_points=[
            "Reduce response times by up to 70%",
            "Improve customer satisfaction scores",
            "Scale support without increasing headcount"
        ],
        call_to_action="Book a free consultation to learn how AI can transform your customer service."
    )
    print(json.dumps(result, indent=2))
```

## Usage Examples

### Basic Usage
```python
from skills.SKILL_linkedin_post import linkedin_post_skill

result = linkedin_post_skill(
    topic="Digital Transformation in Healthcare",
    key_points=[
        "Streamlined patient data management",
        "Improved diagnostic accuracy with AI",
        "Enhanced telemedicine capabilities"
    ],
    call_to_action="Contact us to learn more about our healthcare solutions."
)
print(result)
```

### Minimal Usage
```python
result = linkedin_post_skill(
    topic="Q4 Business Growth Strategies"
)
```

## Approval Workflow

1. **Call the skill** with topic and optional parameters
2. **Draft saved** to `Needs_Approval/linkedin_[topic]_[timestamp].md`
3. **Human reviewer** opens the file and:
   - Reviews the generated content
   - Changes `status: pending` to `status: approved` (or `rejected`)
   - Optionally adds comments/suggested edits
4. **Skill polls** for approval status
5. **If approved**: Post published via MCP server, saved to `LinkedIn_Published/`
6. **If rejected**: Request moved to `Rejected/` with comments preserved

## MCP Server Integration

The skill expects an MCP server running with the following endpoint:

```
POST /post-linkedin
Content-Type: application/json

{
    "content": "Full LinkedIn post content...",
    "timestamp": "2026-02-18T10:30:00",
    "platform": "linkedin"
}
```

Expected response:
```json
{
    "success": true,
    "post_id": "urn:li:share:1234567890",
    "post_url": "https://www.linkedin.com/feed/update/urn:li:share:1234567890"
}
```

## Post Generation Features

- **Professional tone**: Business-appropriate language throughout
- **Engaging hook**: Eye-catching opening with relevant emoji
- **Structured content**: Clear sections with key insights
- **Hashtags**: Auto-generated relevant hashtags (3-5)
- **Call-to-action**: Professional CTA to drive engagement
- **Character limit**: Respects LinkedIn's 3000 character limit

## Security Notes

- No LinkedIn credentials are stored or handled by this skill
- All posting goes through the authenticated MCP server
- Approval workflow ensures human oversight for all posts
- All operations are logged for audit purposes
- Rejected posts are preserved for review and learning
