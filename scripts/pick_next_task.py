#!/usr/bin/env python3
"""
Script to pick up the next task from SPECS/Workplan.md

This script parses the workplan, tracks completed tasks, and recommends
the next task to work on based on priority and dependencies.
"""

import json
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class Task:
    """Represents a workplan task."""
    id: str
    description: str
    phase: str
    priority: str  # P0, P1, P2, P3
    dependencies: list[str] = field(default_factory=list)
    outputs: list[str] = field(default_factory=list)
    acceptance_criteria: str = ""
    raw_text: str = ""
    completed_in_workplan: bool = False

    @property
    def priority_value(self) -> int:
        """Return numeric priority (lower = higher priority)."""
        return int(self.priority[1]) if self.priority.startswith('P') else 99

    @property
    def phase_number(self) -> int:
        """Extract phase number from phase name like 'Phase 1'."""
        match = re.search(r'\d+', self.phase)
        return int(match.group()) if match else 999


def parse_workplan(workplan_path: Path) -> list[Task]:
    """Parse the workplan markdown file and extract all tasks."""
    content = workplan_path.read_text()
    lines = content.splitlines()
    tasks: list[Task] = []

    task_id_pattern = r'(?:P\d+-T\d+(?:\.\d+)?|BUG-T\d+|FU-[A-Z0-9-]+|REBUILD-[A-Z0-9-]+)'
    # Keep canonical phase labels (e.g., "Phase 1") and ignore descriptive suffixes.
    phase_re = re.compile(r'^###\s+(Phase \d+)(?::[^\n]+)?$')
    header_task_re = re.compile(rf'^####\s+(✅\s+)?({task_id_pattern}):\s+(.+)$')
    checklist_task_re = re.compile(rf'^-\s+\[(x|X| )\]\s+({task_id_pattern}):\s+(.+)$')

    current_phase = "Uncategorized"
    seen_ids: set[str] = set()
    i = 0
    while i < len(lines):
        line = lines[i].rstrip()

        phase_match = phase_re.match(line)
        if phase_match:
            current_phase = phase_match.group(1)
            i += 1
            continue

        header_match = header_task_re.match(line.strip())
        checklist_match = checklist_task_re.match(line.strip())
        if not header_match and not checklist_match:
            i += 1
            continue

        if header_match:
            completed_in_workplan = bool(header_match.group(1))
            task_id = header_match.group(2)
            title = header_match.group(3).strip()
            raw_text = line.strip()
        else:
            completed_in_workplan = checklist_match.group(1).lower() == 'x'
            task_id = checklist_match.group(2)
            title = checklist_match.group(3).strip()
            raw_text = line.strip()

        if task_id in seen_ids:
            i += 1
            continue
        seen_ids.add(task_id)

        priority = "P2"
        priority_in_title = re.search(r'\((P\d)\)\s*$', title)
        if priority_in_title:
            priority = priority_in_title.group(1)
            title = re.sub(r'\s*\(P\d\)\s*$', '', title).strip()

        description = title
        dependencies: list[str] = []
        acceptance_criteria = ""

        # Parse metadata lines until next phase/task header.
        j = i + 1
        while j < len(lines):
            next_line = lines[j].strip()
            if phase_re.match(next_line) or header_task_re.match(next_line) or checklist_task_re.match(next_line):
                break

            normalized = next_line.replace('**', '')
            if normalized.startswith('- Description:') or normalized.startswith('Description:'):
                desc_text = normalized.split(':', 1)[1].strip()
                if desc_text:
                    description = desc_text
            elif normalized.startswith('- Priority:') or normalized.startswith('Priority:'):
                priority_match = re.search(r'P\d+', normalized)
                if priority_match:
                    priority = priority_match.group()
            elif normalized.startswith('- Dependencies:') or normalized.startswith('Dependencies:'):
                dep_text = normalized.split(':', 1)[1].strip()
                if dep_text and dep_text.lower() not in ('none', ''):
                    dependencies = [d.strip() for d in dep_text.split(',')]
            elif normalized.startswith('- Acceptance Criteria:'):
                acceptance_criteria = normalized.split(':', 1)[1].strip()

            j += 1

        tasks.append(
            Task(
                id=task_id,
                description=description,
                phase=current_phase,
                priority=priority,
                dependencies=dependencies,
                acceptance_criteria=acceptance_criteria,
                raw_text=raw_text,
                completed_in_workplan=completed_in_workplan,
            )
        )
        i = j

    return tasks


def get_completed_tasks(state_file: Path) -> set[str]:
    """Load the set of completed task IDs."""
    if not state_file.exists():
        return set()
    
    try:
        data = json.loads(state_file.read_text())
        return set(data.get('completed', []))
    except (json.JSONDecodeError, KeyError):
        return set()


def save_completed_tasks(state_file: Path, completed: set[str]) -> None:
    """Save the set of completed task IDs."""
    state_file.parent.mkdir(parents=True, exist_ok=True)
    state_file.write_text(json.dumps({'completed': sorted(completed)}, indent=2))


def get_effective_completed(tasks: list[Task], state_completed: set[str]) -> set[str]:
    """Merge completion from workplan checkmarks and persisted state."""
    workplan_completed = {task.id for task in tasks if task.completed_in_workplan}
    return state_completed | workplan_completed


def find_next_task(tasks: list[Task], completed: set[str]) -> Optional[Task]:
    """Find the next available task based on priority and dependencies."""
    available_tasks = []
    
    for task in tasks:
        if task.id in completed:
            continue
        
        # Check if all dependencies are completed
        deps_satisfied = all(
            dep in completed or dep not in [t.id for t in tasks]
            for dep in task.dependencies
        )
        
        if deps_satisfied:
            available_tasks.append(task)
    
    if not available_tasks:
        return None
    
    # Sort by: phase number, then priority, then task ID
    available_tasks.sort(key=lambda t: (t.phase_number, t.priority_value, t.id))
    
    return available_tasks[0]


def format_task_output(task: Task, all_tasks: list[Task], completed: set[str]) -> str:
    """Format the task for display."""
    # Find blocking dependencies
    blocking = [dep for dep in task.dependencies if dep not in completed]
    
    lines = [
        f"{'=' * 70}",
        f"NEXT TASK: {task.id}",
        f"{'=' * 70}",
        f"",
        f"Phase: {task.phase}",
        f"Priority: {task.priority}",
        f"",
        f"Description: {task.description}",
        f"",
    ]
    
    if task.dependencies:
        lines.append(f"Dependencies:")
        for dep in task.dependencies:
            status = "✓ DONE" if dep in completed else "⏳ PENDING"
            lines.append(f"  - {dep} [{status}]")
        lines.append("")
    
    if blocking:
        lines.append(f"⚠️  WARNING: {len(blocking)} blocking dependencies not yet completed")
        lines.append("")
    
    if task.acceptance_criteria:
        lines.append(f"Acceptance Criteria: {task.acceptance_criteria}")
        lines.append("")
    
    # Show progress
    total = len(all_tasks)
    done = len(completed)
    pct = (done / total * 100) if total > 0 else 0
    lines.append(f"Progress: {done}/{total} tasks completed ({pct:.1f}%)")
    lines.append(f"{'=' * 70}")
    
    return '\n'.join(lines)


def mark_task_done(state_file: Path, task_id: str, workplan_path: Path = Path('SPECS/Workplan.md')) -> bool:
    """Mark a task as completed."""
    completed = get_completed_tasks(state_file)
    
    # Validate task exists in workplan
    if not workplan_path.exists():
        print(f"Error: Workplan not found at {workplan_path}", file=sys.stderr)
        return False
    
    tasks = parse_workplan(workplan_path)
    task_ids = {t.id for t in tasks}
    
    if task_id not in task_ids:
        print(f"Error: Task '{task_id}' not found in workplan", file=sys.stderr)
        print(f"Valid task IDs: {', '.join(sorted(task_ids))}", file=sys.stderr)
        return False
    
    if task_id in completed:
        print(f"Task {task_id} is already marked as done")
        return True
    
    completed.add(task_id)
    save_completed_tasks(state_file, completed)
    print(f"✓ Marked {task_id} as completed")
    return True


def show_progress(tasks: list[Task], completed: set[str]) -> None:
    """Show overall progress by phase."""
    print(f"\n{'=' * 70}")
    print("OVERALL PROGRESS")
    print(f"{'=' * 70}\n")
    
    # Group by phase
    phases = {}
    for task in tasks:
        phase = task.phase
        if phase not in phases:
            phases[phase] = []
        phases[phase].append(task)
    
    total_done = 0
    total_tasks = len(tasks)
    
    for phase_name in sorted(
        phases.keys(),
        key=lambda p: int(re.search(r'\d+', p).group()) if re.search(r'\d+', p) else 999,
    ):
        phase_tasks = phases[phase_name]
        phase_done = sum(1 for t in phase_tasks if t.id in completed)
        total_done += phase_done
        
        p0_total = sum(1 for t in phase_tasks if t.priority == 'P0')
        p0_done = sum(1 for t in phase_tasks if t.priority == 'P0' and t.id in completed)
        
        pct = (phase_done / len(phase_tasks) * 100) if phase_tasks else 0
        bar_length = 30
        filled = int(bar_length * phase_done / len(phase_tasks)) if phase_tasks else 0
        bar = '█' * filled + '░' * (bar_length - filled)
        
        print(f"{phase_name:15} |{bar}| {phase_done}/{len(phase_tasks)} ({pct:.0f}%)")
        if p0_total > 0:
            print(f"{'':15}   P0: {p0_done}/{p0_total} done")
    
    print(f"\n{'=' * 70}")
    total_pct = (total_done / total_tasks * 100) if total_tasks else 0
    print(f"TOTAL: {total_done}/{total_tasks} tasks ({total_pct:.1f}%)")
    print(f"{'=' * 70}\n")


def list_tasks(tasks: list[Task], completed: set[str], phase_filter: Optional[str] = None) -> None:
    """List all tasks with their status."""
    print(f"\n{'=' * 70}")
    print("ALL TASKS")
    print(f"{'=' * 70}\n")
    
    for task in sorted(tasks, key=lambda t: (t.phase_number, t.priority_value, t.id)):
        if phase_filter and phase_filter.lower() not in task.phase.lower():
            continue
        
        status = "✓ DONE" if task.id in completed else "⏳ TODO"
        deps_ok = all(d in completed for d in task.dependencies) if task.dependencies else True
        blocked = " [BLOCKED]" if not deps_ok and task.id not in completed else ""
        
        print(f"{status} {task.id:10} [{task.priority}] {task.description[:50]}{blocked}")
    
    print()


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Pick the next task from the workplan',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                    # Show the next recommended task
  %(prog)s --done P1-T1       # Mark a task as completed
  %(prog)s --progress         # Show overall progress
  %(prog)s --list             # List all tasks
  %(prog)s --list --phase 1   # List Phase 1 tasks only
        """
    )
    
    parser.add_argument('--done', metavar='TASK_ID',
                        help='Mark a task as completed (e.g., P1-T1)')
    parser.add_argument('--progress', action='store_true',
                        help='Show overall progress summary')
    parser.add_argument('--list', action='store_true',
                        help='List all tasks')
    parser.add_argument('--phase', type=str,
                        help='Filter by phase number (e.g., 1, 2)')
    parser.add_argument('--workplan', type=Path, default=Path('SPECS/Workplan.md'),
                        help='Path to workplan file (default: SPECS/Workplan.md)')
    parser.add_argument('--state', type=Path, default=Path('.task_state.json'),
                        help='Path to state file (default: .task_state.json)')
    
    args = parser.parse_args()
    
    # Handle mark done
    if args.done:
        success = mark_task_done(args.state, args.done, args.workplan)
        sys.exit(0 if success else 1)
    
    # Parse workplan
    if not args.workplan.exists():
        print(f"Error: Workplan not found at {args.workplan}", file=sys.stderr)
        print("Make sure you're running from the project root.", file=sys.stderr)
        sys.exit(1)
    
    tasks = parse_workplan(args.workplan)
    if not tasks:
        print("Error: No tasks found in workplan", file=sys.stderr)
        sys.exit(1)
    
    state_completed = get_completed_tasks(args.state)
    completed = get_effective_completed(tasks, state_completed)
    
    # Handle list
    if args.list:
        list_tasks(tasks, completed, args.phase)
        sys.exit(0)
    
    # Handle progress
    if args.progress:
        show_progress(tasks, completed)
        sys.exit(0)
    
    # Default: show next task
    next_task = find_next_task(tasks, completed)
    
    if next_task is None:
        print(f"{'=' * 70}")
        print("🎉 ALL TASKS COMPLETED!")
        print(f"{'=' * 70}")
        print(f"\n{len(tasks)}/{len(tasks)} tasks done (100.0%)")
        sys.exit(0)
    
    print(format_task_output(next_task, tasks, completed))
    
    # Also save the current task suggestion for reference
    suggestion_file = args.state.parent / '.current_task'
    suggestion_file.write_text(f"{next_task.id}: {next_task.description}\n")


if __name__ == '__main__':
    main()
