# DP-003: Thin CLI Handlers

**Rule**: A CLI command function — the callable backing one leaf subcommand —
contains only input parsing/validation and output formatting, and delegates
all actual work to the persistence/store layer (or a future `services/`
layer). It never contains multi-step business logic, direct filesystem/env/
JSON access, or formatting/masking logic duplicated inline instead of calling
the shared helper that already exists for it.

**Reasoning**: The CLI package has two logical layers: an entry dispatcher
(`cli/runner.py`) that builds the root Typer object and mounts each group's
Typer under a name via `add_typer`, and one handler module per command group
(`cli/<group>/handler.py`) — one per group, not one module per leaf command —
that owns that group's `typer.Typer()` object and its
`@<group>_cli.command(...)`-decorated command functions. Those functions
translate between the terminal boundary (prompts, echoes, exit codes) and the
store/service layer underneath. A group's handler module is where behavior
shared across that group's leaf commands (a display helper, an
error-reporting helper) belongs, so sibling commands don't duplicate it.
Command functions are the layer most exposed to reviewers skimming for UX
changes, and the most tempting place to bolt on "just one more step" because
it's the last code touched before something works end to end. Logic that
accumulates there is untestable without going through Typer's `CliRunner`
(slow, requires simulated stdin), duplicates across groups that need the same
behavior (e.g., `config`'s and `show`'s credential handling both needing
masking), and undermines the reason the CLI is organized this way at all:
adding a group or command should be an additive assembly of existing store
operations, not a bespoke reimplementation. The two-layer split keeps the
wiring in `runner.py` a flat, scannable list of `add_typer` calls while each
group's commands live and grow next to each other. The codebase has no
`services/` package yet; `persistence/*_store` packages play that role today.
This principle is written so that when a `services/` package is eventually
extracted, only the store/service seam changes — the CLI seam (thin command
functions calling into *something* below them) does not need to be revisited.

## Violation Signals

Concrete, grep-able or review-detectable patterns that indicate the principle
is being broken.

- A command function doing more than prompt/validate/format/delegate — e.g. it
  fetches from one store, transforms the result, and feeds it into a second
  store call, or contains a loop/branch that reasons about the *meaning* of
  domain data rather than just checking success/failure or input shape.
  - **How to fix**: move the multi-step sequence into the relevant store as a
    named method (or, once one exists, a `services/` function); the command
    function calls it once and only handles the boundary translation.
- Inline duplication of formatting/masking logic instead of calling the
  existing shared helper — e.g. a command function computing
  `"*" * n + value[-4:]` itself instead of importing `mask_secret`.
  - **How to fix**: import and call the existing helper. Grep: string
    literals like `"****"` or slice expressions `[-4:]` appearing under
    `src/` outside `persistence/*/models.py`. Test code is exempt — tests
    legitimately assert masked literals like `"****9876"`, as
    [DP-001](dp-001-test-behavior-not-implementation.md) requires literal
    expected values.
- Direct file/env/JSON access in a command function: `open(`, `.read_text(`,
  `.write_text(`, `json.load`, `json.dump`, `os.environ`, `os.getenv`
  appearing anywhere under `cli/<group>/`.
  - **How to fix**: route through the appropriate `persistence/*_store` (add
    a store method if the operation doesn't exist yet) instead of touching
    the filesystem/env from the command function.
- Command registration living outside a group's handler module — a Typer
  decorator (`@config_cli.command(...)` or equivalent), a group's
  `typer.Typer()` object, or a bound-method/free-function `.command(...)(fn)`
  registration appearing in `cli/runner.py` instead of in
  `cli/<group>/handler.py`.
  - **How to fix**: each group's `typer.Typer()` object and every
    `@<group>_cli.command(...)`-decorated function live in that group's
    `cli/<group>/handler.py`; `cli/runner.py` only builds the root Typer and
    mounts each group with `cli.add_typer(<group>_cli, name=...)`. Grep:
    `\.command\(` or `typer\.Typer\(` appearing in `cli/runner.py`.
- A group handler module importing another group's handler module, or
  importing `cli/runner.py`.
  - **How to fix**: shared logic belongs in the store/service layer, not in a
    sibling group's handler; extract it downward instead of reaching
    sideways or upward. Grep: `from resume_roast.cli\.` inside any file
    under `cli/<group>/` referencing a different group or `runner`.
- Resolving `storage_dir()` or constructing a store at module/import scope in
  a `cli/<group>/handler.py` (e.g. a module-level
  `_store = CredentialsStore(storage_dir())`) instead of inside the command
  function that needs it.
  - **How to fix**: resolve paths and construct stores per-invocation, inside
    the command function body. `storage_dir()` reads its environment variable
    at call time by design; a value captured at import time will silently be
    stale.

## Examples

Concrete before/after or good/bad examples that illustrate the principle in
action.

| Avoid | Prefer |
|-------|--------|
| A command function hand-computing `"****" + value[-4:]` inline | `from resume_roast.persistence.credentials_store import mask_secret` and call it |
| Building `config_cli` or registering `config_cli.command("credentials")(fn)` in `cli/runner.py` | `config_cli = typer.Typer(...)` plus `@config_cli.command("credentials") def credentials() -> None: ...` in `cli/config/handler.py`; `cli/runner.py` only `cli.add_typer(config_cli, name="config", ...)` |
| A command function calling `Path.home() / ".resume-roast"` and reading/writing JSON itself | A command function calling `CredentialsStore(storage_dir()).save(...)` |
| A module-level `_store = CredentialsStore(storage_dir())` in `cli/config/handler.py` | Each command function calling `CredentialsStore(storage_dir())` itself, per invocation |
| A command function branching on what a fetched record's fields *mean* to decide what to do next | The store/service exposes the decision as a single call; the command function branches only on success/failure of that call |

## When to Relax

Conditions where bending this principle is acceptable. Without explicit approval in a spec, the default is to follow the principle.

- Interactive prompt/menu construction (numbered selection loops,
  confirmation prompts) is presentation, not business logic, even though it
  iterates and branches — it stays in the command function as long as it only
  validates/formats input and doesn't interpret domain data.
- Calling exactly one store once is expected orchestration for a command
  with a single domain dependency — the signal is *multiple* stores,
  *multiple* sequential steps, or *duplicated* logic, not the mere presence
  of a store call.
- A group's internal pipeline shape (e.g. how a fetch-and-display command
  structures its "load data, then render it" flow) is design content for the
  spec introducing that group, not something this principle prescribes — it
  only requires that whatever shape is chosen stays thin and delegates.
