"""Dataclasses describing built prompts and reviewer personas."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Persona:
    """A reviewer identity the model adopts when evaluating a resume."""

    label: str
    prompt: str


@dataclass(frozen=True)
class Prompt:
    """What the evaluate builder returns: the one-shot system and user messages."""

    system: str
    user: str
