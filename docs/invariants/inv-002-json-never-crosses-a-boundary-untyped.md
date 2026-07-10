# INV-002: JSON Never Crosses a Boundary Untyped

**Invariant**: Raw JSON — whether loaded from a local file or received from an
API response — is never passed to, stored by, or read from by internal code as
a bare `dict`/`list`/`Any`. It is converted by a dedicated parsing function into
a typed dataclass (or other typed model) at the point it enters the system, and
everything downstream consumes that type, not the raw structure.

**Scope**: Every module that reads JSON from outside the process: local file
stores under `src/resume_roast/persistence/` (each domain's `parser.py`) and,
once added, any HTTP client module that deserializes API responses. Internal
code that only ever handles already-typed models is out of scope — the
invariant binds at the point of ingestion, not everywhere data flows.

## Rationale

Untyped JSON (`dict[str, Any]`) defers every assumption about shape to the
point of use: a missing key, a `None` where a string was expected, or a
renamed field surfaces as a `KeyError`/`TypeError`/silent `None` deep in
business logic, far from where the data entered the system and with no
indication of which external source is to blame. A single parsing layer per
source makes the failure surface once, at the boundary, with a message that
names the source; everything after that point can be written and type-checked
(`pyright --strict`) against a real type instead of "hopefully has these
keys." This is also what makes each store's dataclass/parser/store trio (see
`SPEC-001`) a repeatable pattern rather than a one-off: the parser is always
the seam between "arbitrary JSON" and "data the rest of the program can trust."

## Enforcement Mechanism

- **Type-level**: functions that read external JSON are typed to return the
  parsed model (`Credentials`, `Config`, future API response types), never
  `dict[str, Any]` or `Any`; `pyright --strict`'s `reportUnknownMemberType` /
  `reportUnknownVariableType` catch code that leaks an untyped value past the
  parser boundary.
- **Runtime guard**: the parsing function is the only place a `[key]` /
  `.get()` lookup on raw JSON is allowed; it validates presence, type, and any
  domain constraints (e.g., non-blank) before constructing the model, and
  raises a typed error (e.g., `InvalidSchemaError`) instead of returning a
  partially-valid object.
- **CI check**: `pyright --strict` (`make check`) flags a raw dict escaping a
  parser's return type; code review checks that no module outside a
  `parser.py` (or equivalent ingestion module) calls `json.loads` / a response
  client's `.json()` directly.

## Failure Example

- A function reads `config.json`, gets back `dict[str, Any]`, and returns it
  directly to the CLI layer, which does `data["theme"]` — works today, breaks
  silently (`KeyError`) the day the key is renamed, with no error message
  naming `config.json` as the source.
- An API client does `response.json()["choices"][0]["message"]["content"]`
  inline at the call site instead of through a parser — a changed API response
  shape surfaces as an unhandled `KeyError`/`IndexError` inside business logic
  instead of a named `InvalidSchemaError` at the client boundary.
- A store's `load()` returns the raw parsed JSON instead of calling its
  `parser.py`, so two different call sites independently reimplement "get the
  API key out of this dict," and they drift.

## Testing This Invariant

- **Key assertions**:
  - each domain's parser rejects every documented malformed shape (missing
    field, wrong type, blank value, non-object top level) with a typed error,
    not an unguarded `KeyError`/`TypeError`/`AttributeError`;
  - each domain's store/client return type is the parsed model, never
    `dict[str, Any]` — enforced by `pyright --strict` on the function
    signature, not by a runtime test;
  - no test constructs a domain model by hand-assembling a dict and skipping
    the parser — tests exercise ingestion through the parser (directly or via
    the store/client that calls it), per
    [DP-001](../design-principles/dp-001-test-behavior-not-implementation.md).
- **Gating**: `pyright --strict` in `make check` (every commit); parser
  malformed-shape tests in `make test` and CI.

## Exceptions

- None currently. Ad hoc/debug scripts that print raw JSON for inspection are
  not "internal code" in the sense of this invariant, but must not be promoted
  to production code paths without adding a parser.
