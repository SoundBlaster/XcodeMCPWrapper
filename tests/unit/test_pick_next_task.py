#!/usr/bin/env python3
"""
Test suite for scripts/pick_next_task.py

This module contains unit tests for the task tracking script functionality.
"""

import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from pick_next_task import (
    Task,
    find_next_task,
    format_task_output,
    get_completed_tasks,
    main,
    parse_workplan,
    save_completed_tasks,
)

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def sample_workplan_content():
    """Sample workplan content for testing."""
    return """# Workplan: Test Project

## 1. Overview

Test overview content.

## 2. Phases

### Phase 1: Foundation
**Intent:** Establish project structure.

#### P1-T1: Create Project Directory Structure
- **Description:** Create `src/` and `tests/` directories
- **Priority:** P0
- **Dependencies:** none
- **Parallelizable:** no
- **Outputs/Artifacts:**
  - Directory tree structure
- **Acceptance Criteria:** All directories exist

#### P1-T2: Initialize Python Project
- **Description:** Create `pyproject.toml` with project metadata
- **Priority:** P0
- **Dependencies:** P1-T1
- **Parallelizable:** no
- **Outputs/Artifacts:**
  - `pyproject.toml`
- **Acceptance Criteria:** `pip install -e .` succeeds

#### P1-T3: Configure Linting Tools
- **Description:** Add ruff configuration
- **Priority:** P1
- **Dependencies:** P1-T2
- **Parallelizable:** yes
- **Outputs/Artifacts:**
  - Linting rules
- **Acceptance Criteria:** `ruff check src/` runs

### Phase 2: Implementation
**Intent:** Implement core features.

#### P2-T1: Implement Core Feature
- **Description:** Create the main module
- **Priority:** P0
- **Dependencies:** P1-T2
- **Parallelizable:** no
- **Outputs/Artifacts:**
  - `src/main.py`
- **Acceptance Criteria:** Module imports without errors

#### P2-T2: Add Tests
- **Description:** Write unit tests
- **Priority:** P1
- **Dependencies:** P2-T1
- **Parallelizable:** yes
- **Outputs/Artifacts:**
  - Test files
- **Acceptance Criteria:** Tests pass

### Phase 3: Polish
**Intent:** Final touches.

#### P3-T1: Documentation
- **Description:** Write README
- **Priority:** P2
- **Dependencies:** none
- **Parallelizable:** yes
- **Outputs/Artifacts:**
  - `README.md`
- **Acceptance Criteria:** README is complete
"""


@pytest.fixture
def temp_workplan(tmp_path, sample_workplan_content):
    """Create a temporary workplan file."""
    workplan_path = tmp_path / "Workplan.md"
    workplan_path.write_text(sample_workplan_content)
    return workplan_path


@pytest.fixture
def sample_tasks():
    """Create sample Task objects for testing."""
    return [
        Task(
            id="P1-T1",
            description="Create directories",
            phase="Phase 1",
            priority="P0",
            dependencies=[],
        ),
        Task(
            id="P1-T2",
            description="Create pyproject.toml",
            phase="Phase 1",
            priority="P0",
            dependencies=["P1-T1"],
        ),
        Task(
            id="P1-T3",
            description="Configure linting",
            phase="Phase 1",
            priority="P1",
            dependencies=["P1-T2"],
        ),
        Task(
            id="P2-T1",
            description="Implement feature",
            phase="Phase 2",
            priority="P0",
            dependencies=["P1-T2"],
        ),
        Task(
            id="P2-T2",
            description="Add tests",
            phase="Phase 2",
            priority="P1",
            dependencies=["P2-T1"],
        ),
        Task(
            id="P3-T1", description="Documentation", phase="Phase 3", priority="P2", dependencies=[]
        ),
    ]


# =============================================================================
# Test parse_workplan
# =============================================================================


class TestParseWorkplan:
    """Tests for parse_workplan function."""

    def test_parses_all_tasks(self, temp_workplan):
        """Test that all tasks are parsed from workplan."""
        tasks = parse_workplan(temp_workplan)
        assert len(tasks) == 6
        task_ids = {t.id for t in tasks}
        assert task_ids == {"P1-T1", "P1-T2", "P1-T3", "P2-T1", "P2-T2", "P3-T1"}

    def test_extracts_task_details(self, temp_workplan):
        """Test that task details are correctly extracted."""
        tasks = parse_workplan(temp_workplan)

        p1_t1 = next(t for t in tasks if t.id == "P1-T1")
        assert p1_t1.description == "Create `src/` and `tests/` directories"
        assert p1_t1.phase == "Phase 1"
        assert p1_t1.priority == "P0"
        assert p1_t1.dependencies == []

    def test_trims_phase_title_suffix(self, temp_workplan):
        """Phase labels should keep only the canonical 'Phase N' form."""
        tasks = parse_workplan(temp_workplan)
        phases = {task.id: task.phase for task in tasks}

        assert phases["P1-T1"] == "Phase 1"
        assert phases["P2-T1"] == "Phase 2"
        assert phases["P3-T1"] == "Phase 3"

    def test_extracts_dependencies(self, temp_workplan):
        """Test that dependencies are correctly parsed."""
        tasks = parse_workplan(temp_workplan)

        p1_t2 = next(t for t in tasks if t.id == "P1-T2")
        assert p1_t2.dependencies == ["P1-T1"]

        p2_t1 = next(t for t in tasks if t.id == "P2-T1")
        assert p2_t1.dependencies == ["P1-T2"]

    def test_handles_no_dependencies(self, temp_workplan):
        """Test that tasks with 'none' dependencies are handled."""
        tasks = parse_workplan(temp_workplan)

        p3_t1 = next(t for t in tasks if t.id == "P3-T1")
        assert p3_t1.dependencies == []

    def test_extracts_priorities(self, temp_workplan):
        """Test that priorities are correctly extracted."""
        tasks = parse_workplan(temp_workplan)

        priorities = {t.id: t.priority for t in tasks}
        assert priorities["P1-T1"] == "P0"
        assert priorities["P1-T2"] == "P0"
        assert priorities["P1-T3"] == "P1"
        assert priorities["P2-T1"] == "P0"
        assert priorities["P2-T2"] == "P1"
        assert priorities["P3-T1"] == "P2"

    def test_empty_workplan(self, tmp_path):
        """Test parsing empty workplan returns empty list."""
        workplan_path = tmp_path / "Empty.md"
        workplan_path.write_text("# Empty Workplan\n\nNo tasks here.")
        tasks = parse_workplan(workplan_path)
        assert tasks == []

    def test_nonexistent_file(self, tmp_path):
        """Test that nonexistent file returns empty list."""
        workplan_path = tmp_path / "Nonexistent.md"
        # File doesn't exist, should handle gracefully
        with pytest.raises(FileNotFoundError):
            parse_workplan(workplan_path)


# =============================================================================
# Test Task class
# =============================================================================


class TestTask:
    """Tests for Task dataclass."""

    def test_priority_value_p0(self):
        """Test P0 has lowest numeric priority."""
        task = Task(id="T1", description="Test", phase="Phase 1", priority="P0")
        assert task.priority_value == 0

    def test_priority_value_p1(self):
        """Test P1 priority value."""
        task = Task(id="T1", description="Test", phase="Phase 1", priority="P1")
        assert task.priority_value == 1

    def test_priority_value_p2(self):
        """Test P2 priority value."""
        task = Task(id="T1", description="Test", phase="Phase 1", priority="P2")
        assert task.priority_value == 2

    def test_phase_number_extraction(self):
        """Test phase number extraction from phase name."""
        task = Task(id="T1", description="Test", phase="Phase 5", priority="P0")
        assert task.phase_number == 5

    def test_phase_number_two_digits(self):
        """Test phase number extraction with two digits."""
        task = Task(id="T1", description="Test", phase="Phase 10", priority="P0")
        assert task.phase_number == 10


# =============================================================================
# Test get_completed_tasks / save_completed_tasks
# =============================================================================


class TestCompletedTasks:
    """Tests for task state persistence."""

    def test_get_completed_empty_file(self, tmp_path):
        """Test getting completed tasks from nonexistent file."""
        state_file = tmp_path / "state.json"
        completed = get_completed_tasks(state_file)
        assert completed == set()

    def test_get_completed_with_data(self, tmp_path):
        """Test getting completed tasks with existing data."""
        state_file = tmp_path / "state.json"
        state_file.write_text(json.dumps({"completed": ["P1-T1", "P1-T2"]}))
        completed = get_completed_tasks(state_file)
        assert completed == {"P1-T1", "P1-T2"}

    def test_save_completed_creates_file(self, tmp_path):
        """Test saving completed tasks creates file."""
        state_file = tmp_path / "state.json"
        save_completed_tasks(state_file, {"P1-T1", "P1-T2"})
        assert state_file.exists()
        data = json.loads(state_file.read_text())
        assert set(data["completed"]) == {"P1-T1", "P1-T2"}

    def test_save_completed_overwrites(self, tmp_path):
        """Test saving overwrites existing file."""
        state_file = tmp_path / "state.json"
        state_file.write_text(json.dumps({"completed": ["P1-T1"]}))
        save_completed_tasks(state_file, {"P2-T1"})
        data = json.loads(state_file.read_text())
        assert data["completed"] == ["P2-T1"]

    def test_round_trip(self, tmp_path):
        """Test save and load round trip."""
        state_file = tmp_path / "state.json"
        original = {"P1-T1", "P1-T2", "P2-T1"}
        save_completed_tasks(state_file, original)
        loaded = get_completed_tasks(state_file)
        assert loaded == original


# =============================================================================
# Test find_next_task
# =============================================================================


class TestFindNextTask:
    """Tests for find_next_task function."""

    def test_returns_highest_priority(self, sample_tasks):
        """Test that P0 tasks are returned before P1/P2 within same phase."""
        completed = set()
        next_task = find_next_task(sample_tasks, completed)
        assert next_task is not None
        # P1-T1 is P0 in Phase 1
        assert next_task.id == "P1-T1"

    def test_respects_dependencies(self, sample_tasks):
        """Test that tasks with unmet dependencies are not returned."""
        completed = set()
        # P1-T2 depends on P1-T1, so only P1-T1 and P3-T1 should be available
        available = []
        for task in sample_tasks:
            if all(dep in completed for dep in task.dependencies):
                available.append(task)

        # Should only include P1-T1 (P0) and P3-T1 (P2)
        p0_available = [t for t in available if t.priority == "P0"]
        assert len(p0_available) == 1
        assert p0_available[0].id == "P1-T1"

    def test_returns_none_when_all_done(self, sample_tasks):
        """Test that None is returned when all tasks are completed."""
        completed = {t.id for t in sample_tasks}
        next_task = find_next_task(sample_tasks, completed)
        assert next_task is None

    def test_returns_none_for_empty_tasks(self):
        """Test that None is returned for empty task list."""
        next_task = find_next_task([], set())
        assert next_task is None

    def test_early_phase_priority(self, sample_tasks):
        """Test that earlier phases are prioritized."""
        completed = {"P1-T1"}
        next_task = find_next_task(sample_tasks, completed)
        # P1-T2 should be next (Phase 1, P0)
        assert next_task.id == "P1-T2"

    def test_dependency_chain(self, sample_tasks):
        """Test working through a dependency chain."""
        # Complete P1-T1 and P1-T2
        completed = {"P1-T1", "P1-T2"}
        next_task = find_next_task(sample_tasks, completed)
        # Phase 1 takes priority over Phase 2, so P1-T3 comes before P2-T1
        assert next_task.id == "P1-T3"


# =============================================================================
# Test format_task_output
# =============================================================================


class TestFormatTaskOutput:
    """Tests for format_task_output function."""

    def test_includes_task_id(self, sample_tasks):
        """Test that output includes task ID."""
        task = sample_tasks[0]
        output = format_task_output(task, sample_tasks, set())
        assert task.id in output

    def test_includes_description(self, sample_tasks):
        """Test that output includes task description."""
        task = sample_tasks[0]
        output = format_task_output(task, sample_tasks, set())
        assert task.description in output

    def test_shows_blocking_dependencies(self, sample_tasks):
        """Test that blocking dependencies are marked."""
        task = next(t for t in sample_tasks if t.id == "P1-T2")
        output = format_task_output(task, sample_tasks, set())  # P1-T1 not done
        assert "P1-T1" in output
        assert "PENDING" in output

    def test_shows_completed_dependencies(self, sample_tasks):
        """Test that completed dependencies are marked as done."""
        task = next(t for t in sample_tasks if t.id == "P1-T2")
        output = format_task_output(task, sample_tasks, {"P1-T1"})
        assert "DONE" in output

    def test_shows_progress(self, sample_tasks):
        """Test that progress is shown."""
        task = sample_tasks[0]
        completed = {"P1-T1"}
        output = format_task_output(task, sample_tasks, completed)
        assert "1/6" in output or "16.7%" in output


# =============================================================================
# Test main function
# =============================================================================


class TestMain:
    """Tests for main function and CLI."""

    def test_help_flag(self, temp_workplan, capsys):
        """Test --help outputs usage information."""
        with pytest.raises(SystemExit) as exc_info, patch(
            "sys.argv", ["pick_next_task.py", "--help"]
        ):
            main()
        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "usage:" in captured.out

    def test_list_flag(self, temp_workplan, tmp_path, capsys):
        """Test --list outputs all tasks."""
        state_file = tmp_path / "state.json"
        with pytest.raises(SystemExit) as exc_info, patch(
            "sys.argv",
            [
                "pick_next_task.py",
                "--workplan",
                str(temp_workplan),
                "--state",
                str(state_file),
                "--list",
            ],
        ):
            main()
        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "P1-T1" in captured.out
        assert "P1-T2" in captured.out

    def test_progress_flag(self, temp_workplan, tmp_path, capsys):
        """Test --progress outputs progress summary."""
        state_file = tmp_path / "state.json"
        with pytest.raises(SystemExit) as exc_info, patch(
            "sys.argv",
            [
                "pick_next_task.py",
                "--workplan",
                str(temp_workplan),
                "--state",
                str(state_file),
                "--progress",
            ],
        ):
            main()
        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "OVERALL PROGRESS" in captured.out
        assert "Phase 1" in captured.out

    def test_done_flag(self, temp_workplan, tmp_path, capsys):
        """Test --done marks task as completed."""
        state_file = tmp_path / "state.json"
        with pytest.raises(SystemExit) as exc_info, patch(
            "sys.argv",
            [
                "pick_next_task.py",
                "--workplan",
                str(temp_workplan),
                "--state",
                str(state_file),
                "--done",
                "P1-T1",
            ],
        ):
            main()
        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "Marked P1-T1 as completed" in captured.out

        # Verify state was saved
        completed = get_completed_tasks(state_file)
        assert "P1-T1" in completed

    def test_done_invalid_task(self, temp_workplan, tmp_path, capsys):
        """Test --done with invalid task ID."""
        state_file = tmp_path / "state.json"
        with pytest.raises(SystemExit) as exc_info, patch(
            "sys.argv",
            [
                "pick_next_task.py",
                "--workplan",
                str(temp_workplan),
                "--state",
                str(state_file),
                "--done",
                "INVALID",
            ],
        ):
            main()
        assert exc_info.value.code == 1

    def test_default_shows_next_task(self, temp_workplan, tmp_path, capsys):
        """Test default behavior shows next task."""
        state_file = tmp_path / "state.json"
        with patch(
            "sys.argv",
            ["pick_next_task.py", "--workplan", str(temp_workplan), "--state", str(state_file)],
        ):
            main()
        captured = capsys.readouterr()
        assert "NEXT TASK:" in captured.out
        assert "P1-T1" in captured.out  # Should be first P0 task

    def test_all_tasks_completed(self, temp_workplan, tmp_path, capsys):
        """Test output when all tasks are completed."""
        state_file = tmp_path / "state.json"
        # Mark all tasks as done
        all_tasks = parse_workplan(temp_workplan)
        save_completed_tasks(state_file, {t.id for t in all_tasks})

        with pytest.raises(SystemExit) as exc_info, patch(
            "sys.argv",
            ["pick_next_task.py", "--workplan", str(temp_workplan), "--state", str(state_file)],
        ):
            main()
        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "ALL TASKS COMPLETED" in captured.out

    def test_missing_workplan(self, tmp_path, capsys):
        """Test error when workplan doesn't exist."""
        state_file = tmp_path / "state.json"
        with pytest.raises(SystemExit) as exc_info, patch(
            "sys.argv",
            [
                "pick_next_task.py",
                "--workplan",
                str(tmp_path / "nonexistent.md"),
                "--state",
                str(state_file),
            ],
        ):
            main()
        assert exc_info.value.code == 1


# =============================================================================
# Integration tests
# =============================================================================


class TestIntegration:
    """Integration tests for the full workflow."""

    def test_full_workflow(self, temp_workplan, tmp_path):
        """Test a complete workflow of picking and completing tasks."""
        state_file = tmp_path / "state.json"

        # Get initial tasks
        tasks = parse_workplan(temp_workplan)
        assert len(tasks) == 6

        # Initially, P1-T1 should be next (P0, no deps)
        completed = get_completed_tasks(state_file)
        next_task = find_next_task(tasks, completed)
        assert next_task.id == "P1-T1"

        # Complete P1-T1
        save_completed_tasks(state_file, {"P1-T1"})
        completed = get_completed_tasks(state_file)

        # Now P1-T2 should be next (P0, P1-T1 done)
        next_task = find_next_task(tasks, completed)
        assert next_task.id == "P1-T2"

        # Complete through the chain
        completed = {"P1-T1", "P1-T2"}
        save_completed_tasks(state_file, completed)
        next_task = find_next_task(tasks, completed)
        # Phase 1 takes priority, so P1-T3 comes before P2-T1
        assert next_task.id == "P1-T3"

    def test_phase_filter(self, temp_workplan, tmp_path, capsys):
        """Test --list with --phase filter."""
        state_file = tmp_path / "state.json"
        with pytest.raises(SystemExit) as exc_info, patch(
            "sys.argv",
            [
                "pick_next_task.py",
                "--workplan",
                str(temp_workplan),
                "--state",
                str(state_file),
                "--list",
                "--phase",
                "1",
            ],
        ):
            main()
        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        # Should show Phase 1 tasks
        assert "P1-T1" in captured.out
        assert "P1-T2" in captured.out
        assert "P1-T3" in captured.out
        # But not Phase 2
        assert "P2-T1" not in captured.out


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
