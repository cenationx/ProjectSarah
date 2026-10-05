## Latest offline baseline (2026-10-06, exposure probe)

Default runner includes13 suites and555 checks including48 exposure probe cases.
Runner self-tests:11; preflight self-tests:19. See EXPOSURE-PROBE-OFFLINE.md.
Actual Lua55 fixture execution remains distinct from native Kahlua acceptance.
Earlier totals below are historical.

## Latest offline baseline (2026-10-06, diagnostic sampler)

Default runner includes 12 suites and 507 checks, including 57 sampler fixtures.
Runner self-tests:11; preflight self-tests:19. See SAMPLER-OFFLINE.md for evidence
limits. These run the actual Lua modules through Lupa; native Kahlua/Java/runtime
acceptance remains separate. Earlier counts and examples below are historical.

## Latest offline baseline (2026-10-06, adapter boundary)

Default runner includes 11 suites and 450 checks, including 49 adapter boundary
fixtures. Runner self-tests:11; preflight self-tests:19. See ADAPTER-BOUNDARY-OFFLINE.md
for evidence limits; earlier totals below are historical.

## Latest offline baseline (2026-10-06)

Default runner now includes 10 suites and 401 checks, including 69 collector
fixtures. Runner self-tests:11; preflight self-tests:19. COLLECTOR-OFFLINE.md
records the inert scope and native limits; earlier example totals below are historical.

Current baseline (2026-10-06): 332 checks across 9 suites, including 64 offline
coverage checks, plus 11 runner and 19 preflight self-tests. Examples below with
smaller historical totals illustrate output format only. Coverage remains inert
and native gameplay acceptance is separate.

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

Self-tests keep temporary fixtures under ignored tools/reports/self-test-tmp and remove them after each test. Git dirty status includes tracked modifications and untracked files; ignored reports do not make the checkout dirty.

---

## 8. Native Acceptance Preflight Tool

Before conducting live gameplay acceptance in Project Zomboid, Codex runs the project-local read-only preflight tool to verify environment readiness:

```powershell
$sarahPython = 'C:\Users\rudol\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
& $sarahPython tools/preflight.py
```

### What It Checks (Strictly Read-Only)
- **Git State**: Clean commit, branch name, and dirty working tree status.
- **Offline Test Report**: Confirms `tools/reports/test-report.json` exists, passed, and matches current repository HEAD commit (detects stale reports).
- **Isolated Profile**: Verifies `runtime/isolated` configuration, active case existence (`SarahConsoleNativeCase` or `SarahSpaciousCase`), mod selection in `mods/default.txt` (`SarahFoundation` enabled), and key binding (`Sarah Console=key:67`).
- **File Deployment**: Computes SHA-256 hashes of all 9 required production files versus deployed files in `runtime/isolated/mods/SarahFoundation/` to ensure reviewed source code has been deployed before launching.
- **Temporary Probes**: Detects any diagnostic probes or temporary drivers in the active mod directory.
- **Backup Availability**: Confirms recent baseline backup existence in `runtime/backups/`.
- **Game Processes**: Inspects running processes (`javaw.exe`, `java.exe`, `ProjectZomboid64.exe`) to confirm the game is closed before deployment or pre-test backup.

### Reports Generated
- Markdown: `tools/reports/preflight-report.md`
- JSON: `tools/reports/preflight-report.json`

### Preflight Automated Tests
Unit tests in `tools/test_preflight.py` (19 checks) cover readiness detection, missing files (including missing individual source files), stale reports, dirty-run test reports, mismatched hashes, probe detection, active game processes, process query unknown states, Git status failure handling, and read-only file immutability:
```powershell
& $sarahPython tools/test_preflight.py
```

