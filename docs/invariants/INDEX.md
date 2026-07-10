# Invariants

<!-- Each file documents a single invariant: a property of the system that must
     never be violated. Files are named inv-{nnn}-kebab-case-title.md.

     Specs reference the invariants they must preserve. If a spec intentionally
     changes an invariant, that must be explicitly called out and justified.
-->

- [inv-001-secrets-stay-in-credential-store.md](inv-001-secrets-stay-in-credential-store.md) — Secrets persist only in the credentials file and are never shown unmasked anywhere else.
- [inv-002-json-never-crosses-a-boundary-untyped.md](inv-002-json-never-crosses-a-boundary-untyped.md) — Raw JSON (local files or API responses) is always converted to a typed model by a dedicated parser before internal code touches it.
