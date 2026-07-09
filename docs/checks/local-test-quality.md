# CHECK: Local Test Quality

**Purpose**: Validate all test code introduced on the current branch against the
testing design principles, and fix any violations in place.

**Principles enforced**:

- [DP-001: Test Behavior, Not Implementation](../design-principles/dp-001-test-behavior-not-implementation.md)
- [DP-002: Economical Test Code](../design-principles/dp-002-economical-test-code.md)

**When to run**: Immediately after test bodies are first authored — before any
production code, regardless of whether the tests fail — and again before pushing
if test files changed since the last run.

## Scope

Test code from commits on the current branch that are not on the remote main
branch, restricted to `tests/`. Existing tests untouched by the branch are out
of scope.

## Procedure

1. **Gather the diff.** Compute the base and collect changed test files:

   ```bash
   BASE=$(git merge-base HEAD origin/main 2>/dev/null || git merge-base HEAD main)
   git diff --name-only "$BASE"..HEAD -- tests/
   git diff "$BASE"..HEAD -- tests/
   ```

   If no test files changed, report "nothing to check" and stop.

2. **Read context.** Read every changed test file in full (not just the diff
   hunks — a violation may span unchanged lines), the active `SPEC-{NNN}` if one
   exists (its *Test Plan*, *Acceptance Examples*, and linked invariants), and
   any `conftest.py` fixtures available to the changed files.

3. **Apply DP-001** (behavior, not implementation) to each new or modified test:
   walk its *Violation Signals* one by one — mock/call-count assertions on
   internals, patching the module under test, private-member access, tautological
   expected values, incidental-detail assertions, unasserted spec-promised
   effects, vacuous tests. For each test, run the litmus: name one plausible bug
   it would catch.

4. **Apply DP-002** (economical test code) across the changed files as a group:
   near-identical bodies → parametrize; setup duplicating an existing fixture →
   use the fixture (only if it fits without contortion); repeated setup blocks →
   extract a fixture; branching inside a parametrized body → split.

5. **Fix violations.** Edit the test code so every finding conforms, under the
   guardrails below. Prefer the *How to fix* listed on the matched signal.

6. **Re-verify.** Re-run steps 3–4 on the fixed files, then confirm the suite
   still collects and runs:

   ```bash
   poetry run pytest --collect-only -q
   make check
   ```

   At red stage, changed tests are expected to fail on assertions — collection
   errors, import errors, or fixture errors are not acceptable. `make check`
   test failures are acceptable only at red stage.

## Fix Guardrails

- Touch only files under `tests/`. Never modify production code or the spec's
  scenario list to make a finding disappear.
- Fixes must preserve each scenario's intent from the spec's *Test Plan*: same
  Given/When/Then, stronger or equal assertions. Weakening an assertion is not
  a fix.
- Delete a test only if it is vacuous **and** its scenario is covered by another
  test; otherwise strengthen it.
- If a violation traces back to the spec (e.g., a consequential effect missing
  from *Acceptance Examples*), stop and amend the spec first — do not invent
  expected behavior.
- A finding may be waived instead of fixed only per the principle's *When to
  Relax* conditions; record the waiver in the spec's *Footnotes*.

## Output

Report a table — one row per new/modified test — followed by the actions taken:

| Test | Verdict | Signal matched | Action |
|------|---------|----------------|--------|
| `test_parse_empty_returns_empty_list` | pass | — | none |
| `test_save_calls_repo` | violation | DP-001: call-count on internal | rewrote to assert persisted state |

List every applied fix with its file, and every waiver with its *Footnotes*
reference. End with the `pytest --collect-only` result.
