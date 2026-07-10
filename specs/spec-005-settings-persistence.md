# SPEC-005: Settings Persistence (`config settings` / `show settings`)

---
**Status**: completed
**Created**: 2026-07-10
**TDD**: required
**Coverage target**: repo default (`fail_under = 85` in `pyproject.toml`)
**Commit(s)**:
- 70856c3 (test: add failing tests for settings persistence)
- 47e40ca (feat: add settings persistence with config and show support)
- a01cd48 (fix: rework settings wizard exit semantics and rename to settings.json)

## Summary

`resume-roast` can persist credentials but has nowhere to keep the
non-secret settings the roast pipeline will need: which model to roast with,
the reviewer persona, the candidate level, the feedback model, and the
ensemble model list. SPEC-001 deliberately stubbed the config domain for this
(`persistence/config_store/` exists with an intentionally empty `Config`
dataclass, a pass-through parser, and a `save` that writes `{}`); this spec
fills that stub in and exposes it through two new leaf commands on the
existing groups: `config settings` (an interactive wizard that walks every
setting, offering a numbered menu of registered choices per field, `0` to
keep the current value) and `show settings` (lists every setting's saved
value or `(not set)`). All selectable values come from registries in
`config_store/models.py` — a shared 7-model catalog for the three
model-valued settings, plus fixed `persona`/`level` value sets — mirroring
how `CREDENTIAL_SPECS` drives the credentials commands. Values are never
typed in free-form; they are picked by number. Settings are unset until
configured (no built-in defaults). The API key is **not** a setting — it
already lives in the credentials domain, and keeping it out of `config.json`
is exactly what [INV-001](../docs/invariants/inv-001-secrets-stay-in-credential-store.md)
exists to protect.

### Existing Code

- `src/resume_roast/persistence/config_store/models.py` — the empty `Config`
  stub ("fields arrive with later specs"); gains its fields and the setting
  registries here.
- `src/resume_roast/persistence/config_store/parser.py` — pass-through
  `parse_config` stub; gains real validation.
- `src/resume_roast/persistence/config_store/store.py` — `ConfigStore` with
  a stub `save` that writes `{}`; gains real merge-save. `load()`'s
  missing-file → `Config()` semantics are established by SPEC-001's tests
  and must be preserved.
- `src/resume_roast/persistence/credentials_store/` — the reference
  implementation this spec mirrors: `CredentialSpec`/`CREDENTIAL_SPECS`
  registry shape (`models.py`), optional-but-validated-when-present parsing
  (`parser.py`), and read-merge-write `save` (`store.py`). Note `save`'s
  `secure=True` is credential-specific and **not** copied — `config.json` is
  the shareable file.
- `src/resume_roast/persistence/json_file.py` — `read_json_object` /
  `write_json_object` primitives; reused as-is, no changes.
- `src/resume_roast/persistence/errors.py` — `PersistenceError`,
  `InvalidJsonError`, `InvalidSchemaError`; reused as-is.
- `src/resume_roast/cli/config/handler.py` — owns `config_cli` and the
  `credentials` wizard whose prompt/validate/exit conventions (numbered
  menu, `typer.prompt(type=int)`, invalid selection → one-line stderr +
  exit 1, `PersistenceError` → one-line stderr + exit 1) the new `settings`
  command follows.
- `src/resume_roast/cli/show/handler.py` — owns `show_cli`, the `_NOT_SET`
  literal, and the label-per-line display shape the new `settings` command
  follows.
- `src/resume_roast/cli/runner.py` — **no changes**: both groups are already
  mounted; per DP-003 (revised), new leaf commands register inside their
  group's handler module and appear automatically.
- `tests/persistence/test_config_store.py` — the five SPEC-001 scenarios
  (empty roundtrip, missing-file default, corrupt JSON, non-object top
  level, unknown-key tolerance) must keep passing **unmodified**; new
  scenarios are added alongside them.
- `tests/cli/test_config.py` / `tests/cli/test_show.py` — the CLI test
  files (split by SPEC-004's follow-up); new scenarios are added here, and
  each file's group-help scenario gains an assertion on the new command's
  help-summary text (not a bare `"settings"` substring — see Test Plan for
  why that would be vacuous).
- `tests/conftest.py` — provides the `store_dir` fixture used by
  persistence tests; `tests/cli/conftest.py` provides the autouse
  `resume_roast_home` fixture used by CLI tests. Both reused, unmodified.

## Module Decomposition

- **Modified files**:
  - `src/resume_roast/persistence/config_store/models.py` — `Config` fields,
    `SettingSpec` dataclass, `PERSONAS`/`LEVELS`/`MODEL_CATALOG` value
    registries, `SETTING_SPECS` registry.
  - `src/resume_roast/persistence/config_store/parser.py` — real
    `parse_config` validating every registered setting against its
    registry.
  - `src/resume_roast/persistence/config_store/store.py` — real merge-save;
    `load()` wraps parser schema errors with the file path (mirroring
    `CredentialsStore.load`).
  - `src/resume_roast/persistence/config_store/__init__.py` — additionally
    re-export `SETTING_SPECS` and `SettingSpec`.
  - `src/resume_roast/cli/config/handler.py` — add the
    `@config_cli.command("settings")` wizard function and a `_NOT_SET`
    constant.
  - `src/resume_roast/cli/show/handler.py` — add the
    `@show_cli.command("settings")` display function.
  - `tests/persistence/test_config_store.py` — new scenarios (see Test
    Plan); existing five untouched.
  - `tests/cli/test_config.py` — new wizard scenarios; group-help scenario
    gains one assertion.
  - `tests/cli/test_show.py` — new display scenarios; group-help scenario
    gains one assertion.
- **New files**: none — the config-store trio and both handler modules
  already exist.
- **Explicit non-goals** (required):
  - **No consumer of the settings.** Nothing reads `model`/`persona`/etc.
    to do work yet; the roast/feedback feature that consumes them is a later
    spec, which is also where any semantic constraints between fields (e.g.
    feedback model ∈ ensemble) would be defined.
  - **No built-in defaults.** Every setting is `None` until configured;
    `show settings` prints `(not set)`. Defaults, if ever wanted, arrive
    with the consuming spec.
  - **No API key in `config.json`.** The motivating example JSON contained
    `nvidia_api_key`; that field is deliberately excluded — credentials were
    extracted to their own store by SPEC-001 and INV-001 forbids their
    return. `Config` has no credential fields and the settings commands
    never touch `credentials.json`.
  - **No `models/` package.** The registries live in
    `config_store/models.py`, exactly where `CREDENTIAL_SPECS` lives in its
    domain. The reserved top-level `src/resume_roast/models/` package is for
    cross-domain types; these registries currently have a single domain.
  - **No renaming of the config domain.** User-facing name is "settings";
    the storage domain remains `config_store`/`Config`/`config.json` as
    SPEC-001 named it.
  - **No free-form value entry.** Every value is selected by number from a
    registry. Editing the catalog (adding models, personas, levels) is a
    registry change by a future spec, not a runtime feature.
  - **No per-item ensemble editing.** Changing `ensemble_models` re-picks
    the whole list; add/remove-one ergonomics are out of scope.
  - **No non-interactive flag mode** (`--model X`), no `config credentials`
    changes, no `credentials_store/` or `json_file.py` changes, no
    `runner.py` changes.

## Design Principles Referenced

- [DP-001: Test Behavior, Not Implementation](../docs/design-principles/dp-001-test-behavior-not-implementation.md)
  — CLI scenarios drive stdin through `CliRunner` and assert exit codes,
  output text, and `config.json` contents; store scenarios assert
  load/save observables. No test reaches into wizard internals.
- [DP-002: Economical Test Code](../docs/design-principles/dp-002-economical-test-code.md)
  — the malformed-shape parser scenarios are parametrized over
  (field, bad value) pairs rather than written as near-identical functions;
  CLI tests reuse the existing `resume_roast_home` autouse fixture.
- [DP-003: Thin CLI Handlers](../docs/design-principles/dp-003-thin-cli-handlers.md)
  — the wizard is numbered-menu prompt construction, explicitly covered by
  DP-003's "When to Relax" (interactive menus are presentation); all
  persistence goes through exactly one `ConfigStore` (one `load`, at most
  one `save`). Registration follows the revised mechanism:
  `@config_cli.command("settings")` / `@show_cli.command("settings")` in
  the group's own handler module; `storage_dir()` resolved inside the
  function body per invocation.

## Invariants Referenced

- [INV-001: Secrets Stay in the Credential Store](../docs/invariants/inv-001-secrets-stay-in-credential-store.md)
  — the settings domain is the "shareable file" side of the config/
  credentials split. Enforced here as: `Config` has no credential field,
  and saving settings never creates or modifies `credentials.json`
  (`test_save_settings_never_touches_credentials_file`, the mirror image of
  the existing `test_saving_credentials_never_touches_config_file`).
- [INV-002: JSON Never Crosses a Boundary Untyped](../docs/invariants/inv-002-json-never-crosses-a-boundary-untyped.md)
  — `parse_config` becomes a real ingestion parser: every documented
  malformed shape (wrong type, unregistered value, malformed list) raises
  `InvalidSchemaError` at the boundary, and both handlers consume only the
  typed `Config`. Enforced by the `test_load_rejects_*` scenarios plus
  `pyright --strict`.

## Pre-implementation Self-Check

- DP-001 — every scenario drives the public surface (CLI invocation or
  store call) and asserts observable results (exit code, output, file
  contents); expected values are literals (`"recruiter"`,
  `"Model: (not set)"`), not recomputed.
- DP-002 — malformed-shape scenarios are parametrized; no new fixtures are
  invented where `store_dir`/`resume_roast_home` fit.
- DP-003 — `settings` (config) contains only menu rendering, selection
  validation, and one `ConfigStore.save`; `settings` (show) contains only
  one `ConfigStore.load` and formatting. Registries are imported from
  `config_store`, never duplicated inline. Both Typer registrations stay in
  their group's handler module.
- INV-001 — guaranteed by construction (no credential field on `Config`)
  and by the never-touches-credentials test.
- INV-002 — guaranteed by `parse_config` being the only place raw config
  JSON is inspected, with rejection tests for each malformed shape.

## Test Plan (written first)

### `tests/persistence/test_config_store.py`

Existing five scenarios pass unmodified (the empty-roundtrip scenario stays
green because merge-saving an all-`None` `Config` over a missing file still
writes `{}`). New scenarios:

- `test_save_then_load_roundtrips_full_settings` — save a `Config` with all
  five fields set (values drawn from the registries), load returns an equal
  `Config`, and `config.json` contains the expected JSON object (list for
  `ensemble_models`).
- `test_save_preserves_fields_not_included_in_update` — pre-write
  `config.json` with a full set of registered fields **plus one unknown key**
  (e.g. `"future_setting": 1`); save `Config(persona="hiring-manager")`; load
  shows the new persona, every other registered field unchanged, and
  `config.json` still contains the unknown key byte-for-byte (proves the
  merge preserves unrecognized keys already in the file, not just registered
  ones).
- `test_save_settings_never_touches_credentials_file` — pre-write a marker
  `credentials.json`; saving settings leaves its bytes identical (INV-001).
- `test_load_rejects_unregistered_scalar_value` — parametrized over
  (key, bad value) for `model`, `persona`, `level`, `feedback_model`
  covering both a wrong-type value (e.g. `3`) and a string not in the
  registry (e.g. `"ceo"`, `"gpt-4"`); each raises `InvalidSchemaError`
  naming the file path (INV-002).
- `test_load_rejects_malformed_ensemble` — parametrized: not a list
  (`"x"`), empty list, list containing a non-catalog string, list
  containing a duplicate, list containing a non-string item (e.g. `[3]`);
  each raises `InvalidSchemaError` naming the file path (INV-002).
- `test_load_tolerates_unknown_keys_alongside_known_ones` — load
  `{"persona": "recruiter", "future_setting": 1}`; asserts
  `Config(persona="recruiter")` — the combined known-key-parses /
  unknown-key-ignored case (the two existing tolerance/parsing scenarios
  each cover only one half of this).
- `test_load_treats_explicit_null_as_absent` — load `{"persona": None}`;
  asserts `Config(persona=None)` with no exception raised — proves JSON
  `null` is tolerated as absent, not rejected.
- `test_save_ignores_empty_ensemble_tuple` — save
  `Config(ensemble_models=("nvidia/nemotron-3-super-120b-a12b",))`, then save
  `Config(ensemble_models=())` on top; load still returns the first save's
  ensemble tuple unchanged, and `config.json` remains loadable (no
  `InvalidSchemaError`) — proves the corruption guard, not just that it's
  documented.

### `tests/cli/test_config.py`

- `test_config_settings_saves_selected_values` — drive the wizard with
  literal stdin `1\n1\n2\n7\n3,1,3\n`; exit 0, stdout names the save
  destination, and `config.json` equals exactly
  `{"model": "nvidia/nemotron-3-super-120b-a12b", "persona": "recruiter",
  "level": "entry", "feedback_model": "meta/llama-3.1-8b-instruct",
  "ensemble_models": ["meta/llama-4-maverick-17b-128e-instruct",
  "nvidia/nemotron-3-super-120b-a12b"]}` — the ensemble input `3,1,3` is
  deliberately non-ascending with a duplicate so the assertion can only pass
  if selection order is preserved (not sorted) and the duplicate is dropped
  by first occurrence (not by an unordered `set`).
- `test_config_settings_keeps_current_values_when_skipped` — seed
  `Config(model="deepseek-ai/deepseek-v4-flash")` via `ConfigStore`, drive
  the wizard with literal stdin `0\n1\n2\n0\n0\n`; asserts the first prompt
  shows `"Model [current: deepseek-ai/deepseek-v4-flash]:"`, exit 0, and
  `config.json` equals exactly
  `{"model": "deepseek-ai/deepseek-v4-flash", "persona": "recruiter",
  "level": "entry"}` — matches the fourth Acceptance Example below
  literally.
- `test_config_settings_reports_no_changes_when_all_skipped` — enter `0`
  five times; exit 0, `No changes.` in stdout, `config.json` not created.
- `test_config_settings_rejects_out_of_range_selection` — an out-of-range
  number at the first menu; exit 1, non-empty stderr, no traceback, no
  file written.
- `test_config_settings_rejects_malformed_ensemble_input` — parametrized:
  valid picks up to the ensemble prompt, then either a non-numeric token
  (`1,foo`) or an out-of-range/negative token (`1,9` and `1,-1` — negative
  tokens must be rejected explicitly, not silently accepted via Python's
  negative-index semantics); each case exits 1, non-empty stderr, no file
  written (earlier picks are discarded).
- `test_config_group_shows_help_without_subcommand` — existing scenario
  gains `assert "Walk through" in result.stdout` (the `settings` command's
  help summary line, distinct from the group's own "Manage settings and
  credentials." description — a bare `"settings"` substring is already
  present in the group help today via that description and would not
  detect a missing command).

### `tests/cli/test_show.py`

- `test_show_settings_displays_saved_values` — seed a full config via
  `ConfigStore`; asserts stdout equals exactly the five-line block from the
  Acceptance Example below, in `SETTING_SPECS` order, with `ensemble_models`
  comma-joined — an exact match (not mere containment) so a reordered or
  reversed display fails the test.
- `test_show_settings_reports_not_set_when_missing` — no config file;
  every line reads `<label>: (not set)`, exit 0.
- `test_show_group_shows_help_without_subcommand` — existing scenario gains
  `assert "List every" in result.stdout` (the `settings` command's help
  summary line, distinct from the group's own "Display saved settings and
  credentials." description — same reasoning as the `config` group's
  equivalent scenario).

**Constraints**:

- Every Acceptance Example below maps to at least one scenario above.
- INV-001 → `test_save_settings_never_touches_credentials_file`; INV-002 →
  the two `test_load_rejects_*` parametrized scenarios.
- Red/green evidence: separate `test:` then `feat:` commits on the branch
  (`make check-tdd` enforces the ordering).
- Immediately after test bodies are authored — before any production code —
  run the [Local Test Quality check](../docs/checks/local-test-quality.md)
  against DP-001/DP-002; waivers recorded in *Footnotes*.

**Red/green record**: n/a — separate `test:`/`feat:` commits.

## Execution Order

0. [Spec review](../docs/checks/spec-review.md) (optional, at user's
   discretion) — findings resolved by the author before implementation.
1. Author all new/extended test scenarios across the three test files;
   observe red locally (`poetry run pytest`).
2. **Run Local Test Quality check** — validate the new test code against
   DP-001/DP-002 before any production code.
3. Commit as `test: add failing tests for settings persistence`.
4. Implement `config_store/models.py`, `parser.py`, `store.py`,
   `__init__.py`; observe the persistence tests green.
5. Implement `settings` in `cli/config/handler.py` and
   `cli/show/handler.py`; observe the CLI tests green.
6. `make check` clean (ruff format/check, pyright strict).
7. Commit as `feat: add settings persistence with config and show support`.
8. Manual smoke test (see Definition of Done).

## Changes Required

### `src/resume_roast/persistence/config_store/models.py`

- **Interface**:

  ```python
  @dataclass(frozen=True)
  class SettingSpec:
      """Describes one setting: storage key, display label, allowed choices."""

      key: str
      label: str
      choices: tuple[str, ...]
      multi: bool = False


  PERSONAS: tuple[str, ...] = ("recruiter", "hiring-manager")
  LEVELS: tuple[str, ...] = ("intern", "entry", "mid", "senior")
  MODEL_CATALOG: tuple[str, ...] = (
      "nvidia/nemotron-3-super-120b-a12b",
      "mistralai/mistral-large-3-675b-instruct-2512",
      "meta/llama-4-maverick-17b-128e-instruct",
      "nvidia/llama-3.3-nemotron-super-49b-v1.5",
      "deepseek-ai/deepseek-v4-flash",
      "deepseek-ai/deepseek-v4-pro",
      "meta/llama-3.1-8b-instruct",
  )

  SETTING_SPECS: tuple[SettingSpec, ...] = (
      SettingSpec(key="model", label="Model", choices=MODEL_CATALOG),
      SettingSpec(key="persona", label="Persona", choices=PERSONAS),
      SettingSpec(key="level", label="Level", choices=LEVELS),
      SettingSpec(key="feedback_model", label="Feedback model", choices=MODEL_CATALOG),
      SettingSpec(key="ensemble_models", label="Ensemble models", choices=MODEL_CATALOG, multi=True),
  )


  @dataclass(frozen=True)
  class Config:
      model: str | None = None
      persona: str | None = None
      level: str | None = None
      feedback_model: str | None = None
      ensemble_models: tuple[str, ...] | None = None
  ```

- **Behavior**: pure data — the field definitions and the registries that
  drive both wizard menus and parser validation. `SETTING_SPECS` order
  defines wizard and display order (matching the motivating example:
  model, persona, level, feedback model, ensemble).
- **Acceptance Examples**: n/a — exercised through the store and CLI
  examples below.
- **Data flow**: imported by `parser.py` (validation), `cli/config/handler.py`
  (menus), and `cli/show/handler.py` (labels/order).
- **Edge cases**: `ensemble_models` is a `tuple`, not a `list`, so `Config`
  stays hashable/frozen-safe; JSON serialization renders it as an array.
  **Corruption guard**: `Config` is an unvalidated frozen dataclass, so
  `Config(ensemble_models=())` (empty tuple, distinct from `None`) is
  directly constructible — and `ConfigStore.save` must never write it as-is.
  An empty tuple is non-`None`, so a naive overlay would serialize it as
  `"ensemble_models": []`, which `parse_config` immediately rejects
  (non-empty list required) — bricking the file: writable but never
  loadable again. `ConfigStore.save` treats an empty `ensemble_models` tuple
  the same as `None` (skipped in the merge overlay); see
  `config_store/store.py` below for the enforcement.
- **Strategy**: mirror `CredentialSpec`/`CREDENTIAL_SPECS` exactly; the
  catalog values are a registry snapshot (changing them later is a spec-level
  registry edit and will invalidate stored values by design — the parser
  rejects values no longer registered).
- **Tests**: covered via the store and CLI scenarios; no direct tests of
  constants.

### `src/resume_roast/persistence/config_store/parser.py`

- **Interface**:

  ```python
  def parse_config(data: dict[str, Any]) -> Config: ...
  ```

- **Behavior**: every setting is optional — a key that is absent **or whose
  value is JSON `null`** leaves the field `None` (mirroring
  `parse_credentials`'s `data.get(key)` + `is None` check exactly: a null
  value is indistinguishable from an absent key, never a validation error).
  Unknown keys are ignored, preserving SPEC-001's tolerance test. When a key
  is present with a **non-null** value: a scalar setting must be a `str`
  that is a member of its spec's `choices`; `ensemble_models` must be a
  non-empty list of unique strings, each a member of `MODEL_CATALOG`, and is
  converted to a `tuple`. Violations raise `InvalidSchemaError` with a
  message naming the offending key (the store prefixes the file path).
- **Acceptance Examples**:

  ```text
  Input:  parse_config({"persona": "recruiter", "future_setting": 1})
  Output: Config(persona="recruiter")
  ```

  ```text
  Input:  parse_config({"persona": None})
  Output: Config(persona=None)   # null treated as absent, not an error
  ```

  ```text
  Input:  parse_config({"persona": "ceo"})
  Output: raises InvalidSchemaError("persona must be one of: recruiter, hiring-manager")
  ```

  ```text
  Input:  parse_config({"ensemble_models": []})
  Output: raises InvalidSchemaError (non-empty list required)
  ```

- **Data flow**: called only by `ConfigStore.load` on the output of
  `read_json_object` — the single INV-002 ingestion seam for this domain.
- **Edge cases**: wrong-type non-null scalars (numbers, lists) rejected;
  JSON `null` on any key tolerated as absent (not rejected — see Behavior);
  duplicate ensemble entries rejected; ensemble items of non-string type
  rejected.
- **Strategy**: iterate `SETTING_SPECS` and dispatch on `spec.multi` rather
  than hand-writing five per-field blocks; mirror `parse_credentials`'s
  shape, including its `is None` absence check.
- **Tests**: `test_load_rejects_unregistered_scalar_value`,
  `test_load_rejects_malformed_ensemble`,
  `test_load_tolerates_unknown_keys_alongside_known_ones`,
  `test_load_treats_explicit_null_as_absent`, plus the roundtrip scenarios.

### `src/resume_roast/persistence/config_store/store.py`

- **Interface**: unchanged —
  `load() -> Config`, `save(config: Config) -> None`, `path` property.
- **Behavior**: `load()` keeps missing-file → `Config()`; parser
  `InvalidSchemaError`s are re-raised prefixed with the file path, exactly
  as `CredentialsStore.load` does. `save()` becomes read-merge-write:
  read the existing JSON object if the file exists, overlay every
  non-`None` field of the given `Config` (via `asdict`) — **except an empty
  `ensemble_models` tuple (`()`), which is treated as `None` and skipped in
  the overlay** (the corruption guard from `models.py`: writing `[]` would
  produce a file `parse_config` immediately rejects) — atomically write
  with `write_json_object(path, merged)` — **without** `secure=True`
  (`config.json` is the shareable file; 0600 is a credentials-only
  property).
- **Acceptance Examples**:

  ```text
  Input:  ConfigStore(dir).save(Config(persona="recruiter")) over
          config.json containing {"model": "meta/llama-3.1-8b-instruct"}
  Output: config.json == {"model": "meta/llama-3.1-8b-instruct", "persona": "recruiter"}
  ```

  ```text
  Input:  ConfigStore(dir).save(Config(ensemble_models=("nvidia/nemotron-3-super-120b-a12b",)))
          then ConfigStore(dir).save(Config(ensemble_models=()))
  Output: config.json still has
          "ensemble_models": ["nvidia/nemotron-3-super-120b-a12b"] — the
          empty-tuple save is a no-op for that field, not an overwrite to []
  ```

- **Data flow**: identical lifecycle to `CredentialsStore` minus secure
  mode.
- **Edge cases**: unwritable directory → `PersistenceError` (from
  `write_json_object`); an empty `ensemble_models` tuple is skipped in the
  overlay rather than written (corruption guard, see above); merging
  preserves unknown keys already present in the file (same
  forward-compatibility behavior as the credentials store).
- **Strategy**: transcribe `CredentialsStore.save`'s merge, drop
  `secure=True`.
- **Tests**: roundtrip; `test_save_preserves_fields_not_included_in_update`
  (covers both registered-field and unknown-key preservation);
  `test_save_ignores_empty_ensemble_tuple` (corruption guard);
  never-touches-credentials; the existing SPEC-001 scenarios unmodified.

### `src/resume_roast/persistence/config_store/__init__.py`

- **Change**: re-export `SettingSpec` and `SETTING_SPECS` alongside the
  existing `Config`/`ConfigStore` (mirroring how `credentials_store`'s
  `__init__` exposes `CREDENTIAL_SPECS`). Handlers import only from this
  package root.
- **Tests**: exercised transitively by every import in the new code.

### `src/resume_roast/cli/config/handler.py`

- **Interface**:

  ```python
  @config_cli.command("settings")
  def settings() -> None:
      """Walk through each setting, selecting values from numbered menus."""
      ...
  ```

- **Behavior**: loads current config once
  (`ConfigStore(storage_dir()).load()`), then for each spec in
  `SETTING_SPECS`, in order:
  1. echoes the field header with its current value —
     `Model [current: (not set)]:` — where the current value is the saved
     scalar, the comma-joined ensemble, or `(not set)`;
  2. echoes the numbered choices (`  1. …` per entry) followed by
     `  0. Keep current`;
  3. single-select fields: `typer.prompt("Enter a number", type=int)`;
     `0` keeps the current value (field skipped), a valid index records the
     chosen value, anything out of range → `Error: invalid selection` on
     stderr, exit 1, nothing written;
  4. multi-select (`ensemble_models`):
     `typer.prompt("Enter numbers separated by commas (0 to keep current)")`
     as a string; a bare `0` — and only a bare `0`, the sole content of the
     input — skips; otherwise the input is split on commas, tokens
     stripped — every token must be an integer **in range 1..N** (`0` is
     therefore invalid here, the same as any other out-of-range token: `0`
     only means "keep current" when it is the entire input, not when mixed
     with other numbers, e.g. `0,2,3` is an invalid-token error, not a
     partial skip), duplicates are de-duplicated preserving first
     occurrence, and selection order defines the stored order; any invalid
     token → error, exit 1, nothing written.

  After the walk: if no field was changed, echoes `No changes.` and exits 0
  without writing. Otherwise saves once via `ConfigStore.save`,
  `PersistenceError` reported as a one-line stderr error with exit 1, and
  on success echoes `Saved settings to {store.path}`.
- **Acceptance Examples**:

  ```text
  Input:  resume-roast config settings, stdin "1\n1\n2\n7\n3,1,3\n"
          (model=1, persona=1, level=2, feedback_model=7,
           ensemble="3,1,3" — non-ascending with a duplicate, to prove
           order is preserved and dedup is first-occurrence, not sorted)
  Output: exit 0; "Saved settings to …/config.json"; config.json ==
          {"model": "nvidia/nemotron-3-super-120b-a12b",
           "persona": "recruiter",
           "level": "entry",
           "feedback_model": "meta/llama-3.1-8b-instruct",
           "ensemble_models": ["meta/llama-4-maverick-17b-128e-instruct",
                               "nvidia/nemotron-3-super-120b-a12b"]}
  ```

  ```text
  Input:  resume-roast config settings, stdin "0\n0\n0\n0\n0\n"
  Output: exit 0; "No changes."; config.json not created
  ```

  ```text
  Input:  resume-roast config settings, stdin "99\n"
  Output: exit 1; one-line error on stderr; nothing written
  ```

  ```text
  Input:  resume-roast config settings   (config.json has
          {"model": "deepseek-ai/deepseek-v4-flash"}), stdin "0\n1\n2\n0\n0\n"
          (model skipped, persona=1, level=2, feedback_model skipped,
           ensemble skipped)
  Output: first prompt shows
          "Model [current: deepseek-ai/deepseek-v4-flash]:"; exit 0;
          config.json == {"model": "deepseek-ai/deepseek-v4-flash",
                          "persona": "recruiter",
                          "level": "entry"}
          — the skipped model field is carried over from the existing file
          (via the store's read-merge-write, not because the wizard
          re-selects it), and skipped fields never gain a key.
  ```

- **Data flow**: one `ConfigStore.load` (to display current values), local
  accumulation of chosen values, at most one `ConfigStore.save`. No other
  I/O.
- **Edge cases**: fail-fast on the first **out-of-range** selection at any
  single-select menu, and on the first invalid (non-numeric or
  out-of-range/negative) token at the ensemble prompt — both exit 1
  immediately, no re-prompt. Note `typer.prompt(type=int)` (Click) natively
  *re-prompts* on non-integer input at single-select menus rather than
  failing fast — identical to `config credentials`'s existing behavior, not
  a new gap this spec introduces; only out-of-range integers and malformed
  ensemble tokens are fail-fast. All-skip run writes nothing;
  partially-completed wizard that errors writes nothing (save happens only
  at the end).
- **Strategy**: iterate `SETTING_SPECS` generically (one loop, branch on
  `spec.multi`) — no per-field code. Accumulate updates with
  `dataclasses.replace(updates, **{spec.key: value})` starting from
  `Config()` so the construction stays `pyright --strict`-clean. "No
  changes" means every field was skipped via `0` — i.e. `updates ==
  Config()`. A **same-value selection** (picking the numbered option that
  matches the already-saved value) still assigns that field in `updates`
  and therefore still triggers a save — the wizard does not compare the
  picked value against the current one to detect a no-op; only a bare `0`
  counts as "unchanged." This is intentional to keep the wizard simple, not
  an optimization opportunity for the implementer to add. Mirror
  `credentials`'s error/exit conventions exactly.
- **Tests**: the `test_config_settings_*` scenarios and the extended
  group-help assertion.

### `src/resume_roast/cli/show/handler.py`

- **Interface**:

  ```python
  @show_cli.command("settings")
  def settings() -> None:
      """List every setting's saved value, or (not set)."""
      ...
  ```

- **Behavior**: loads config once, iterates `SETTING_SPECS`, echoes one
  `{label}: {value}` line per setting — the saved scalar, the comma-joined
  ensemble (`", ".join`), or `(not set)` for `None`.
- **Acceptance Examples**:

  ```text
  Input:  resume-roast show settings   (nothing saved)
  Output: Model: (not set)
          Persona: (not set)
          Level: (not set)
          Feedback model: (not set)
          Ensemble models: (not set)
  ```

  ```text
  Input:  resume-roast show settings   (full config saved)
  Output: Model: nvidia/nemotron-3-super-120b-a12b
          Persona: recruiter
          Level: entry
          Feedback model: meta/llama-3.1-8b-instruct
          Ensemble models: nvidia/nemotron-3-super-120b-a12b, meta/llama-4-maverick-17b-128e-instruct
  ```

- **Data flow**: one `ConfigStore.load` → format → `typer.echo`. Nothing
  else.
- **Edge cases**: none beyond `(not set)` — settings are not secret, so no
  masking applies (and none may creep in: any secret-valued field belongs
  in the credentials domain, per INV-001).
- **Strategy**: mirror `show credentials`'s loop, reusing `_NOT_SET`;
  branch on `spec.multi` for the join.
- **Tests**: the `test_show_settings_*` scenarios and the extended
  group-help assertion.

## Definition of Done — Hard Gates

All of these must be true for this spec to be marked completed:

- [ ] All tests pass (`make test`), including SPEC-001's five config-store
      scenarios unmodified.
- [ ] Coverage target met (repo default, `fail_under = 85`).
- [ ] `make check` passes (ruff format/check, pyright strict).
- [ ] `make check-tdd` passes (`test:` commit precedes `feat:` commit).
- [ ] Every Acceptance Example above has a corresponding passing test.
- [ ] INV-001 enforcement test passes
      (`test_save_settings_never_touches_credentials_file`).
- [ ] INV-002 enforcement tests pass (the two `test_load_rejects_*`
      parametrized scenarios).
- [ ] Manual smoke test, both entry points: `config settings` full walk
      saves the expected `config.json`; a second run shows current values
      and all-`0` produces `No changes.`; `show settings` renders both the
      not-set and configured states; `config`/`show` group help lists both
      `credentials` and `settings`. (Settings prompts are visible-input, so
      the Windows hidden-input limitation from SPEC-002/003 does **not**
      apply here — the full wizard is drivable in a real terminal.)

## Advisory Reports

Available at the user's discretion; findings go to
`reports/{check-name}-005.md` and do not block closure:

- [Spec Review](../docs/checks/spec-review.md) — recommended before
  implementation; this spec fixes registry values (personas, levels, model
  catalog) that are product decisions worth a second look.
- [Local Test Quality](../docs/checks/local-test-quality.md) — mandatory at
  Execution Order step 2 (not advisory).
- [Dead Code](../docs/checks/dead-code.md) — run at green.
- [Local Doc Drift](../docs/checks/local-doc-drift.md) — run at green;
  `docs/development.md`'s CLI examples may want a `settings` mention.
- [Code Review](../docs/checks/code-review.md) — run before closure.
- [Workflow Conformance](../docs/checks/workflow-conformance.md) — run
  before closure.

## Constraints

- No new third-party dependencies; no `pyproject.toml` changes.
- No new files — this spec only fills in existing modules.
- `config.json` is written **without** secure mode; `credentials.json` is
  never read or written by any settings code path.
- All selectable values come from the registries in
  `config_store/models.py`; neither handler defines its own value lists or
  literals beyond `_NOT_SET`, `(not set)`-style presentation strings, and
  prompt text.
- `parse_config` is the only code that inspects raw config JSON (INV-002);
  handlers consume `Config` only.
- Wizard/display field order is `SETTING_SPECS` order — a single source of
  truth for both commands.
- `storage_dir()` resolved and `ConfigStore` constructed inside each
  command function body, per invocation (DP-003).
- SPEC-001's five config-store test scenarios must pass unmodified; the two
  group-help CLI scenarios may only gain one assertion each, on the new
  command's help-summary text (see Test Plan — not a bare `"settings"`
  substring, which the group description already contains).
- Completed specs (SPEC-001 through SPEC-004) are immutable — not edited.

## Dependencies

- SPEC-001 — provides the config-store stub being filled in, the JSON file
  primitives, error types, and `storage_dir()`.
- SPEC-004 — provides the per-group Typer wiring (`config_cli`/`show_cli`)
  the new commands register against.

## Footnotes

### Manual Corrections

Populated after agent completes implementation. Each entry documents
something the agent got wrong and how it was manually corrected. This serves
as training signal for future specs.

- Post-implementation, the user requested three behavior changes to the
  spec as originally written, applied in commit a01cd48:
  1. **Storage filename**: `ConfigStore.FILENAME` changed from
     `config.json` to `settings.json`. Every reference to `config.json`
     throughout this spec's Behavior/Acceptance-Example prose (e.g. the
     `config settings` and `store.save` examples) is stale relative to the
     shipped code — the domain name (`config_store`/`Config`) is unchanged
     per the spec's own non-goal, only the on-disk filename moved.
  2. **`show settings` ensemble display**: the comma-joined ensemble line
     is now bracketed, e.g. `Ensemble models: [a, b]` instead of
     `Ensemble models: a, b`, so it reads visibly as a list.
  3. **`config settings` wizard exit/keep-current semantics**: the
     original spec had `0` mean "keep current value" per field. The user
     asked for `0` to instead exit the whole wizard immediately without
     saving (echoing `Cancelled.`, exit 0, mirroring `config credentials`'s
     cancel), and for a blank (Enter-only) response to mean "keep current"
     for that field instead. This also dropped `typer.prompt(type=int)`'s
     native re-prompt-on-non-integer behavior for the single-select
     prompts (needed to accept a blank string), so a non-numeric
     single-select entry now fails fast with `Error: invalid selection`
     (exit 1) rather than re-prompting — covered by
     `test_config_settings_rejects_non_numeric_selection`. New coverage:
     `test_config_settings_exits_without_saving_when_zero_entered`
     (parametrized over exiting at a single-select vs. the ensemble
     prompt).
