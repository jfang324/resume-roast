# DP-001: Test Behavior, Not Implementation

**Rule**: Tests assert observable behavior at the module boundary — given inputs,
the outputs and effects promised by the spec's *Acceptance Examples* — never the
implementation that produces them.

**Reasoning**: Tests are the spec's success criteria. A test coupled to the
implementation breaks on refactors instead of bugs; a tautological test (expected
value recomputed with the implementation's own logic) can never fail; a vacuous
test passes against any implementation. All three satisfy the TDD ordering gate
(`make check-tdd`) while proving nothing, so test quality must be reviewed
against this principle immediately after test bodies are first authored — before
any production code exists, regardless of whether the tests fail.

## Violation Signals

Concrete, grep-able or review-detectable patterns that indicate the principle
is being broken.

- `assert_called_once` / `assert_called_with` / `call_count` on an internal
  collaborator: the test pins *how* the module works, not *what* it produces.
  - **How to fix**: Assert the boundary observable instead — return value,
    raised exception, or persisted state the caller can see.
- `mock.patch` targeting internals of the module under test (its own private
  functions or classes): the test freezes the current decomposition.
  - **How to fix**: Mock only true externals (network, clock, filesystem,
    third-party APIs) at the module boundary; let internals run for real.
- Tests reading private members (`obj._x`, `module._helper`): behavior invisible
  to callers is not behavior.
  - **How to fix**: Assert through the public API. If the private state matters,
    the spec is missing a public observable — amend the spec.
- Expected value computed in the test with the same algorithm the implementation
  uses (tautology): the test passes even when the shared logic is wrong.
  - **How to fix**: Use literal expected values copied from the spec's
    *Acceptance Examples*.
- Asserting incidental details — exact log or `repr` strings, ordering of
  unordered structures, timing: the test fails on harmless changes.
  - **How to fix**: Assert the semantic outcome (the record exists, the error
    type is raised, the set contains the element).
- A spec-promised effect (file write, DB row, state mutation, emitted event)
  with no assertion covering it: the behavior is half-tested, and regressions in
  the unasserted effect pass silently.
  - **How to fix**: Assert every consequential effect named in the spec's
    *Behavior* and *Acceptance Examples* for the scenario under test. If an
    effect that matters is missing from the spec, amend the spec first.
- Vacuous test: no realistic incorrect implementation would make it fail
  (e.g., asserting a call returned *something*, or re-asserting setup state).
  - **How to fix**: Strengthen or delete. Litmus test: for each test, name one
    plausible bug it would catch; if none can be named, it is not a test.

## Examples

Concrete before/after or good/bad examples that illustrate the principle in
action.

| Avoid | Prefer |
|-------|--------|
| `mock_repo.save.assert_called_once()` | `assert repo.get(record.id) == record` |
| `assert result == compute_expected(raw_input)` (same formula as the implementation) | `assert result == Result.ok("literal-from-spec")` |
| `assert parser._tokens == ["a", "b"]` | `assert parser.parse("a,b") == ["a", "b"]` |
| `assert "Processed 3 items in 0.2s" in caplog.text` | `assert processed.count == 3` |

## When to Relax

Conditions where bending this principle is acceptable. Without explicit approval in a spec, the default is to follow the principle.

- The outbound interaction *is* the contract: e.g., "must call the payment API
  exactly once per order." There the call assertion on that boundary **is** the
  observable behavior. The spec must state the interaction contract explicitly;
  record the relaxation in the spec's *Footnotes*.
