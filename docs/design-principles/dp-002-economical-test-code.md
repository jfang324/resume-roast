# DP-002: Economical Test Code

**Rule**: Structure test code with the same economy as production code —
parameterize repeated cases and reuse existing fixtures — so each behavior and
each piece of setup is stated exactly once.

**Reasoning**: Duplicated test bodies and copy-pasted setup make suites expensive
to change: one behavioral change forces N edits, drift between the copies hides
which differences are intentional, and reviewers stop reading near-identical
blocks. For an agent, duplication also inflates the diff and invites divergence
between cases that were meant to be uniform. Economy is subordinate to clarity —
a test must still read as a standalone Given/When/Then (see
[DP-001](dp-001-test-behavior-not-implementation.md)).

## Violation Signals

Concrete, grep-able or review-detectable patterns that indicate the principle
is being broken.

- Near-identical test functions differing only in literals
  (`test_parse_a` / `test_parse_b` / `test_parse_c` with the same body):
  - **How to fix**: Collapse into one `@pytest.mark.parametrize` with one case
    per acceptance example, using case `id`s that name the scenario.
- Inline setup that rebuilds what an existing fixture already provides
  (constructing the same object graph that a `conftest.py` fixture yields):
  - **How to fix**: Take the fixture as a parameter — but only when it fits
    naturally; see *When to Relax*.
- The same multi-line setup block copy-pasted across tests in a module:
  - **How to fix**: Extract a fixture or factory function in the nearest
    `conftest.py` (module-local if only one file needs it).
- Branching inside a parametrized test body (`if case == ...:` selecting
  different assertions): the cases are not the same behavior.
  - **How to fix**: Split into separate tests, one per behavior; parameterize
    only cases that share the same Given/When/Then shape.
- Fixture contortion: taking a fixture and then overriding most of its state to
  make it fit.
  - **How to fix**: Use local setup instead; a fixture that needs undoing is the
    wrong fixture.

## Examples

Concrete before/after or good/bad examples that illustrate the principle in
action.

| Avoid | Prefer |
|-------|--------|
| Three copies of the same test body with different input/output literals | `@pytest.mark.parametrize("raw, expected", [("a,b", ["a", "b"]), ("", []), ...], ids=[...])` |
| Building the same `User(...)` object graph inline in five tests | A `user` fixture in `conftest.py`, taken as a parameter |
| `if case == "empty": assert result == [] else: assert result == expected` inside one parametrized test | Two tests: `test_parse_empty_returns_empty_list` and a parametrized happy-path test |
| Taking the `user` fixture, then reassigning most of its fields | Local construction of the exact object the test needs |

## When to Relax

Conditions where bending this principle is acceptable. Without explicit approval in a spec, the default is to follow the principle.

- Clarity beats DRY in tests: a case whose setup or assertions differ
  meaningfully deserves its own named test, even if its inputs look similar to
  a parametrized group.
- When no existing fixture fits without overriding a substantial part of it,
  local setup is the correct choice — do not force reuse.
