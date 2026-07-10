# Features Index

<!-- This file maps top-level user-facing features to the specs that touched them.
     Format:
     ## Feature: {name}
     - {spec-filename} — {brief relevance / what it did}
-->

## Feature: CLI structure

- spec-002-restructure-cli-into-package.md — restructured `cli.py` into a
  `cli/` package (dispatcher + one handler class per command group), per
  DP-003; pure refactor, no user-visible behavior change.
- spec-004-rewire-cli-runner-and-typer-groups.md — re-wired the `cli/`
  package: renamed `cli/app.py` → `cli/runner.py`, and replaced the
  handler-class + bound-method registration with a `typer.Typer()` +
  `@<group>_cli.command(...)`-decorated function per command group, owned by
  that group's own `cli/<group>/handler.py`; DP-003 revised accordingly.
  Pure refactor, no user-visible behavior change.

## Feature: Credentials management

- spec-001-config-and-credential-storage.md — added `config credentials`
  (set/overwrite a registered credential, hidden input, masked confirmation).
- spec-003-show-credentials.md — added `show credentials` (lists every
  registered credential masked, or `(not set)`), built as the `show` group
  on top of SPEC-002's `cli/` package structure.

## Feature: Settings management

- spec-001-config-and-credential-storage.md — stubbed the `config_store/`
  domain (empty `Config`, pass-through parser, no-op save) this feature
  fills in.
- spec-005-settings-persistence.md — added `config settings` (numbered-menu
  wizard for model/persona/level/feedback-model/ensemble) and `show
  settings` (lists every setting or `(not set)`), backed by `settings.json`.
