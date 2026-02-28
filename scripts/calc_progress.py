#!/usr/bin/env python3
"""
Calculate progress from SPECS/Workplan.md

Usage:
    python scripts/calc_progress.py              # Show overall progress
    python scripts/calc_progress.py --phase P1   # Show Phase 1 tasks
    python scripts/calc_progress.py --todo       # List pending tasks
    python scripts/calc_progress.py --markdown   # Output as markdown
    python scripts/calc_progress.py --json       # Output as JSON
"""

import re
import sys
from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional

EMPTY_CYCLE_MARKER = "intentionally reset for the next planning cycle"


@dataclass
class Task:
    id: str
    title: str
    priority: str
    phase: str
    dependencies: List[str]
    parallelizable: bool
    completed: bool = False


def clean_value(text: str) -> str:
    """Remove markdown bold markers and strip whitespace."""
    return text.replace('**', '').strip()


def parse_workplan(filepath: Path) -> List[Task]:
    """Parse workplan markdown and extract tasks."""
    content = filepath.read_text()
    lines = content.split('\n')
    tasks = []
    current_phase = ""
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Track current phase
        phase_match = re.match(r'### Phase (\d+):', line)
        if phase_match:
            current_phase = f"P{phase_match.group(1)}"
        
        # Parse task header
        task_match = re.match(r'#### (P\d+-T\d+): (.+)', line)
        if task_match and current_phase:
            task_id = task_match.group(1)
            title = task_match.group(2)
            
            # Parse task details from following lines
            j = i + 1
            priority = ""
            dependencies = []
            parallelizable = False
            
            while j < len(lines) and not lines[j].startswith('#### ') and not lines[j].startswith('### '):
                l = lines[j]
                if l.startswith('- **Description:**'):
                    pass  # Skip for now
                elif l.startswith('- **Priority:**'):
                    priority = clean_value(l.split(':', 1)[1])
                elif l.startswith('- **Dependencies:**'):
                    deps_str = clean_value(l.split(':', 1)[1])
                    if deps_str.lower() != 'none':
                        dependencies = [clean_value(d) for d in deps_str.split(',')]
                elif l.startswith('- **Parallelizable:**'):
                    parallelizable = 'yes' in l.lower()
                elif l.startswith('- **Acceptance Criteria:**'):
                    # Last field we care about, can stop here
                    break
                j += 1
            
            tasks.append(Task(
                id=task_id,
                title=title,
                priority=priority,
                phase=current_phase,
                dependencies=dependencies,
                parallelizable=parallelizable,
                completed=False
            ))
            
            i = j
        else:
            i += 1
    
    return tasks


def is_intentionally_empty_workplan(filepath: Path) -> bool:
    """Return True when workplan is a deliberate empty-cycle placeholder."""
    try:
        content = filepath.read_text().lower()
    except OSError:
        return False
    return EMPTY_CYCLE_MARKER in content


def empty_progress() -> dict:
    """Return a zeroed progress payload for empty planning cycles."""
    return {
        'total': 0,
        'completed': 0,
        'pending': 0,
        'percent': 0.0,
        'by_priority': {
            'P0': {'total': 0, 'completed': 0},
            'P1': {'total': 0, 'completed': 0},
            'P2': {'total': 0, 'completed': 0},
            'P3': {'total': 0, 'completed': 0},
        },
        'by_phase': {},
    }


def calculate_progress(tasks: List[Task]) -> dict:
    """Calculate progress statistics."""
    if not tasks:
        return {}
    
    total = len(tasks)
    completed = sum(1 for t in tasks if t.completed)
    by_priority = {'P0': [], 'P1': [], 'P2': [], 'P3': []}
    by_phase = {}
    
    for task in tasks:
        by_priority.setdefault(task.priority, []).append(task)
        by_phase.setdefault(task.phase, []).append(task)
    
    return {
        'total': total,
        'completed': completed,
        'pending': total - completed,
        'percent': (completed / total * 100) if total > 0 else 0,
        'by_priority': {
            p: {
                'total': len(by_priority.get(p, [])),
                'completed': sum(1 for t in by_priority.get(p, []) if t.completed),
            }
            for p in ['P0', 'P1', 'P2', 'P3']
        },
        'by_phase': {
            phase: {
                'total': len(tasks_list),
                'completed': sum(1 for t in tasks_list if t.completed),
            }
            for phase, tasks_list in sorted(by_phase.items())
        }
    }


def format_progress(progress: dict, markdown: bool = False) -> str:
    """Format progress as text or markdown."""
    lines = []
    
    if markdown:
        lines.append("# Progress Report")
        lines.append("")
        lines.append(f"**Overall:** {progress['completed']}/{progress['total']} tasks ({progress['percent']:.1f}%)")
        lines.append("")
        lines.append("## By Priority")
        lines.append("")
        lines.append("| Priority | Completed | Total | Percent |")
        lines.append("|----------|-----------|-------|---------|")
        for p in ['P0', 'P1', 'P2', 'P3']:
            data = progress['by_priority'][p]
            pct = (data['completed'] / data['total'] * 100) if data['total'] > 0 else 0
            lines.append(f"| {p} | {data['completed']} | {data['total']} | {pct:.1f}% |")
        lines.append("")
        lines.append("## By Phase")
        lines.append("")
        lines.append("| Phase | Completed | Total | Percent |")
        lines.append("|-------|-----------|-------|---------|")
        for phase, data in progress['by_phase'].items():
            pct = (data['completed'] / data['total'] * 100) if data['total'] > 0 else 0
            lines.append(f"| {phase} | {data['completed']} | {data['total']} | {pct:.1f}% |")
    else:
        lines.append("=" * 50)
        lines.append("WORKPLAN PROGRESS")
        lines.append("=" * 50)
        lines.append("")
        lines.append(f"Overall: {progress['completed']}/{progress['total']} tasks ({progress['percent']:.1f}%)")
        lines.append("")
        lines.append("By Priority:")
        for p in ['P0', 'P1', 'P2', 'P3']:
            data = progress['by_priority'][p]
            pct = (data['completed'] / data['total'] * 100) if data['total'] > 0 else 0
            bar = '█' * int(pct / 10) + '░' * (10 - int(pct / 10))
            lines.append(f"  {p}: {bar} {data['completed']}/{data['total']} ({pct:.1f}%)")
        lines.append("")
        lines.append("By Phase:")
        for phase, data in progress['by_phase'].items():
            pct = (data['completed'] / data['total'] * 100) if data['total'] > 0 else 0
            bar = '█' * int(pct / 10) + '░' * (10 - int(pct / 10))
            lines.append(f"  {phase}: {bar} {data['completed']}/{data['total']} ({pct:.1f}%)")
    
    return '\n'.join(lines)


def list_tasks(tasks: List[Task], phase: Optional[str] = None, pending_only: bool = False):
    """List tasks, optionally filtered."""
    filtered = tasks
    
    if phase:
        filtered = [t for t in filtered if t.phase == phase]
    
    if pending_only:
        filtered = [t for t in filtered if not t.completed]
    
    print(f"\nTasks ({len(filtered)} found):\n")
    print(f"{'ID':<10} {'Priority':<8} {'Parallel':<8} {'Title'}")
    print("-" * 70)
    
    for task in sorted(filtered, key=lambda t: t.id):
        status = "✓" if task.completed else " "
        parallel = "yes" if task.parallelizable else "no"
        print(f"[{status}] {task.id:<8} {task.priority:<8} {parallel:<8} {task.title}")


def main():
    workplan_path = Path(__file__).parent.parent / "SPECS" / "Workplan.md"
    args = sys.argv[1:]
    
    if not workplan_path.exists():
        print(f"Error: Workplan not found at {workplan_path}")
        sys.exit(1)

    if '--help' in args or '-h' in args:
        print(__doc__)
        sys.exit(0)

    tasks = parse_workplan(workplan_path)
    if not tasks:
        if is_intentionally_empty_workplan(workplan_path):
            if '--phase' in args:
                idx = args.index('--phase')
                phase = args[idx + 1] if idx + 1 < len(args) else None
                list_tasks([], phase=phase)
            elif '--todo' in args:
                list_tasks([], pending_only=True)
            elif '--markdown' in args:
                print(format_progress(empty_progress(), markdown=True))
            elif '--json' in args:
                import json
                print(json.dumps(empty_progress(), indent=2))
            else:
                print("No tasks available. Workplan is intentionally reset for the next planning cycle.")
            sys.exit(0)
        print("No tasks found in workplan")
        sys.exit(1)
    
    if '--phase' in args:
        idx = args.index('--phase')
        phase = args[idx + 1] if idx + 1 < len(args) else None
        list_tasks(tasks, phase=phase)
    elif '--todo' in args:
        list_tasks(tasks, pending_only=True)
    elif '--markdown' in args:
        progress = calculate_progress(tasks)
        print(format_progress(progress, markdown=True))
    elif '--json' in args:
        import json
        progress = calculate_progress(tasks)
        print(json.dumps(progress, indent=2))
    else:
        progress = calculate_progress(tasks)
        print(format_progress(progress))
        print(f"\nRun with --help for more options")


if __name__ == '__main__':
    main()
