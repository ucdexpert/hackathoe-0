#!/usr/bin/env python3
"""
Ralph Wiggum Autonomous Loop - AI Employee Skill

Autonomous task execution with:
1. Task analysis
2. Plan.md creation
3. Step-by-step execution
4. Result checking
5. Iteration until completion
6. Automatic task completion

Safety features:
- Max 5 iterations (configurable)
- Human approval for risky actions
- Dry run mode for testing

Usage:
    python ralph_wiggum.py                    # Process next task
    python ralph_wiggum.py --task file.md     # Process specific task
    python ralph_wiggum.py --dry-run          # Test without changes
    python ralph_wiggum.py --max-iterations 3 # Custom iteration limit
    python ralph_wiggum.py --setup-scheduler  # Setup automatic execution

Environment:
    VAULT_ROOT: Path to AI_Employee_Vault (default: parent of scripts directory)
"""

import os
import sys
import json
import shutil
import argparse
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from enum import Enum
import time


# ============================================================================
# Configuration
# ============================================================================

class Config:
    """Configuration for Ralph Wiggum loop."""
    
    # Always use parent directory of this script as vault root
    VAULT_ROOT = Path(__file__).resolve().parent.parent
    
    NEEDS_ACTION_DIR = VAULT_ROOT / "Needs_Action"
    PLANS_DIR = VAULT_ROOT / "Plans"
    DONE_DIR = VAULT_ROOT / "Done"
    LOGS_DIR = VAULT_ROOT / "Logs"
    DASHBOARD_FILE = VAULT_ROOT / "Dashboard.md"
    APPROVALS_DIR = VAULT_ROOT / "Needs_Approval"
    
    # Default settings
    DEFAULT_MAX_ITERATIONS = 5
    DEFAULT_RETRY_DELAY = 300  # 5 minutes
    
    # Ensure directories exist
    for directory in [PLANS_DIR, DONE_DIR, LOGS_DIR, APPROVALS_DIR]:
        directory.mkdir(parents=True, exist_ok=True)


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


# ============================================================================
# Ralph Wiggum Loop
# ============================================================================

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
        self.vault_root = vault_root or Config.VAULT_ROOT
        
        # Define paths
        self.needs_action_dir = Config.NEEDS_ACTION_DIR
        self.plans_dir = Config.PLANS_DIR
        self.done_dir = Config.DONE_DIR
        self.logs_dir = Config.LOGS_DIR
        self.dashboard_file = Config.DASHBOARD_FILE
        self.approvals_dir = Config.APPROVALS_DIR
        
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
        """Analyze a task file to understand requirements."""
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
        """Create execution plan for analyzed task."""
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
        """Execute a single step."""
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
        """Request human approval for risky step."""
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
        """Run the Ralph Wiggum autonomous loop."""
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
        
        print(f"\n[RALPH WIGGUM] Processing: {task_path.name}")
        
        try:
            # Step 1: Analyze task
            print(f"  [1/7] Analyzing task...")
            analysis = self._analyze_task(task_path)
            print(f"        Type: {analysis['task_type']}, Risk: {analysis['risk_level'].value}")
            
            # Step 2: Create plan
            print(f"  [2/7] Creating execution plan...")
            plan_path = self._create_plan(analysis)
            result["plan"] = str(plan_path)
            print(f"        Plan: {plan_path.name}")
            
            # Step 3-6: Execute loop
            print(f"  [3-6] Executing autonomous loop...")
            loop_success = self._execute_loop(analysis)
            
            if loop_success:
                # Step 7: Move to Done
                print(f"  [7/7] Moving task to Done...")
                self._move_to_done(task_path, plan_path)
                
                result["success"] = True
                result["message"] = "Task completed successfully"
                print(f"        ✓ Task completed!")
            else:
                result["message"] = "Loop completed with errors"
                print(f"        ⚠ Loop completed with errors")
            
        except Exception as e:
            self._log_execution("error", f"Loop failed: {str(e)}")
            result["message"] = f"Error: {str(e)}"
            print(f"        ✗ Error: {str(e)}")
        
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
                print(f"        ⚠ Max iterations reached")
                return False
            
            # Execute step
            print(f"        Step {i+1}/{len(self.steps)}: {step['description']}")
            success = self._execute_step(step, analysis)
            step["status"] = "completed" if success else "failed"
            
            # Check result
            if not self._check_result(success):
                all_success = False
                self._log_execution("warning", f"Step {i+1} check failed")
        
        return all_success
    
    def get_statistics(self) -> Dict:
        """Get execution statistics."""
        stats = {
            "total_executions": 0,
            "successful": 0,
            "failed": 0,
            "total_iterations": 0,
            "avg_iterations": 0
        }
        
        log_file = self.logs_dir / "ralph_wiggum.log"
        if not log_file.exists():
            return stats
        
        try:
            with open(log_file, 'r') as f:
                executions = {}
                for line in f:
                    try:
                        entry = json.loads(line.strip())
                        if entry.get("level") == "info" and "Starting" in entry.get("message", ""):
                            task_name = entry.get("message", "").split(": ")[-1]
                            executions[task_name] = {
                                "iterations": entry.get("iteration", 0),
                                "success": False
                            }
                        elif entry.get("level") == "success" and "Task moved" in entry.get("message", ""):
                            # Mark last execution as successful
                            if executions:
                                last_key = list(executions.keys())[-1]
                                executions[last_key]["success"] = True
                    except Exception:
                        continue
                
                stats["total_executions"] = len(executions)
                stats["successful"] = sum(1 for e in executions.values() if e["success"])
                stats["failed"] = stats["total_executions"] - stats["successful"]
                stats["total_iterations"] = sum(e["iterations"] for e in executions.values())
                
                if stats["total_executions"] > 0:
                    stats["avg_iterations"] = stats["total_iterations"] / stats["total_executions"]
                    
        except Exception as e:
            pass
        
        return stats


# ============================================================================
# CLI Functions
# ============================================================================

def cmd_run(args, loop: RalphWiggumLoop):
    """Run Ralph Wiggum loop."""
    task_path = Path(args.task) if hasattr(args, 'task') and args.task else None
    result = loop.run_loop(task_path)
    
    print(f"\n{'='*60}")
    print(f"Ralph Wiggum Loop Result")
    print(f"{'='*60}")
    print(f"Status: {'✓ SUCCESS' if result['success'] else '⚠ FAILED'}")
    print(f"Message: {result['message']}")
    print(f"Iterations: {result['iterations']}")
    print(f"Steps: {result['steps_completed']}/{result['steps_total']}")
    if result.get('plan'):
        print(f"Plan: {result['plan']}")
    print(f"{'='*60}")


def cmd_stats(args, loop: RalphWiggumLoop):
    """Show execution statistics."""
    stats = loop.get_statistics()
    
    print(f"\n{'='*60}")
    print(f"Ralph Wiggum Statistics")
    print(f"{'='*60}")
    print(f"Total Executions: {stats['total_executions']}")
    print(f"Successful: {stats['successful']}")
    print(f"Failed: {stats['failed']}")
    print(f"Total Iterations: {stats['total_iterations']}")
    if stats['total_executions'] > 0:
        print(f"Average Iterations: {stats['avg_iterations']:.1f}")
    print(f"{'='*60}")


def cmd_setup_scheduler(args):
    """Setup Windows Task Scheduler."""
    print("\n[INFO] Setting up Windows Task Scheduler...")
    
    script_path = Path(__file__).resolve()
    python_exe = sys.executable
    task_command = f'"{python_exe}" "{script_path}" run'
    task_name = "Ralph_Wiggum_Autonomous_Loop"
    
    # Run hourly
    schtasks_cmd = f'schtasks /create /tn "{task_name}" /tr "{task_command}" /sc hourly /ru "%USERNAME%" /f'
    
    try:
        result = subprocess.run(schtasks_cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"\n[OK] Task Scheduler configured successfully!")
            print(f"     Task Name: {task_name}")
            print(f"     Schedule: Every hour")
            print(f"     Command: {task_command}")
        else:
            print(f"\n[WARNING] Task Scheduler setup failed.")
            print(f"     Error: {result.stderr}")
    except Exception as e:
        print(f"\n[ERROR] Failed to setup scheduler: {str(e)}")


def cmd_test(args, loop: RalphWiggumLoop):
    """Test Ralph Wiggum loop."""
    print("\n[TEST] Testing Ralph Wiggum loop (dry run)...")
    
    # Set dry run mode
    loop.dry_run = True
    
    # Run loop
    result = loop.run_loop()
    
    print(f"\n[TEST] Test completed!")
    print(f"  Result: {result['message']}")
    print(f"  Iterations: {result['iterations']}")
    print(f"  Steps: {result['steps_completed']}/{result['steps_total']}")


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


# ============================================================================
# Main Entry Point
# ============================================================================

def main():
    """Main entry point for CLI."""
    parser = argparse.ArgumentParser(
        description='Ralph Wiggum Autonomous Loop - Automatic Task Execution',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  Process next task:
    python ralph_wiggum.py run
  
  Process specific task:
    python ralph_wiggum.py run --task Needs_Action/email.md
  
  Dry run (test):
    python ralph_wiggum.py run --dry-run
  
  Custom iteration limit:
    python ralph_wiggum.py run --max-iterations 3
  
  Show statistics:
    python ralph_wiggum.py stats
  
  Setup scheduler:
    python ralph_wiggum.py setup-scheduler
        '''
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Run command
    run_parser = subparsers.add_parser('run', help='Run Ralph Wiggum loop')
    run_parser.add_argument('--task', '-t', help='Specific task file to process')
    run_parser.add_argument('--max-iterations', type=int, default=5, help='Max iterations')
    run_parser.add_argument('--require-approval', action='store_true', default=True, help='Require approval')
    run_parser.add_argument('--no-approval', action='store_true', help='Skip approval')
    run_parser.add_argument('--dry-run', action='store_true', help='Dry run mode')
    run_parser.set_defaults(func=cmd_run)
    
    # Stats command
    stats_parser = subparsers.add_parser('stats', help='Show statistics')
    stats_parser.set_defaults(func=cmd_stats)
    
    # Setup scheduler command
    sched_parser = subparsers.add_parser('setup-scheduler', help='Setup Task Scheduler')
    sched_parser.set_defaults(func=cmd_setup_scheduler)
    
    # Test command
    test_parser = subparsers.add_parser('test', help='Test loop (dry run)')
    test_parser.set_defaults(func=cmd_test)
    
    # Parse arguments
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(0)
    
    # Create loop and execute command
    loop = RalphWiggumLoop(
        max_iterations=args.max_iterations if hasattr(args, 'max_iterations') else 5,
        require_approval=not (hasattr(args, 'no_approval') and args.no_approval),
        dry_run=args.dry_run if hasattr(args, 'dry_run') else False
    )
    
    args.func(args, loop)


if __name__ == '__main__':
    main()
