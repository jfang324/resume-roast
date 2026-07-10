# Design Principles

<!-- Each file in this directory documents a single design principle: a rule with
     concrete examples. Files should be named dp-{nnn}-kebab-case-title.md.

     When writing a spec, reference the relevant DP docs so the agent can look
     them up if the brief explanation in the spec is insufficient.
-->

- [dp-001-test-behavior-not-implementation.md](dp-001-test-behavior-not-implementation.md) — Tests assert observable behavior at the module boundary, never the implementation that produces it.
- [dp-002-economical-test-code.md](dp-002-economical-test-code.md) — Parameterize repeated cases and reuse fitting fixtures so each behavior and setup is stated once.
- [dp-003-thin-cli-handlers.md](dp-003-thin-cli-handlers.md) — CLI handler methods parse, validate, and format only; they delegate all real work to the persistence/service layer beneath them.
