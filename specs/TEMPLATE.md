# SPEC-{NNN}: {Descriptive Title}

**Status**: pending | active | completed
**Created**: YYYY-MM-DD
**Commit(s)**: <!-- Populated on completion. One `- hash (description)` per commit. -->

## Summary

One-paragraph description of what this spec achieves and why it exists. Should be
understandable without reading any other file.

## Design Principles Referenced

Each principle is listed with its core rule and a brief note on how it applies to
this spec. The agent should read the linked doc if the application is unclear.

- [DP-{NNN}: {Title}](docs/design-principles/dp-{nnn}-title.md) — _{How/why this principle applies here.}_

## Invariants Referenced

- [INV-{NNN}: {Title}](docs/invariants/inv-{nnn}-title.md) — _{How/why this invariant must hold.}_

## Changes Required

### `{path/to/module.py}`

- **Interface**: Exact public API surface — function signatures, class names,
  method signatures, types, exception types. If the interface is not final,
  mark what is provisional.
- **Behavior**: What this code does, including happy path, error cases, and
  side effects (e.g., writes to disk, network calls, logging).
- **Data flow**: How data enters and leaves this module — call order, pipeline
  stages, transformation steps.
- **Edge cases**: Known edge cases the agent must handle (e.g., empty input,
  corrupt data, concurrent access, platform-specific paths).
- **Tests required**: Specific test scenarios that must exist. Key cases the
  reviewer will check. Coverage target if applicable.

### `{path/to/module2.py}`

- ...

## Definition of Done

All of these must be true for this spec to be marked completed:

- [ ] All tests pass (`make test` or equivalent).
- [ ] Coverage threshold met (see above).
- [ ] `make check` (lint + typecheck) passes with no new errors.
- [ ] Manual smoke test: {specific manual verification steps, if any}.
- [ ] No new lint warnings or type errors in changed files.

## Constraints

- List of hard constraints the implementation must obey.
- e.g., "No new third-party dependencies without approval."
- e.g., "All user-facing strings must be in `constants.py`."

## Dependencies

- SPEC-{NNN} — _{reason / must be completed first}_

## Footnotes

### Manual Corrections

Populated after agent completes implementation. Each entry documents something the
agent got wrong and how it was manually corrected. This serves as training signal
for future specs.

- `{commit ref}` — _{What was wrong and how it was fixed.}_
