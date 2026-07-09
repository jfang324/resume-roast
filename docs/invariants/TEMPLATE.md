# INV-{NNN}: {Descriptive Title}

**Invariant**: A single, testable statement of a property that must never be
violated.

**Scope**: Which modules, layers, or behaviors this invariant applies to.

## Rationale

Why this invariant exists — what breaks if it is violated, and what the
consequences would be.

## Enforcement Mechanism

How the invariant is enforced at the code level.

- **Type-level**: `NewType`, protocols, sealed classes, etc. (enforced at
  compile/check time).
- **Runtime guard**: Assertions, validation functions, `__post_init__` checks.
- **CI check**: Separate script, linter rule, or test suite.

Choose the strongest mechanism that is feasible.

## Failure Example

What a violation of this invariant looks like in practice. Useful for agents
to recognize when they are about to break it.

- _{Input/code pattern that violates the invariant.}_
- _{Expected failure mode (runtime error, test failure, silent corruption).}_

## Testing This Invariant

What tests to write and when they run. This complements *Enforcement
Mechanism*: enforcement is how code prevents violation; testing is how
the developer proves it works.

- **Key assertions**: Specific assert-level checks that must appear in tests.
  e.g., `assert decrypt(encrypt(x)) == x`.
- **Gating**: When are these tests run? (pre-commit, CI, nightly)

## Exceptions

- Any conditions under which this invariant may be relaxed. Exceptions must be
  explicit (gated behind a flag, clearly documented) and approved via spec
  discussion.
- When an exception is granted, this section must be updated to link back to
  the spec that authorized it.
