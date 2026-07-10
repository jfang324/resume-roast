# SPEC-004: Re-wire the CLI Package into a Runner and Per-Group Typer Modules

---
**Status**: completed
**Created**: 2026-07-10
**TDD**: optional
**Why optional**: pure refactor — no behavior change, no new commands. Every
existing `tests/test_cli.py` scenario passes with only the mechanical
`app`→`cli` symbol rename applied to its import and `runner.invoke` calls;
that rename-only pass is the proof of behavior preservation, not new
red/green test evidence.
**Coverage target**: repo default (`fail_under = 85` in `pyproject.toml`)
**Commit(s)**:
- e8367a3 (refactor: re-wire cli into runner + per-group typer modules)

## Summary

The `cli/` package built by SPEC-002/SPEC-003 wires every command through a
single dispatcher (`cli/app.py`) that constructs each group's `typer.Typer`
object, instantiates a one-method handler *class* per group
(`ConfigHandler`, `ShowHandler`), and registers each leaf command by binding
its method (`config_app.command("credentials")(handler.credentials)`). Two
problems motivate this refactor. First, `app.py` is an inaccurate name: that
file wires only the CLI, but the project will grow a TUI as a second
front-end, so "app" over-claims — the file is the CLI *runner*. Second, the
handler-class-plus-bound-method wiring is a non-idiomatic workaround: a class
that exists solely to hold one method, registered by binding to dodge Typer
reading `self` as a spurious CLI argument. Typer's idiomatic shape — a
module-level `typer.Typer()` per group with `@<group>_cli.command(...)`
decorated functions — expresses the same thing directly. This spec renames
`cli/app.py` → `cli/runner.py` (root object `cli`), moves each group's Typer
object and its command registration into that group's own
`cli/<group>/handler.py` as decorated module-level functions, and reduces the
runner to `add_typer` assembly. It is a pure refactor: no new commands, no
behavior change. It reverses only the *structural mechanism* prescribed by
[DP-003](../docs/design-principles/dp-003-thin-cli-handlers.md) (handler
class + centralized bound-method registration), not its thesis (the CLI layer
parses/validates/formats and delegates all real work to the store layer);
DP-003 is revised in the same Phase-1 authoring step to describe the new
shape.

### Existing Code

- `src/resume_roast/cli/app.py` — the dispatcher being renamed and thinned;
  currently constructs the root `app`, both group Typers, both handler
  instances, and both bound-method registrations. Read to move its
  `add_typer` calls into `runner.py` and its group-Typer construction down
  into the handler modules.
- `src/resume_roast/cli/config/handler.py` — `ConfigHandler` with one method,
  `credentials`; its body moves verbatim into a decorated module-level
  function. Note the currently-present `from __future__ import annotations`
  has nothing to defer (only `-> None`) and is dropped when rewritten.
- `src/resume_roast/cli/show/handler.py` — `ShowHandler` with one method,
  `credentials`; same transformation.
- `src/resume_roast/cli/__init__.py` — re-exports `app`; changes to re-export
  `cli` from `runner.py`. The only file the `[project.scripts]` entry point
  and `__main__.py` resolve through.
- `src/resume_roast/__main__.py` — `from resume_roast.cli import app` / `app()`;
  becomes `cli` / `cli()`.
- `pyproject.toml` — `[project.scripts] resume-roast = "resume_roast.cli:app"`;
  the attribute renames to `:cli`. Line 15.
- `tests/test_cli.py` — imports `app` and calls `runner.invoke(app, ...)`
  fifteen times; the complete behavior suite. Gets the mechanical
  `app`→`cli` rename only — no scenario changes.
- `docs/design-principles/dp-003-thin-cli-handlers.md` — the design principle
  whose *mechanism* this spec inverts. **Revised during Phase 1 authoring**
  (Reasoning + the two structural violation signals + Examples table) so it
  describes per-group Typer modules with decorators. The implementation agent
  reads the revised version but **must not create or modify it** — it is a
  spec-authoring artifact, exactly as SPEC-002 treated DP-003 when it was
  first written.
- `docs/invariants/inv-001-secrets-stay-in-credential-store.md` — its *Scope*
  line names `src/resume_roast/cli/app.py`; goes stale the moment this spec
  lands and is updated as part of it (the `cli/config/handler.py` reference in
  the same line still holds).
- `src/resume_roast/persistence/__init__.py` — reference for the 0-byte
  package-marker convention the `cli/config/` and `cli/show/` `__init__.py`
  files follow (unchanged by this spec, but they must stay 0-byte).
- `specs/spec-002-restructure-cli-into-package.md` and
  `specs/spec-003-show-credentials.md` — completed and immutable; their bodies
  describe the handler-class shape this spec supersedes. **Not edited**; each
  receives a one-line Footnote at closure pointing here (see Phase 4).

## Module Decomposition

- **Renames / moves**:
  - `src/resume_roast/cli/app.py` → `src/resume_roast/cli/runner.py` — the
    root Typer object is renamed `app` → `cli`; the file is reduced to root
    construction plus two `add_typer` calls. Group-Typer construction and
    command registration move out (see below). Shows in `git diff` as a delete
    plus a new file, expected for a rename with content change.
- **Modified files**:
  - `src/resume_roast/cli/config/handler.py` — `ConfigHandler` class replaced
    by a module-level `config_cli = typer.Typer(no_args_is_help=True)` and a
    `@config_cli.command("credentials")` function holding the method body
    verbatim. Drops `self` and the dead `from __future__ import annotations`.
  - `src/resume_roast/cli/show/handler.py` — `ShowHandler` class replaced by a
    module-level `show_cli = typer.Typer(no_args_is_help=True)` and a
    `@show_cli.command("credentials")` function holding the method body
    verbatim. Drops `self`.
  - `src/resume_roast/cli/__init__.py` — re-export changes from
    `from resume_roast.cli.app import app` / `__all__ = ["app"]` to
    `from resume_roast.cli.runner import cli` / `__all__ = ["cli"]`.
  - `src/resume_roast/__main__.py` — `app` → `cli` in the import and the call.
  - `pyproject.toml` — `[project.scripts]` value `resume_roast.cli:app` →
    `resume_roast.cli:cli` (line 15).
  - `tests/test_cli.py` — import `app` → `cli`; every `runner.invoke(app, ...)`
    → `runner.invoke(cli, ...)`. Mechanical symbol rename only.
  - `docs/invariants/inv-001-secrets-stay-in-credential-store.md` — *Scope*
    line reference `src/resume_roast/cli/app.py` → `src/resume_roast/cli/runner.py`.
- **Explicit non-goals** (required):
  - **No new commands, groups, or flags.** `config credentials` and
    `show credentials` remain the only commands.
  - **No behavior change of any kind.** Every prompt string, echo, exit code,
    masking rule, `(not set)` output, and error path is byte-for-byte identical
    to today. The `no_args_is_help=True` flag is preserved on the root object
    and **on both group Typers** — see Constraints; dropping it from a group
    would change `config`/`show` group-help behavior and break two tests.
  - **No new test scenarios.** `tests/test_cli.py` changes only by the
    `app`→`cli` symbol rename; the fifteen scenarios and their assertions are
    untouched. That rename-only pass is the behavior-preservation proof.
  - **No filename change to the handler modules.** They stay
    `cli/config/handler.py` and `cli/show/handler.py` — each still handles a
    single subcommand and is a handler in principle even without a class;
    `commands.py` would wrongly imply multiple subcommands.
  - **No `services/` or `models/` package.** Unchanged from SPEC-002's
    non-goals; `persistence/*_store` continues to play the store role.
  - **No changes inside `persistence/`.**
  - **No 0-byte `__init__.py` changes.** `cli/config/__init__.py` and
    `cli/show/__init__.py` stay 0-byte markers.

## Design Principles Referenced

- [DP-003: Thin CLI Handlers](../docs/design-principles/dp-003-thin-cli-handlers.md)
  — this spec adopts DP-003's **revised** structural shape: each group owns
  its `typer.Typer()` and its `@<group>_cli.command(...)` functions in
  `cli/<group>/handler.py`; `runner.py` only assembles them via `add_typer`.
  The command bodies are copied verbatim from the already-thin current
  handlers — this spec proves the revised *layout* supports the thesis
  (parse/validate/format, delegate to the store), it does not change any
  command logic.

## Invariants Referenced

- [INV-001: Secrets Stay in the Credential Store](../docs/invariants/inv-001-secrets-stay-in-credential-store.md)
  — both credentials commands remain fully subject to INV-001; their masking
  and hidden-input behavior move, unchanged. This spec also updates INV-001's
  *Scope* file reference (see Modified files) so the doc keeps pointing at the
  real file. Enforced by the unmodified (bar the symbol rename)
  `test_config_credentials_masks_key_in_output` and
  `test_show_credentials_displays_masked_value_not_full_key`.

## Pre-implementation Self-Check

- DP-003 (revised) — satisfied by construction: each command function
  contains only the copied prompt/validate/format/delegate body;
  `runner.py` contains only root-Typer construction and two `add_typer`
  calls; each group's `typer.Typer()` and `@command` decorator live in that
  group's `handler.py`. `storage_dir()` is still called inside each function
  body, per invocation — never at module scope. Any latent DP-003 thesis
  violation noticed while moving a body (none expected — both commands already
  only prompt/format and delegate to `CredentialsStore`/`mask_secret`) is
  recorded as a follow-up in *Footnotes*, never fixed inline, since a
  behavioral fold-in would invalidate the rename-only-tests proof.
- INV-001 — masking and hidden-input behavior are copied unchanged; the two
  masking tests re-run against the new layout are the enforcement proof. The
  INV-001 doc edit is structural accuracy, not new enforcement.

## Test Plan (written first)

### `tests/test_cli.py`

No new test scenarios. The existing fifteen scenarios remain the complete
behavior-preservation proof and pass after only the mechanical `app`→`cli`
symbol rename (import line plus every `runner.invoke(...)` first argument).
Two scenarios are load-bearing for this refactor's one real risk (a group
Typer losing `no_args_is_help=True`) and must be observed passing explicitly:

- `test_config_group_shows_help_without_subcommand` — invokes `["config"]`
  with no subcommand and asserts `"credentials"` in stdout.
- `test_show_group_shows_help_without_subcommand` — invokes `["show"]` and
  asserts `"credentials"` in stdout.

Both depend on each group Typer keeping `no_args_is_help=True`; a bare
`typer.Typer()` on a single-command group routes the no-subcommand case
differently and drops `"credentials"` from stdout.

**Constraints** (adapted for `TDD: optional`):

- This spec adds no test scenarios; the template's "every Acceptance Example
  maps to a test scenario" constraint is satisfied by each Acceptance Example
  below being marked "n/a — pure refactor, covered by the existing scenario"
  rather than omitted.
- The usual red/green ordering gate does not apply. `scripts/check_tdd.py`
  exempts commits typed `refactor:` from requiring test-first evidence — the
  single production-code commit in *Execution Order* **must** use the
  `refactor:` type for this reason; hard requirement, not style.
- The Local Test Quality check (DP-001/DP-002) does not apply — no new test
  code is authored; the only test edit is a symbol rename.

**Red/green record**: n/a — no new test scenarios; the `refactor:` commit type
is exempt from the `make check-tdd` gate (see Constraints above).

## Execution Order

0. [Spec review](../docs/checks/spec-review.md) (optional, at user's
   discretion) — if run, findings are resolved by the author before any
   implementation work.
1. Rewrite `src/resume_roast/cli/config/handler.py` and
   `src/resume_roast/cli/show/handler.py` to module-level `<group>_cli`
   Typer objects (`no_args_is_help=True`) with decorated command functions,
   bodies copied verbatim; drop `self` and the dead `__future__` import.
2. Create `src/resume_roast/cli/runner.py` (root `cli`, two `add_typer`
   calls) and delete `src/resume_roast/cli/app.py`.
3. Update `src/resume_roast/cli/__init__.py`, `src/resume_roast/__main__.py`,
   and `pyproject.toml` line 15 to the `cli` symbol / `:cli` entry point.
4. Apply the mechanical `app`→`cli` rename in `tests/test_cli.py`.
5. Run `poetry run pytest tests/test_cli.py` and confirm every scenario
   passes against the new layout — this *is* the verification step for a pure
   refactor; there is no separate red step. Confirm the two group-help
   scenarios explicitly (Correction A guard).
6. Update `docs/invariants/inv-001-...md`'s *Scope* line.
7. `make check` clean (ruff format/check, pyright strict); `make check-tdd`
   OK via the `refactor:` exemption.
8. Commit as a single `refactor:` commit (e.g.
   `refactor: re-wire cli into runner + per-group typer modules`) covering the
   handler rewrites, the `app.py`→`runner.py` rename, the `__init__`/
   `__main__`/`pyproject`/test edits, and the INV-001 doc update.

## Changes Required

### `src/resume_roast/cli/config/handler.py`

- **Interface**:

  ```python
  """Commands under `resume-roast config`."""

  import typer

  from resume_roast.persistence.credentials_store import (
      CREDENTIAL_SPECS,
      Credentials,
      CredentialsStore,
      mask_secret,
  )
  from resume_roast.persistence.errors import PersistenceError
  from resume_roast.persistence.paths import storage_dir

  config_cli = typer.Typer(no_args_is_help=True)


  @config_cli.command("credentials")
  def credentials() -> None:
      """Select and save one of the supported API keys."""
      ...
  ```

- **Behavior**: behaviorally identical to the current `ConfigHandler.credentials` —
  numbered credential-selection menu, cancel option, hidden/confirmed key
  prompt, blank-after-strip rejection (exit 1, no write),
  `CredentialsStore(storage_dir()).save(...)`, `PersistenceError` caught and
  reported as a one-line error (exit 1, no traceback), masked success message
  via `mask_secret`. `storage_dir()` is called inside the function body, per
  invocation — never at module scope.
- **Acceptance Examples**: n/a — pure refactor; identical to the Acceptance
  Examples recorded for the `config credentials` command in SPEC-001/SPEC-002,
  all covered by the (symbol-renamed only) `test_config_credentials_*` and
  `test_config_group_shows_help_without_subcommand` scenarios.
- **Data flow**: Typer parses the invocation and calls the decorated function
  directly (no `self`, no bound method) → prompt/strip/validate → `Credentials`
  → `CredentialsStore.save` → masked confirmation via `mask_secret`. Still the
  only code in this group that prints and the only code that calls
  `storage_dir()`.
- **Edge cases**: identical to today (mismatched/empty confirmation handled by
  the prompt library; out-of-range/blank selection; cancel exits without a key
  prompt; existing key silently overwritten; unwritable store dir →
  `PersistenceError` → exit 1).
- **Strategy**: copy the method body verbatim into the decorated function; do
  not "improve" it while moving it — that would break the pure-refactor
  guarantee and make the test suite an inadequate proof. Remove the
  `from __future__ import annotations` line (no deferred annotations to
  support). The decorated function's zero-argument signature is what Typer
  introspects — the reason the class + bound-method dance existed is now moot.
- **Tests**: covered by the `test_config_credentials_*` and
  `test_config_group_shows_help_without_subcommand` scenarios — see *Test Plan*.

### `src/resume_roast/cli/show/handler.py`

- **Interface**:

  ```python
  """Commands under `resume-roast show`."""

  import typer

  from resume_roast.persistence.credentials_store import (
      CREDENTIAL_SPECS,
      CredentialsStore,
      mask_secret,
  )
  from resume_roast.persistence.paths import storage_dir

  _NOT_SET = "(not set)"

  show_cli = typer.Typer(no_args_is_help=True)


  @show_cli.command("credentials")
  def credentials() -> None:
      """List every registered credential, masked, or (not set)."""
      ...
  ```

- **Behavior**: behaviorally identical to the current `ShowHandler.credentials` —
  loads `CredentialsStore(storage_dir()).load()`, iterates `CREDENTIAL_SPECS`,
  echoes `"{label}: {masked-or-(not set)}"` per spec. `storage_dir()` called
  inside the body, per invocation.
- **Acceptance Examples**: n/a — pure refactor; identical to SPEC-003's
  Acceptance Examples, covered by the (symbol-renamed only)
  `test_show_credentials_*` and `test_show_group_shows_help_without_subcommand`
  scenarios.
- **Data flow**: Typer calls the decorated function directly → load via
  `CredentialsStore` → per-spec mask/format → `typer.echo`. Only code in this
  group that prints; only code that calls `storage_dir()`.
- **Edge cases**: identical to today (no credentials file → every spec renders
  `(not set)`; a stored value → masked to last 4 via `mask_secret`).
- **Strategy**: copy the method body verbatim; keep `_NOT_SET` at module
  scope. Drop `self`.
- **Tests**: covered by the `test_show_credentials_*` and
  `test_show_group_shows_help_without_subcommand` scenarios — see *Test Plan*.

### `src/resume_roast/cli/runner.py`

- **Interface**:

  ```python
  """Wires the resume-roast Typer application from group-level Typer instances."""

  import typer

  from resume_roast.cli.config.handler import config_cli
  from resume_roast.cli.show.handler import show_cli

  cli = typer.Typer(no_args_is_help=True)
  cli.add_typer(config_cli, name="config", help="Manage settings and credentials.")
  cli.add_typer(show_cli, name="show", help="Display saved settings and credentials.")
  ```

- **Behavior**: constructs the root Typer object `cli` and mounts each group's
  Typer under its name via `add_typer`. This is the only file that calls
  `add_typer`; it constructs no group Typer and registers no leaf command
  (both now live in the group handler modules). It imports each group's Typer
  object, never a handler class (there are none) and never another group's
  internals.
- **Acceptance Examples**: n/a — pure refactor. `resume-roast config credentials`,
  `resume-roast show credentials`, and the bare-group help paths behave
  identically to today; covered by the (symbol-renamed) suite.
- **Data flow**: `runner.py` imports `config_cli`/`show_cli` → `add_typer`
  mounts each under the root `cli`. No group module imports `runner.py`
  (no upward import); no group module imports another group (no sideways
  import).
- **Edge cases**: none — each group's command name is scoped to its own Typer,
  so `config credentials` and `show credentials` never collide.
- **Strategy**: keep `runner.py` free of any logic beyond root-Typer
  construction and `add_typer` — it is the "entry dispatcher" half of DP-003,
  held to the same thinness standard, now for topology only.
- **Tests**: covered transitively — `tests/test_cli.py` exercises `cli`
  (built here) via `CliRunner`.

### `src/resume_roast/cli/__init__.py`

- **Interface**:

  ```python
  """CLI entry point for resume-roast."""

  from resume_roast.cli.runner import cli

  __all__ = ["cli"]
  ```

- **Behavior**: re-exports the root Typer object built in `runner.py`. The sole
  file the `[project.scripts]` entry point (`resume_roast.cli:cli`) and
  `__main__.py`'s `from resume_roast.cli import cli` resolve through.
- **Acceptance Examples**: n/a — pure refactor; covered by the suite importing
  `cli` this way continuing to pass, and by the manual smoke test still
  launching.
- **Data flow**: Python's import machinery sets `resume_roast.cli.runner` (the
  submodule), then the `from ... import cli` statement rebinds
  `resume_roast.cli.cli` to the Typer instance, so `resume_roast.cli:cli`
  always resolves to it.
- **Edge cases**: none.
- **Strategy**: exactly this two-line shape; no other re-exports.
- **Tests**: covered transitively — the test import line exercises this.

### `src/resume_roast/__main__.py`

- **Interface**:

  ```python
  """Support for python -m resume_roast."""

  from resume_roast.cli import cli

  if __name__ == "__main__":
      cli()
  ```

- **Behavior**: `python -m resume_roast` resolves `cli` and invokes it.
  Identical dispatch to today, `app` renamed to `cli`.
- **Acceptance Examples**: n/a — covered by the manual smoke test
  (`python -m resume_roast show credentials`).
- **Tests**: none — `__main__.py` is excluded from coverage
  (`omit = ["**/__main__.py"]`) and exercised only by the smoke test.

### `pyproject.toml`

- **Change**: line 15, `[project.scripts]`, `resume-roast = "resume_roast.cli:app"`
  → `resume-roast = "resume_roast.cli:cli"`.
- **Behavior**: the `resume-roast` console script resolves the renamed root
  object. No other `pyproject.toml` change.
- **Tests**: none — verified by the bare `resume-roast` smoke test.

### `tests/test_cli.py`

- **Change**: `from resume_roast.cli import app` → `from resume_roast.cli import
  cli`; every `runner.invoke(app, ...)` → `runner.invoke(cli, ...)`. No
  scenario, assertion, fixture, or input change.
- **Behavior**: the fifteen scenarios continue to exercise the same CLI
  behavior against the renamed root object. This rename-only pass is the
  behavior-preservation proof for the refactor.
- **Tests**: this *is* the test file.

### `docs/invariants/inv-001-secrets-stay-in-credential-store.md`

- **Change**: in the *Scope* section, replace `src/resume_roast/cli/app.py`
  with `src/resume_roast/cli/runner.py` (which only wires the groups). The
  `src/resume_roast/cli/config/handler.py` reference in the same line is
  unchanged — it still holds the prompt/masking behavior.
- **Behavior**: documentation-only edit; no code or test impact.
- **Tests**: none — doc accuracy only.

## Definition of Done — Hard Gates

All of these must be true for this spec to be marked completed:

- [x] All tests pass (`make test`), with `tests/test_cli.py` changed only by
      the `app`→`cli` symbol rename. — 31 passed, 1 skipped (pre-existing).
- [x] `git diff` on `tests/test_cli.py` shows only the import line and
      `runner.invoke` first-argument renames — no scenario/assertion changes.
      — confirmed via `git diff a140dc8 e8367a3 -- tests/test_cli.py`.
- [x] Coverage target met (repo default, `fail_under = 85`). — 98.58%.
- [x] `make check` passes (ruff format/check, pyright strict). — clean, 0
      errors.
- [x] `make check-tdd` passes — via the `refactor:` commit-type exemption. —
      OK (2 commits checked).
- [x] `test_config_group_shows_help_without_subcommand` and
      `test_show_group_shows_help_without_subcommand` pass — the explicit guard
      that both group Typers kept `no_args_is_help=True`. — both pass.
- [x] Manual smoke test, both entry points (`resume-roast ...` and
      `python -m resume_roast ...`): bare `resume-roast` shows help;
      `show credentials` prints `NVIDIA API key: (not set)` with nothing saved
      and `****NNNN` after a key is seeded; `config`/`show` with no subcommand
      show group help. — all confirmed live (`****5678` after seeding via
      `CredentialsStore`, full key never printed). Note: after this refactor
      the console script wrapper had to be regenerated via `poetry install`
      to pick up the new `resume_roast.cli:cli` entry point — see Footnotes.
      (The `config credentials` save path itself is only verifiable through
      the test suite on Windows, same pre-existing hidden-input limitation
      noted in SPEC-002/003.)
- [x] `poetry run resume-roast` (bare, via `[project.scripts]`) still resolves
      and shows help against the `:cli` entry point. — confirmed, after
      `poetry install` regenerated the script.
- [x] INV-001 has passing enforcement tests
      (`test_config_credentials_masks_key_in_output`,
      `test_show_credentials_displays_masked_value_not_full_key`) and its Scope
      doc reference is updated. — both pass; Scope line now points at
      `cli/runner.py`.

## Advisory Reports

The following checks are available at the user's discretion (see
`docs/checks/`). If run, findings go to `reports/{check-name}-004.md` and do
not block closure:

- [Local Doc Drift](../docs/checks/local-doc-drift.md) — worth running given
  the INV-001 Scope edit and DP-003 revision, to confirm no other doc still
  references `cli/app.py`, `ConfigHandler`/`ShowHandler`, or the bound-method
  wiring by name.
- [Dead Code](../docs/checks/dead-code.md) — confirms no handler-class
  remnant or unused import survives the rewrite.
- [Code Review](../docs/checks/code-review.md) — recommended, since this
  re-establishes the wiring pattern every future CLI group will copy.
- [Workflow Conformance](../docs/checks/workflow-conformance.md) — verifies
  this spec's front-matter/index metadata and the SPEC-002/003 footnotes
  before closure.

## Constraints

- No new third-party dependencies.
- Only line 15 of `pyproject.toml` changes.
- `cli/runner.py` is the only file that calls `add_typer`; it constructs only
  the root `cli` Typer and no group Typer.
- Each command group owns its `typer.Typer(no_args_is_help=True)` and its
  `@<group>_cli.command(...)` functions in `cli/<group>/handler.py`. Both the
  root and both group Typers keep `no_args_is_help=True`.
- Command functions resolve `storage_dir()` and construct any stores inside
  the function body, per invocation — never at module/import scope.
- `cli/config/__init__.py` and `cli/show/__init__.py` stay 0-byte markers.
- `tests/test_cli.py` changes only by the `app`→`cli` symbol rename — no
  scenario, assertion, fixture, or input edits.
- `specs/spec-001-config-and-credential-storage.md`,
  `specs/spec-002-restructure-cli-into-package.md`, and
  `specs/spec-003-show-credentials.md` are completed and immutable — not
  edited in their bodies; SPEC-002/003 receive a closing Footnote only.

## Dependencies

- SPEC-002 — established the `cli/` package and the handler-class shape this
  spec re-wires.
- SPEC-003 — added the `show` group re-wired here alongside `config`.

## Footnotes

### Manual Corrections

Populated after agent completes implementation. Each entry documents something
the agent got wrong and how it was manually corrected. This serves as training
signal for future specs.

- **Stale installed console script after the `[project.scripts]` rename**:
  the spec's manual smoke test step (`resume-roast`, bare) initially failed
  with `ImportError: cannot import name 'app' from 'resume_roast.cli'` even
  though `pyproject.toml` line 15 was correctly updated to
  `resume_roast.cli:cli`. The installed `.venv/Scripts/resume-roast` wrapper
  script is generated by Poetry at install time from the `[project.scripts]`
  entry point and does not regenerate itself when `pyproject.toml` changes —
  it still imported `app`. Fixed by running `poetry install` (not part of the
  spec's Execution Order) to regenerate the wrapper before smoke-testing.
  Future specs that rename a `[project.scripts]` target should add
  `poetry install` as an explicit Execution Order step before the manual
  smoke test, not assume the console script self-updates.
