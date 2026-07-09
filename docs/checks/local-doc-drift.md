# CHECK: Local Doc Drift

**Purpose**: Ensure documentation affected by the current branch matches the
branch's implementation, and fix drift in place.

**Reasoning**: Implementation moves during a spec; documentation written early
(or untouched elsewhere in the repo) silently goes stale. Drift caught at green
is a small edit; drift discovered later is misinformation with authority.

**Mode**: Fixes description-type drift directly (docstrings, README, guides).
Contract documents are never rewritten — see *Authority Rule*.

**When to run**: After implementation reaches green, before the spec's
*Definition of Done*. Re-run if the implementation is reworked afterward.

## Authority Rule

Documentation splits into two kinds, and drift direction decides the remedy:

- **Descriptions** — docstrings, `README.md`, `docs/development.md`: they follow
  the code. Stale description → fix the description.
- **Contracts** — the active spec's *Interface* / *Acceptance Examples*, DP and
  INV docs: the code follows them. Code contradicting a contract is an
  implementation bug — flag it for reconciliation; never edit the contract to
  match the code.

## Scope

Both directions of the branch diff against remote main:

1. **Code changed on the branch** → documentation that describes it (docstrings
   in the changed modules; README / guide sections mentioning the changed
   behavior, commands, or paths; the active spec).
2. **Docs changed on the branch** → their claims verified against the actual
   code.

## Procedure

1. **Compute the branch diff.**

   ```bash
   BASE=$(git merge-base HEAD origin/main 2>/dev/null || git merge-base HEAD main)
   git diff --name-only "$BASE"..HEAD
   ```

2. **Docstrings in changed source files.** For every module, class, and function
   touched by the branch, verify its docstring against the object itself:
   documented parameters exist with the right names and defaults; documented
   return values and raised exceptions match the code; described behavior and
   side effects are what the code does; any example in the docstring would
   actually produce the shown result.

3. **Prose docs referencing changed code.** For every symbol, command, CLI flag,
   or path the branch renamed, removed, or changed, search `README.md` and
   `docs/**/*.md` for mentions and verify each one still holds.

4. **Changed doc files.** For every `.md` file the branch touched, verify:
   referenced commands exist (make targets in the `Makefile`, `poetry` scripts,
   entry points in `pyproject.toml`); referenced paths exist; code snippets
   match current interfaces; relative links resolve.

5. **Authority screen.** Classify each mismatch using the *Authority Rule*.
   Contract mismatches are reported, not fixed.

6. **Fix and re-verify.** Edit descriptions in place to match the
   implementation, then run `make check` (docstring lint — `D401`, `D415` —
   applies to edited docstrings).

## Fix Guardrails

- Edit documentation text only. Never change code behavior to make a doc claim
  true — that is spec work, not drift repair.
- Never edit a contract document (spec Interface/Acceptance Examples, DP, INV)
  to match the code; report the mismatch instead.
- A fix must not drop information: if a docstring documents behavior the code
  genuinely has but the wording is stale, update the wording — don't delete the
  documentation.

## Output

Table of findings and actions, then any contract mismatches, then the
`make check` result:

| Doc location | Stale claim | Actual | Action |
|--------------|-------------|--------|--------|
| `src/resume_roast/parser.py::parse` docstring | "raises IOError on empty input" | raises `ValueError` | docstring updated |
| `docs/development.md` | `make lint-all` | target is `make lint` | command corrected |

**Contract mismatches** (not fixed — reconcile with the spec):

- _{contract doc + claim vs. observed code behavior.}_
