#!/usr/bin/env python3
"""Single-entry offline test runner for Project Sarah.

Executes offline test suites, verifies result summaries and exit codes,
and generates Markdown and JSON reports.
"""

import argparse
import datetime
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DOCUMENTED_PYTHON = Path(
    r"C:\Users\rudol\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
)

DEFAULT_SUITES = [
    "tools/test_foundation.py",
    "tools/test_render.py",
    "tools/test_checkpoint.py",
    "tools/test_commands.py",
    "tools/test_console.py",
    "tools/test_driver.py",
    "tools/test_follow.py",
    "tools/test_perception.py",
    "tools/test_coverage.py",
]

DISCLAIMER = "These are offline fixture checks and do not establish native gameplay acceptance."


def resolve_interpreter(explicit_python=None):
    """Resolve a Python interpreter without automatic installation."""
    if explicit_python:
        p = Path(explicit_python).expanduser().resolve()
        if not p.is_file():
            raise FileNotFoundError(f"Explicit Python interpreter not found: {explicit_python}")
        return p

    env_python = os.environ.get("SARAH_PYTHON")
    if env_python:
        p = Path(env_python).expanduser().resolve()
        if p.is_file():
            return p

    if DOCUMENTED_PYTHON.is_file():
        return DOCUMENTED_PYTHON

    current = Path(sys.executable).resolve()
    if current.is_file():
        return current

    which_py = shutil.which("python") or shutil.which("python3")
    if which_py:
        return Path(which_py).resolve()

    raise FileNotFoundError("Could not resolve a suitable Python interpreter.")


def get_git_info(repo_root):
    """Gather Git commit, branch, and dirty status without failing if git is missing."""
    info = {
        "available": False,
        "commit": "unavailable",
        "branch": "unavailable",
        "dirty": False,
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
        if r_head.returncode == 0 and r_head.stdout.strip():
            info["commit"] = r_head.stdout.strip()
            info["available"] = True
        else:
            return info

        r_br = subprocess.run(
            [git_bin, "branch", "--show-current"],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            timeout=5,
        )
        if r_br.returncode == 0 and r_br.stdout.strip():
            info["branch"] = r_br.stdout.strip()
        else:
            info["branch"] = "detached"

        r_st = subprocess.run(
            [git_bin, "status", "--porcelain"],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            timeout=5,
        )
        if r_st.returncode == 0:
            lines = [l for l in r_st.stdout.splitlines() if l.strip()]
            info["dirty"] = len(lines) > 0
    except (subprocess.SubprocessError, OSError):
        pass

    return info


def sanitize_path(path_obj_or_str, repo_root):
    """Sanitize path to avoid leaking machine-specific home directories."""
    p_str = str(path_obj_or_str).replace("\\", "/")
    root_str = str(repo_root).replace("\\", "/")
    if p_str.startswith(root_str):
        rel = p_str[len(root_str):].lstrip("/")
        return rel
    home_str = str(Path.home()).replace("\\", "/")
    if p_str.startswith(home_str):
        return "<home>" + p_str[len(home_str):]
    return p_str


def run_suite(interpreter, suite_path, repo_root, timeout=60):
    """Execute a single test suite, preserving real exit code and parsing summary."""
    start_time = time.perf_counter()
    env = os.environ.copy()
    deps_path = repo_root / "tools/dependencies/python"
    if deps_path.is_dir():
        existing_pypath = env.get("PYTHONPATH", "")
        env["PYTHONPATH"] = (
            str(deps_path) + (os.pathsep + existing_pypath if existing_pypath else "")
        )

    suite_name = sanitize_path(suite_path, repo_root)

    try:
        proc = subprocess.run(
            [str(interpreter), str(suite_path)],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env,
        )
        duration = round(time.perf_counter() - start_time, 3)
        stdout = proc.stdout or ""
        stderr = proc.stderr or ""
        returncode = proc.returncode

        matches = re.findall(r"^RESULT\s+(\d+)\s+.*passed", stdout, re.MULTILINE)
        check_count = int(matches[-1]) if matches else 0
        missing_summary = len(matches) == 0

        if returncode != 0:
            outcome = "failed"
            err_lines = [l for l in (stderr or stdout).splitlines() if l.strip()]
            details = err_lines[-1] if err_lines else f"Exited with code {returncode}"
            failure_reason = f"Process exit {returncode}: {details}"
        elif missing_summary:
            outcome = "failed"
            failure_reason = "Missing valid RESULT summary in output"
        elif check_count == 0:
            outcome = "failed"
            failure_reason = "Suite reported 0 passing checks"
        else:
            outcome = "passed"
            failure_reason = None

        return {
            "name": suite_name,
            "outcome": outcome,
            "checks": check_count,
            "duration_seconds": duration,
            "returncode": returncode,
            "failure_details": failure_reason,
            "stdout": stdout,
            "stderr": stderr,
        }

    except subprocess.TimeoutExpired as e:
        duration = round(time.perf_counter() - start_time, 3)
        return {
            "name": suite_name,
            "outcome": "failed",
            "checks": 0,
            "duration_seconds": duration,
            "returncode": -1,
            "failure_details": f"Timed out after {timeout} seconds",
            "stdout": e.stdout if isinstance(e.stdout, str) else "",
            "stderr": e.stderr if isinstance(e.stderr, str) else "",
        }
    except Exception as e:
        duration = round(time.perf_counter() - start_time, 3)
        return {
            "name": suite_name,
            "outcome": "failed",
            "checks": 0,
            "duration_seconds": duration,
            "returncode": -1,
            "failure_details": f"Execution error: {str(e)}",
            "stdout": "",
            "stderr": "",
        }


def generate_reports(report_dir, run_data):
    """Write concise Markdown and machine-readable JSON reports."""
    report_dir = Path(report_dir).resolve()
    report_dir.mkdir(parents=True, exist_ok=True)

    json_path = report_dir / "test-report.json"
    md_path = report_dir / "test-report.md"

    json_data = {
        "timestamp": run_data["timestamp"],
        "disclaimer": run_data["disclaimer"],
        "git": run_data["git"],
        "environment": run_data["environment"],
        "summary": run_data["summary"],
        "suites": [
            {
                "name": s["name"],
                "outcome": s["outcome"],
                "checks": s["checks"],
                "duration_seconds": s["duration_seconds"],
                "returncode": s["returncode"],
                "failure_details": s["failure_details"],
            }
            for s in run_data["suites"]
        ],
    }

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(json_data, f, indent=2)

    s = run_data["summary"]
    status_badge = "PASSED" if s["overall"] == "passed" else "FAILED"
    git_info = run_data["git"]
    git_str = (
        f"`{git_info['commit'][:7]}` (branch: `{git_info['branch']}`, dirty: `{git_info['dirty']}`)"
        if git_info["available"]
        else "unavailable"
    )

    md_lines = [
        "# Project Sarah Offline Verification Report",
        "",
        f"> **Notice**: {run_data['disclaimer']}",
        "",
        f"- **Overall Status**: **{status_badge}**",
        f"- **Timestamp**: {run_data['timestamp']}",
        f"- **Git Status**: {git_str}",
        f"- **Interpreter**: `{run_data['environment']['interpreter']}`",
        f"- **Total Checks**: **{s['total_checks']}** passed across {s['passed_suites']}/{s['total_suites']} suites",
        f"- **Total Duration**: {s['duration_seconds']}s",
        "",
        "## Suite Results",
        "",
        "| Suite | Outcome | Checks | Duration | Details |",
        "|---|---|---|---|---|",
    ]

    for suite in run_data["suites"]:
        outcome_str = "**PASS**" if suite["outcome"] == "passed" else "**FAIL**"
        details_str = suite["failure_details"] or "-"
        details_str = details_str.replace("|", "/")
        md_lines.append(
            f"| `{suite['name']}` | {outcome_str} | {suite['checks']} | {suite['duration_seconds']}s | {details_str} |"
        )

    md_lines.extend([
        "",
        "---",
        f"*Report generated by `tools/run_tests.py` at {run_data['timestamp']}*",
        "",
    ])

    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))

    return json_path, md_path


def main(argv=None):
    parser = argparse.ArgumentParser(description="Single-entry offline test runner for Project Sarah.")
    parser.add_argument("--python", dest="python", default=None, help="Explicit path to Python interpreter")
    parser.add_argument("--report-dir", dest="report_dir", default=None, help="Directory to save test reports (default: tools/reports)")
    parser.add_argument("--suites", dest="suites", nargs="+", default=None, help="Specific suite file(s) to execute")
    parser.add_argument("--timeout", dest="timeout", type=int, default=60, help="Per-suite timeout in seconds (default: 60)")
    parser.add_argument("--quiet", dest="quiet", action="store_true", help="Suppress streaming test output")
    parser.add_argument("--self-test", dest="self_test", action="store_true", help="Run runner self-tests (tools/test_runner.py)")

    args = parser.parse_args(argv)

    if args.self_test:
        self_test_path = REPO_ROOT / "tools/test_runner.py"
        py = resolve_interpreter(args.python)
        res = subprocess.run([str(py), str(self_test_path)], cwd=str(REPO_ROOT))
        return res.returncode

    try:
        interpreter = resolve_interpreter(args.python)
    except FileNotFoundError as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        return 1

    report_dir = Path(args.report_dir).resolve() if args.report_dir else REPO_ROOT / "tools/reports"

    suite_list = args.suites if args.suites else DEFAULT_SUITES
    resolved_suites = []
    for s in suite_list:
        p = Path(s)
        if not p.is_absolute():
            p = (REPO_ROOT / p).resolve()
        if not p.is_file():
            print(f"[ERROR] Suite file not found: {s}", file=sys.stderr)
            return 1
        resolved_suites.append(p)

    git_info = get_git_info(REPO_ROOT)
    sanitized_interpreter = sanitize_path(interpreter, REPO_ROOT)

    if not args.quiet:
        print("=" * 68)
        print("Project Sarah Offline Verification Runner")
        print(f"Interpreter: {sanitized_interpreter}")
        print(f"Git commit:  {git_info['commit'][:10] if git_info['available'] else 'unavailable'} (branch: {git_info['branch']}, dirty: {git_info['dirty']})")
        print(f"Suites:      {len(resolved_suites)} to run")
        print(f"Notice:      {DISCLAIMER}")
        print("=" * 68)

    overall_start = time.perf_counter()
    suites_results = []

    for suite_path in resolved_suites:
        res = run_suite(interpreter, suite_path, REPO_ROOT, timeout=args.timeout)
        suites_results.append(res)

        if not args.quiet:
            if res["outcome"] == "passed":
                print(f"  [PASS] {res['name']} ({res['checks']} checks, {res['duration_seconds']}s)")
            else:
                print(f"  [FAIL] {res['name']} ({res['duration_seconds']}s): {res['failure_details']}")

    overall_duration = round(time.perf_counter() - overall_start, 3)

    passed_suites = sum(1 for s in suites_results if s["outcome"] == "passed")
    failed_suites = sum(1 for s in suites_results if s["outcome"] == "failed")
    total_checks = sum(s["checks"] for s in suites_results if s["outcome"] == "passed")
    overall_status = "passed" if (failed_suites == 0 and passed_suites > 0) else "failed"

    timestamp_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

    run_data = {
        "timestamp": timestamp_iso,
        "disclaimer": DISCLAIMER,
        "git": git_info,
        "environment": {
            "interpreter": sanitized_interpreter,
            "platform": sys.platform,
        },
        "summary": {
            "overall": overall_status,
            "total_checks": total_checks,
            "passed_suites": passed_suites,
            "failed_suites": failed_suites,
            "total_suites": len(suites_results),
            "duration_seconds": overall_duration,
        },
        "suites": suites_results,
    }

    json_path, md_path = generate_reports(report_dir, run_data)

    if not args.quiet:
        print("-" * 68)
        if overall_status == "passed":
            print(f"OVERALL RESULT: PASSED ({total_checks} checks across {passed_suites} suites, {overall_duration}s)")
        else:
            print(f"OVERALL RESULT: FAILED ({failed_suites}/{len(suites_results)} suites failed, {overall_duration}s)")
        print(f"Reports generated:")
        print(f"  Markdown: {sanitize_path(md_path, REPO_ROOT)}")
        print(f"  JSON:     {sanitize_path(json_path, REPO_ROOT)}")
        print("=" * 68)

    return 0 if overall_status == "passed" else 1


if __name__ == "__main__":
    sys.exit(main())
