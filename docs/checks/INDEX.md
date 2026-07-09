# Checks

<!-- Each file in this directory is an executable check prompt: a self-contained
     procedure an agent runs at a designated point in the spec workflow to
     validate (and where allowed, fix) work against the design principles and
     invariants. Files should be named kebab-case-title.md.

     Reference the relevant check from a spec's Test Plan or Execution Order so
     the agent knows when to run it.
-->

- [local-test-quality.md](local-test-quality.md) — Validates test code new to the current branch against DP-001/DP-002 and fixes violations in place.
- [dead-code.md](dead-code.md) — Detects code left dead by the branch's design iterations; report-only, findings go to the user for review.
- [local-doc-drift.md](local-doc-drift.md) — Verifies docs affected by the branch match its implementation; fixes description drift in place, contracts are never rewritten.
- [global-doc-drift.md](global-doc-drift.md) — Repo-wide audit of all docstrings and prose docs against the implementation; report-only.
- [workflow-conformance.md](workflow-conformance.md) — Verifies the branch's changes carry the workflow's required metadata (spec front-matter, sections, index entries, waivers, commit conventions); fixes mechanical gaps, reports judgment gaps.
- [code-review.md](code-review.md) — Reviews the branch diff for correctness, quality, and spec conformance; delivers an adversarially-hardened fix prompt, report-only.
