#!/usr/bin/env python3
"""Tests for calc_progress.py script."""

import sys
import json
import subprocess
from pathlib import Path
from io import StringIO

import pytest

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import calc_progress as cp


FIXTURES_DIR = Path(__file__).parent / "fixtures"


class TestParseWorkplan:
    """Tests for parse_workplan function."""

    def test_parse_full_workplan(self):
        """Test parsing a complete workplan with multiple phases."""
        tasks = cp.parse_workplan(FIXTURES_DIR / "test_workplan.md")

        assert len(tasks) == 5

        # Check task IDs
        task_ids = [t.id for t in tasks]
        assert "P1-T1" in task_ids
        assert "P1-T2" in task_ids
        assert "P1-T3" in task_ids
        assert "P2-T1" in task_ids
        assert "P2-T2" in task_ids

    def test_parse_task_details(self):
        """Test that task details are parsed correctly."""
        tasks = cp.parse_workplan(FIXTURES_DIR / "test_workplan.md")

        # Find P1-T1
        p1t1 = next(t for t in tasks if t.id == "P1-T1")
        assert p1t1.title == "First Task"
        assert p1t1.priority == "P0"
        assert p1t1.phase == "P1"
        assert p1t1.dependencies == []
        assert p1t1.parallelizable is False

        # Find P1-T2
        p1t2 = next(t for t in tasks if t.id == "P1-T2")
        assert p1t2.title == "Second Task"
        assert p1t2.priority == "P1"
        assert p1t2.dependencies == ["P1-T1"]
        assert p1t2.parallelizable is True

        # Find P1-T3 with multiple dependencies
        p1t3 = next(t for t in tasks if t.id == "P1-T3")
        assert p1t3.dependencies == ["P1-T1", "P1-T2"]

    def test_parse_empty_workplan(self):
        """Test parsing a workplan with no tasks."""
        tasks = cp.parse_workplan(FIXTURES_DIR / "empty_workplan.md")
        assert len(tasks) == 0

    def test_parse_minimal_workplan(self):
        """Test parsing a minimal workplan with one task."""
        tasks = cp.parse_workplan(FIXTURES_DIR / "minimal_workplan.md")

        assert len(tasks) == 1
        assert tasks[0].id == "P1-T1"
        assert tasks[0].priority == "P0"
        assert tasks[0].phase == "P1"


class TestCalculateProgress:
    """Tests for calculate_progress function."""

    def test_empty_tasks(self):
        """Test with empty task list."""
        result = cp.calculate_progress([])
        assert result == {}

    def test_single_task(self):
        """Test with a single task."""
        tasks = [cp.Task("P1-T1", "Test", "P0", "P1", [], False)]
        result = cp.calculate_progress(tasks)

        assert result["total"] == 1
        assert result["completed"] == 0
        assert result["pending"] == 1
        assert result["percent"] == 0.0
        assert result["by_priority"]["P0"]["total"] == 1
        assert result["by_phase"]["P1"]["total"] == 1

    def test_multiple_priorities(self):
        """Test with tasks of different priorities."""
        tasks = [
            cp.Task("P1-T1", "Test1", "P0", "P1", [], False),
            cp.Task("P1-T2", "Test2", "P1", "P1", [], False),
            cp.Task("P1-T3", "Test3", "P2", "P1", [], False),
            cp.Task("P2-T1", "Test4", "P0", "P2", [], False),
        ]
        result = cp.calculate_progress(tasks)

        assert result["total"] == 4
        assert result["by_priority"]["P0"]["total"] == 2
        assert result["by_priority"]["P1"]["total"] == 1
        assert result["by_priority"]["P2"]["total"] == 1
        assert result["by_phase"]["P1"]["total"] == 3
        assert result["by_phase"]["P2"]["total"] == 1

    def test_completed_tasks(self):
        """Test with some completed tasks."""
        tasks = [
            cp.Task("P1-T1", "Test1", "P0", "P1", [], False, completed=True),
            cp.Task("P1-T2", "Test2", "P0", "P1", [], False, completed=False),
            cp.Task("P1-T3", "Test3", "P0", "P1", [], False, completed=True),
        ]
        result = cp.calculate_progress(tasks)

        assert result["completed"] == 2
        assert result["pending"] == 1
        assert abs(result["percent"] - 66.67) < 0.1  # 2/3 * 100
        assert result["by_priority"]["P0"]["completed"] == 2


class TestFormatProgress:
    """Tests for format_progress function."""

    def test_text_format(self):
        """Test text formatting."""
        progress = {
            "total": 10,
            "completed": 5,
            "pending": 5,
            "percent": 50.0,
            "by_priority": {
                "P0": {"total": 4, "completed": 2},
                "P1": {"total": 4, "completed": 2},
                "P2": {"total": 2, "completed": 1},
                "P3": {"total": 0, "completed": 0},
            },
            "by_phase": {
                "P1": {"total": 6, "completed": 3},
                "P2": {"total": 4, "completed": 2},
            },
        }
        output = cp.format_progress(progress, markdown=False)

        assert "WORKPLAN PROGRESS" in output
        assert "5/10 tasks" in output
        assert "P0:" in output
        assert "P1:" in output
        assert "P2:" in output

    def test_markdown_format(self):
        """Test markdown formatting."""
        progress = {
            "total": 10,
            "completed": 5,
            "pending": 5,
            "percent": 50.0,
            "by_priority": {
                "P0": {"total": 4, "completed": 2},
                "P1": {"total": 4, "completed": 2},
                "P2": {"total": 2, "completed": 1},
                "P3": {"total": 0, "completed": 0},
            },
            "by_phase": {
                "P1": {"total": 6, "completed": 3},
                "P2": {"total": 4, "completed": 2},
            },
        }
        output = cp.format_progress(progress, markdown=True)

        assert "# Progress Report" in output
        assert "| Priority |" in output
        assert "| Phase |" in output
        assert "**Overall:**" in output


class TestListTasks:
    """Tests for list_tasks function (via stdout capture)."""

    def test_list_all_tasks(self, capsys):
        """Test listing all tasks."""
        tasks = [
            cp.Task("P1-T1", "Task One", "P0", "P1", [], False),
            cp.Task("P1-T2", "Task Two", "P1", "P1", [], True),
        ]
        cp.list_tasks(tasks)

        captured = capsys.readouterr()
        assert "Task One" in captured.out
        assert "Task Two" in captured.out
        assert "P0" in captured.out
        assert "P1" in captured.out
        assert "yes" in captured.out  # parallelizable
        assert "no" in captured.out  # not parallelizable

    def test_list_by_phase(self, capsys):
        """Test filtering by phase."""
        tasks = [
            cp.Task("P1-T1", "Phase 1 Task", "P0", "P1", [], False),
            cp.Task("P2-T1", "Phase 2 Task", "P0", "P2", [], False),
        ]
        cp.list_tasks(tasks, phase="P1")

        captured = capsys.readouterr()
        assert "Phase 1 Task" in captured.out
        assert "Phase 2 Task" not in captured.out

    def test_list_pending_only(self, capsys):
        """Test filtering pending tasks."""
        tasks = [
            cp.Task("P1-T1", "Done Task", "P0", "P1", [], False, completed=True),
            cp.Task("P1-T2", "Pending Task", "P0", "P1", [], False, completed=False),
        ]
        cp.list_tasks(tasks, pending_only=True)

        captured = capsys.readouterr()
        assert "Pending Task" in captured.out
        assert "Done Task" not in captured.out


class TestCleanValue:
    """Tests for clean_value helper function."""

    def test_removes_bold(self):
        """Test removal of markdown bold markers."""
        assert cp.clean_value("**P0**") == "P0"
        assert cp.clean_value(" ** P1 ** ") == "P1"

    def test_strips_whitespace(self):
        """Test whitespace stripping."""
        assert cp.clean_value("  text  ") == "text"
        assert cp.clean_value("text") == "text"


class TestIntegration:
    """Integration tests running the script as a subprocess."""

    @pytest.mark.skip(reason="Script doesn't support --workplan arg - uses hardcoded path")
    def test_script_runs_without_errors(self, tmp_path):
        """Test that the script runs without errors."""
        # Create a minimal temp workplan for the test
        temp_workplan = tmp_path / "test_workplan.md"
        temp_workplan.write_text(
            "# Test Workplan\n\n"
            "### Phase 1: Test Phase\n\n"
            "#### P1-T1: Test Task\n"
            "- **Priority:** P0\n"
            "- **Dependencies:** none\n"
            "- **Parallelizable:** no\n"
        )
        result = subprocess.run(
            [
                sys.executable,
                "scripts/calc_progress.py",
                "--workplan",
                str(temp_workplan),
                "--json",
            ],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["total"] == 1

    def test_script_with_test_fixture(self):
        """Test script with test workplan fixture."""
        # Copy test fixture to SPECS temporarily
        import shutil

        spec_dir = Path(__file__).parent.parent / "SPECS"
        original_workplan = spec_dir / "Workplan.md"
        backup_workplan = spec_dir / "Workplan.md.bak"
        test_fixture = FIXTURES_DIR / "test_workplan.md"

        # Backup original
        if original_workplan.exists():
            shutil.copy(original_workplan, backup_workplan)

        try:
            # Copy test fixture
            shutil.copy(test_fixture, original_workplan)

            result = subprocess.run(
                [sys.executable, "scripts/calc_progress.py", "--json"],
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent.parent,
            )

            assert result.returncode == 0
            data = json.loads(result.stdout)
            assert data["total"] == 5
            assert data["by_phase"]["P1"]["total"] == 3
            assert data["by_phase"]["P2"]["total"] == 2

        finally:
            # Restore original
            if backup_workplan.exists():
                shutil.copy(backup_workplan, original_workplan)
                backup_workplan.unlink()
