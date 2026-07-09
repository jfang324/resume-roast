# Workflow

## Project Overview

Resume Roast is an AI-powered resume editing environment with a CLI for quick
evaluations and a TUI for interactive, agentic tailoring.

## The Four-Phase Workflow

### Phase 1 — Spec Authoring

The user and an AI discuss a feature, architecture tradeoffs, design principles,
and invariants. The AI produces a spec document following
[specs/TEMPLATE.md](../specs/TEMPLATE.md). The user reviews and approves the
spec. After approval, the spec is immutable except for commit refs and
footnotes, which are populated during Phases 3 and 4.

### Phase 2 — Spec Review (optional)

Before any implementation code is written, the user may direct a fresh sub-agent
(not the spec author) to run the [Spec Review check](checks/spec-review.md)
against the drafted spec. The reasoning that produced a defect tends to also
produce the review that misses it, so a separate context is used. Findings are
delivered to the user and resolved back into the spec before Phase 3 begins.

### Phase 3 — Implementation

An implementation agent follows these steps in order:

1. **Read the spec in full** — including all linked design principles and
   invariants. Understand the Module Decomposition, Changes Required, and
   Constraints before writing any code.

2. **Run the Pre-implementation Self-Check** — verify each linked design
   principle and invariant actually applies to this spec and state why. If a
   link cannot be justified, the spec must be amended before proceeding.

3. **Follow the Execution Order** — the spec's numbered checklist dictates the
   sequence: test file first, Local Test Quality check second, production file
   third, lint cleanup fourth.

4. **Author test bodies first** — write the scenarios from the Test Plan as
   failing test code. Observe red locally.

5. **Write production code** — make the failing tests pass (green).

6. **Lint and typecheck cleanup** — run `make check` and resolve all issues.

7. **Satisfy the Definition of Done** — every checkbox in the spec's
   Definition of Done — Hard Gates must be true. These cover tests, coverage,
   `make check`, `make check-tdd`, all Acceptance Examples, and all linked INV
   enforcement tests.

### Phase 4 — Review & Closure

1. The user reviews the branch, applies any manual fixes directly.
2. All commit hashes are recorded in the spec's front-matter.
3. Manual corrections are documented in the spec's Footnotes section with
   descriptions of what was wrong and how it was fixed.
4. At the user's discretion, any of the checks in [docs/checks/](checks/) may be
   run by pointing a fresh sub-agent at the relevant check file. The available
   checks are:
   - [Spec Review](checks/spec-review.md) — adversarial review of a drafted spec
   - [Dead Code](checks/dead-code.md) — detects code left dead by design iterations
   - [Local Doc Drift](checks/local-doc-drift.md) — fixes doc drift on affected files
   - [Global Doc Drift](checks/global-doc-drift.md) — periodic repo-wide doc audit
   - [Workflow Conformance](checks/workflow-conformance.md) — verifies metadata
     and index entries
   - [Code Review](checks/code-review.md) — reviews the branch diff for
     correctness and spec conformance
5. The [Features Index](../specs/INDEX.md) is updated to map the feature to
   this spec.
6. The spec's status is set to **completed**.

## Repository Reference

| Path | Purpose |
|------|---------|
| `specs/` | Spec documents indexed in `INDEX.md`; `TEMPLATE.md` is the canonical structure. |
| `docs/design-principles/` | Design rules with violation signals and fix guidance. |
| `docs/invariants/` | System invariants with enforcement mechanisms and tests. |
| `docs/checks/` | Executable check prompts run at the user's discretion. |
| `reports/` | Check findings written here, one file per run (gitignored). |
| `scripts/check_tdd.py` | Automates the TDD gate (`make check-tdd`). |

## Makefile Commands

| Command | Purpose |
|---------|---------|
| `make test` | Run all tests with coverage. |
| `make check` | Run `ruff format --check`, `ruff check`, `pyright`. |
| `make check-tdd` | Verify red-then-green evidence on the current branch. |
| `make format` | Auto-format with Ruff. |
| `make lint` | Lint with Ruff. |
| `make typecheck` | Type check with Pyright. |
