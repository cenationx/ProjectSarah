#!/usr/bin/env python3
"""Automated tests for Project Sarah acceptance preflight tool (tools/preflight.py).

Verifies readiness detection, missing files, stale reports, mismatched
deployment, probe detection, running processes, and read-only invariants.
Uses Python standard library only.
"""

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[1]
PREFLIGHT_SCRIPT = REPO_ROOT / "tools/preflight.py"

sys.path.insert(0, str(REPO_ROOT / "tools"))
import preflight


class TestPreflight(unittest.TestCase):
    """Test suite for tools/preflight.py."""

    def setUp(self):
        temp_root = REPO_ROOT / "tools/reports/self-test-tmp"
        temp_root.mkdir(parents=True, exist_ok=True)
        self.temp_dir = tempfile.TemporaryDirectory(dir=temp_root)
        self.mock_root = Path(self.temp_dir.name)
        self.mock_repo = self.mock_root / "repo"
        self.mock_runtime = self.mock_root / "runtime"
        self.reports_dir = self.mock_root / "reports"

        self._build_mock_environment()

    def tearDown(self):
        self.temp_dir.cleanup()

    def _build_mock_environment(self):
        """Create a complete, fully matching mock environment."""
        self.mock_repo.mkdir(parents=True)
        self.mock_runtime.mkdir(parents=True)
        self.reports_dir.mkdir(parents=True)

        # 1. Source files in mock_repo/foundation/SarahFoundation
        src_root = self.mock_repo / "foundation/SarahFoundation"
        for rel in preflight.REQUIRED_PRODUCTION_FILES:
            f = src_root / rel
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_text(f"content of {rel}\n", encoding="utf-8")

        # 2. Deployed files in mock_runtime/isolated/mods/SarahFoundation (matching source)
        dst_root = self.mock_runtime / "isolated/mods/SarahFoundation"
        for rel in preflight.REQUIRED_PRODUCTION_FILES:
            f = dst_root / rel
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_text(f"content of {rel}\n", encoding="utf-8")

        # 3. Isolated profile files
        iso_root = self.mock_runtime / "isolated"
        (iso_root / "options.ini").write_text("bSound=true\n", encoding="utf-8")
        (iso_root / "latestSave.ini").write_text("SarahConsoleNativeCase\nRising\n", encoding="utf-8")

        save_case_dir = iso_root / "Saves/Rising/SarahConsoleNativeCase"
        save_case_dir.mkdir(parents=True, exist_ok=True)
        (save_case_dir / "map_t.bin").write_text("save-data", encoding="utf-8")

        mods_dir = iso_root / "mods"
        mods_dir.mkdir(parents=True, exist_ok=True)
        (mods_dir / "default.txt").write_text("VERSION = 1,\nmods\n{\n    mod = SarahFoundation,\n}\n", encoding="utf-8")

        lua_dir = iso_root / "Lua"
        lua_dir.mkdir(parents=True, exist_ok=True)
        (lua_dir / "keysB42.ini").write_text("Forward=key:17\nSarah Console=key:67\n", encoding="utf-8")

        # 4. Disabled probes dir
        disabled_dir = self.mock_runtime / "disabled-probes"
        disabled_dir.mkdir(parents=True, exist_ok=True)
        (disabled_dir / "ZZSarahEscapeProbe.lua").write_text("-- probe", encoding="utf-8")

        # 5. Backups dir
        backups_dir = self.mock_runtime / "backups"
        backup1 = backups_dir / "slice-c-native-20261005-143139"
        backup1.mkdir(parents=True, exist_ok=True)
        (backup1 / "latestSave.ini").write_text("backup-data", encoding="utf-8")

        # 6. Test report in mock_repo/tools/reports/test-report.json
        test_rep_dir = self.mock_repo / "tools/reports"
        test_rep_dir.mkdir(parents=True, exist_ok=True)
        report_data = {
            "timestamp": "2026-10-05T12:00:00+00:00",
            "git": {"commit": "mockcommit1234567890abcdef", "branch": "main", "dirty": False},
            "summary": {"overall": "passed", "total_checks": 153},
        }
        (test_rep_dir / "test-report.json").write_text(json.dumps(report_data), encoding="utf-8")

    def _mock_git(self, commit="mockcommit1234567890abcdef", branch="main", dirty=False):
        return {
            "available": True,
            "commit": commit,
            "short_commit": commit[:7],
            "branch": branch,
            "dirty": dirty,
            "status": "dirty" if dirty else "clean",
            "summary": f"Git is {'dirty' if dirty else 'clean'} at {commit[:7]} (branch: {branch})",
        }

    def _mock_processes_clean(self):
        return {"status": "clean", "running_processes": [], "query_supported": True, "summary": "No game processes running"}

    def test_ready_environment(self):
        """When all conditions are met, preflight reports READY."""
        with patch("preflight.get_git_info", return_value=self._mock_git()), \
             patch("preflight.check_game_processes", return_value=self._mock_processes_clean()):
            data = preflight.run_preflight(self.mock_repo, self.mock_runtime)

        self.assertTrue(data["ready"])
        self.assertEqual(data["overall"], "READY")
        self.assertEqual(len(data["blockers"]), 0)
        self.assertEqual(data["checks"]["deployed_files"]["status"], "synced")
        self.assertEqual(data["checks"]["temporary_probes"]["status"], "clean")
        self.assertEqual(data["checks"]["backups"]["status"], "available")
        self.assertEqual(data["checks"]["isolated_profile"]["status"], "ready")
        self.assertEqual(data["checks"]["test_report"]["status"], "synced")

    def test_missing_test_report(self):
        """Missing test-report.json blocks readiness with clear message."""
        report_file = self.mock_repo / "tools/reports/test-report.json"
        report_file.unlink()

        with patch("preflight.get_git_info", return_value=self._mock_git()), \
             patch("preflight.check_game_processes", return_value=self._mock_processes_clean()):
            data = preflight.run_preflight(self.mock_repo, self.mock_runtime)

        self.assertFalse(data["ready"])
        self.assertEqual(data["overall"], "BLOCKED")
        self.assertEqual(data["checks"]["test_report"]["status"], "missing")
        self.assertTrue(any("test report is missing" in b.lower() for b in data["blockers"]))

    def test_stale_test_report(self):
        """Stale test report (commit mismatch) blocks readiness."""
        report_file = self.mock_repo / "tools/reports/test-report.json"
        stale_data = {
            "git": {"commit": "oldcommit0000000000000000"},
            "summary": {"overall": "passed", "total_checks": 153},
        }
        report_file.write_text(json.dumps(stale_data), encoding="utf-8")

        with patch("preflight.get_git_info", return_value=self._mock_git(commit="newcommit1111111111111111")), \
             patch("preflight.check_game_processes", return_value=self._mock_processes_clean()):
            data = preflight.run_preflight(self.mock_repo, self.mock_runtime)

        self.assertFalse(data["ready"])
        self.assertEqual(data["overall"], "BLOCKED")
        self.assertEqual(data["checks"]["test_report"]["status"], "stale")
        self.assertTrue(any("stale" in b.lower() for b in data["blockers"]))

    def test_failed_test_report(self):
        """Test report showing failed checks blocks readiness."""
        report_file = self.mock_repo / "tools/reports/test-report.json"
        failed_data = {
            "git": {"commit": "mockcommit1234567890abcdef"},
            "summary": {"overall": "failed", "total_checks": 150},
        }
        report_file.write_text(json.dumps(failed_data), encoding="utf-8")

        with patch("preflight.get_git_info", return_value=self._mock_git()), \
             patch("preflight.check_game_processes", return_value=self._mock_processes_clean()):
            data = preflight.run_preflight(self.mock_repo, self.mock_runtime)

        self.assertFalse(data["ready"])
        self.assertEqual(data["checks"]["test_report"]["status"], "failed")

    def test_mismatched_deployed_file(self):
        """When deployed file hash differs from source, preflight reports different and blocks."""
        deployed_console = self.mock_runtime / "isolated/mods/SarahFoundation/42/media/lua/client/Sarah/Console.lua"
        deployed_console.write_text("old deployed code\n", encoding="utf-8")

        with patch("preflight.get_git_info", return_value=self._mock_git()), \
             patch("preflight.check_game_processes", return_value=self._mock_processes_clean()):
            data = preflight.run_preflight(self.mock_repo, self.mock_runtime)

        self.assertFalse(data["ready"])
        self.assertEqual(data["overall"], "BLOCKED")
        self.assertEqual(data["checks"]["deployed_files"]["status"], "different")
        self.assertIn("42/media/lua/client/Sarah/Console.lua", data["checks"]["deployed_files"]["mismatched_files"])
        self.assertTrue(any("differ from source" in b for b in data["blockers"]))

    def test_missing_deployed_file(self):
        """Missing deployed file is detected and blocks readiness."""
        deployed_ui = self.mock_runtime / "isolated/mods/SarahFoundation/42/media/lua/shared/Translate/EN/UI.json"
        deployed_ui.unlink()

        with patch("preflight.get_git_info", return_value=self._mock_git()), \
             patch("preflight.check_game_processes", return_value=self._mock_processes_clean()):
            data = preflight.run_preflight(self.mock_repo, self.mock_runtime)

        self.assertFalse(data["ready"])
        self.assertEqual(data["checks"]["deployed_files"]["status"], "missing")
        self.assertIn("42/media/lua/shared/Translate/EN/UI.json", data["checks"]["deployed_files"]["missing_files"])

    def test_probe_detection(self):
        """Temporary probe in deployed mod directory is detected and blocks readiness."""
        probe_file = self.mock_runtime / "isolated/mods/SarahFoundation/42/media/lua/client/ZZSarahEscapeProbe.lua"
        probe_file.write_text("-- probe", encoding="utf-8")

        with patch("preflight.get_git_info", return_value=self._mock_git()), \
             patch("preflight.check_game_processes", return_value=self._mock_processes_clean()):
            data = preflight.run_preflight(self.mock_repo, self.mock_runtime)

        self.assertFalse(data["ready"])
        self.assertEqual(data["checks"]["temporary_probes"]["status"], "probes_detected")
        self.assertTrue(any("ZZSarahEscapeProbe.lua" in p for p in data["checks"]["temporary_probes"]["probes_found"]))
        self.assertTrue(any("temporary probes detected" in b.lower() for b in data["blockers"]))

    def test_game_process_running(self):
        """Running game process is detected and blocks readiness."""
        mock_proc = {
            "status": "running",
            "running_processes": [{"name": "javaw.exe", "pid": "12345"}],
            "query_supported": True,
            "summary": "Game process running: javaw.exe (PID 12345)",
        }
        with patch("preflight.get_git_info", return_value=self._mock_git()), \
             patch("preflight.check_game_processes", return_value=mock_proc):
            data = preflight.run_preflight(self.mock_repo, self.mock_runtime)

        self.assertFalse(data["ready"])
        self.assertEqual(data["checks"]["game_processes"]["status"], "running")
        self.assertTrue(any("javaw.exe" in b for b in data["blockers"]))

    def test_missing_backups(self):
        """Missing or empty backups directory blocks readiness."""
        backups_dir = self.mock_runtime / "backups"
        shutil.rmtree(backups_dir)

        with patch("preflight.get_git_info", return_value=self._mock_git()), \
             patch("preflight.check_game_processes", return_value=self._mock_processes_clean()):
            data = preflight.run_preflight(self.mock_repo, self.mock_runtime)

        self.assertFalse(data["ready"])
        self.assertEqual(data["checks"]["backups"]["status"], "missing")
        self.assertTrue(any("backups" in b.lower() for b in data["blockers"]))

    def test_isolated_profile_misconfigured_mod(self):
        """Misconfigured default.txt without SarahFoundation blocks readiness."""
        default_txt = self.mock_runtime / "isolated/mods/default.txt"
        default_txt.write_text("VERSION = 1,\nmods\n{\n    mod = OtherMod,\n}\n", encoding="utf-8")

        with patch("preflight.get_git_info", return_value=self._mock_git()), \
             patch("preflight.check_game_processes", return_value=self._mock_processes_clean()):
            data = preflight.run_preflight(self.mock_repo, self.mock_runtime)

        self.assertFalse(data["ready"])
        self.assertEqual(data["checks"]["isolated_profile"]["status"], "misconfigured")

    def test_isolated_profile_missing_case(self):
        """Active save case not existing in Saves directory blocks readiness."""
        latest_save = self.mock_runtime / "isolated/latestSave.ini"
        latest_save.write_text("NonExistentCase\nRising\n", encoding="utf-8")

        with patch("preflight.get_git_info", return_value=self._mock_git()), \
             patch("preflight.check_game_processes", return_value=self._mock_processes_clean()):
            data = preflight.run_preflight(self.mock_repo, self.mock_runtime)

        self.assertFalse(data["ready"])
        self.assertEqual(data["checks"]["isolated_profile"]["status"], "missing_case")

    def test_individual_source_file_missing_blocks_readiness(self):
        """When an individual source file is missing from repository, preflight reports source_missing and blocks."""
        src_console = self.mock_repo / "foundation/SarahFoundation/42/media/lua/client/Sarah/Console.lua"
        src_console.unlink()

        with patch("preflight.get_git_info", return_value=self._mock_git()), \
             patch("preflight.check_game_processes", return_value=self._mock_processes_clean()):
            data = preflight.run_preflight(self.mock_repo, self.mock_runtime)

        self.assertFalse(data["ready"])
        self.assertEqual(data["overall"], "BLOCKED")
        self.assertEqual(data["checks"]["deployed_files"]["status"], "source_missing")
        self.assertEqual(data["checks"]["deployed_files"]["source_missing_count"], 1)
        self.assertIn("42/media/lua/client/Sarah/Console.lua", data["checks"]["deployed_files"]["source_missing_files"])
        self.assertTrue(any("source file(s) missing from repository" in b for b in data["blockers"]))

    def test_git_status_failure_reports_unknown(self):
        """When git status command fails, get_git_info reports status=unknown and dirty=unknown."""
        mock_head = subprocess.CompletedProcess(args=["git", "rev-parse", "HEAD"], returncode=0, stdout="mockcommit1234567890abcdef\n")
        mock_branch = subprocess.CompletedProcess(args=["git", "rev-parse", "--abbrev-ref", "HEAD"], returncode=0, stdout="main\n")
        mock_status_fail = subprocess.CompletedProcess(args=["git", "status", "--porcelain"], returncode=1, stdout="", stderr="git error")

        def mock_subprocess_run(cmd, *args, **kwargs):
            if "rev-parse" in cmd and "HEAD" in cmd and "--abbrev-ref" not in cmd:
                return mock_head
            elif "--abbrev-ref" in cmd:
                return mock_branch
            elif "status" in cmd:
                return mock_status_fail
            return subprocess.CompletedProcess(args=cmd, returncode=0, stdout="")

        with patch("subprocess.run", side_effect=mock_subprocess_run), \
             patch("shutil.which", return_value="/usr/bin/git"), \
             patch.dict(os.environ, {"SARAH_GIT": "git"}):
            git_info = preflight.get_git_info(self.mock_repo)

        self.assertTrue(git_info["available"])
        self.assertEqual(git_info["status"], "unknown")
        self.assertEqual(git_info["dirty"], "unknown")
        self.assertIn("Git status query failed", git_info["summary"])

        # Also verify evaluate_preflight treats unknown git as unverified and not ready
        with patch("preflight.get_git_info", return_value=git_info), \
             patch("preflight.check_game_processes", return_value=self._mock_processes_clean()):
            data = preflight.run_preflight(self.mock_repo, self.mock_runtime)

        self.assertFalse(data["ready"])
        self.assertEqual(data["overall"], "UNKNOWN")
        self.assertIn(git_info["summary"], data["unknowns"])

    def test_unknown_process_query_reports_unknown_overall(self):
        """When game process querying is unavailable (status=unknown), preflight reports UNKNOWN and not ready."""
        mock_proc_unknown = {
            "status": "unknown",
            "running_processes": [],
            "query_supported": False,
            "summary": "Process query unavailable; verify game is closed via task manager",
        }
        with patch("preflight.get_git_info", return_value=self._mock_git()), \
             patch("preflight.check_game_processes", return_value=mock_proc_unknown):
            data = preflight.run_preflight(self.mock_repo, self.mock_runtime)

        self.assertFalse(data["ready"])
        self.assertEqual(data["overall"], "UNKNOWN")
        self.assertIn(mock_proc_unknown["summary"], data["unknowns"])

    def test_unverified_test_report_commit_reports_unknown_overall(self):
        """When test report commit match cannot be verified, preflight reports UNKNOWN and not ready."""
        mock_git_unavail = {
            "available": False,
            "commit": "unavailable",
            "short_commit": "unavailable",
            "branch": "unavailable",
            "dirty": "unknown",
            "status": "unknown",
            "summary": "Git binary or repository metadata unavailable",
        }
        with patch("preflight.get_git_info", return_value=mock_git_unavail), \
             patch("preflight.check_game_processes", return_value=self._mock_processes_clean()):
            data = preflight.run_preflight(self.mock_repo, self.mock_runtime)

        self.assertFalse(data["ready"])
        self.assertEqual(data["overall"], "UNKNOWN")
        self.assertEqual(data["checks"]["test_report"]["status"], "unknown_commit")
        self.assertTrue(any("commit match cannot be verified" in u for u in data["unknowns"]))

    def test_passing_report_from_dirty_run_blocks_readiness(self):
        """A passing test report generated against a dirty working tree does NOT prove clean HEAD tested and blocks."""
        report_file = self.mock_repo / "tools/reports/test-report.json"
        dirty_run_data = {
            "git": {"commit": "mockcommit1234567890abcdef", "branch": "main", "dirty": True},
            "summary": {"overall": "passed", "total_checks": 153},
        }
        report_file.write_text(json.dumps(dirty_run_data), encoding="utf-8")

        with patch("preflight.get_git_info", return_value=self._mock_git()), \
             patch("preflight.check_game_processes", return_value=self._mock_processes_clean()):
            data = preflight.run_preflight(self.mock_repo, self.mock_runtime)

        self.assertFalse(data["ready"])
        self.assertEqual(data["overall"], "BLOCKED")
        self.assertEqual(data["checks"]["test_report"]["status"], "dirty_run")
        self.assertTrue(any("dirty working tree" in b for b in data["blockers"]))

    def test_readonly_invariant(self):
        """Preflight execution does NOT modify any source, runtime, or save files."""
        # Collect file hashes across entire mock environment before run
        before_hashes = {}
        for p in self.mock_root.rglob("*"):
            if p.is_file() and not p.is_relative_to(self.reports_dir):
                before_hashes[str(p)] = preflight.sha256_file(p)

        with patch("preflight.get_git_info", return_value=self._mock_git()), \
             patch("preflight.check_game_processes", return_value=self._mock_processes_clean()):
            preflight.run_preflight(self.mock_repo, self.mock_runtime)

        # Collect file hashes after run
        after_hashes = {}
        for p in self.mock_root.rglob("*"):
            if p.is_file() and not p.is_relative_to(self.reports_dir):
                after_hashes[str(p)] = preflight.sha256_file(p)

        self.assertEqual(before_hashes, after_hashes, "Preflight modified files in repository or runtime!")

    def test_report_formatting(self):
        """Preflight generates properly structured Markdown report."""
        with patch("preflight.get_git_info", return_value=self._mock_git()), \
             patch("preflight.check_game_processes", return_value=self._mock_processes_clean()):
            data = preflight.run_preflight(self.mock_repo, self.mock_runtime)

        md = preflight.format_markdown_report(data)
        self.assertIn("# Project Sarah Native Acceptance Preflight Report", md)
        self.assertIn("READY", md)
        self.assertIn("Inspection Details", md)
        self.assertIn("Git State", md)
        self.assertIn("File Deployment", md)

    def test_cli_execution_with_reports(self):
        """CLI invocation executes cleanly, generates reports, and respects exit flags."""
        cmd = [
            sys.executable,
            str(PREFLIGHT_SCRIPT),
            "--repo-root", str(self.mock_repo),
            "--runtime-root", str(self.mock_runtime),
            "--reports-dir", str(self.reports_dir),
            "--no-strict",
        ]
        with patch.dict(os.environ, {"SARAH_GIT": "none"}):
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=10)

        self.assertEqual(r.returncode, 0)
        self.assertIn("Project Sarah Native Acceptance Preflight", r.stdout)
        self.assertTrue((self.reports_dir / "preflight-report.json").is_file())
        self.assertTrue((self.reports_dir / "preflight-report.md").is_file())


if __name__ == "__main__":
    unittest.main()
