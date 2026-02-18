# task-planner

## Description
A Claude Agent Skill that generates structured Plan.md files from input task descriptions. Breaks down tasks into clear, actionable components with objective, key steps, risks, resources, and time estimates.

## Parameters
- `task_description` (string, required): The task description to be converted into a structured plan.

## Functionality
When invoked, this skill:
1. Accepts a task description as input
2. Analyzes and breaks down the task into structured components
3. Generates a clean, well-organized markdown plan
4. Saves the output to the Plans folder as Plan_<timestamp>.md
5. Does not execute any external actions
6. Complies with Silver Tier requirements

## Constraints
- Clear reasoning throughout the plan
- No unnecessary verbosity
- Structured markdown output only
- No external API calls or system actions
- Local vault operations only

## Implementation
```python
import os
from datetime import datetime

def task_planner_skill(task_description):
    """
    Generates a structured Plan.md file from an input task description.
    
    Args:
        task_description (str): The task to be converted into a structured plan.
    
    Returns:
        str: Path to the created plan file.
    """
    # Ensure Plans directory exists
    plans_dir = "Plans"
    if not os.path.exists(plans_dir):
        os.makedirs(plans_dir)
    
    # Generate timestamp for filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    plan_filename = f"Plan_{timestamp}.md"
    plan_filepath = os.path.join(plans_dir, plan_filename)
    
    # Analyze task and generate structured plan
    plan_content = generate_plan_content(task_description)
    
    # Save plan to file
    with open(plan_filepath, 'w', encoding='utf-8') as f:
        f.write(plan_content)
    
    return f"Plan created: {plan_filepath}"

def generate_plan_content(task_description):
    """
    Analyzes task description and generates structured plan content.
    """
    # Extract key components from task description
    objective = extract_objective(task_description)
    key_steps = generate_key_steps(task_description)
    risks = identify_risks(task_description)
    resources = identify_resources(task_description)
    estimated_time = estimate_completion_time(task_description)
    
    # Build structured markdown content
    plan_content = f"""# Task Plan

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

## Objective

{objective}

---

## Key Steps

{format_checklist(key_steps)}

---

## Risks

{format_risks(risks)}

---

## Required Resources

{format_resources(resources)}

---

## Estimated Completion Time

{estimated_time}

---

## Notes

Add any additional considerations or context-specific details here.
"""
    
    return plan_content

def extract_objective(task_description):
    """
    Extracts the primary objective from the task description.
    """
    # Simple extraction - in a real implementation, this could use NLP
    objective = task_description.strip()
    
    # Ensure it starts with an action verb
    action_verbs = [
        'Create', 'Build', 'Develop', 'Implement', 'Design', 'Write',
        'Review', 'Analyze', 'Test', 'Deploy', 'Configure', 'Set up',
        'Update', 'Fix', 'Resolve', 'Complete', 'Generate', 'Process'
    ]
    
    for verb in action_verbs:
        if objective.lower().startswith(verb.lower()):
            return objective
    
    # If no action verb found, prepend "Complete the following:"
    return f"Complete the following: {objective}"

def generate_key_steps(task_description):
    """
    Generates a list of key steps based on the task description.
    """
    task_lower = task_description.lower()
    
    # Default steps for general tasks
    steps = [
        "Review task requirements and constraints",
        "Identify necessary resources and dependencies",
        "Execute primary task actions",
        "Verify completion and quality",
        "Document results and outcomes"
    ]
    
    # Add context-specific steps based on task type
    if 'code' in task_lower or 'program' in task_lower or 'script' in task_lower:
        steps = [
            "Analyze requirements and define specifications",
            "Design solution architecture",
            "Write initial code implementation",
            "Test functionality and edge cases",
            "Review and refactor code",
            "Document code and usage instructions"
        ]
    elif 'report' in task_lower or 'document' in task_lower or 'write' in task_lower:
        steps = [
            "Gather relevant information and data",
            "Outline document structure",
            "Draft initial content",
            "Review and revise content",
            "Format and finalize document",
            "Submit or distribute report"
        ]
    elif 'email' in task_lower or 'message' in task_lower or 'communicate' in task_lower:
        steps = [
            "Identify key message points",
            "Determine appropriate tone and style",
            "Draft message content",
            "Review for clarity and accuracy",
            "Send or schedule delivery"
        ]
    elif 'review' in task_lower or 'analyze' in task_lower or 'audit' in task_lower:
        steps = [
            "Define review scope and criteria",
            "Gather materials for review",
            "Conduct systematic analysis",
            "Document findings and observations",
            "Provide recommendations",
            "Submit review report"
        ]
    
    return steps

def identify_risks(task_description):
    """
    Identifies potential risks based on the task description.
    """
    task_lower = task_description.lower()
    
    risks = []
    
    # General risks
    risks.append("Task may take longer than estimated if complications arise")
    risks.append("Dependencies on external factors may cause delays")
    
    # Context-specific risks
    if 'code' in task_lower or 'script' in task_lower:
        risks.append("Code may contain bugs requiring additional testing")
        risks.append("Integration issues with existing systems")
    
    if 'deadline' in task_lower or 'urgent' in task_lower:
        risks.append("Time pressure may impact quality")
    
    if 'data' in task_lower or 'information' in task_lower:
        risks.append("Data accuracy and completeness concerns")
    
    if 'approval' in task_lower or 'permission' in task_lower:
        risks.append("Awaiting external approval may cause delays")
    
    return risks

def identify_resources(task_description):
    """
    Identifies required resources based on the task description.
    """
    task_lower = task_description.lower()
    
    resources = []
    
    # Default resources
    resources.append("Access to relevant documentation and references")
    resources.append("Appropriate tools and software")
    
    # Context-specific resources
    if 'code' in task_lower or 'program' in task_lower:
        resources.append("Development environment and IDE")
        resources.append("Version control access")
        resources.append("Testing frameworks")
    
    if 'report' in task_lower or 'document' in task_lower:
        resources.append("Source data and reference materials")
        resources.append("Document templates")
    
    if 'email' in task_lower or 'communicate' in task_lower:
        resources.append("Email client or communication platform")
        resources.append("Contact information")
    
    if 'review' in task_lower or 'analyze' in task_lower:
        resources.append("Access to materials being reviewed")
        resources.append("Analysis tools or frameworks")
    
    return resources

def estimate_completion_time(task_description):
    """
    Estimates completion time based on the task description.
    """
    task_lower = task_description.lower()
    
    # Check for explicit time mentions
    time_indicators = {
        'urgent': '1-2 hours (expedited)',
        'asap': '1-2 hours (expedited)',
        'today': '4-8 hours (same day)',
        'week': '2-5 business days',
        'month': '2-4 weeks'
    }
    
    for indicator, estimate in time_indicators.items():
        if indicator in task_lower:
            return estimate
    
    # Estimate based on task type
    if 'quick' in task_lower or 'simple' in task_lower:
        return "30 minutes - 1 hour"
    elif 'review' in task_lower or 'analyze' in task_lower:
        return "2-4 hours"
    elif 'report' in task_lower or 'document' in task_lower:
        return "4-8 hours"
    elif 'code' in task_lower or 'script' in task_lower:
        return "4-16 hours (depending on complexity)"
    else:
        return "2-4 hours (standard task)"

def format_checklist(steps):
    """
    Formats steps as a markdown checklist.
    """
    checklist = ""
    for i, step in enumerate(steps, 1):
        checklist += f"- [ ] {step}\n"
    return checklist

def format_risks(risks):
    """
    Formats risks as a markdown list.
    """
    formatted = ""
    for risk in risks:
        formatted += f"- {risk}\n"
    return formatted

def format_resources(resources):
    """
    Formats resources as a markdown list.
    """
    formatted = ""
    for resource in resources:
        formatted += f"- {resource}\n"
    return formatted

# Execute the skill when called
if __name__ == "__main__":
    # Example usage
    sample_task = "Create a Python script to automate daily reports"
    result = task_planner_skill(sample_task)
    print(result)
```

## Usage Examples

### Example 1: Code Task
**Input:**
```
Create a Python script to automate daily reports
```

**Output (Plans/Plan_YYYYMMDD_HHMMSS.md):**
```markdown
# Task Plan

**Generated:** 2024-01-15 10:30:00

---

## Objective

Create a Python script to automate daily reports

---

## Key Steps

- [ ] Analyze requirements and define specifications
- [ ] Design solution architecture
- [ ] Write initial code implementation
- [ ] Test functionality and edge cases
- [ ] Review and refactor code
- [ ] Document code and usage instructions

---

## Risks

- Code may contain bugs requiring additional testing
- Integration issues with existing systems
- Task may take longer than estimated if complications arise
- Dependencies on external factors may cause delays

---

## Required Resources

- Development environment and IDE
- Version control access
- Testing frameworks
- Access to relevant documentation and references
- Appropriate tools and software

---

## Estimated Completion Time

4-16 hours (depending on complexity)

---

## Notes

Add any additional considerations or context-specific details here.
```

### Example 2: Document Task
**Input:**
```
Write a quarterly performance report
```

**Output:**
```markdown
# Task Plan

**Generated:** 2024-01-15 11:00:00

---

## Objective

Complete the following: Write a quarterly performance report

---

## Key Steps

- [ ] Gather relevant information and data
- [ ] Outline document structure
- [ ] Draft initial content
- [ ] Review and revise content
- [ ] Format and finalize document
- [ ] Submit or distribute report

---

## Risks

- Data accuracy and completeness concerns
- Task may take longer than estimated if complications arise
- Dependencies on external factors may cause delays

---

## Required Resources

- Source data and reference materials
- Document templates
- Access to relevant documentation and references
- Appropriate tools and software

---

## Estimated Completion Time

4-8 hours

---

## Notes

Add any additional considerations or context-specific details here.
```

## Compliance Notes

- **Silver Tier Compliant:** Yes
- **External Actions:** None
- **Local Operations Only:** Yes
- **Structured Output:** Markdown only
- **Clear Reasoning:** Included in all plan components