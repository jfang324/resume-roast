# CHECK: Spec Review

**Purpose**: Adversarially review a drafted spec before implementation begins,
so defects are caught at the only point where every downstream check can't —
upstream of the contract they all enforce.

**Reasoning**: Every other check validates conformance *to* the spec: tests
must use its acceptance-example literals, code-review flags divergence from its
interfaces, doc-drift treats it as authoritative. A wrong acceptance example is
therefore not caught downstream — it is rigorously enforced. Spec errors are
cheapest at draft time and compound afterward.

**Mode**: Report-only. The spec is the user's contract; this check prepares
findings for the user's review — it never amends the spec itself.

**When to run**: When a spec is drafted, before its **Status** moves
`pending → active` and before any test or implementation work starts. Re-run
after substantial spec amendments.

## Scope

The spec under review, its referenced DP/INV docs, and the existing code it
touches. Structural conformance (front-matter fields, required sections,
index entries) is owned by
[workflow-conformance](workflow-conformance.md) — spot a structural gap,
record a one-line pointer, and stay on semantics.

## Procedure

1. **Load context.** Read the spec in full, every DP/INV it references, and
   the existing files named in its *Existing Code* and *Module Decomposition*
   sections (verify those paths exist).

2. **Semantic review.** Work through the spec looking for:

   - **Example defects**: acceptance examples that contradict each other, the
     *Summary*, or the *Behavior* text; outputs that are wrong or unverifiable;
     examples not expressible as observable behavior at the module boundary.
   - **Interface defects**: fenced signatures that the examples don't actually
     use, types that don't compose across modules, interfaces the *Data flow*
     section can't be implemented against.
   - **Decomposition mismatches**: modules in *Changes Required* missing from
     *Module Decomposition* or vice versa; *Explicit non-goals* that are empty,
     vacuous, or fail to bound the obvious scope-creep directions.
   - **Coverage holes**: acceptance examples with no *Test Plan* scenario;
     linked INV-{NNN}s with no enforcing scenario; *Edge cases* mentioned in
     prose but absent from both examples and test plan.
   - **Ambiguity**: anything that would force the implementing agent to guess —
     unspecified error behavior, undefined terms, "handle appropriately".
   - **Dependency reality**: listed SPEC dependencies exist and are completed.

   Every finding needs a location (spec section), a severity
   (**blocker** / **should-fix** / **nit**), and concrete evidence.

3. **Adversarial hardening (max 3 rounds).**

   **Round 1**: spawn a fresh sub-agent with the spec and the findings draft,
   and this brief:

   > You are reviewing a spec-review findings list before it is delivered. For
   > every finding, verify it against the spec text and classify it CONFIRMED
   > or DISPUTED (state why). Then attack the spec itself two ways: (1) derive
   > any contradiction among the acceptance examples, interfaces, and prose;
   > (2) describe an implementation that satisfies every acceptance example
   > while still violating the spec's stated intent — if you can construct
   > one, the spec underspecifies, and that gap is a new finding. Push back
   > freely — a shorter, correct findings list beats a padded one.

   Resolve each response before the next round: re-check DISPUTED findings and
   drop them unless defensible with evidence; verify reviewer-added findings
   yourself. **Rounds 2–3**: continue the same reviewer with the revision;
   stop early on an all-CONFIRMED round with nothing added.

4. **Deliver.** Write the findings to `reports/spec-review-{NNN}.md` (the
   gitignored working-docs drawer; delete once acted on) and present them in
   full with a provenance note (findings count by severity, rounds run,
   dropped/added counts, CONTESTED items with both positions — the user is
   the tiebreaker).

## Report Rules

- Findings propose amendments; only the user applies them. The spec is not
  edited by this check.
- The "wrong-but-conforming implementation" probe (step 3) is the core value
  of the adversarial round — never skip it to save a round.
- Unresolved disputes after round 3 are marked `CONTESTED`, never silently
  kept or dropped.

## Output

The findings document, one row per finding:

| Spec section | Severity | Finding | Evidence | Suggested amendment |
|--------------|----------|---------|----------|---------------------|
| Acceptance Examples | blocker | examples 2 and 4 give different outputs for the same input class | `example("")` → `[]` vs `raises ValueError` | pick one; state the rule in *Behavior* |
| Non-goals | should-fix | section lists only "no UI changes" — does not bound persistence scope | Module Decomposition adds a storage module the Summary never mentions | add explicit persistence non-goal or justify the module |

End with: "No changes were made. Awaiting review."

## Termination

- Reviewer round returns all-CONFIRMED with no additions → deliver.
- 3 rounds completed → deliver with `CONTESTED` markers.
- The spec has no acceptance examples yet → report that it is not reviewable;
  a spec without examples is a summary, not a contract.
