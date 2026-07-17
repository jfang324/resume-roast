"""Enums for the generate-block service."""

from enum import Enum


class GenerateBlockCommand(Enum):
    """Generate-block's slash commands; each value is the name the user types."""

    GENERATE = "generate"
