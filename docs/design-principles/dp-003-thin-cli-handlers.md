# DP-003: Thin CLI Handlers

**Rule**: A CLI handler method — the callable backing one leaf subcommand —
contains only input parsing/validation and output formatting, and delegates
all actual work to the persistence/store layer (or a future `services/`
layer). It never contains multi-step business logic, direct filesystem/env/
JSON access, or formatting/masking logic duplicated inline instead of calling
the shared helper that already exists for it.

**Reasoning**: The CLI package has two logical layers: an entry dispatcher
(`cli/app.py`) that builds the Typer app and every group's Typer object and
wires each leaf command into them, and one handler class per command group —
one per group, not one module per leaf command — whose methods translate
between the terminal boundary (prompts, echoes, exit codes) and the store/
service layer underneath. A group's handler class is where behavior shared
across that group's leaf commands (a display helper, an error-reporting
helper) belongs, so sibling commands don't duplicate it. Handler methods are
the layer most exposed to reviewers skimming for UX changes, and the most
tempting place to bolt on "just one more step" because it's the last code
touched before something works end to end. Logic that accumulates there is
untestable without going through Typer's `CliRunner` (slow, requires
simulated stdin), duplicates across groups that need the same behavior (e.g.,
`config`'s and a later `show`'s credential handling both needing masking),
and undermines the reason the CLI is organized this way at all: adding a
group or command should be an additive assembly of existing store operations,
not a bespoke reimplementation. The codebase has no `services/` package yet;
`persistence/*_store` packages play that role today. This principle is
written so that when a `services/` package is eventually extracted, only the
store/service seam changes — the CLI seam (thin handler methods calling into
*something* below them) does not need to be revisited.

## Violation Signals

Concrete, grep-able or review-detectable patterns that indicate the principle
is being broken.

- A handler method doing more than prompt/validate/format/delegate — e.g. it
  fetches from one store, transforms the result, and feeds it into a second
  store call, or contains a loop/branch that reasons about the *meaning* of
  domain data rather than just checking success/failure or input shape.
  - **How to fix**: move the multi-step sequence into the relevant store as a
    named method (or, once one exists, a `services/` function); the handler
    method calls it once and only handles the boundary translation.
- Inline duplication of formatting/masking logic instead of calling the
  existing shared helper — e.g. a handler method computing
  `"*" * n + value[-4:]` itself instead of importing `mask_secret`.
  - **How to fix**: import and call the existing helper. Grep: string
    literals like `"****"` or slice expressions `[-4:]` appearing under
    `src/` outside `persistence/*/models.py`. Test code is exempt — tests
    legitimately assert masked literals like `"****9876"`, as
    [DP-001](dp-001-test-behavior-not-implementation.md) requires literal
    expected values.
- Direct file/env/JSON access in a handler method: `open(`, `.read_text(`,
  `.write_text(`, `json.load`, `json.dump`, `os.environ`, `os.getenv`
  appearing anywhere under `cli/<group>/`.
  - **How to fix**: route through the appropriate `persistence/*_store` (add
    a store method if the operation doesn't exist yet) instead of touching
    the filesystem/env from the handler.
- A Typer decorator (`@config_app.command(...)` or equivalent) applied
  anywhere outside `cli/app.py`.
  - **How to fix**: handler methods stay undecorated; `cli/app.py`
    instantiates the group's handler and registers each bound method once —
    `config_app.command("credentials")(handler.credentials)`. Grep:
    `@\w+_app\.command` outside `app.py`.
- A handler class importing another group's handler, or importing
  `cli/app.py`.
  - **How to fix**: shared logic belongs in the store/service layer, not in a
    sibling group's handler; extract it downward instead of reaching
    sideways or upward. Grep: `from resume_roast.cli\.` inside any file
    under `cli/<group>/` referencing a different group.
- A handler class constructing a store or resolving `storage_dir()` in
  `__init__` or at class level instead of inside the method that needs it.
  - **How to fix**: resolve paths and construct stores per-invocation, inside
    the method body. `storage_dir()` reads its environment variable at call
    time by design; a handler instantiated once at import time that caches
    this at construction will silently use a stale value.

## Examples

Concrete before/after or good/bad examples that illustrate the principle in
action.

| Avoid | Prefer |
|-------|--------|
| A handler method hand-computing `"****" + value[-4:]` inline | `from resume_roast.persistence.credentials_store import mask_secret` and call it |
| `@config_app.command("credentials")` applied directly to a handler method | A plain `def credentials(self) -> None: ...` method; `config_app.command("credentials")(handler.credentials)` registered once in `cli/app.py` |
| A handler method calling `Path.home() / ".resume-roast"` and reading/writing JSON itself | A handler method calling `CredentialsStore(storage_dir()).save(...)` |
| A handler class resolving `self._store = CredentialsStore(storage_dir())` in `__init__` | Each method calling `CredentialsStore(storage_dir())` itself, per invocation |
| A handler method branching on what a fetched record's fields *mean* to decide what to do next | The store/service exposes the decision as a single call; the handler method branches only on success/failure of that call |

## When to Relax

Conditions where bending this principle is acceptable. Without explicit approval in a spec, the default is to follow the principle.

- Interactive prompt/menu construction (numbered selection loops,
  confirmation prompts) is presentation, not business logic, even though it
  iterates and branches — it stays in the handler method as long as it only
  validates/formats input and doesn't interpret domain data.
- Calling exactly one store once is expected orchestration for a command
  with a single domain dependency — the signal is *multiple* stores,
  *multiple* sequential steps, or *duplicated* logic, not the mere presence
  of a store call.
- A group's internal pipeline shape (e.g. how a fetch-and-display command
  structures its "load data, then render it" flow) is design content for the
  spec introducing that group, not something this principle prescribes — it
  only requires that whatever shape is chosen stays thin and delegates.
