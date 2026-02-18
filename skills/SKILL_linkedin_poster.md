# SKILL_linkedin_poster

## Description
Automates LinkedIn posting for the AI Employee, creating professional, value-focused business content according to posting schedule rules, with mandatory human approval before publication.

## Parameters
None

## Functionality
When invoked, this skill enables the AI Employee to:
1. Create professional business posts based on content guidelines
2. Follow established content guidelines (professional, value-focused)
3. Apply posting schedule rules
4. Generate approval requests before posting
5. Log all posting activities

## Implementation
```python
import os
import json
from datetime import datetime, timedelta

def linkedin_poster_skill():
    """
    Creates and manages LinkedIn posts for the AI Employee.
    """
    # Define folder paths
    content_dir = "LinkedIn_Content"
    drafts_dir = "LinkedIn_Drafts"
    needs_approval_dir = "Needs_Approval"
    published_dir = "LinkedIn_Published"
    logs_dir = "Logs"
    
    # Ensure directories exist
    for directory in [content_dir, drafts_dir, needs_approval_dir, published_dir, logs_dir]:
        if not os.path.exists(directory):
            os.makedirs(directory)
    
    # Check if it's time to create a post based on schedule
    if should_create_post():
        # 1. Create a professional business post
        post_content = create_business_post()
        
        # 2. Save as draft
        draft_filename = f"linkedin_draft_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        draft_path = os.path.join(drafts_dir, draft_filename)
        
        with open(draft_path, 'w', encoding='utf-8') as f:
            f.write(post_content)
        
        # 3. Create approval request (mandatory for all LinkedIn posts)
        approval_result = create_post_approval_request(draft_path, post_content)
        
        # 4. Log the activity
        activity_entry = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'action': 'Post Draft Created',
            'item': draft_filename,
            'details': 'Approval required before posting to LinkedIn'
        }
        
        log_linkedin_activity(logs_dir, [activity_entry], 1)
        
        return f"LinkedIn post draft created: {draft_filename}. Approval required before posting."
    else:
        return "Not time to create a LinkedIn post based on schedule."

def should_create_post():
    """
    Determines if it's time to create a LinkedIn post based on schedule rules.
    """
    # Simple scheduling: post once every 2 days
    # In a real implementation, this could be more sophisticated
    posts_dir = "LinkedIn_Published"
    if not os.path.exists(posts_dir):
        os.makedirs(posts_dir)
        return True  # Post if no previous posts exist
    
    # Check the most recent post
    files = [f for f in os.listdir(posts_dir) if f.endswith('.md')]
    if not files:
        return True  # Post if no previous posts exist
    
    # Sort files by date in filename
    files.sort(reverse=True)
    latest_post = files[0]
    
    # Extract date from filename (format: linkedin_published_YYYYMMDD_HHMMSS.md)
    try:
        date_part = latest_post.split('_')[2]  # Gets YYYYMMDD part
        year = int(date_part[:4])
        month = int(date_part[4:6])
        day = int(date_part[6:8])
        
        latest_date = datetime(year, month, day)
        today = datetime.now()
        
        # Post if it's been at least 2 days since the last post
        return (today - latest_date).days >= 2
    except (IndexError, ValueError):
        # If parsing fails, assume it's time to post
        return True

def create_business_post():
    """
    Creates a professional, value-focused business post.
    """
    topics = [
        "Industry insights and trends",
        "Tips for professional growth",
        "Thoughts on innovation",
        "Reflections on leadership",
        "Analysis of market developments",
        "Best practices in business",
        "Lessons learned from experience",
        "Future predictions for the industry"
    ]
    
    # Randomly select a topic (in a real implementation, this could be more sophisticated)
    import random
    selected_topic = random.choice(topics)
    
    post_content = f"""# LinkedIn Post Draft

## Topic
{selected_topic}

## Content
In today's rapidly evolving business landscape, staying ahead requires continuous learning and adaptation. 

Key points to consider:
- Embrace change as an opportunity for growth
- Invest in developing both technical and soft skills
- Build meaningful professional relationships
- Stay informed about industry trends and innovations

What are your thoughts on this topic? I'd love to hear your perspective in the comments.

#ProfessionalDevelopment #BusinessGrowth #Innovation #Leadership

## Post Guidelines Followed
- Professional tone maintained
- Value-focused content provided
- Engaging question included
- Relevant hashtags added
- Appropriate length for LinkedIn
"""
    
    return post_content

def create_post_approval_request(draft_path, post_content):
    """
    Creates an approval request for a LinkedIn post.
    """
    needs_approval_dir = "Needs_Approval"
    if not os.path.exists(needs_approval_dir):
        os.makedirs(needs_approval_dir)
    
    draft_name = os.path.basename(draft_path)
    approval_filename = f"linkedin_approval_{os.path.splitext(draft_name)[0]}.md"
    approval_filepath = os.path.join(needs_approval_dir, approval_filename)
    
    approval_content = f"""# LinkedIn Post Approval Request

## Post Content
{post_content}

## Justification for Approval
All LinkedIn posts require human approval before publishing to ensure brand alignment and appropriateness.

## Action Required
Please review the post content and approve, modify, or reject before it can be published to LinkedIn.
"""

    with open(approval_filepath, 'w', encoding='utf-8') as f:
        f.write(approval_content)
    
    return True

def log_linkedin_activity(logs_dir, activity_entries, processed_count):
    """
    Logs LinkedIn posting activities in JSON format.
    """
    log_entry = {
        "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "operation": "linkedin_posting",
        "processed_count": processed_count,
        "activities": activity_entries,
        "status": "completed"
    }
    
    log_file = os.path.join(logs_dir, f"linkedin_posting_{datetime.now().strftime('%Y%m%d')}.json")
    
    # Read existing logs if file exists
    existing_logs = []
    if os.path.exists(log_file):
        with open(log_file, 'r', encoding='utf-8') as f:
            try:
                existing_logs = json.load(f)
            except json.JSONDecodeError:
                existing_logs = []
    
    # Append new log entry
    existing_logs.append(log_entry)
    
    # Write back to file
    with open(log_file, 'w', encoding='utf-8') as f:
        json.dump(existing_logs, f, indent=2)

# Execute the skill when called
result = linkedin_poster_skill()
result
```