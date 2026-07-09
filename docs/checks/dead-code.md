# CHECK: Dead Code

**Purpose**: Detect code left dead by the current branch's own iteration —
artifacts of previous design attempts — and report them for user review.

**Reasoning**: Agents left to their own devices frequently iterate on their own
design without correctly cleaning up artifacts of previous attempts: superseded
functions, orphaned helpers, unused imports, commented-out blocks. This check
surfaces those artifacts before a spec is marked done.

**Mode**: Report-only. Unlike
[local-test-quality](local-test-quality.md), this check never deletes or edits
code. It summarizes and lists findings for the user's review; deletion happens
only after the user explicitly approves specific findings.

**When to run**: After implementation reaches green (all tests passing), before
the spec's *Definition of Done* — dead code can't be judged until the final
design has settled. Re-run if the implementation is reworked afterward.

## Scope

The whole repo is scanned (a branch change can orphan pre-existing code), but
every finding is classified by attribution to the branch:

- **(a) Introduced by the branch** — new code that nothing references.
- **(b) Orphaned by the branch** — pre-existing code whose last caller was
  removed or replaced on this branch.
- **(c) Pre-existing dead code** — was already dead before this branch; listed
  as candidates for a follow-up cleanup spec, since deleting it exceeds the
  current spec's *Module Decomposition* scope.

## Procedure

1. **Compute the branch diff.**

   ```bash
   BASE=$(git merge-base HEAD origin/main 2>/dev/null || git merge-base HEAD main)
   git diff --name-only "$BASE"..HEAD
   git diff "$BASE"..HEAD
   ```

2. **Tool pass.** Run `poetry run ruff check .` — the repo's select list already
   flags unused imports (`F401`), unused variables (`F841`), and unused
   arguments (`ARG`). Record hits, and also grep the branch diff for new
   `noqa` comments suppressing those codes: a suppression is a finding, not an
   exemption.

3. **Reference pass.** For every `def` / `class` added or modified on the
   branch, search the repo for references outside its own definition. Flag:
   - symbols with zero references anywhere;
   - symbols referenced **only from tests** — production code that exists to
     satisfy a test is a design smell (flag it; the resolution belongs to the
     user);
   - modules no other module imports;
   - versioned-name artifacts: `foo_v2` / `foo_new` / `foo_old` / `_legacy`
     siblings where only one variant has callers — the signature of an
     abandoned design iteration.

4. **Texture pass** over the branch diff:
   - commented-out code blocks;
   - unreachable code: `if False:` / `if 0:` branches, statements after an
     unconditional `return` / `raise` / `continue`;
   - `__all__` entries naming symbols that no longer exist;
   - TODO/FIXME markers referring to approaches the branch has since abandoned.

5. **Implicit-reference screen.** Before classifying any symbol as dead, check
   it against references that don't appear as call sites:
   - `[project.scripts]` / entry points in `pyproject.toml`;
   - pytest fixtures (referenced by parameter name, never called) and
     `conftest.py` hooks;
   - dunder methods (called by the runtime);
   - `__init__.py` re-exports that the spec designates as public API.

   A symbol reachable through any of these is not dead — drop the finding.

6. **Summarize.** Compile the report in the format below and stop. **Apply no
   fixes.** Deletions the user approves are performed afterward as ordinary
   spec work, with `make check` run to prove nothing broke.

## Report Rules

- Every finding carries its evidence — the reference-search result showing zero
  callers — so the user can verify a finding without re-running the scan.
- A symbol the spec mandates (listed in *Module Decomposition* or an
  *Interface* block) that has no callers is not dead code; report it as a
  **spec-vs-implementation mismatch** to reconcile with the spec.
- Never resolve a finding by adding a caller to make code "used."
- Do not silently drop uncertain findings; report them with the uncertainty
  stated (e.g., "possibly reachable via reflection").

## Output

Summary counts by category, then one row per finding:

| Symbol / file | Category | Evidence | Suggested action |
|---------------|----------|----------|------------------|
| `src/resume_roast/parser.py::parse_v1` | (b) orphaned | only caller replaced by `parse` in `a1b2c3d`; repo-wide search: 0 references | delete after review |
| `src/resume_roast/utils.py::retry` | (c) pre-existing | 0 references at merge base and at HEAD | candidate for cleanup spec |

End with: "No changes were made. Awaiting review."
