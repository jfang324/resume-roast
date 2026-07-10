"""Shared errors for JSON-backed persistence stores."""

from __future__ import annotations


class PersistenceError(Exception):
    """Base for all persistence failures."""


class InvalidJsonError(PersistenceError):
    """A store file exists but is not valid JSON."""


class InvalidSchemaError(PersistenceError):
    """A store file is valid JSON but not the shape the parser expects."""
