"""Shared errors raised by every JSON-backed store."""


class PersistenceError(Exception):
    """Base for all persistence failures."""


class InvalidJsonError(PersistenceError):
    """A store file exists but is not valid JSON."""


class InvalidSchemaError(PersistenceError):
    """A store file is valid JSON but not the shape a parser expects."""
