# Desktop key-delivery diagnostic: 2026-10-04

Scope: installed Windows Computer Use plugin 26.930.31730 and Project Zomboid
42.21.0, isolated SarahConsoleNativeCase only. No normal profile or installed
files changed. This is a reproducible limitation report, not a repaired helper.

Observed with target window explicitly activated and visually inspected:
- press_key i hid the visible inventory bars. Ordinary key input reaches game.
- press_key F9 did not open Sarah Console, both paused and running.
- press_key Escape while running did not open the vanilla game menu.
- Physical F9/Escape work; user's latest fixed-console retest passes first
  Escape close and subsequent Escape normal menu. Raw probe corroborates console
  closure on physical Escape and guard=true. Automated Escape produced no new
  raw Escape transition in this probe's latest log.
- Screenshots and mouse work. Focus alone does not resolve special-key delivery.

Supported API: press_key({window,key}); no duration, repeat, key-down or key-up
parameter. Exact failure cause unknown: key translation/injection or polling
are possibilities. Do not claim short duration as established. Repeating tool
calls or Lua-triggered commands would not verify a real held physical key.

Required tool-side improvement: reliable special-key delivery plus documented
key-down/key-up or configurable hold duration, tested in this native game.
The installed skill requires Computer Use JS APIs for Windows automation and
prohibits a custom helper protocol client. No bundled helper/package edits,
extra input helper, or emergency-stop override were attempted. No bug report
was sent externally. Keep physical Escape separate from active Computer Use
calls, because it can stop the tool session.

Workaround: automate screenshots, mouse, working ordinary keys and scripted
policy tests; user performs the small physical F-key/Escape/hold subset.
Current game remains running and paused; observation probe remains deployed.

## Bounded raw-key comparison (Codex, 2026-10-04)

Read-only probe scans raw codes 1..255 each OnTick and records OnKeyPressed.
Physical held I validated it: down tick 5094, release event 5167, up 5168.
Initial automated I, F9, Tab and Return sequence produced no logged transitions;
HUD changes were observed but cannot alone establish matching raw-key delivery.
Later I control sequence produced code 23 down 5529, release 5623, up 5624.
This followed the user physical control and the automated I retry; source
attribution cannot be guaranteed if human input overlapped. No extra raw key
codes were observed during subsequent automated F9, F1 and Escape attempts.
F9 did not open console; Escape did not open vanilla menu. Probe recorded no
out-of-range or script errors during this test. Left was not tested.

Conclusion: ordinary I state can reach the game and probe, while special keys
remain unobserved under this API. Exact mapping/injection/timing cause unknown;
no helper repair demonstrated. No unsupported API or helper used. Keep the
physical-key workaround; do not change Sarah's production input path merely to
make automation pass. Evidence: ../evidence/input-comparison-summary.txt.

Game closed normally (SAVED a, GameThread exited; native window absent).
Final case: runtime/backups/input-comparison-20261004/After-comparison.
Raw log: runtime/input-comparison-console.txt. Input and Escape probes disabled
outside deployed mod. Production Escape fix remains deployed. No normal settings
or installed files changed. Next practical task: remaining slice A acceptance,
not further repetitions of unsupported hold/timing tests.
