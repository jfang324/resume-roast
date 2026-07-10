# SPEC-002: Restructure CLI into a Package

---
**Status**: pending
**Created**: 2026-07-09
**TDD**: optional
**Why optional**: pure refactor — no behavior change, no new commands. Every
existing `tests/test_cli.py` scenario passes unmodified; that unmodified pass
is the proof of behavior preservation, not new red/green test evidence.
**Coverage target**: repo default (`fail_under = 85` in `pyproject.toml`)
**Commit(s)**: <!-- Populated on completion. One `- hash (description)` per commit. -->

## Summary

`src/resume_roast/cli.py` is currently a single flat module holding the
Typer app, the `config` command group, and the `credentials` command's full
implementation together. The CLI is expected to grow more command groups
(a `show` group next, further `config` subcommands after that) and
eventually back a TUI; a flat file forces every new command to either
duplicate CLI wiring inline or keep growing one file indefinitely, with no
structural boundary between "parse/format at the terminal" and "actual
behavior." This spec restructures `cli.py` into a `cli/` package with a
repeatable shape — one thin handler class per command group, wired to Typer
from a single dispatcher module — and is a pure refactor: no new commands,
no behavior change, no new tests. It also introduces the design principle
that shape follows, [DP-003](../docs/design-principles/dp-003-thin-cli-handlers.md),
so future command groups adopt it by default.

### Existing Code

- `src/resume_roast/cli.py` — the file being decomposed; contains `app`,
  `config_app`, and the `credentials` command in full.
- `docs/design-principles/dp-003-thin-cli-handlers.md` — the design
  principle this spec's layout follows; authored and registered in
  `docs/design-principles/INDEX.md` during spec authoring (Phase 1). The
  implementation agent reads it but must not create or modify it.
- `src/resume_roast/__main__.py` — `from resume_roast.cli import app`; must
  keep resolving unchanged.
- `tests/test_cli.py` — `from resume_roast.cli import app`; the complete
  behavior-preservation suite; must pass with **zero modifications**.
- `src/resume_roast/persistence/__init__.py` — reference example of this
  codebase's pure-package-marker convention: a literal 0-byte file.
  `cli/config/__init__.py` follows this same convention.
- `src/resume_roast/persistence/credentials_store/__init__.py` — reference
  example of the re-exporting `__init__.py` style (import + `__all__`) that
  `cli/__init__.py` follows.
- `docs/invariants/inv-001-secrets-stay-in-credential-store.md` — its
  *Scope* section names `src/resume_roast/cli.py` by path; goes stale the
  moment this spec lands and is updated as part of it.
- `specs/spec-001-config-and-credential-storage.md` — also names `cli.py`,
  but per `docs/workflow.md` Phase 1, a completed spec is immutable except
  for commit refs/footnotes. **Not modified by this spec.**
- `pyproject.toml` — `[project.scripts] resume-roast = "resume_roast.cli:app"`
  and `[tool.poetry] packages = [{include = "resume_roast", from = "src"}]`;
  both already resolve correctly against a package (not just a module) and
  need no change.

## Module Decomposition

- **New files**:
  - `src/resume_roast/cli/__init__.py` — re-exports `app`:
    `from resume_roast.cli.app import app` + `__all__ = ["app"]`. The only
    file `resume_roast.cli:app` (entry point) and `__main__.py` ever touch.
  - `src/resume_roast/cli/app.py` — the entry dispatcher: builds the root
    `app = typer.Typer(...)`, builds `config_app`, mounts it via
    `app.add_typer(config_app, name="config", ...)`, instantiates
    `ConfigHandler`, and registers its bound method:
    `config_app.command("credentials")(handler.credentials)`. The only file
    in the package that constructs a Typer object or calls `.command()`/
    `.add_typer()`.
  - `src/resume_roast/cli/config/__init__.py` — empty, 0 bytes, matching
    `persistence/__init__.py`'s convention. `app.py` imports
    `ConfigHandler` directly from `cli/config/handler.py`, never through
    this file.
  - `src/resume_roast/cli/config/handler.py` — `ConfigHandler` class with
    one method, `credentials(self) -> None`, containing the current
    command body unchanged (menu prompt, cancel option, choice validation,
    key prompt, blank-after-strip check, save, masked confirmation,
    `PersistenceError` handling); the only differences from today's
    function are the removed decorator and the added `self` parameter.
- **Modified files**:
  - `docs/invariants/inv-001-secrets-stay-in-credential-store.md` — update
    the *Scope* line's file reference from `src/resume_roast/cli.py` to
    `src/resume_roast/cli/config/handler.py` (where the masking/prompt
    behavior lives) and `src/resume_roast/cli/app.py` (which only wires it).
- **Renames / moves**:
  - `src/resume_roast/cli.py` → deleted; its Typer/wiring code moves to
    `src/resume_roast/cli/app.py`, its command body moves to
    `src/resume_roast/cli/config/handler.py`. This shows in `git diff` as a
    delete plus two new files, not a clean rename — expected for a
    decomposition, not a defect.
- **Explicit non-goals** (required):
  - **No new commands, groups, or flags.** `resume-roast config credentials`
    remains the only command; a `show` group is a later spec's addition, not
    part of this one.
  - **No behavior change of any kind.** Every prompt string, message, exit
    code, masking rule, and error path is byte-for-byte identical to current
    `cli.py`.
  - **No new tests.** `tests/test_cli.py` is the sole verification
    mechanism and passes with **zero edits, including its import line** —
    that unmodified pass is the actual proof of behavior preservation for a
    pure refactor.
  - **No `services/` package.** `persistence/*_store` packages continue to
    play that role; per DP-003's "When to Relax" (one store per domain is
    expected orchestration), inventing a `services/` abstraction now would
    be premature.
  - **No `models/` package.** A future `src/resume_roast/models/` package
    (sibling to `persistence/`) is reserved for cross-group/presentation
    types a future `show`-style handler may need — not created here, since
    nothing in this spec needs one.
  - **No changes inside `persistence/`.**
  - **No `pyproject.toml` changes** — `resume_roast.cli:app` and the
    poetry `packages` include already resolve correctly against a package;
    verified, not modified.
  - **This is real package structure for one command (about to be two)** —
    a deliberate bet on future growth, justified by the roadmap (the CLI is
    expected to grow `config`/`show`/etc. groups plus a future TUI). Called
    out explicitly, separate from the file-shuffling mechanics, so the bet
    is knowingly approved, not just the mechanics.

## Design Principles Referenced

- [DP-003: Thin CLI Handlers](../docs/design-principles/dp-003-thin-cli-handlers.md)
  — `ConfigHandler.credentials`'s body is copied verbatim from the
  already-thin current implementation; this spec proves the *layout*
  supports the principle (dispatcher vs. handler class), not that any logic
  changes to fit it.

## Invariants Referenced

- [INV-001: Secrets Stay in the Credential Store](../docs/invariants/inv-001-secrets-stay-in-credential-store.md)
  — the credentials command remains fully subject to INV-001; its masking
  and hidden-input behavior are moved, not changed. This spec also updates
  INV-001's *Scope* file reference (see Modified files) so the invariant
  doc keeps pointing at the real file.

## Pre-implementation Self-Check

- DP-003 — satisfied by construction: `ConfigHandler.credentials` contains
  only the copied prompt/validate/delegate body; `cli/app.py` contains only
  Typer object construction and `.command()` registration, no business
  logic. Any DP-003 violation discovered in the existing implementation
  while moving it (there is not expected to be one — the current
  `credentials` command already only prompts, validates, and delegates to
  `CredentialsStore`/`mask_secret`) is recorded as a follow-up in
  *Footnotes*, never fixed inline in this refactor — folding a behavioral
  fix into a "pure refactor" would invalidate the unmodified-tests proof.
- INV-001 — masking and hidden-input behavior are copied unchanged;
  `test_config_credentials_masks_key_in_output` re-run against the new
  layout is the enforcement proof. The INV-001 doc edit is structural
  accuracy, not new enforcement.

## Test Plan (written first)

### `tests/test_cli.py`

No new test scenarios. The existing eight scenarios
(`test_config_credentials_saves_prompted_key`,
`test_config_credentials_masks_key_in_output`,
`test_config_credentials_rejects_blank_key`,
`test_config_credentials_rejects_out_of_range_selection`,
`test_config_credentials_cancels_without_saving`,
`test_config_credentials_overwrites_existing_key`,
`test_config_credentials_reports_storage_failure`,
`test_config_group_shows_help_without_subcommand`) are the **complete**
behavior-preservation proof and must pass **unmodified — no edits to this
file, including its import line**.

Import-line note: `tests/test_cli.py` imports `from resume_roast.cli import
app`. Because `cli/__init__.py` re-exports `app` from `cli/app.py`, this
import continues to resolve to the same Typer instance after the
restructuring — Python's import machinery sets the `resume_roast.cli`
package's `app` attribute to the submodule first, then the `from
resume_roast.cli.app import app` statement inside `__init__.py` immediately
rebinds it to the Typer instance. No change to this import line is needed.

**Constraints** (adapted for `TDD: optional`):

- This spec adds no test scenarios; the template's "every Acceptance
  Example maps to a test scenario" constraint is satisfied by each
  Acceptance Example below being marked "n/a — pure refactor, covered by
  the unmodified existing test" rather than omitted.
- The usual red/green ordering gate does not apply. `scripts/check_tdd.py`
  exempts commits typed `refactor:` from requiring test-first evidence or
  `[red]`/`[green]` markers — the single production-code commit in
  *Execution Order* below **must** use the `refactor:` type for this
  reason; this is a hard requirement, not a style choice.
- The Local Test Quality check (DP-001/DP-002) does not apply — no new test
  code is authored.

**Red/green record**: n/a — no test changes; the `refactor:` commit type is
exempt from the `make check-tdd` gate (see Constraints above).

## Execution Order

0. [Spec review](../docs/checks/spec-review.md) (optional, at user's
   discretion) — if run, findings are resolved by the author before any
   implementation work.
1. Create `src/resume_roast/cli/` package: `__init__.py`, `app.py`,
   `config/__init__.py`, `config/handler.py`, moving code exactly per
   *Changes Required* below. No test file changes in this step.
2. Delete `src/resume_roast/cli.py`.
3. Run `poetry run pytest tests/test_cli.py` locally and confirm every
   scenario passes unmodified against the new layout — this *is* the
   verification step for a pure refactor; there is no separate red step.
4. Update `docs/invariants/inv-001-secrets-stay-in-credential-store.md`'s
   *Scope* line.
5. Commit as a single `refactor:` commit (e.g.
   `refactor: restructure cli.py into a cli/ package`) covering the new
   `cli/` files, the deletion of `cli.py`, and the INV-001 doc update —
   `refactor:` is exempt from `make check-tdd`'s red-then-green
   requirement.
6. Lint + typecheck cleanup — `make check` clean.

## Changes Required

### `src/resume_roast/cli/__init__.py`

- **Interface**:

  ```python
  from resume_roast.cli.app import app

  __all__ = ["app"]
  ```

- **Behavior**: re-exports the Typer application instance built in
  `cli/app.py`. This is the sole file `resume_roast.cli:app` (the
  `[project.scripts]` entry point) and `__main__.py`'s
  `from resume_roast.cli import app` resolve through.
- **Acceptance Examples**: n/a — pure refactor; covered by the unmodified
  `tests/test_cli.py` (which imports `app` this way) continuing to pass,
  and by the manual smoke test (`poetry run resume-roast config
  credentials`) still launching.
- **Data flow**: `resume_roast.cli.app` (the attribute) is set to the
  submodule by Python's import machinery, then immediately rebound to the
  Typer instance by the `from ... import app` statement — `resume_roast.cli:app`
  therefore always resolves to the Typer instance.
- **Edge cases**: none.
- **Strategy**: exactly this two-line shape; do not add other re-exports.
- **Tests**: covered transitively — `tests/test_cli.py`'s import line is
  the direct exercise of this contract.

### `src/resume_roast/cli/app.py`

- **Interface**:

  ```python
  """Builds the resume-roast Typer application and wires commands to it."""

  import typer

  from resume_roast.cli.config.handler import ConfigHandler

  app = typer.Typer(no_args_is_help=True)

  config_app = typer.Typer(no_args_is_help=True)
  app.add_typer(config_app, name="config", help="Manage settings and credentials.")

  config_handler = ConfigHandler()
  config_app.command("credentials")(config_handler.credentials)
  ```

- **Behavior**: constructs the root Typer app and every group Typer app,
  instantiates each group's handler class, and registers every handler
  method against its group by explicit call on the *bound* method — never
  by decorator, and never the unbound class function (an unbound function
  would expose `self` as a spurious CLI argument to Typer's signature
  introspection). This is the single wiring point for the entire CLI
  topology; no other file constructs a Typer object or calls `.command()`.
- **Acceptance Examples**: n/a — pure refactor. `resume-roast config
  credentials` and `resume-roast config` (group help) behave identically to
  today; covered by the unmodified `test_config_credentials_*` and
  `test_config_group_shows_help_without_subcommand` scenarios.
- **Data flow**: `app.py` imports a group's handler class → instantiates it
  → registers its bound methods on the appropriate group Typer → the group
  Typer is attached to the root `app`. No handler ever imports `app.py` or
  another group's handler (no upward or sideways imports — see DP-003).
- **Edge cases**: none — distinct handler class names per group (e.g.
  `ConfigHandler`, a later `ShowHandler`) mean same-named leaf commands
  across groups (e.g. both exposing a `credentials` command) never collide
  at the wiring point, since each is a differently-named bound method.
- **Strategy**: keep `app.py` free of any logic beyond Typer object
  construction, handler instantiation, and `.command()`/`.add_typer()`
  calls — it is the "entry dispatcher" half of DP-003, held to the same
  thinness standard as handler methods, just for topology instead of
  business logic.
- **Tests**: covered transitively — `tests/test_cli.py` exercises `app`
  (built here) via `CliRunner`.

### `src/resume_roast/cli/config/__init__.py`

- **Interface**: empty file (0 bytes) — matches
  `src/resume_roast/persistence/__init__.py`'s existing convention.
- **Behavior**: pure package marker; no imports, no re-exports.
- **Acceptance Examples**: n/a.
- **Data flow**: none — `app.py` imports `ConfigHandler` directly from
  `cli.config.handler`, never through this `__init__.py`.
- **Edge cases**: none.
- **Strategy**: do not add a docstring or re-export "for convenience."
- **Tests**: none required; empty file.

### `src/resume_roast/cli/config/handler.py`

- **Interface**:

  ```python
  class ConfigHandler:
      def credentials(self) -> None: ...
  ```

  (`credentials` is undecorated — its body is identical to today's
  `@config_app.command("credentials")`-decorated function in `cli.py`, and
  its signature gains only `self`, which is invisible to Typer: the bound
  method registered in `app.py` presents the same zero-argument signature
  to Typer's introspection as today's free function. The class holds no
  other state.)

- **Behavior**: behaviorally identical to the current implementation —
  numbered credential-selection menu (`CREDENTIAL_SPECS`), cancel option,
  hidden/confirmed key prompt, blank-after-strip rejection (exit 1, no
  write), `CredentialsStore(storage_dir()).save(...)`, `PersistenceError`
  caught and reported as a one-line error (exit 1, no traceback), masked
  success message via `mask_secret`. `storage_dir()` is called inside the
  method body, per invocation, exactly as today — never cached on `self` or
  resolved in `__init__`.
- **Acceptance Examples**: n/a — pure refactor; identical to the Acceptance
  Examples already recorded for `cli.py` in SPEC-001 (`resume-roast config
  credentials` success/masked-output, blank-key rejection, `resume-roast
  config` group help) plus this branch's cancel-option behavior, all of
  which remain covered by the unmodified `tests/test_cli.py`.
- **Data flow**: identical to today — Typer prompt → strip/validate →
  `Credentials` → `CredentialsStore.save` → masked confirmation via
  `mask_secret`. Still the only code that prints and the only code that
  calls `storage_dir()`.
- **Edge cases**: identical to today (mismatched/empty confirmation handled
  natively by the prompt library; out-of-range/blank selections; cancel
  option exits without prompting for a key; existing key silently
  overwritten; unwritable store dir → `PersistenceError` → exit 1).
- **Strategy**: this class is the DP-003 exemplar — copy the method body
  verbatim; do not "improve" it while moving it, since that would break the
  pure-refactor guarantee and make `tests/test_cli.py` an inadequate proof
  if something incidentally changed.
- **Tests**: `tests/test_cli.py`'s existing eight scenarios, unmodified —
  see *Test Plan* above.

### `docs/invariants/inv-001-secrets-stay-in-credential-store.md`

- **Change**: in the *Scope* section, replace the reference to
  `src/resume_roast/cli.py` with `src/resume_roast/cli/config/handler.py`
  (where the prompt/masking behavior lives) and `src/resume_roast/cli/app.py`
  (which only wires it).
- **Behavior**: documentation-only edit; no code or test impact.
- **Tests**: none — doc accuracy only.

## Definition of Done — Hard Gates

All of these must be true for this spec to be marked completed:

- [ ] All tests pass (`make test`), including `tests/test_cli.py`'s
      scenarios **unmodified**.
- [ ] `git diff` on `tests/test_cli.py` is empty — the behavior-preservation
      proof for this pure refactor.
- [ ] Coverage target met (repo default, `fail_under = 85`).
- [ ] `make check` passes (ruff format/check, pyright strict).
- [ ] `make check-tdd` passes — via the `refactor:` commit-type exemption,
      not via test-first evidence.
- [ ] Manual smoke test: `poetry run resume-roast config credentials` and
      `python -m resume_roast config credentials` both behave identically
      to pre-refactor (masked confirmation, file contents, overwrite,
      cancel).
- [ ] `poetry run resume-roast` (bare, via `[project.scripts]`) still
      resolves and shows help.
- [ ] INV-001 has a passing enforcement test
      (`test_config_credentials_masks_key_in_output`, unmodified) and its
      Scope doc reference is updated.

## Advisory Reports

The following checks are available at the user's discretion (see
`docs/checks/`). If run, findings go to `reports/{check-name}-002.md` and do
not block closure:

- [Local Doc Drift](../docs/checks/local-doc-drift.md) — worth running
  given the INV-001 Scope edit, to confirm no other doc references `cli.py`
  by path were missed.
- [Code Review](../docs/checks/code-review.md) — recommended, since this
  establishes the wiring pattern every future CLI group will copy; worth an
  extra pass on `cli/app.py`'s handler-instantiation-and-wiring convention
  before it's load-bearing precedent.
- [Workflow Conformance](../docs/checks/workflow-conformance.md) — verifies
  this spec's own front-matter/index metadata before closure.

## Constraints

- No new third-party dependencies.
- No `pyproject.toml` changes.
- `cli/app.py` is the only file that constructs a Typer object or calls
  `.command()`/`.add_typer()`.
- Each command group has exactly one handler class, instantiated once in
  `cli/app.py`; leaf commands are registered as that instance's bound
  methods, never as unbound class functions or decorated free functions.
- Handler methods resolve `storage_dir()` and construct any stores they
  need inside the method body, per invocation — never cached in `__init__`
  or at class/module level.
- `cli/config/__init__.py` (and every future group `__init__.py`) stays a
  0-byte marker — no re-exports, no Typer objects.
- `tests/test_cli.py` must not be edited in any way as part of this spec.
- `specs/spec-001-config-and-credential-storage.md` is completed and
  immutable — not touched, even though it references the old `cli.py`
  path.

## Dependencies

- SPEC-001 — provides the `cli.py` being restructured and the
  `persistence/` stores it delegates to.

## Footnotes

### Manual Corrections

Populated after agent completes implementation. Each entry documents something the
agent got wrong and how it was manually corrected. This serves as training signal
for future specs.

- `{commit ref}` — _{What was wrong and how it was fixed.}_
