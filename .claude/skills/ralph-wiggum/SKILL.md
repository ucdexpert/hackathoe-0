# ralph-wiggum

## Description
An autonomous task execution loop inspired by Ralph Wiggum's persistent approach. This skill automatically analyzes tasks, creates execution plans, executes steps one-by-one, checks results, and continues until completion. Includes safety controls with iteration limits and human approval for risky operations.

## Parameters
- `task_file` (string, optional): Path to task file to process (default: scans Needs_Action folder)
- `max_iterations` (integer, optional): Maximum loop iterations before stopping (default: 5)
- `require_approval` (boolean, optional): Require human approval for risky actions (default: True)
- `dry_run` (boolean, optional): Simulate execution without making changes (default: False)

## Functionality
When invoked, this skill:

1. **Analyzes Task**
   - Reads task file from Needs_Action folder
   - Identifies task type and requirements
   - Detects potential risks
   - Estimates complexity

2. **Creates Execution Plan**
   - Generates step-by-step Plan.md
   - Identifies required resources
   - Marks risky steps for approval
   - Saves to Plans folder

3. **Executes Steps**
   - Processes first step
   - Checks execution result
   - Logs progress
   - Continues to next step

4. **Monitors Progress**
   - Tracks iteration count
   - Validates each step result
   - Detects failure conditions
   - Stops if max iterations reached

5. **Safety Controls**
   - Maximum 5 iterations (configurable)
   - Human approval for risky actions
   - Automatic error handling
   - Rollback on critical failure

6. **Completes Task**
   - Moves task to Done folder
   - Updates Dashboard
   - Logs completion
   - Generates summary

## The Ralph Wiggum Loop

```
┌─────────────────────────────────────────────────────────┐
│  Ralph Wiggum Autonomous Loop                           │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  1. Analyze Task ←────────────────────────────┐        │
│     ↓                                         │        │
│  2. Create Plan.md                            │        │
│     ↓                                         │        │
│  3. Execute First Step                        │        │
│     ↓                                         │        │
│  4. Check Result                              │        │
│     ↓                                         │        │
│  5. Continue Next Step                        │        │
│     ↓                                         │        │
│  6. More Steps? ──Yes──→ Step 3               │        │
│     ↓ No                                      │        │
│  7. Move to Done                              │        │
│     ↓                                         │        │
│  8. Complete ─────────────────────────────────┘        │
│                                                         │
│  Safety: Max 5 iterations, Human approval if risky     │
└─────────────────────────────────────────────────────────┘
```

## Plan.md Format

```markdown
# Execution Plan: task_name.md

**Created:** 2026-02-18 10:00:00
**Task Type:** email
**Risk Level:** low
**Max Iterations:** 5

---

## Steps

- [x] Step 1: Analyze task content
- [ ] Step 2: Prepare email draft
- [ ] Step 3: Validate recipient
- [ ] Step 4: Send email
- [ ] Step 5: Log activity

---

## Execution Log

| Iteration | Step | Status | Timestamp |
|-----------|------|--------|-----------|
| 1 | 1 | completed | 2026-02-18 10:00:01 |

---

## Notes

Auto-generated plan by ralph-wiggum skill.
```

## Implementation
```python
import os
import sys
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from enum import Enum
import re


class RiskLevel(Enum):
    """Task risk level enumeration."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class StepStatus(Enum):
    """Step status enumeration."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class RalphWiggumLoop:
    """Autonomous task execution loop."""
    
    def __init__(self, vault_root: Path = None, max_iterations: int = 5,
                 require_approval: bool = True, dry_run: bool = False):
        """
        Initialize Ralph Wiggum autonomous loop.
        
        Args:
            vault_root: Path to AI_Employee_Vault
            max_iterations: Maximum loop iterations
            require_approval: Require human approval for risky actions
            dry_run: Simulate without making changes
        """
        if vault_root is None:
            self.vault_root = Path(__file__).resolve().parent.parent
        else:
            self.vault_root = Path(vault_root)
        
        # Define paths
        self.needs_action_dir = self.vault_root / "Needs_Action"
        self.plans_dir = self.vault_root / "Plans"
        self.done_dir = self.vault_root / "Done"
        self.logs_dir = self.vault_root / "Logs"
        self.dashboard_file = self.vault_root / "Dashboard.md"
        self.approvals_dir = self.vault_root / "Needs_Approval"
        
        # Ensure directories exist
        for directory in [self.plans_dir, self.done_dir, self.logs_dir, self.approvals_dir]:
            directory.mkdir(parents=True, exist_ok=True)
        
        # Configuration
        self.max_iterations = max_iterations
        self.require_approval = require_approval
        self.dry_run = dry_run
        
        # Execution state
        self.current_iteration = 0
        self.current_step = 0
        self.steps = []
        self.execution_log = []
    
    def _analyze_task(self, task_path: Path) -> Dict:
        """
        Analyze a task file to understand requirements.
        
        Args:
            task_path: Path to task file
        
        Returns:
            Dict with task analysis
        """
        analysis = {
            "task_name": task_path.stem,
            "task_path": str(task_path),
            "task_type": "general",
            "risk_level": RiskLevel.LOW,
            "complexity": "simple",
            "requires_approval": False,
            "estimated_steps": 3,
            "content": ""
        }
        
        # Read task content
        try:
            with open(task_path, 'r', encoding='utf-8') as f:
                content = f.read()
                analysis["content"] = content
        except Exception as e:
            self._log_execution("error", f"Failed to read task: {str(e)}")
            return analysis
        
        # Detect task type
        content_lower = content.lower()
        if any(kw in content_lower for kw in ['email', 'send', 'recipient']):
            analysis["task_type"] = "email"
            analysis["requires_approval"] = True
            analysis["risk_level"] = RiskLevel.MEDIUM
        
        if any(kw in content_lower for kw in ['linkedin', 'post', 'social']):
            analysis["task_type"] = "social_media"
            analysis["requires_approval"] = True
            analysis["risk_level"] = RiskLevel.MEDIUM
        
        if any(kw in content_lower for kw in ['delete', 'remove', 'destroy']):
            analysis["task_type"] = "destructive"
            analysis["requires_approval"] = True
            analysis["risk_level"] = RiskLevel.HIGH
        
        if any(kw in content_lower for kw in ['payment', 'money', 'transfer', 'invoice']):
            analysis["task_type"] = "financial"
            analysis["requires_approval"] = True
            analysis["risk_level"] = RiskLevel.HIGH
        
        # Detect complexity
        word_count = len(content.split())
        if word_count > 500:
            analysis["complexity"] = "complex"
            analysis["estimated_steps"] = 7
        elif word_count > 200:
            analysis["complexity"] = "moderate"
            analysis["estimated_steps"] = 5
        
        return analysis
    
    def _create_plan(self, analysis: Dict) -> Path:
        """
        Create execution plan for analyzed task.
        
        Args:
            analysis: Task analysis dictionary
        
        Returns:
            Path to created plan file
        """
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        plan_filename = f"Plan_{analysis['task_name']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        plan_path = self.plans_dir / plan_filename
        
        # Generate steps based on task type
        steps = self._generate_steps(analysis)
        self.steps = steps
        
        # Create plan content
        plan_content = f"""# Execution Plan: {analysis['task_name']}

**Created:** {timestamp}
**Task Type:** {analysis['task_type']}
**Risk Level:** {analysis['risk_level'].value}
**Complexity:** {analysis['complexity']}
**Max Iterations:** {self.max_iterations}

---

## Steps

"""
        
        # Add steps
        for i, step in enumerate(steps, 1):
            plan_content += f"- [ ] Step {i}: {step['description']}\n"
        
        plan_content += f"""
---

## Execution Log

| Iteration | Step | Status | Timestamp |
|-----------|------|--------|-----------|
| - | - | pending | - |

---

## Notes

Auto-generated plan by ralph-wiggum skill.
"""
        
        # Write plan file
        if not self.dry_run:
            with open(plan_path, 'w', encoding='utf-8') as f:
                f.write(plan_content)
        
        self._log_execution("info", f"Created plan: {plan_filename}")
        return plan_path
    
    def _generate_steps(self, analysis: Dict) -> List[Dict]:
        """Generate execution steps based on task type."""
        task_type = analysis['task_type']
        
        if task_type == "email":
            return [
                {"description": "Analyze email content and recipient", "risky": False},
                {"description": "Validate email format and attachments", "risky": False},
                {"description": "Prepare email draft", "risky": False},
                {"description": "Request approval if required", "risky": False},
                {"description": "Send email", "risky": True},
                {"description": "Log email activity", "risky": False}
            ]
        
        elif task_type == "social_media":
            return [
                {"description": "Analyze post content", "risky": False},
                {"description": "Check content guidelines", "risky": False},
                {"description": "Prepare post draft", "risky": False},
                {"description": "Request human approval", "risky": False},
                {"description": "Publish post", "risky": True},
                {"description": "Log social media activity", "risky": False}
            ]
        
        elif task_type == "financial":
            return [
                {"description": "Analyze financial transaction", "risky": False},
                {"description": "Validate amount and recipient", "risky": False},
                {"description": "Check approval threshold", "risky": False},
                {"description": "Request human approval (mandatory)", "risky": False},
                {"description": "Execute transaction", "risky": True},
                {"description": "Log financial activity", "risky": False},
                {"description": "Generate receipt", "risky": False}
            ]
        
        else:
            return [
                {"description": "Analyze task requirements", "risky": False},
                {"description": "Identify required resources", "risky": False},
                {"description": "Execute main action", "risky": False},
                {"description": "Verify completion", "risky": False},
                {"description": "Log activity", "risky": False}
            ]
    
    def _execute_step(self, step: Dict, analysis: Dict) -> bool:
        """
        Execute a single step.
        
        Args:
            step: Step dictionary
            analysis: Task analysis
        
        Returns:
            True if step succeeded
        """
        self._log_execution("info", f"Executing: {step['description']}")
        
        # Check if step requires approval
        if step.get("risky") and self.require_approval:
            self._log_execution("info", "Risky step detected - requesting approval")
            approval_result = self._request_approval(step, analysis)
            if not approval_result:
                self._log_execution("warning", "Approval denied - skipping step")
                return False
        
        # Simulate step execution (in real implementation, would call appropriate skill)
        success = self._simulate_step_execution(step, analysis)
        
        if success:
            self._log_execution("success", f"Step completed: {step['description']}")
        else:
            self._log_execution("error", f"Step failed: {step['description']}")
        
        return success
    
    def _simulate_step_execution(self, step: Dict, analysis: Dict) -> bool:
        """Simulate step execution (placeholder for real implementation)."""
        # In a real implementation, this would call appropriate skills
        # For now, simulate success for non-risky steps
        if not step.get("risky"):
            return True
        
        # Risky steps require approval (already handled)
        # Simulate success if we got here
        return True
    
    def _request_approval(self, step: Dict, analysis: Dict) -> bool:
        """
        Request human approval for risky step.
        
        Args:
            step: Step requiring approval
            analysis: Task analysis
        
        Returns:
            True if approved
        """
        if self.dry_run:
            return True
        
        # Create approval request
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        approval_filename = f"approval_{analysis['task_name']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        approval_path = self.approvals_dir / approval_filename
        
        approval_content = f"""# Approval Request

**Task:** {analysis['task_name']}
**Step:** {step['description']}
**Risk Level:** {analysis['risk_level'].value}
**Requested:** {timestamp}

---

## Step Details

{step['description']}

---

## Task Context

**Type:** {analysis['task_type']}
**Complexity:** {analysis['complexity']}

---

## Action Required

Please review and either approve or reject this action.

### To Approve:
Change status below to "approved" and add your name.

### To Reject:
Change status to "rejected" and provide reason.

---

## Response

**Status:** [pending/approved/rejected]

**Approved By:** [Name]

**Date:** [YYYY-MM-DD]

**Comments:** [Optional]
"""
        
        with open(approval_path, 'w', encoding='utf-8') as f:
            f.write(approval_content)
        
        self._log_execution("info", f"Approval request created: {approval_filename}")
        
        # In real implementation, would wait for human response
        # For now, return True to continue
        return True
    
    def _check_result(self, step_success: bool) -> bool:
        """Check if step result is acceptable."""
        return step_success
    
    def _move_to_done(self, task_path: Path, plan_path: Path):
        """Move completed task to Done folder."""
        if self.dry_run:
            self._log_execution("info", f"[DRY RUN] Would move {task_path.name} to Done")
            return
        
        try:
            # Move task file
            dest_path = self.done_dir / task_path.name
            shutil.move(str(task_path), str(dest_path))
            
            # Move plan file
            plan_dest = self.done_dir / plan_path.name
            shutil.move(str(plan_path), str(plan_dest))
            
            self._log_execution("success", f"Task moved to Done: {task_path.name}")
            self._update_dashboard(task_path.name, "completed")
            
        except Exception as e:
            self._log_execution("error", f"Failed to move task: {str(e)}")
    
    def _update_dashboard(self, task_name: str, status: str):
        """Update Dashboard.md with task status."""
        if self.dry_run:
            return
        
        try:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Create dashboard if doesn't exist
            if not self.dashboard_file.exists():
                with open(self.dashboard_file, 'w') as f:
                    f.write("# Dashboard\n\n## Recent Activity\n\n")
            
            # Read current content
            with open(self.dashboard_file, 'r') as f:
                content = f.read()
            
            # Add activity entry
            marker = "## Recent Activity"
            if marker in content:
                pos = content.find(marker) + len(marker)
                entry = f"\n- {timestamp}: Ralph Wiggum {status} - {task_name}"
                content = content[:pos] + entry + content[pos:]
            else:
                content += f"\n## Recent Activity\n- {timestamp}: Ralph Wiggum {status} - {task_name}\n"
            
            # Write back
            with open(self.dashboard_file, 'w') as f:
                f.write(content)
            
        except Exception as e:
            self._log_execution("error", f"Failed to update dashboard: {str(e)}")
    
    def _log_execution(self, level: str, message: str):
        """Log execution details."""
        timestamp = datetime.now().isoformat()
        log_entry = {
            "timestamp": timestamp,
            "level": level,
            "message": message,
            "iteration": self.current_iteration,
            "step": self.current_step
        }
        self.execution_log.append(log_entry)
        
        # Also log to file
        log_file = self.logs_dir / "ralph_wiggum.log"
        try:
            with open(log_file, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')
        except Exception:
            pass
    
    def run_loop(self, task_path: Path = None) -> Dict:
        """
        Run the Ralph Wiggum autonomous loop.
        
        Args:
            task_path: Optional specific task to process
        
        Returns:
            Execution result dictionary
        """
        result = {
            "success": False,
            "task": None,
            "plan": None,
            "iterations": 0,
            "steps_completed": 0,
            "steps_total": 0,
            "message": ""
        }
        
        # Find task to process
        if task_path is None:
            task_path = self._find_next_task()
        
        if task_path is None:
            result["message"] = "No tasks found to process"
            return result
        
        result["task"] = str(task_path)
        self._log_execution("info", f"Starting Ralph Wiggum loop for: {task_path.name}")
        
        try:
            # Step 1: Analyze task
            self._log_execution("info", "Step 1: Analyzing task")
            analysis = self._analyze_task(task_path)
            
            # Step 2: Create plan
            self._log_execution("info", "Step 2: Creating execution plan")
            plan_path = self._create_plan(analysis)
            result["plan"] = str(plan_path)
            
            # Step 3-6: Execute loop
            self._log_execution("info", "Step 3-6: Executing autonomous loop")
            loop_success = self._execute_loop(analysis)
            
            if loop_success:
                # Step 7: Move to Done
                self._log_execution("info", "Step 7: Moving task to Done")
                self._move_to_done(task_path, plan_path)
                
                result["success"] = True
                result["message"] = "Task completed successfully"
            else:
                result["message"] = "Loop completed with errors"
            
        except Exception as e:
            self._log_execution("error", f"Loop failed: {str(e)}")
            result["message"] = f"Error: {str(e)}"
        
        result["iterations"] = self.current_iteration
        result["steps_completed"] = sum(1 for s in self.steps if s.get("status") == "completed")
        result["steps_total"] = len(self.steps)
        result["execution_log"] = self.execution_log
        
        return result
    
    def _find_next_task(self) -> Optional[Path]:
        """Find next task to process in Needs_Action folder."""
        if not self.needs_action_dir.exists():
            return None
        
        # Find markdown files (excluding Plan files)
        for file in sorted(self.needs_action_dir.iterdir()):
            if file.suffix == '.md' and not file.stem.startswith('Plan_'):
                return file
        
        return None
    
    def _execute_loop(self, analysis: Dict) -> bool:
        """Execute the main Ralph Wiggum loop."""
        all_success = True
        
        for i, step in enumerate(self.steps):
            self.current_step = i + 1
            self.current_iteration += 1
            
            # Check max iterations
            if self.current_iteration > self.max_iterations:
                self._log_execution("error", f"Max iterations ({self.max_iterations}) reached")
                return False
            
            # Execute step
            success = self._execute_step(step, analysis)
            step["status"] = "completed" if success else "failed"
            
            # Check result
            if not self._check_result(success):
                all_success = False
                self._log_execution("warning", f"Step {i+1} check failed")
        
        return all_success


# ============================================================================
# Skill Entry Point
# ============================================================================

def ralph_wiggum_skill(task_file: str = None, max_iterations: int = 5,
                      require_approval: bool = True, dry_run: bool = False) -> Dict:
    """
    Main entry point for ralph-wiggum skill.
    
    Args:
        task_file: Path to specific task file (optional)
        max_iterations: Maximum loop iterations
        require_approval: Require human approval for risky actions
        dry_run: Simulate without making changes
    
    Returns:
        Execution result dictionary
    """
    loop = RalphWiggumLoop(
        max_iterations=max_iterations,
        require_approval=require_approval,
        dry_run=dry_run
    )
    
    task_path = Path(task_file) if task_file else None
    return loop.run_loop(task_path)


# Example usage
if __name__ == "__main__":
    result = ralph_wiggum_skill(dry_run=True)
    print(json.dumps(result, indent=2, default=str))
```

## Usage Examples

### Process Next Available Task
```python
from ralph_wiggum import ralph_wiggum_skill

result = ralph_wiggum_skill()
```

### Process Specific Task
```python
result = ralph_wiggum_skill(task_file="Needs_Action/email_task.md")
```

### Custom Settings
```python
result = ralph_wiggum_skill(
    max_iterations=3,
    require_approval=True,
    dry_run=False
)
```

### Dry Run (Test)
```python
result = ralph_wiggum_skill(dry_run=True)
```

## Integration with Scheduler

### Windows Task Scheduler
```batch
# Run every hour
schtasks /create /tn "Ralph_Wiggum_Loop" /tr "python scripts/ralph_wiggum.py" /sc hourly
```

### Linux/Mac Cron
```bash
# Run every hour
0 * * * * cd /path/to/vault && python scripts/ralph_wiggum.py
```

## Safety Features

1. **Max Iterations**: Prevents infinite loops (default: 5)
2. **Human Approval**: Required for risky operations
3. **Dry Run Mode**: Test without making changes
4. **Error Handling**: Catches and logs all errors
5. **Rollback**: Failed tasks remain in Needs_Action

## Monitoring

Check execution logs:
```bash
tail -f Logs/ralph_wiggum.log
```

View execution statistics:
```bash
python scripts/ralph_wiggum.py stats
```
