# INV-001: Secrets Stay in the Credential Store

**Invariant**: Secret values (API keys) are persisted only in the credentials
file, and never appear — in full — in any other file, in stdout/stderr, in log
output, or in exception messages. Any display of a secret is masked to at most
its last 4 characters.

**Scope**: Every module that touches credentials: the persistence layer
(`src/resume_roast/persistence/`, in particular `credentials_store/` and the
shared `errors.py`/`json_file.py`) and the CLI
(`src/resume_roast/cli/config/handler.py`, where the prompt/masking behavior
lives, and `src/resume_roast/cli/runner.py`, which only wires it), plus any
future module that reads the API key to call an API.

## Rationale

The config/credentials split exists so that config can be shared, versioned, or
debugged freely and so credentials can later be encrypted without touching
config handling. Both properties die the moment a secret leaks into
`config.json`, a log line, or terminal output: users copy-paste config files
and terminal sessions into issues and chats. A leaked API key is a billing and
abuse incident, not a cosmetic bug.

## Enforcement Mechanism

- **Runtime guard**: all display of secrets goes through a single masking
  helper (`mask_secret`); CLI input uses hidden prompts (no echo); storage
  errors report file paths and parse failures, never file contents.
- **CI check**: tests assert the full key is absent from captured CLI output
  and from `config.json` after every operation (see below). Runs in `make
  test` and CI.

Type-level enforcement (e.g., a `Secret` wrapper whose `__repr__` masks) is the
stronger mechanism and should be adopted if secrets start flowing through more
than these two modules.

## Failure Example

- `config credentials` printing "Saved key sk-ant-api03-..." — full key echoed
  to the terminal and into the user's scrollback/paste buffer.
- An `InvalidSchemaError`/`InvalidJsonError` raised on corrupt JSON that
  includes the file's contents in its message — the secret ends up in a
  traceback.
- Writing `anthropic_api_key` into `config.json` "temporarily" — the secret now
  lives in the shareable file.

## Testing This Invariant

- **Key assertions**:
  - after any `config credentials` invocation, the full key string does not
    appear in captured stdout/stderr; the masked form does;
  - after saving credentials, `config.json` (if present) does not contain the
    key string;
  - `mask_secret(key)` never returns more than the last 4 characters of its
    input.
- **Gating**: every `make test` run and CI; these are ordinary pytest tests,
  not a separate suite.

## Exceptions

- None currently. The credentials file itself is the sole permitted location by
  definition. Any future exception (e.g., a `--show-key` debugging flag) must
  be authorized by a spec and recorded here with a link.
