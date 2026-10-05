#!/usr/bin/env python3
"""Project-local read-only acceptance preflight tool for Project Sarah.

Inspects Git state, test reports, isolated profile settings, production
versus deployed file hashes, temporary probes, backup availability,
and running game processes. Produces JSON and Markdown reports.

DOES NOT modify, deploy, backup, start, stop, or repair anything.
"""

import argparse
import datetime
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

REQUIRED_PRODUCTION_FILES = [
    "42/media/lua/client/SarahFoundation.lua",
    "42/media/lua/client/Sarah/Commands.lua",
    "42/media/lua/client/Sarah/Console.lua",
    "42/media/lua/client/Sarah/Engine.lua",
    "42/media/lua/client/Sarah/Lifecycle.lua",
    "42/media/lua/client/Sarah/Observations.lua",
    "42/media/lua/shared/Translate/EN/UI.json",
    "42/mod.info",
    "README.md",
]

TARGET_GAME_PROCESSES = ["javaw.exe", "java.exe", "ProjectZomboid64.exe"]


def sha256_file(filepath: Path) -> str:
    """Compute SHA-256 hash of a file."""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def get_git_info(repo_root: Path) -> dict:
    """Gather Git commit, branch, and dirty status without modifying anything."""
    info = {
        "available": False,
        "commit": "unavailable",
        "short_commit": "unavailable",
        "branch": "unavailable",
        "dirty": False,
        "status": "unknown",
        "summary": "Git binary or repository metadata unavailable",
    }

    env_git = os.environ.get("SARAH_GIT")
    if env_git in ("none", "unavailable", "0", ""):
        return info

    git_bin = None
    if env_git and Path(env_git).is_file():
        git_bin = str(Path(env_git).resolve())
    elif shutil.which("git"):
        git_bin = shutil.which("git")
    else:
        cache_git = (
            Path.home()
            / ".cache/codex-runtimes/codex-primary-runtime/dependencies/native/git/cmd/git.exe"
        )
        if cache_git.is_file():
            git_bin = str(cache_git)

    if not git_bin:
        return info

    try:
        r_head = subprocess.run(
            [git_bin, "rev-parse", "HEAD"],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            timeout=5,
        )
        if r_head.returncode != 0:
            return info
        commit = r_head.stdout.strip()

        r_branch = subprocess.run(
            [git_bin, "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            timeout=5,
        )
        branch = r_branch.stdout.strip() if r_branch.returncode == 0 else "unknown"

        r_status = subprocess.run(
            [git_bin, "status", "--porcelain"],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            timeout=5,
        )

        info["available"] = True
        info["commit"] = commit
        info["short_commit"] = commit[:7] if len(commit) >= 7 else commit
        info["branch"] = branch

        if r_status.returncode == 0:
            dirty = bool(r_status.stdout.strip())
            info["dirty"] = dirty
            info["status"] = "dirty" if dirty else "clean"
            info["summary"] = (
                f"Git is {info['status']} at {info['short_commit']} (branch: {branch})"
            )
        else:
            info["dirty"] = "unknown"
            info["status"] = "unknown"
            info["summary"] = (
                f"Git status query failed (exit {r_status.returncode}) at {info['short_commit']} (branch: {branch})"
            )
        return info
    except Exception as e:
        info["dirty"] = "unknown"
        info["status"] = "unknown"
        info["summary"] = f"Git inspection error: {e}"
        return info


def check_test_report(repo_root: Path, git_info: dict) -> dict:
    """Inspect tools/reports/test-report.json against Git state."""
    report_path = repo_root / "tools/reports/test-report.json"
    result = {
        "status": "missing",
        "path": "tools/reports/test-report.json",
        "exists": False,
        "commit": None,
        "short_commit": None,
        "matches_head": False,
        "overall": "unknown",
        "total_checks": 0,
        "summary": "Offline test report missing. Run tools/run_tests.py first.",
    }

    if not report_path.is_file():
        return result

    result["exists"] = True
    try:
        data = json.loads(report_path.read_text(encoding="utf-8"))
        rep_git = data.get("git", {})
        rep_commit = rep_git.get("commit")
        rep_dirty = rep_git.get("dirty", False)
        rep_summary = data.get("summary", {})
        overall = rep_summary.get("overall", "unknown")
        total_checks = rep_summary.get("total_checks", 0)

        result["commit"] = rep_commit
        result["short_commit"] = rep_commit[:7] if rep_commit and len(rep_commit) >= 7 else rep_commit
        result["report_dirty"] = rep_dirty
        result["overall"] = overall
        result["total_checks"] = total_checks

        if git_info.get("available") and git_info.get("commit") != "unavailable":
            head_commit = git_info["commit"]
            if rep_commit == head_commit:
                result["matches_head"] = True
                if rep_dirty:
                    result["status"] = "dirty_run"
                    result["summary"] = (
                        f"Unverified: test report for {result['short_commit']} was run against a dirty working tree, not clean HEAD. Re-run tools/run_tests.py on clean checkout."
                    )
                elif overall == "passed":
                    result["status"] = "synced"
                    result["summary"] = (
                        f"Synced: {total_checks} checks passed at {result['short_commit']}"
                    )
                else:
                    result["status"] = "failed"
                    result["summary"] = (
                        f"Failed: test report indicates overall status '{overall}'"
                    )
            else:
                result["matches_head"] = False
                result["status"] = "stale"
                result["summary"] = (
                    f"Stale: test report is for {result['short_commit']}, but repo HEAD is at {git_info['short_commit']}."
                )
        else:
            result["status"] = "unknown_commit"
            result["summary"] = (
                f"Present ({total_checks} checks, {overall}), but Git commit match cannot be verified."
            )
        return result
    except Exception as e:
        result["status"] = "corrupt"
        result["summary"] = f"Test report exists but is invalid JSON: {e}"
        return result


def check_isolated_profile(runtime_root: Path) -> dict:
    """Inspect isolated runtime profile, mod selection, and key settings."""
    iso_root = runtime_root / "isolated"
    result = {
        "status": "missing",
        "root_exists": False,
        "active_case": None,
        "case_exists": False,
        "default_mods": [],
        "foundation_enabled": False,
        "key_binding": None,
        "key_binding_valid": False,
        "options_exists": False,
        "summary": "Isolated runtime directory missing",
    }

    if not iso_root.is_dir():
        return result

    result["root_exists"] = True
    options_file = iso_root / "options.ini"
    result["options_exists"] = options_file.is_file()

    # Inspect latestSave.ini
    latest_save = iso_root / "latestSave.ini"
    active_case = None
    save_folder = "Rising"
    if latest_save.is_file():
        lines = [line.strip() for line in latest_save.read_text(encoding="utf-8", errors="replace").splitlines() if line.strip()]
        if len(lines) >= 1:
            active_case = lines[0]
        if len(lines) >= 2:
            save_folder = lines[1]
    result["active_case"] = active_case

    if active_case:
        case_dir = iso_root / "Saves" / save_folder / active_case
        result["case_exists"] = case_dir.is_dir()
    else:
        result["case_exists"] = False

    # Inspect mods/default.txt
    default_txt = iso_root / "mods/default.txt"
    mods_found = []
    if default_txt.is_file():
        content = default_txt.read_text(encoding="utf-8", errors="replace")
        for m in re.finditer(r"mod\s*=\s*([A-Za-z0-9_-]+)", content):
            mods_found.append(m.group(1))
    result["default_mods"] = mods_found
    result["foundation_enabled"] = ("SarahFoundation" in mods_found)

    # Inspect Lua/keysB42.ini
    keys_file = iso_root / "Lua/keysB42.ini"
    if keys_file.is_file():
        keys_content = keys_file.read_text(encoding="utf-8", errors="replace")
        m_bind = re.search(r"Sarah Console\s*=\s*(key:\d+)", keys_content)
        if m_bind:
            result["key_binding"] = m_bind.group(1)
            result["key_binding_valid"] = (m_bind.group(1) == "key:67")  # F9

    # Determine status
    if not result["active_case"] or not result["case_exists"]:
        result["status"] = "missing_case"
        result["summary"] = f"Active case '{active_case or 'none'}' does not exist under isolated Saves"
    elif not result["foundation_enabled"]:
        result["status"] = "misconfigured"
        result["summary"] = "SarahFoundation is not enabled in isolated mods/default.txt"
    elif not result["key_binding"]:
        result["status"] = "misconfigured"
        result["summary"] = "Sarah Console binding missing from isolated keysB42.ini"
    else:
        result["status"] = "ready"
        key_label = "F9" if result["key_binding"] == "key:67" else result["key_binding"]
        result["summary"] = (
            f"Configured for '{active_case}', SarahFoundation enabled, binding: {key_label}"
        )
    return result


def check_deployed_files(repo_root: Path, runtime_root: Path) -> dict:
    """Compare required production source files against deployed mod files."""
    src_root = repo_root / "foundation/SarahFoundation"
    dst_root = runtime_root / "isolated/mods/SarahFoundation"

    result = {
        "status": "synced",
        "total_required": len(REQUIRED_PRODUCTION_FILES),
        "matching_count": 0,
        "different_count": 0,
        "missing_count": 0,
        "source_missing_count": 0,
        "files": {},
        "mismatched_files": [],
        "missing_files": [],
        "source_missing_files": [],
        "summary": "",
    }

    if not src_root.is_dir():
        result["status"] = "source_missing"
        result["source_missing_count"] = len(REQUIRED_PRODUCTION_FILES)
        result["source_missing_files"] = list(REQUIRED_PRODUCTION_FILES)
        result["summary"] = "Production source directory foundation/SarahFoundation missing"
        return result

    if not dst_root.is_dir():
        result["status"] = "missing"
        result["missing_count"] = len(REQUIRED_PRODUCTION_FILES)
        result["missing_files"] = list(REQUIRED_PRODUCTION_FILES)
        result["summary"] = "Deployed mod directory runtime/isolated/mods/SarahFoundation missing"
        return result

    for rel_str in REQUIRED_PRODUCTION_FILES:
        rel_path = Path(rel_str)
        src_file = src_root / rel_path
        dst_file = dst_root / rel_path

        src_hash = None
        dst_hash = None
        file_status = "unknown"

        if src_file.is_file():
            src_hash = sha256_file(src_file)
        else:
            file_status = "source_missing"
            result["source_missing_count"] += 1
            result["source_missing_files"].append(rel_str)

        if file_status != "source_missing":
            if dst_file.is_file():
                dst_hash = sha256_file(dst_file)
                if src_hash == dst_hash:
                    file_status = "matching"
                    result["matching_count"] += 1
                else:
                    file_status = "different"
                    result["different_count"] += 1
                    result["mismatched_files"].append(rel_str)
            else:
                file_status = "missing"
                result["missing_count"] += 1
                result["missing_files"].append(rel_str)
        else:
            if dst_file.is_file():
                dst_hash = sha256_file(dst_file)
            else:
                result["missing_count"] += 1
                result["missing_files"].append(rel_str)

        result["files"][rel_str] = {
            "source_hash": src_hash[:8] if src_hash else None,
            "deployed_hash": dst_hash[:8] if dst_hash else None,
            "status": file_status,
        }

    if result["source_missing_count"] > 0:
        result["status"] = "source_missing"
        result["summary"] = (
            f"{result['source_missing_count']} production source file(s) missing from repository: {', '.join(result['source_missing_files'])}"
        )
    elif result["missing_count"] > 0:
        result["status"] = "missing"
        result["summary"] = (
            f"{result['missing_count']} deployed file(s) missing from isolated mod directory"
        )
    elif result["different_count"] > 0:
        result["status"] = "different"
        result["summary"] = (
            f"{result['different_count']} deployed file(s) differ from source: {', '.join(result['mismatched_files'])}"
        )
    else:
        result["status"] = "synced"
        result["summary"] = f"All {result['matching_count']} production files match deployed mod"

    return result


def check_temporary_probes(runtime_root: Path) -> dict:
    """Detect temporary probes or drivers inside the active mod directory."""
    dst_root = runtime_root / "isolated/mods/SarahFoundation"
    disabled_root = runtime_root / "disabled-probes"

    result = {
        "status": "clean",
        "probes_found": [],
        "disabled_probes_count": 0,
        "summary": "",
    }

    if disabled_root.is_dir():
        result["disabled_probes_count"] = sum(1 for p in disabled_root.iterdir() if p.is_file())

    if not dst_root.is_dir():
        result["status"] = "mod_missing"
        result["summary"] = "Deployed mod directory missing"
        return result

    probes = []
    for p in dst_root.rglob("*.lua"):
        name = p.name
        if "Probe" in name or "Driver" in name or name.startswith("ZZ"):
            probes.append(str(p.relative_to(dst_root)).replace("\\", "/"))

    result["probes_found"] = probes
    if probes:
        result["status"] = "probes_detected"
        result["summary"] = f"Temporary probes detected in active mod: {', '.join(probes)}"
    else:
        result["status"] = "clean"
        result["summary"] = (
            f"No temporary probes in active mod ({result['disabled_probes_count']} safely in disabled-probes)"
        )
    return result


def check_backups(runtime_root: Path) -> dict:
    """Inspect backup availability in runtime/backups/."""
    backups_root = runtime_root / "backups"
    result = {
        "status": "missing",
        "total_backups": 0,
        "latest_backup": None,
        "summary": "Backup directory missing or empty",
    }

    if not backups_root.is_dir():
        return result

    backup_dirs = [d for d in backups_root.iterdir() if d.is_dir()]
    result["total_backups"] = len(backup_dirs)

    if backup_dirs:
        # Sort by mtime (fallback to name)
        sorted_dirs = sorted(backup_dirs, key=lambda d: (d.stat().st_mtime, d.name))
        result["latest_backup"] = sorted_dirs[-1].name
        result["status"] = "available"
        result["summary"] = (
            f"{len(backup_dirs)} backup(s) available (latest: {result['latest_backup']})"
        )
    return result


def check_game_processes(target_names=None) -> dict:
    """Read-only check if game processes are currently running."""
    targets = target_names or TARGET_GAME_PROCESSES
    result = {
        "status": "clean",
        "running_processes": [],
        "query_supported": False,
        "summary": "",
    }

    if sys.platform == "win32":
        try:
            # Run tasklist with CSV output and filter
            r = subprocess.run(
                ["tasklist", "/FO", "CSV", "/NH"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if r.returncode == 0:
                result["query_supported"] = True
                running = []
                for line in r.stdout.splitlines():
                    line = line.strip()
                    if not line:
                        continue
                    parts = [p.strip(' "') for p in line.split('","')]
                    if len(parts) >= 2:
                        img_name, pid_str = parts[0], parts[1]
                        for tgt in targets:
                            if img_name.lower() == tgt.lower():
                                running.append({"name": img_name, "pid": pid_str})
                result["running_processes"] = running
                if running:
                    result["status"] = "running"
                    desc = ", ".join(f"{p['name']} (PID {p['pid']})" for p in running)
                    result["summary"] = f"Game process currently running: {desc}"
                else:
                    result["status"] = "clean"
                    result["summary"] = "No game processes running (game is CLOSED)"
                return result
        except Exception:
            pass

    # Fallback or non-Windows platform
    try:
        r = subprocess.run(["ps", "-A"], capture_output=True, text=True, timeout=5)
        if r.returncode == 0:
            result["query_supported"] = True
            running = []
            for line in r.stdout.splitlines():
                for tgt in targets:
                    base_tgt = tgt.replace(".exe", "").lower()
                    if base_tgt in line.lower():
                        parts = line.strip().split()
                        pid_str = parts[0] if parts else "?"
                        running.append({"name": tgt, "pid": pid_str})
            result["running_processes"] = running
            if running:
                result["status"] = "running"
                result["summary"] = f"Game process running: {len(running)} found"
            else:
                result["status"] = "clean"
                result["summary"] = "No game processes running"
            return result
    except Exception:
        pass

    result["status"] = "unknown"
    result["summary"] = "Process query unavailable; verify game is closed via task manager"
    return result


def evaluate_preflight(checks: dict) -> dict:
    """Evaluate overall readiness and collect blocking reasons, unverified checks, and warnings."""
    blockers = []
    unknowns = []
    warnings = []

    # 1. Git State
    git_st = checks["git"]["status"]
    if git_st == "dirty":
        blockers.append("Git working tree is dirty (uncommitted or untracked changes).")
    elif git_st == "unknown" or not checks["git"].get("available", True):
        unknowns.append(checks["git"]["summary"])

    # 2. Test Report
    rep_st = checks["test_report"]["status"]
    if rep_st == "missing":
        blockers.append("Offline test report is missing. Run tools/run_tests.py before native testing.")
    elif rep_st == "stale":
        blockers.append(checks["test_report"]["summary"])
    elif rep_st == "failed":
        blockers.append("Offline test suite has failed checks; fix issues before native testing.")
    elif rep_st == "corrupt":
        blockers.append(checks["test_report"]["summary"])
    elif rep_st == "dirty_run":
        blockers.append(checks["test_report"]["summary"])
    elif rep_st in ("unknown_commit", "unknown"):
        unknowns.append(checks["test_report"]["summary"])

    # 3. Isolated Profile
    prof_st = checks["isolated_profile"]["status"]
    if prof_st in ("missing", "missing_case", "misconfigured"):
        blockers.append(checks["isolated_profile"]["summary"])

    # 4. Deployed Files
    dep_st = checks["deployed_files"]["status"]
    if dep_st in ("missing", "source_missing", "different"):
        blockers.append(checks["deployed_files"]["summary"])

    # 5. Probes
    prb_st = checks["temporary_probes"]["status"]
    if prb_st in ("probes_detected", "mod_missing"):
        blockers.append(checks["temporary_probes"]["summary"])

    # 6. Backups
    bak_st = checks["backups"]["status"]
    if bak_st == "missing":
        blockers.append("No baseline backups available in runtime/backups/.")

    # 7. Game Processes
    proc_st = checks["game_processes"]["status"]
    if proc_st == "running":
        blockers.append(checks["game_processes"]["summary"])
    elif proc_st == "unknown":
        unknowns.append(checks["game_processes"]["summary"])

    if blockers:
        overall = "BLOCKED"
        is_ready = False
    elif unknowns:
        overall = "UNKNOWN"
        is_ready = False
    else:
        overall = "READY"
        is_ready = True

    return {
        "ready": is_ready,
        "overall": overall,
        "blockers": blockers,
        "unknowns": unknowns,
        "warnings": warnings,
    }


def run_preflight(repo_root=None, runtime_root=None) -> dict:
    """Perform the full read-only preflight inspection."""
    repo = Path(repo_root or REPO_ROOT).resolve()
    runtime = Path(runtime_root or (repo / "runtime")).resolve()

    timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
    git_info = get_git_info(repo)
    test_report_info = check_test_report(repo, git_info)
    profile_info = check_isolated_profile(runtime)
    deployed_info = check_deployed_files(repo, runtime)
    probes_info = check_temporary_probes(runtime)
    backups_info = check_backups(runtime)
    process_info = check_game_processes()

    checks = {
        "git": git_info,
        "test_report": test_report_info,
        "isolated_profile": profile_info,
        "deployed_files": deployed_info,
        "temporary_probes": probes_info,
        "backups": backups_info,
        "game_processes": process_info,
    }

    eval_result = evaluate_preflight(checks)

    return {
        "timestamp": timestamp,
        "notice": "Read-only acceptance preflight report; no files, saves, or processes modified.",
        "overall": eval_result["overall"],
        "ready": eval_result["ready"],
        "blockers": eval_result["blockers"],
        "unknowns": eval_result["unknowns"],
        "warnings": eval_result["warnings"],
        "checks": checks,
    }


def format_markdown_report(data: dict) -> str:
    """Format concise Markdown report."""
    checks = data["checks"]
    status_icon = data["overall"]

    lines = [
        "# Project Sarah Native Acceptance Preflight Report",
        "",
        "> **Notice**: Read-only preflight inspection. No game files, saves, settings, or processes were modified.",
        "",
        f"- **Overall Readiness**: **{status_icon}**",
        f"- **Timestamp**: `{data['timestamp']}`",
        f"- **Git Status**: `{checks['git'].get('short_commit', 'unknown')}` ({checks['git'].get('status', 'unknown')})",
        f"- **Test Report**: `{checks['test_report'].get('status', 'unknown')}` ({checks['test_report'].get('total_checks', 0)} checks)",
        f"- **Isolated Profile**: `{checks['isolated_profile'].get('status', 'unknown')}` ({checks['isolated_profile'].get('active_case', 'none')})",
        f"- **File Deployment**: `{checks['deployed_files'].get('status', 'unknown')}` ({checks['deployed_files'].get('matching_count', 0)}/{checks['deployed_files'].get('total_required', 0)} matching)",
        f"- **Temporary Probes**: `{checks['temporary_probes'].get('status', 'unknown')}`",
        f"- **Backups**: `{checks['backups'].get('status', 'unknown')}` ({checks['backups'].get('total_backups', 0)} available)",
        f"- **Game Processes**: `{checks['game_processes'].get('status', 'unknown')}`",
        "",
        "## Inspection Details",
        "",
        "| Category | Status | Summary |",
        "|---|---|---|",
        f"| Git State | **{checks['git']['status'].upper()}** | {checks['git']['summary']} |",
        f"| Offline Test Report | **{checks['test_report']['status'].upper()}** | {checks['test_report']['summary']} |",
        f"| Isolated Profile | **{checks['isolated_profile']['status'].upper()}** | {checks['isolated_profile']['summary']} |",
        f"| File Deployment | **{checks['deployed_files']['status'].upper()}** | {checks['deployed_files']['summary']} |",
        f"| Temporary Probes | **{checks['temporary_probes']['status'].upper()}** | {checks['temporary_probes']['summary']} |",
        f"| Backup Availability | **{checks['backups']['status'].upper()}** | {checks['backups']['summary']} |",
        f"| Game Processes | **{checks['game_processes']['status'].upper()}** | {checks['game_processes']['summary']} |",
        "",
    ]

    if data["blockers"]:
        lines.append("## Readiness Blockers")
        lines.append("")
        for b in data["blockers"]:
            lines.append(f"- :x: {b}")
        lines.append("")

    if data.get("unknowns"):
        lines.append("## Unverified Checks (Not Ready)")
        lines.append("")
        for u in data["unknowns"]:
            lines.append(f"- :question: {u}")
        lines.append("")

    if data["warnings"]:
        lines.append("## Warnings")
        lines.append("")
        for w in data["warnings"]:
            lines.append(f"- :warning: {w}")
        lines.append("")

    lines.append("---")
    lines.append(f"*Report generated by `tools/preflight.py` at {data['timestamp']}*")
    lines.append("")
    return "\n".join(lines)


def print_terminal_summary(data: dict):
    """Print clean terminal summary banner."""
    checks = data["checks"]
    print("=" * 68)
    print("Project Sarah Native Acceptance Preflight (Read-Only)")
    git_sum = f"{checks['git'].get('short_commit', 'unknown')} ({checks['git'].get('branch', 'unknown')}, {checks['git'].get('status', 'unknown')})"
    print(f"Git commit:  {git_sum}")
    print("Notice:      Read-only preflight inspection; no files or processes modified.")
    print("=" * 68)

    def print_item(label, st, summary):
        tag = "[PASS]" if st in ("clean", "synced", "ready", "available") else "[WARN]" if st in ("stale", "different", "dirty_run", "unknown", "unknown_commit") else "[FAIL]"
        print(f"  {tag:<7} {label}: {st} ({summary})")

    print_item("Git State", checks["git"]["status"], checks["git"]["summary"])
    print_item("Test Report", checks["test_report"]["status"], checks["test_report"]["summary"])
    print_item("Isolated Profile", checks["isolated_profile"]["status"], checks["isolated_profile"]["summary"])
    print_item("File Deployment", checks["deployed_files"]["status"], checks["deployed_files"]["summary"])
    print_item("Temporary Probes", checks["temporary_probes"]["status"], checks["temporary_probes"]["summary"])
    print_item("Backup Availability", checks["backups"]["status"], checks["backups"]["summary"])
    print_item("Game Processes", checks["game_processes"]["status"], checks["game_processes"]["summary"])

    print("-" * 68)
    if data["ready"]:
        print("OVERALL PREFLIGHT: READY FOR NATIVE ACCEPTANCE")
    elif data["overall"] == "UNKNOWN":
        print(f"OVERALL PREFLIGHT: UNKNOWN ({len(data.get('unknowns', []))} essential check(s) unverified / not-ready)")
        for u in data.get("unknowns", []):
            print(f"  - {u}")
    else:
        print(f"OVERALL PREFLIGHT: BLOCKED ({len(data['blockers'])} item(s) require action)")
        for b in data["blockers"]:
            print(f"  - {b}")
    print("Reports generated:")
    print("  Markdown: tools/reports/preflight-report.md")
    print("  JSON:     tools/reports/preflight-report.json")
    print("=" * 68)


def main():
    parser = argparse.ArgumentParser(description="Read-only acceptance preflight tool.")
    parser.add_argument("--repo-root", default=str(REPO_ROOT), help="Repository root path.")
    parser.add_argument("--runtime-root", default=None, help="Runtime root path.")
    parser.add_argument("--reports-dir", default=None, help="Reports output directory.")
    parser.add_argument("--quiet", "-q", action="store_true", help="Suppress terminal output.")
    parser.add_argument("--no-strict", action="store_true", help="Always exit 0 regardless of blockers.")

    args = parser.parse_args()
    repo_path = Path(args.repo_root).resolve()
    runtime_path = Path(args.runtime_root).resolve() if args.runtime_root else repo_path / "runtime"
    reports_dir = Path(args.reports_dir).resolve() if args.reports_dir else repo_path / "tools/reports"

    data = run_preflight(repo_path, runtime_path)

    # Write reports under reports_dir (ignored by Git)
    reports_dir.mkdir(parents=True, exist_ok=True)
    json_path = reports_dir / "preflight-report.json"
    md_path = reports_dir / "preflight-report.md"

    json_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    md_path.write_text(format_markdown_report(data), encoding="utf-8")

    if not args.quiet:
        print_terminal_summary(data)

    if not args.no_strict and not data["ready"]:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
