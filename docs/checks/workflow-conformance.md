# CHECK: Workflow Conformance

**Purpose**: Verify that everything the current branch changed carries the
metadata and structure the workflow expects — spec front-matter, template
sections, index entries, waiver records, commit conventions — and fix the
mechanical gaps.

**Reasoning**: The workflow's guarantees live in its bookkeeping: a spec whose
*Commit(s)* line is empty can't be audited, an unlisted doc is invisible to the
next spec author, a mistyped commit prefix silently changes how `make
check-tdd` treats the commit. Agents reliably produce the artifact and
unreliably produce the paperwork around it.

**Mode**: Fixes mechanically derivable gaps in place (missing index entries,
malformed field formats). Anything requiring judgment — status decisions,
feature-mapping wording, waiver justifications — is reported for the user.

**When to run**: At the spec's *Definition of Done*, immediately before the
[code-review check](code-review.md). The repo-wide, periodic counterpart of
the integrity portion of this check is
[global-doc-drift](global-doc-drift.md) step 3.

## Scope

Everything added or modified on the current branch:

```bash
BASE=$(git merge-base HEAD origin/main 2>/dev/null || git merge-base HEAD main)
git diff --name-only "$BASE"..HEAD
git log --format='%h %s' "$BASE"..HEAD
```

## Procedure

1. **Spec conformance.** For each spec file the branch added or modified,
   against `specs/TEMPLATE.md`:
   - front-matter complete and well-formed: **Status** is one of
     `pending | active | completed`; **Created** is `YYYY-MM-DD`; **TDD** is
     `required | optional`, with the conditional **Why optional** line present
     exactly when optional; **Coverage target** stated;
   - every template section present; *Explicit non-goals* non-empty;
   - every referenced `DP-{NNN}` / `INV-{NNN}` link resolves, and each has its
     *Pre-implementation Self-Check* entry;
   - if **Status: completed**: *Commit(s)* populated with the branch's actual
     hashes, every *Definition of Done* checkbox ticked, and every Acceptance
     Example traceable to a Test Plan scenario.

2. **Doc-category conformance.** For each new or modified doc under
   `docs/design-principles/`, `docs/invariants/`, or `docs/checks/`:
   - it follows its category's `TEMPLATE.md` sections (checks follow the
     established Purpose / Mode / When to run / Scope / Procedure / Output
     shape);
   - its ID is unique and sequential within the category, and the filename
     matches the `dp-{nnn}-kebab-case-title.md` convention where one applies;
   - its category `INDEX.md` lists it exactly once, and no index entry points
     at a missing file (both directions, for entries the branch touched).

3. **Spec index.** If the branch completes a spec, `specs/INDEX.md` maps the
   affected feature(s) to it per that file's format comment.

4. **Waiver records.** For each check the workflow required on this branch
   (test-quality at red; dead-code, doc-drift, this check at green), confirm
   that any waivers it produced are recorded where its doc says they belong
   (spec *Footnotes*); if commit messages use `[red]`/`[green]` markers,
   confirm the spec's *Red/green record* names those commits.

5. **Commit conventions.** Every branch commit subject uses a conventional
   type prefix (`feat:`, `test:`, `chore:`, `docs:`, `ci:`, `build:`,
   `refactor:`, `style:`, `fix:`). Flag untyped or mistyped subjects — the
   TDD gate's exemptions key off these prefixes, so a wrong type is not
   cosmetic.

6. **Fix and report.** Apply mechanical fixes (index entries whose one-line
   description is evident from the doc itself, field format corrections,
   populating *Commit(s)* from `git log`). Report everything else.

## Fix Guardrails

- Never invent judgment content: status transitions, waiver justifications,
  feature-mapping descriptions, and *Why optional* reasons come from the user
  or the spec author — report their absence, don't fabricate them.
- Never tick a *Definition of Done* checkbox — checkboxes record that work
  happened, and this check cannot make work have happened.
- Commit messages are immutable history here: flag convention violations,
  never rewrite commits.

## Output

Fixes applied, then findings needing the user, each with its evidence:

| Location | Kind | Finding | Action |
|----------|------|---------|--------|
| `specs/spec-004-parser.md` | front-matter | *Commit(s)* empty; branch has 3 commits | populated from git log |
| `docs/checks/INDEX.md` | index | `new-check.md` exists but unlisted | entry added |
| `specs/spec-004-parser.md` | judgment | *Why optional* missing while `TDD: optional` | reported — needs author's reason |
| commit `a1b2c3d` | convention | subject has no type prefix | reported — immutable |
