# CHECK: Code Review

**Purpose**: Review the diff between the current branch and remote main and
produce a **fix prompt** — a self-contained document listing every verified
issue with a high-level fix for each — hardened by an adversarial reviewer
before delivery.

**Reasoning**: The other checks each police one defect class; this one catches
what falls between them — correctness bugs, unhandled error paths, design
problems, and drift from the spec's stated scope. Findings are adversarially
verified because unreviewed review output has the same failure mode as
unreviewed code: confident, plausible, and sometimes wrong.

**Mode**: Report-only. This check never edits code and never commits. The
deliverable is the fix prompt, handed to the user to apply or discard.

**When to run**: After implementation reaches green and the other *Definition
of Done* checks have run — before the spec is marked completed or a PR is
opened. Also on demand for any branch.

## Scope

The **committed** branch work only:

```bash
git fetch origin
git diff origin/main...HEAD    # three-dot: unrelated changes on main don't pollute the diff
```

Uncommitted working-tree changes are noted in the delivery but excluded from
review. Defect classes owned by a dedicated check — test quality
([local-test-quality](local-test-quality.md)), dead code
([dead-code](dead-code.md)), documentation drift
([local-doc-drift](local-doc-drift.md)) — are not re-reviewed in depth: spot a
symptom, record a one-line pointer to run that check, and move on.

## Procedure

1. **Gather context.**

   ```bash
   git fetch origin
   git log --oneline origin/main..HEAD    # intent, from commit messages
   git diff --stat origin/main...HEAD     # shape of the change
   git diff origin/main...HEAD            # the diff under review
   ```

   Also read the active `SPEC-{NNN}` if one exists — it defines what the branch
   was *supposed* to do.

2. **Review the diff.** For each changed file, read the diff **plus enough
   surrounding code** to judge it in context — a hunk that looks wrong in
   isolation may be fine given its callers, and vice versa. Check three things:

   - **Contract violations** the diff introduces or worsens: design-principle
     breaches (cite the DP-{NNN} and the matched *Violation Signal*), invariant
     risks (cite the INV-{NNN}), and spec conformance — files outside *Module
     Decomposition*, behavior beyond the *Explicit non-goals* (agent
     over-implementation), interfaces that differ from the spec's fenced
     signatures. Pre-existing violations untouched by this branch are out of
     scope.
   - **General quality**: correctness bugs, unhandled error paths, missing or
     weak coverage of new behavior, duplication, naming, unnecessary
     complexity.
   - **Handoffs**: symptoms belonging to another check, recorded as pointers
     per *Scope*.

   Every finding needs a location (`file:line`), a severity (**blocker** /
   **should-fix** / **nit**), and concrete evidence — a finding you can't point
   at doesn't go in the prompt.

3. **Draft the fix prompt.** A single self-contained document containing:

   - one paragraph summarizing what the branch does and the overall state of
     the review;
   - per-issue entries: location, severity, contract citation where applicable
     (DP/INV/spec section), what's wrong, why it matters, and a **high-level
     fix** (direction, not a patch);
   - the closing instruction: "After all changes, run `make check` and
     `make check-tdd` and fix any regressions before finishing."

4. **Adversarial review (max 3 rounds).**

   **Round 1**: spawn a fresh sub-agent with the draft prompt, the git commands
   from step 1, and this brief:

   > You are reviewing a code-review fix prompt before it is delivered, for the
   > branch diff you can reproduce with the git commands below. For every
   > finding in the prompt, verify it against the actual code and classify it:
   > CONFIRMED (the issue is real and the fix direction is sound) or DISPUTED
   > (state why: false positive, wrong location, misread context, or fix
   > guidance that would make things worse). Also flag any fix guidance too
   > vague to act on, and add any issue in the same diff that the prompt missed
   > (with file:line evidence). Push back freely — a shorter, correct prompt
   > beats a longer, padded one.

   **Resolve each response before the next round**: re-check DISPUTED findings
   against the code yourself and drop them unless you can defend them with
   concrete evidence (say why in the revision); verify reviewer-added findings
   yourself before incorporating — the reviewer can be wrong too; sharpen any
   fix guidance flagged as vague.

   **Rounds 2–3**: continue the **same** reviewer (so it can check whether its
   pushback was actually addressed) with the revised prompt. Stop early when a
   round comes back all-CONFIRMED with nothing added.

5. **Deliver.** Write the final prompt to `reports/code-review-<branch>.md` —
   the repo's gitignored working-docs drawer (delete the file once acted on).
   Present it in full with a provenance note:

   ```text
   Review of <branch> vs origin/main (<N> commits, <M> files)
   Findings: X delivered (A blocker, B should-fix, C nit)
   Adversarial rounds: R — Y dropped after pushback, Z added by reviewer
   Contested: <findings still disputed at round 3, marked CONTESTED in the
   prompt with both positions — the user is the tiebreaker>
   Excluded: <uncommitted working-tree changes, if any>
   ```

## Report Rules

- Every finding carries `file:line` evidence; unverifiable findings are dropped,
  not hedged.
- Disputes unresolved after round 3 are marked `CONTESTED` in the prompt with
  both positions — never silently kept or dropped.
- Never expand scope to pre-existing issues the branch didn't touch; note them
  at most as a one-line candidates list for a follow-up spec.

## Output

The fix prompt at `reports/code-review-<branch>.md`, presented in full with its
provenance note. End with: "No changes were made. Awaiting review."

## Termination

- Reviewer round returns all-CONFIRMED with no additions → deliver.
- 3 rounds completed → deliver, with `CONTESTED` markers for unresolved
  disputes.
- The diff is empty (branch at or behind `origin/main`) → report that; nothing
  to review.
