# Development Guide

## Setup

Install dependencies including dev dependencies:

```bash
poetry install --with dev
```

Install both Git hook stages:

```bash
poetry run pre-commit install
poetry run pre-commit install --hook-type pre-push
```

The pre-push hook runs heavier local checks like Pyright and pytest before pushing.

## Running the App

Enter the virtual environment:

```bash
poetry shell
```

Then run the application:

```bash
resume-roast
```

## Testing

Run all tests and generate coverage report:

```bash
make test
make report
```

Run a targeted test file or test case:

```bash
poetry run coverage run -m pytest tests/unit/workers/test_download_worker.py -v
poetry run coverage run -m pytest tests/unit/workers/test_download_worker.py::TestDownloadWorkerDoWork::test_do_work_returns_merging_job -v
```

## Code Quality

Run linting, type checking, formatting:

```bash
make check
```

### Spec-driven TDD

Every `SPEC-{NNN}` includes a *Test Plan* written before any implementation.
Tests are specified as scenarios (not code) in the spec document; the agent then
authors the test bodies **first**, observes them fail (red), and only then writes
the production code that makes them pass (green).

Red-then-green evidence must be visible on the branch in one of two forms:

- separate commits: a `test: ...` commit that lands before the corresponding
  `feat: ...` commit, or
- a single commit whose message carries `[red]` and `[green]` markers, paired
  with a *Red/green record* note in the spec.

The TDD gate verifies this ordering over the commits on the current branch:

```bash
make check-tdd
```

(implemented in `scripts/check_tdd.py`). Commits typed `docs:`, `chore:`, `ci:`,
`build:`, `refactor:`, or `style:` are exempt, matching the reasons a spec may
declare `TDD: optional` (pure refactor, rename, deps bump, doc-only change).

To opt a whole spec out (e.g., a pure rename), set `TDD: optional` on the spec
front-matter with a one-line reason.

Before implementation starts, run the report-only
[Spec Review check](checks/spec-review.md) on the drafted spec — every later
check enforces conformance to the spec, so spec defects must be caught here or
not at all. Checks are best executed by a fresh sub-agent given only the check
doc and the repo, not the implementing context — the reasoning that produced a
defect tends to also produce the review that misses it.

Ordering alone doesn't prove the tests are any good. Immediately after test
bodies are first authored — regardless of whether they fail — run the
[Local Test Quality check](checks/local-test-quality.md) (`docs/checks/` holds
these executable check prompts), which validates the branch's new test code
against the testing design principles (DP-001, DP-002) and fixes violations.
Once the implementation is green, run the report-only
[Dead Code check](checks/dead-code.md) to surface artifacts of abandoned design
iterations for review, and the [Local Doc Drift check](checks/local-doc-drift.md)
to fix documentation the branch's changes made stale, before the spec's
Definition of Done. Then run the
[Workflow Conformance check](checks/workflow-conformance.md), which verifies the
branch's specs, docs, and indexes carry all the metadata the workflow expects,
fixing mechanical gaps in place. Last, run the report-only
[Code Review check](checks/code-review.md), which reviews the branch diff for
correctness, quality, and spec conformance and delivers an
adversarially-hardened fix prompt to `todo/` (gitignored) for the user to apply
or discard. Periodically — after several specs, or before a milestone —
run the report-only [Global Doc Drift check](checks/global-doc-drift.md), which
audits every docstring and prose doc in the repo against the implementation.

See `specs/TEMPLATE.md` for the full spec structure.
