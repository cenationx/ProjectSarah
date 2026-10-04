# Project Sarah: instructions for every coding agent

Read `docs/STATUS.md`, `docs/ROADMAP.md` and `docs/HANDOFF.md` before changing code.
These files are the shared project state; chat history is supplementary.

## Scope and safeguards

- Canonical workspace: `G:\Codex\Project Sarah`. Keep source, dependencies,
  probes, logs and backups under this project. Installed game files are read-only.
- The user has explicitly deferred the external AI layer. Do not install or
  implement a model, dialogue service or AI integration without a new explicit
  user instruction. Future AI milestones in the roadmap are proposals only.
- Focus on the smallest dependable single-player NPC foundation for PZ 42.21.0.
  Do not claim that the complete PZNS framework is compatible.
- Test only in the isolated profile documented in HANDOFF. Before any live test,
  close the test game, back up the disposable world, and document how to restore
  it. Never use or modify normal saves/settings. Preserve the latest test state
  before restoring an older backup.
- Keep original PZNS source and MIT notices intact. Sarah uses PolyForm
  Noncommercial; earlier MIT versions retain their existing permissions.
- Do not publish game binaries, decompiled game source, saves, raw machine logs,
  credentials or project-local dependencies. Respect `.gitignore`.

## Start and finish a work session

1. Inspect Git status, branch and recent commits; preserve other work. If another
   agent is active, do not edit the same checkout concurrently. Agree ownership
   or use a separate branch/worktree before parallel work.
2. Read the shared state files. Select one bounded next task from STATUS. Check
   local runtime state rather than assuming the notes are still current.
3. Run checks appropriate to the change. Distinguish automated policy tests,
   game API inspection, live gameplay tests and unverified behavior.
4. At each completed task, before a handoff, and periodically during long work,
   update STATUS with the exact state and next step. Keep ROADMAP milestone
   checkboxes synchronized. Update HANDOFF if setup or recovery steps changed.
5. Commit the source, documentation and relevant sanitized evidence together.
   Push the checkpoint when authorized (the user has requested shared Git
   checkpoints), and verify the remote branch matches. Do not force-push.
6. If interrupted before completion, mark work IN PROGRESS rather than DONE.
   Record modified files, tests run, failures, active processes, backup location
   and the next concrete action. An unfinished checkpoint may be committed with
   a clear WIP message; never describe it as tested or production-ready.

Always end with a short user-facing update: outcome, test boundary, checkpoint
commit and what remains. Update the files during work, not only at the very end;
an abrupt usage cutoff can occur before a final message.
