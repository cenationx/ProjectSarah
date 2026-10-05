#!/usr/bin/env python3
"""Automated tests for Project Sarah's test runner (tools/run_tests.py).

Tests the runner against small controlled child-process fixtures without
re-running the entire production suite. Uses Python standard library only.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path
import run_tests

REPO_ROOT = Path(__file__).resolve().parents[1]
RUNNER_SCRIPT = REPO_ROOT / "tools/run_tests.py"


class TestRunner(unittest.TestCase):
    """Test suite for tools/run_tests.py."""

    def setUp(self):
        temp_root = REPO_ROOT / "tools/reports/self-test-tmp"
        temp_root.mkdir(parents=True, exist_ok=True)
        self.temp_dir = tempfile.TemporaryDirectory(dir=temp_root)
        self.temp_path = Path(self.temp_dir.name)
        self.python_bin = sys.executable

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_temporary_files_stay_in_project(self):
        self.assertTrue(self.temp_path.resolve().is_relative_to(REPO_ROOT.resolve()))
        self.assertTrue(self.temp_path.is_dir())

    def test_git_dirty_includes_untracked_files(self):
        for status, expected in (("?? new-source.py\n", True), (" M tracked.py\n", True), ("", False)):
            with self.subTest(status=status):
                responses = [subprocess.CompletedProcess([], 0, "abc123\n", ""),
                             subprocess.CompletedProcess([], 0, "main\n", ""),
                             subprocess.CompletedProcess([], 0, status, "")]
                with patch.dict(os.environ, {"SARAH_GIT": str(Path(sys.executable))}), \
                     patch.object(run_tests.subprocess, "run", side_effect=responses):
                    info = run_tests.get_git_info(REPO_ROOT)
                self.assertTrue(info["available"])
                self.assertEqual(info["dirty"], expected)

    def _run_runner(self, args, cwd=None, env=None):
        cmd = [self.python_bin, str(RUNNER_SCRIPT)] + args
        proc_env = os.environ.copy()
        if env:
            proc_env.update(env)
        return subprocess.run(
            cmd,
            cwd=str(cwd or REPO_ROOT),
            capture_output=True,
            text=True,
            env=proc_env,
        )

    def test_success_suite(self):
        """A valid suite returning exit code 0 and RESULT summary passes."""
        suite_file = self.temp_path / "dummy_success.py"
        suite_file.write_text(
            "print('PASS check1')\n"
            "print('PASS check2')\n"
            "print('RESULT 2 checks passed')\n",
            encoding="utf-8",
        )
        report_dir = self.temp_path / "reports"

        res = self._run_runner([
            "--suites", str(suite_file),
            "--report-dir", str(report_dir),
            "--python", self.python_bin,
        ])
        self.assertEqual(res.returncode, 0, f"Expected 0, got {res.returncode}\n{res.stderr}")

        json_path = report_dir / "test-report.json"
        self.assertTrue(json_path.is_file())
        with open(json_path, encoding="utf-8") as f:
            data = json.load(f)

        self.assertEqual(data["summary"]["overall"], "passed")
        self.assertEqual(data["summary"]["total_checks"], 2)
        self.assertEqual(data["summary"]["passed_suites"], 1)
        self.assertEqual(data["summary"]["failed_suites"], 0)
        self.assertIn("These are offline fixture checks", data["disclaimer"])

        md_path = report_dir / "test-report.md"
        self.assertTrue(md_path.is_file())
        md_text = md_path.read_text(encoding="utf-8")
        self.assertIn("- **Overall Status**: **PASSED**", md_text)
        self.assertIn("2** passed", md_text)
        self.assertIn("These are offline fixture checks", md_text)

    def test_nonzero_exit_suite(self):
        """A suite exiting with a non-zero exit code fails overall."""
        suite_file = self.temp_path / "dummy_fail.py"
        suite_file.write_text(
            "import sys\n"
            "print('FAIL some_test')\n"
            "sys.exit(3)\n",
            encoding="utf-8",
        )
        report_dir = self.temp_path / "reports"

        res = self._run_runner([
            "--suites", str(suite_file),
            "--report-dir", str(report_dir),
            "--python", self.python_bin,
        ])
        self.assertEqual(res.returncode, 1)

        json_path = report_dir / "test-report.json"
        with open(json_path, encoding="utf-8") as f:
            data = json.load(f)

        self.assertEqual(data["summary"]["overall"], "failed")
        self.assertEqual(data["summary"]["failed_suites"], 1)
        self.assertIn("3", data["suites"][0]["failure_details"])

    def test_missing_summary(self):
        """A suite exiting 0 without a RESULT line fails overall."""
        suite_file = self.temp_path / "dummy_no_summary.py"
        suite_file.write_text(
            "print('PASS check1')\n"
            "print('All tests completed without error.')\n",
            encoding="utf-8",
        )
        report_dir = self.temp_path / "reports"

        res = self._run_runner([
            "--suites", str(suite_file),
            "--report-dir", str(report_dir),
            "--python", self.python_bin,
        ])
        self.assertEqual(res.returncode, 1)

        json_path = report_dir / "test-report.json"
        with open(json_path, encoding="utf-8") as f:
            data = json.load(f)

        self.assertEqual(data["summary"]["overall"], "failed")
        self.assertIn("Missing valid RESULT summary", data["suites"][0]["failure_details"])

    def test_crash_suite(self):
        """A suite throwing an unhandled exception fails overall with traceback details."""
        suite_file = self.temp_path / "dummy_crash.py"
        suite_file.write_text(
            "raise RuntimeError('Deliberate suite crash simulation')\n",
            encoding="utf-8",
        )
        report_dir = self.temp_path / "reports"

        res = self._run_runner([
            "--suites", str(suite_file),
            "--report-dir", str(report_dir),
            "--python", self.python_bin,
        ])
        self.assertEqual(res.returncode, 1)

        json_path = report_dir / "test-report.json"
        with open(json_path, encoding="utf-8") as f:
            data = json.load(f)

        self.assertEqual(data["summary"]["overall"], "failed")
        self.assertIn("Deliberate suite crash simulation", data["suites"][0]["failure_details"])

    def test_timeout_suite(self):
        """A hanging suite is terminated and fails when exceeding per-suite timeout."""
        suite_file = self.temp_path / "dummy_timeout.py"
        suite_file.write_text(
            "import time\n"
            "time.sleep(10)\n",
            encoding="utf-8",
        )
        report_dir = self.temp_path / "reports"

        res = self._run_runner([
            "--suites", str(suite_file),
            "--report-dir", str(report_dir),
            "--timeout", "1",
            "--python", self.python_bin,
        ])
        self.assertEqual(res.returncode, 1)

        json_path = report_dir / "test-report.json"
        with open(json_path, encoding="utf-8") as f:
            data = json.load(f)

        self.assertEqual(data["summary"]["overall"], "failed")
        self.assertIn("Timed out after 1 seconds", data["suites"][0]["failure_details"])

    def test_paths_containing_spaces(self):
        """Suites and report directories with spaces in path resolve and execute cleanly."""
        spaced_dir = self.temp_path / "path with spaces" / "sub dir with spaces"
        spaced_dir.mkdir(parents=True)
        suite_file = spaced_dir / "dummy spaced suite.py"
        suite_file.write_text(
            "print('PASS spaced_check')\n"
            "print('RESULT 3 spaced checks passed')\n",
            encoding="utf-8",
        )
        report_dir = spaced_dir / "report folder with spaces"

        res = self._run_runner([
            "--suites", str(suite_file),
            "--report-dir", str(report_dir),
            "--python", self.python_bin,
        ])
        self.assertEqual(res.returncode, 0, f"Failed on paths with spaces: {res.stderr}")

        json_path = report_dir / "test-report.json"
        self.assertTrue(json_path.is_file())
        with open(json_path, encoding="utf-8") as f:
            data = json.load(f)

        self.assertEqual(data["summary"]["overall"], "passed")
        self.assertEqual(data["summary"]["total_checks"], 3)

    def test_invocation_from_another_directory(self):
        """Runner executes and resolves relative paths cleanly when invoked from outside repo."""
        suite_file = self.temp_path / "dummy_foreign.py"
        suite_file.write_text(
            "print('PASS foreign_test')\n"
            "print('RESULT 1 foreign check passed')\n",
            encoding="utf-8",
        )
        report_dir = self.temp_path / "foreign_reports"
        foreign_cwd = self.temp_path

        res = self._run_runner(
            [
                "--suites", str(suite_file),
                "--report-dir", str(report_dir),
                "--python", self.python_bin,
            ],
            cwd=foreign_cwd,
        )
        self.assertEqual(res.returncode, 0, f"Failed from foreign cwd: {res.stderr}")

        json_path = report_dir / "test-report.json"
        self.assertTrue(json_path.is_file())
        with open(json_path, encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(data["summary"]["overall"], "passed")

    def test_unavailable_git(self):
        """When Git is unavailable, runner continues, marks git unavailable, and records tests."""
        suite_file = self.temp_path / "dummy_no_git.py"
        suite_file.write_text(
            "print('PASS gitless_check')\n"
            "print('RESULT 5 gitless checks passed')\n",
            encoding="utf-8",
        )
        report_dir = self.temp_path / "gitless_reports"

        # Construct an environment simulating unavailable git
        clean_env = {
            "SYSTEMROOT": os.environ.get("SYSTEMROOT", "C:\\Windows"),
            "PATH": "",
            "SARAH_GIT": "none",
        }

        res = self._run_runner(
            [
                "--suites", str(suite_file),
                "--report-dir", str(report_dir),
                "--python", self.python_bin,
            ],
            env=clean_env,
        )
        self.assertEqual(res.returncode, 0, f"Failed without git: {res.stderr}")

        json_path = report_dir / "test-report.json"
        with open(json_path, encoding="utf-8") as f:
            data = json.load(f)

        self.assertFalse(data["git"]["available"])
        self.assertEqual(data["git"]["commit"], "unavailable")
        self.assertEqual(data["summary"]["overall"], "passed")
        self.assertEqual(data["summary"]["total_checks"], 5)

    def test_multiple_result_summaries_takes_final(self):
        """When a suite outputs intermediate RESULT lines followed by a final summary, runner takes the final count."""
        suite_file = self.temp_path / "dummy_multiple_summaries.py"
        suite_file.write_text(
            "print('PASS part1')\n"
            "print('RESULT 2 intermediate checks passed')\n"
            "print('PASS part2')\n"
            "print('RESULT 5 total checks passed')\n",
            encoding="utf-8",
        )
        report_dir = self.temp_path / "reports_mult"

        res = self._run_runner([
            "--suites", str(suite_file),
            "--report-dir", str(report_dir),
            "--python", self.python_bin,
        ])
        self.assertEqual(res.returncode, 0)

        json_path = report_dir / "test-report.json"
        with open(json_path, encoding="utf-8") as f:
            data = json.load(f)

        self.assertEqual(data["summary"]["overall"], "passed")
        self.assertEqual(data["summary"]["total_checks"], 5)
        self.assertEqual(data["suites"][0]["checks"], 5)


def main():
    suite = unittest.TestLoader().loadTestsFromTestCase(TestRunner)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)


if __name__ == "__main__":
    main()
