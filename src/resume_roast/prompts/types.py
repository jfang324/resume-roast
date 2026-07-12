"""Dataclasses describing built prompts and reviewer personas."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Persona:
    """A reviewer identity the model adopts when evaluating a resume."""

    label: str
    prompt: str


@dataclass(frozen=True)
class Prompt:
    """What every prompt builder returns.

    One-shot features (evaluate) always set ``user``. Chat-style features
    (refine, generate-block) build only the system message and take their
    user turns from the live conversation.
    """

    system: str
    user: str | None = None
