# SPEC-003: `show credentials` Command

---

**Status**: completed
**Created**: 2026-07-09
**TDD**: required
**Coverage target**: repo default (`fail_under = 85` in `pyproject.toml`)
**Commit(s)**:
- 83315b1 (test: add failing tests for show credentials command)
- ac5ac5d (feat: add show credentials command)

## Summary

`resume-roast` can _set_ a credential (`config credentials`) but has no way to
check what's already saved without opening `~/.resume-roast/credentials.json`
by hand. This spec adds a new top-level `show` command group with a
`show credentials` command that lists every registered credential (from
`CREDENTIAL_SPECS`) alongside its masked value — or `(not set)` if it has not
been configured. `show` is a new sibling group to `config`, built as the
second command group under the `cli/` package that SPEC-002 established:
`cli/show/handler.py` holds a `ShowHandler` class wired into the app from
`cli/app.py`, exactly mirroring `ConfigHandler`. Adding this group is
purely additive to `cli/app.py` (no edits to `cli/config/`), which is the
concrete payoff of SPEC-002's restructuring and the first real test of it.

### Existing Code

- `src/resume_roast/cli/app.py` — the single wiring point; builds the root
  `app` and `config_app`, instantiates `ConfigHandler`, and registers its
  bound method. This spec adds the parallel `show_app` + `ShowHandler` lines
  here and nothing else in this file changes.
- `src/resume_roast/cli/config/handler.py` — `ConfigHandler`, the reference
  shape for a group handler class (thin, delegates to the store, calls
  `mask_secret` for display). `ShowHandler` follows the same shape.
- `src/resume_roast/persistence/credentials_store/__init__.py` — re-exports
  `CREDENTIAL_SPECS`, `Credentials`, `CredentialsStore`, `mask_secret`.
  `ShowHandler` imports all four from here (never from submodules).
- `src/resume_roast/persistence/credentials_store/models.py` — `CredentialSpec`
  (`.key`, `.label`), `Credentials` (`nvidia_api_key: str | None`), and
  `mask_secret`. `ShowHandler` reads each spec's value off `Credentials` via
  its `.key` and masks set values through `mask_secret`.
- `src/resume_roast/persistence/credentials_store/store.py` —
  `CredentialsStore.load()` returns `Credentials | None` (`None` when the
  file is absent). `show credentials` handles both.
- `tests/test_cli.py` — existing flat CLI test module using Typer's
  `CliRunner` and the autouse `resume_roast_home` fixture; this spec's CLI
  scenarios are added here.
- [DP-003: Thin CLI Handlers](../docs/design-principles/dp-003-thin-cli-handlers.md)
  — the principle `ShowHandler` must satisfy; read before implementing.

## Module Decomposition

- **New files**:
    - `src/resume_roast/cli/show/__init__.py` — empty, 0 bytes, matching the
      `cli/config/__init__.py` / `persistence/__init__.py` marker convention.
    - `src/resume_roast/cli/show/handler.py` — `ShowHandler` class with one
      method, `credentials(self) -> None`, that loads credentials and echoes
      one masked line per registered spec.
- **Modified files**:
    - `src/resume_roast/cli/app.py` — add three lines: build `show_app`, mount
      it with `app.add_typer(..., name="show", ...)`, instantiate
      `ShowHandler`, and register `show_app.command("credentials")(show_handler.credentials)`.
      No other line in this file changes.
    - `tests/test_cli.py` — add the `show credentials` scenarios in _Test Plan_.
- **Renames / moves**: none.
- **Explicit non-goals** (required):
    - **No `show settings` command.** This spec stands up the `show` group and
      its first member only. Adding `settings` later is a one-handler-method +
      three-line-wiring addition and must not require touching this spec's
      files — that additive property is the acceptance bar for "modular."
    - **No shared "describable domain" abstraction** between `ShowHandler` and
      a future settings display. One instance does not justify a generic
      interface (same judgment SPEC-001 applied to an abstract `Store` base and
      SPEC-002 applied to a `services/` layer). A second `show` target may
      extract shared shape then.
    - **No new domain/display function in `persistence/`.** The label +
      `(not set)` composition is CLI presentation, not domain knowledge, so it
      lives in `ShowHandler`, not in `credentials_store/models.py`. Only the
      masking (`mask_secret`) is reused from the domain layer. Putting
      presentation strings like `(not set)` into the persistence layer would
      itself be a DP-003-adjacent smell.
    - **No changes to `config credentials`** (the set-flow) — untouched.
    - **No corrupt-file handling.** If `CredentialsStore.load()` raises
      `PersistenceError` on a malformed `credentials.json`, it propagates as it
      does for every other `load()` caller today; adding display-command error
      UX for that case is out of scope.
    - **No machine-readable output flag** (`--json`, etc.) — plain text only,
      deferred until a consumer needs it.
    - **No masking-format changes** — reuses `mask_secret` exactly as-is (at
      most the last 4 characters visible).

## Design Principles Referenced

- [DP-001: Test Behavior, Not Implementation](../docs/design-principles/dp-001-test-behavior-not-implementation.md)
  — `ShowHandler.credentials` is exercised through Typer's `CliRunner`
  against captured stdout and exit code (the observable boundary). Its
  internal load-then-format flow is not tested through private members; the
  masked lines on stdout are the behavior under test.
- [DP-002: Economical Test Code](../docs/design-principles/dp-002-economical-test-code.md)
  — CLI scenarios reuse the existing autouse `resume_roast_home` fixture and
  the `CredentialsStore` save helper already used in `tests/test_cli.py`; no
  new fixtures or copied setup blocks.
- [DP-003: Thin CLI Handlers](../docs/design-principles/dp-003-thin-cli-handlers.md)
  — `ShowHandler.credentials` only loads via the store, formats via
  `mask_secret`, and echoes; it holds no state, resolves `storage_dir()`
  inside the method body, and contains no filesystem/JSON access of its own.

## Invariants Referenced

- [INV-001: Secrets Stay in the Credential Store](../docs/invariants/inv-001-secrets-stay-in-credential-store.md)
  — `show credentials` is a new display surface for secrets and must mask
  every value through `mask_secret`, never printing a full key. Enforced by
  `test_show_credentials_displays_masked_value_not_full_key` below. This spec
  adds another masked display path (like the existing save-confirmation
  message); it does **not** add an exception to INV-001.

## Pre-implementation Self-Check

- DP-001 — CLI scenarios assert on `CliRunner` output/exit code only, using
  literal expected strings (`"****9876"`, `"(not set)"`) copied from this
  spec's Acceptance Examples, not recomputed with the handler's own logic.
- DP-002 — the "set" and "not set" scenarios have genuinely different setup
  (one saves a key first, one does not), so they are separate named tests,
  not a forced parametrize; both reuse the existing fixture. This is the
  DP-002 "clarity beats DRY" allowance, stated explicitly.
- DP-003 — verified by construction: `ShowHandler.credentials` loads
  `CredentialsStore(storage_dir()).load()`, iterates `CREDENTIAL_SPECS` for
  presentation (permitted by DP-003's "When to Relax"), masks through the
  shared `mask_secret`, and echoes. No inline masking, no direct file/env
  access, `storage_dir()` resolved per-invocation.
- INV-001 — guaranteed structurally: the handler's only rendering of a value
  is `mask_secret(value)` or the literal `"(not set)"`; the enforcement test
  asserts the full key is absent from output.

## Test Plan (written first)

### `tests/test_cli.py`

Reuses the distinctive test key `nvapi-test-9876` <!-- pragma: allowlist secret --> and the autouse
`resume_roast_home` fixture already established in this module.

- `test_show_credentials_displays_masked_value_not_full_key` — Given a key
  saved to the store dir (`nvidia_api_key="nvapi-test-9876"`), running <!-- pragma: allowlist secret -->
  `resume-roast show credentials` exits 0, and combined stdout+stderr
  contains the masked form `****9876` and does **not** contain the full key
  anywhere (enforces INV-001).
- `test_show_credentials_reports_not_set_when_missing` — Given an empty store
  dir (no `credentials.json`), running `resume-roast show credentials` exits
  0 and output contains `NVIDIA API key: (not set)`.
- `test_show_group_shows_help_without_subcommand` — `resume-roast show` alone
  exits 0 and prints group help listing `credentials`.

**Constraints**:

- Every _Acceptance Example_ in _Changes Required_ must map to at least one
  scenario here. If an example has no test, the spec is incomplete.
- Every linked INV-{NNN} must have a corresponding scenario whose purpose is
  enforcing it. Invariants without a test are treated as not enforced.
- A reviewer must be able to find red-then-green evidence: either separate
  commits (`test: ...` then `feat: ...`) on the branch, or `[red]` and
  `[green]` markers in a single commit message paired with a _Red/green
  record_ note here. `make check-tdd` enforces this ordering.
- Immediately after test bodies are authored — before any production code —
  run the [Local Test Quality check](../docs/checks/local-test-quality.md),
  which validates new tests against DP-001 and DP-002 and fixes violations.
  Waivers are recorded in _Footnotes_.

**Red/green record**: n/a — this spec uses separate `test:`/`feat:` commits
(Execution Order steps 1 and 3), not single-commit `[red]/[green]` markers.

## Execution Order

0. [Spec review](../docs/checks/spec-review.md) (optional, at user's
   discretion) — if run, findings are resolved by the author before any test
   or implementation work.
1. Add the three scenarios to `tests/test_cli.py`; observe failing locally
   (`test:` commit — red). The `show credentials` command does not exist yet,
   so the invocations error out.
2. Run the [Local Test Quality check](../docs/checks/local-test-quality.md);
   fix or waive findings.
3. Create `cli/show/__init__.py` (empty) and `cli/show/handler.py`
   (`ShowHandler`), then add the `show_app` wiring to `cli/app.py`; tests
   pass (`feat:` commit — green).
4. Lint + typecheck cleanup — `make check` clean.

## Changes Required

### `src/resume_roast/cli/show/handler.py`

- **Interface**:

    ```python
    class ShowHandler:
        def credentials(self) -> None: ...
    ```

- **Behavior**: loads `CredentialsStore(storage_dir()).load()` (a
  `Credentials | None`). For each `spec` in `CREDENTIAL_SPECS`, in order,
  reads the value via `getattr(credentials, spec.key)` when `credentials` is
  not `None` (else treats it as unset) and echoes one line
  `f"{spec.label}: {shown}"`, where `shown` is `mask_secret(value)` for a
  non-`None`, non-blank string value and the literal `"(not set)"`
  otherwise. Always exits 0 — a missing store dir/file is a valid "nothing
  set yet" state, not a failure. `storage_dir()` is resolved inside the
  method body, per invocation (DP-003); the class holds no state.
- **Acceptance Examples**:

    ```text
    Input:  resume-roast show credentials   (credentials.json has nvidia_api_key="nvapi-test-9876")  <!-- pragma: allowlist secret -->
    Output: NVIDIA API key: ****9876   ; exit 0
    ```

    ```text
    Input:  resume-roast show credentials   (no credentials.json present)
    Output: NVIDIA API key: (not set)   ; exit 0
    ```

- **Data flow**: `CredentialsStore.load()` → iterate `CREDENTIAL_SPECS` →
  `mask_secret` per set value → `typer.echo` per line. `ShowHandler` is the
  only code in this command that prints; it does not touch `json` or the
  filesystem directly (all via `CredentialsStore`).
- **Edge cases**: first run (no file → `load()` returns `None` → every spec
  renders `(not set)`); a spec whose value is present but blank after strip
  (not producible via the current save path, which rejects blank input, but
  the handler treats a blank string as unset defensively); `CREDENTIAL_SPECS`
  gaining a second entry later (the loop already covers all of them, no
  change needed).
- **Strategy**: mirror `ConfigHandler`'s shape — a thin class method that
  delegates to the store and reuses `mask_secret`. Avoid: importing anything
  from `cli/app.py` or `cli/config/`, reading files/env directly, or
  reimplementing masking. Keep the label + `(not set)` formatting here (it is
  CLI presentation), not in `persistence/`.
- **Tests**: `test_show_credentials_*` scenarios in _Test Plan_.

### `src/resume_roast/cli/show/__init__.py`

- **Interface**: empty file (0 bytes) — matches the `cli/config/__init__.py`
  marker convention.
- **Behavior**: pure package marker; no imports, no re-exports.
- **Acceptance Examples**: n/a.
- **Data flow**: none — `app.py` imports `ShowHandler` directly from
  `cli.show.handler`.
- **Edge cases**: none.
- **Strategy**: do not add a docstring or re-export.
- **Tests**: none required; empty file.

### `src/resume_roast/cli/app.py`

- **Interface** (added lines — the existing `config` wiring is unchanged):

    ```python
    from resume_roast.cli.show.handler import ShowHandler

    show_app = typer.Typer(no_args_is_help=True)
    app.add_typer(show_app, name="show", help="Display saved settings and credentials.")

    show_handler = ShowHandler()
    show_app.command("credentials")(show_handler.credentials)
    ```

- **Behavior**: registers the `show` group and its `credentials` command by
  the same bound-method mechanism `config` uses. `app.py` remains the only
  file that constructs Typer objects or calls `.command()`/`.add_typer()`.
- **Acceptance Examples**:

    ```text
    Input:  resume-roast show
    Output: group help listing the credentials subcommand   ; exit 0
    ```

- **Data flow**: `app.py` imports `ShowHandler` → instantiates it → registers
  its bound `credentials` method on `show_app` → `show_app` is attached to
  the root `app`. No collision with `config`'s `credentials` command because
  the two are distinct bound methods on distinctly-named handler classes
  (`ConfigHandler` vs. `ShowHandler`) — the property SPEC-002 designed for.
- **Edge cases**: none.
- **Strategy**: additive only — do not refactor or reorder the existing
  `config` wiring; append the `show` block.
- **Tests**: `test_show_group_shows_help_without_subcommand` in _Test Plan_.

## Definition of Done — Hard Gates

All of these must be true for this spec to be marked completed:

- [x] All tests pass (`make test` or equivalent). — 31 passed, 1 skipped.
- [x] Coverage target met (see **Coverage target** in the front-matter). — 99%.
- [x] `make check` passes. — clean.
- [x] `make check-tdd` passes. — OK.
- [x] Manual smoke test: `poetry run resume-roast show credentials` with no
      credentials saved (expect `NVIDIA API key: (not set)`), then after
      `poetry run resume-roast config credentials` saves a dummy key (expect
      the masked form to match the save-confirmation's mask). — confirmed
      live through both `resume-roast` and `python -m resume_roast` entry
      points, isolated via `RESUME_ROAST_HOME`: `(not set)` with nothing
      saved, `****5678` after saving `nvapi-smoketest-5678`. The save step
      itself was seeded directly through `CredentialsStore` rather than the
      interactive prompt, since Click's `hide_input=True` cannot be driven
      by piped stdin on Windows (same pre-existing platform limitation noted
      in SPEC-002); the prompt-driven save path is covered by the
      `CliRunner` test suite instead.
- [x] Every _Acceptance Example_ has a corresponding passing test. — confirmed.
- [x] Every linked INV-{NNN} has a passing enforcement test. — confirmed
      (`test_show_credentials_displays_masked_value_not_full_key`).

## Advisory Reports

The following checks are available at the user's discretion (see
`docs/checks/`). If run, findings go to `reports/{check-name}-003.md` and do
not block closure:

- [Spec Review](../docs/checks/spec-review.md) — recommended: this is the
  first spec to exercise SPEC-002's "adding a group is additive" claim, worth
  an adversarial read before implementation.
- [Local Doc Drift](../docs/checks/local-doc-drift.md) — `docs/development.md`
  documents the command surface and may want a `show credentials` mention.
- [Workflow Conformance](../docs/checks/workflow-conformance.md) — verifies
  front-matter/index metadata before closure.
- [Code Review](../docs/checks/code-review.md) — standard pre-closure review.

## Constraints

- No new runtime dependencies.
- `pyright` strict and `ruff` clean per `make check`; Python 3.12.
- `ShowHandler` must not import Typer-app objects from `cli/app.py`, import
  from `cli/config/`, or touch the filesystem/env directly — only through
  `CredentialsStore` and `storage_dir()` (DP-003).
- `cli/app.py` remains the only file that constructs a Typer object or calls
  `.command()`/`.add_typer()`.
- `cli/show/__init__.py` stays a 0-byte marker.
- The `show` group must remain independently extensible: adding
  `show settings` later must not require editing `ShowHandler.credentials`.

## Dependencies

- SPEC-002 — provides the `cli/` package structure, `cli/app.py` wiring
  point, and DP-003, all of which this spec builds on.
- SPEC-001 — provides `CredentialsStore`, `CREDENTIAL_SPECS`, `Credentials`,
  and `mask_secret`.

## Footnotes

### Manual Corrections

Populated after agent completes implementation. Each entry documents something the
agent got wrong and how it was manually corrected. This serves as training signal
for future specs.

- `{commit ref}` — _{What was wrong and how it was fixed.}_
