# Project Sarah: Offline Verification Workflow

This document details the single-entry verification workflow for Project Sarah, documenting how to run, configure, and troubleshoot the offline test suite.

---

## 1. Quick Start

Run the entire offline test suite with a single command from any working directory:

```powershell
& "C:\Users\rudol\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" tools/run_tests.py
```

Expected output:
```
====================================================================
Project Sarah Offline Verification Runner
Interpreter: <home>/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe
Git commit:  762e74c51d (branch: main, dirty: False)
Suites:      6 to run
Notice:      These are offline fixture checks and do not establish native gameplay acceptance.
====================================================================
  [PASS] tools/test_foundation.py (29 checks, 0.05s)
  [PASS] tools/test_render.py (15 checks, 0.05s)
  [PASS] tools/test_checkpoint.py (8 checks, 0.05s)
  [PASS] tools/test_commands.py (54 checks, 0.05s)
  [PASS] tools/test_console.py (19 checks, 0.05s)
  [PASS] tools/test_driver.py (14 checks, 0.06s)
--------------------------------------------------------------------
OVERALL RESULT: PASSED (139 checks across 6 suites, 0.30s)
Reports generated:
  Markdown: tools/reports/test-report.md
  JSON:     tools/reports/test-report.json
====================================================================
```

---

## 2. Python Interpreter Resolution & Overrides

The runner (`tools/run_tests.py`) resolves the Python interpreter in the following order:

1. **CLI Flag (`--python`)**:
   ```powershell
   & python tools/run_tests.py --python "C:\path\to\python.exe"
   ```
2. **Environment Variable (`SARAH_PYTHON`)**:
   ```powershell
   $env:SARAH_PYTHON = "C:\path\to\python.exe"
   & python tools/run_tests.py
   ```
3. **Documented Default Runtime**:
   `C:\Users\rudol\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe`
4. **Current Executable (`sys.executable`)** or system `PATH` lookup (`python` / `python3`).

*Note*: No packages are installed automatically. All suites import Lupa from the project-local `tools/dependencies/python` directory.

---

## 3. Command Options

| Flag | Default | Description |
|---|---|---|
| `--python PATH` | Documented runtime | Explicit path to Python interpreter |
| `--suites PATH ...` | All 6 suites | Run specific suite(s) |
| `--report-dir PATH` | `tools/reports` | Directory where markdown and JSON reports are saved |
| `--timeout SECONDS` | `60` | Per-suite timeout in seconds before terminating process |
| `--quiet` | `False` | Suppress per-suite progress streaming |
| `--self-test` | `False` | Execute the runner's self-test suite (`tools/test_runner.py`) |

---

## 4. Reports & Outputs

The runner generates two reports in the ignored project-local directory `tools/reports/`:
- **Markdown Report (`tools/reports/test-report.md`)**: Human-readable table summarizing overall status, git commit/branch, interpreter, per-suite check count, and execution time.
- **JSON Report (`tools/reports/test-report.json`)**: Machine-readable schema containing metadata, git state, per-suite return codes, check counts, and failure details.

The report directory `/tools/reports/` is explicitly ignored by Git in `.gitignore` to avoid publishing machine-specific paths or raw logs to version control.

---

## 5. Runner Self-Tests

The runner itself is covered by automated unit tests in `tools/test_runner.py` using standard library only (`unittest`, `subprocess`, `tempfile`, `json`). It uses isolated child-process fixtures to test:
1. Suite success and RESULT count extraction.
2. Non-zero exit codes.
3. Missing RESULT summary detection.
4. Unhandled child process crashes and tracebacks.
5. Per-suite timeout enforcement and process cleanup.
6. Execution with spaces in file paths and directories.
7. Invocation from foreign working directories.
8. Graceful handling of unavailable Git.
9. Multiple RESULT lines taking the final cumulative summary.

Run self-tests with:
```powershell
& "C:\Users\rudol\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" tools/run_tests.py --self-test
```

---

## 6. Failure Troubleshooting

- **Process exit code != 0**: A suite encountered an unhandled exception or failed assertion. Inspect child stderr output or review `failure_details` in `tools/reports/test-report.json`.
- **Missing valid RESULT summary**: The suite finished with exit code 0, but did not print a matching `RESULT <N> ... passed` line. The runner marks this as a failure.
- **Timed out after N seconds**: A suite exceeded the timeout limit (default 60s). Check for infinite loops or increase `--timeout`.
- **ModuleNotFoundError: No module named 'lupa'**: The selected Python interpreter does not support or locate `tools/dependencies/python/lupa`. Verify that the documented runtime or a compatible 64-bit Python is used.

---

## 7. Offline Checks vs. Native Gameplay Acceptance

> [!IMPORTANT]
> **These are offline fixture checks and do not establish native gameplay acceptance.**

- **Offline policy checks** (139 passing checks across 6 suites) exercise Lua modules, commands, state machines, and engine adapters within isolated Lupa runtimes against mock engine objects. They verify contracts, memory boundaries, lifecycle invalidation, error handling, and state preservation.
- **Native gameplay acceptance** requires launching the actual Project Zomboid 42.21.0 engine process in the isolated test case (`SarahConsoleNativeCase`), exercising physical key input, real Java thread scheduling, and engine timed action queues.
- **Slice C native acceptance remains PENDING** Codex live testing per [`docs/M1-slice-c-checklist.md`](file:///G:/Codex/Project%20Sarah/docs/M1-slice-c-checklist.md).
