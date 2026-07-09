# CHECK: Global Doc Drift

**Purpose**: Audit the entire repository's documentation — every docstring plus
all prose docs (`README.md`, `docs/**`) — for accuracy against the current
implementation, and report findings for user review.

**Reasoning**: [local-doc-drift](local-doc-drift.md) only sees what a branch
touched; drift also accumulates in the gaps — docs describing code no branch has
revisited, README claims outdated by several specs ago, index files missing
entries. A periodic whole-repo audit catches what the per-branch check cannot.

**Mode**: Report-only. This check never edits anything; findings go to the user
for review, and approved fixes are applied afterward (description fixes may then
be delegated back to [local-doc-drift](local-doc-drift.md)'s guardrails).

**When to run**: Periodically — after several specs complete, before a release
or milestone, or whenever documentation trust is in doubt. Not tied to a spec
or branch.

## Authority Rule

Same as [local-doc-drift](local-doc-drift.md): descriptions (docstrings, README,
guides) follow the code; contracts (specs, DP, INV docs) lead the code. A
contract-vs-code mismatch is reported as an implementation bug, not doc drift.

## Scope

The whole repository at HEAD — no branch restriction:

- every docstring in `src/` and `tests/` (module, class, function);
- `README.md`, `docs/development.md`, and all other prose under `docs/`;
- index and template integrity across `specs/` and the `docs/` categories;
- contract docs' claims about their own enforcement.

## Procedure

1. **Docstring sweep.** Enumerate every Python file under `src/` and `tests/`.
   For each docstring, verify: documented parameters exist with matching names
   and defaults; documented returns and raised exceptions match the code;
   described behavior and side effects are what the code does; docstring
   examples would produce the shown results.

2. **Prose command-and-path sweep.** For `README.md` and every doc under
   `docs/`: each referenced command exists (make targets in the `Makefile`,
   `poetry` invocations, entry points in `pyproject.toml`); each referenced
   file path exists; each code snippet matches the current interface; each
   described feature or behavior exists in the code.

3. **Cross-doc integrity.** Every `dp-`, `inv-`, check, and spec file appears
   exactly once in its category's `INDEX.md`, and every index entry points at a
   file that exists; all relative markdown links resolve; completed specs carry
   the metadata their template requires (e.g., populated *Commit(s)*).

4. **Contract self-consistency.** For each INV doc, verify the *Enforcement
   Mechanism* and *Testing This Invariant* claims: the named guard, check, or
   test actually exists and runs where the doc says it does. For each DP/check
   doc, verify tools and commands it cites (e.g., lint rules, scripts) are
   still configured.

5. **Summarize.** Compile the report below and stop. **Apply no fixes.**

## Report Rules

- Every finding carries its evidence (the claim, and what was actually found in
  code or config) so the user can verify without re-running the audit.
- Classify each finding: **description drift** (doc should change),
  **contract mismatch** (code should change — implementation bug), or
  **integrity gap** (missing index entry, broken link, absent metadata).
- Do not silently drop uncertain findings; state the uncertainty.
- Never resolve a finding by weakening the documentation's claim.

## Output

Summary counts by classification, then one row per finding:

| Doc location | Classification | Claim | Actual | Suggested fix |
|--------------|----------------|-------|--------|---------------|
| `README.md` | description drift | "run with `resume-roast --serve`" | no `--serve` flag exists | update README |
| `docs/invariants/inv-002-....md` | contract mismatch | "enforced by `__post_init__` guard" | no guard present in `Config` | implement the guard |
| `docs/design-principles/INDEX.md` | integrity gap | — | `dp-003-....md` exists but is unlisted | add index entry |

End with: "No changes were made. Awaiting review."
