# SPEC-{NNN}: {Descriptive Title}

---
**Status**: pending | active | completed
**Created**: YYYY-MM-DD
**TDD**: required | optional
**Why optional** (conditional): _{Cite one of: pure refactor, rename, deps bump, doc-only change. If "required", omit this line.}_
**Commit(s)**: <!-- Populated on completion. One `- hash (description)` per commit. -->

## Summary

One-paragraph description of what this spec achieves and why it exists. Should be
understandable without reading any other file.

## Module Decomposition

Hard list of what this spec introduces, moves, or renames. The agent must not
add files outside this list without amending this section first.

- **New files**: _{`path/to/new_module.py` — purpose.}_
- **Renames / moves**: _{`old.py` → `new.py` — reason.}_
- **Explicit non-goals** (required): _{What this spec will NOT do. Critical for
  preventing agent over-implementation.}_

## Design Principles Referenced

Each principle is listed with its core rule and a brief note on how it applies to
this spec. The agent should read the linked doc if the application is unclear.

- [DP-{NNN}: {Title}](docs/design-principles/dp-{nnn}-title.md) — _{How/why this principle applies here.}_

## Invariants Referenced

- [INV-{NNN}: {Title}](docs/invariants/inv-{nnn}-title.md) — _{How/why this invariant must hold. Tie the invariant to a test scenario in the Test Plan below.}_

## Pre-implementation Self-Check

Before writing any code, the agent must verify each linked principle and
invariant applies to this spec and state how. If any link cannot be justified,
the spec must be amended or the link removed.

- DP-{NNN} — _{How this spec respects (or deliberately relaxes) this principle.}_
- INV-{NNN} — _{How this spec guarantees the invariant via tests.}_

## Test Plan (written first)

For each module under *Changes Required*, enumerate the test scenarios that must
be authored **before** any production code in that module lands. Each entry is
a scenario, not a method name — describe the observable behavior under test.

### `tests/test_{module}.py`

- `test_{scenario}_returns_{expected}` — _{Given {input}, when {action}, then {observable result}. Tie to INV-{NNN} if one applies.}_
- `test_{scenario}_raises_{X}_when_{Y}` — _{...}_
- ...

**Constraints**:

- Every *Acceptance Example* in *Changes Required* must map to at least one
  scenario here. If an example has no test, the spec is incomplete.
- Every linked INV-{NNN} must have a corresponding scenario whose purpose is
  enforcing it. Invariants without a test are treated as not enforced.
- A reviewer must be able to find red-then-green evidence: either separate
  commits (`test: ...` then `feat: ...`) on the branch, or `[red]` and `[green]`
  markers in a single commit message paired with a *Red/green record* note in
  this spec.

## Execution Order

Numbered checklist of the order in which files are produced. TDD order
(test-first, red, green) is part of this sequence.

1. _{Add `tests/test_X.py` first; observe failing locally.}_
2. _{Add `src/X.py` to satisfy tests.}_
3. _{Lint + typecheck clean-up.}_

## Changes Required

### `{path/to/module.py}`

- **Interface** (fenced code block required):

  ```python
  def example(input: str) -> Result: ...
  ```

- **Behavior**: What this code does, including happy path, error cases, and
  side effects (e.g., writes to disk, network calls, logging).
- **Acceptance Examples** (fenced input/output pairs required):

  ```text
  Input:  example("foo")
  Output: Result.ok(...)
  ```

  ```text
  Input:  example("")
  Output: raises ValueError("empty input")
  ```

- **Data flow**: How data enters and leaves this module — call order, pipeline
  stages, transformation steps.
- **Edge cases**: Known edge cases the agent must handle (e.g., empty input,
  corrupt data, concurrent access, platform-specific paths).
- **Strategy**: Implementation approach — libraries to use, patterns to follow,
  things to explicitly avoid. e.g., "Use PBKDF2HMAC with 600k iterations,
  not a custom hash."
- **Red/green record**: How the reviewer locates the failing-then-passing
  evidence for this module (commit hashes or `[red]/[green]` markers + spec
  note).
- **Tests required**: Cross-reference to the scenarios in *Test Plan*; this
  section exists to keep the linkage visible at the module level. Coverage
  target if applicable.

### `{path/to/module2.py}`

- ...

## Definition of Done

All of these must be true for this spec to be marked completed:

- [ ] All tests pass (`make test` or equivalent).
- [ ] Coverage threshold met (see above).
- [ ] `make check` (lint + typecheck) passes with no new errors.
- [ ] `make check-tdd` passes (TDD gate, see `docs/development.md`).
- [ ] Manual smoke test: {specific manual verification steps, if any}.
- [ ] No new lint warnings or type errors in changed files.
- [ ] Every *Acceptance Example* has a corresponding passing test.
- [ ] Every linked INV-{NNN} has a passing enforcement test.

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
