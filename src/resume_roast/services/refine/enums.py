"""Enums for the refine service."""

from enum import Enum


class RefineCommand(Enum):
    """Refine's slash commands; each value is the name the user types."""

    REPLACE = "replace"
    GENERATE = "generate"
