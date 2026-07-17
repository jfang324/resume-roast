"""Enums for the chat command pipeline."""

from enum import Enum


class ArgPolicy(Enum):
    """Whether a command's argument is required or optional."""

    REQUIRED = "required"
    OPTIONAL = "optional"
