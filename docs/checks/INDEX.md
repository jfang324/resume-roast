# Checks

<!-- Each file in this directory is an executable check prompt: a self-contained
     procedure an agent runs at a designated point in the spec workflow to
     validate (and where allowed, fix) work against the design principles and
     invariants. Files should be named kebab-case-title.md.

     Reference the relevant check from a spec's Test Plan or Execution Order so
     the agent knows when to run it.
-->

- [local-test-quality.md](local-test-quality.md) — Validates test code new to the current branch against DP-001/DP-002 and fixes violations in place.
