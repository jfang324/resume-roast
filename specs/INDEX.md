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
