"""Display helpers shared across subcommand groups."""

NOT_SET = "(not set)"
"""Shown wherever an optional value has nothing saved."""


def display_value(value: str | tuple[str, ...]) -> str:
    """Render a setting value for prompts and display."""
    return ", ".join(value) if isinstance(value, tuple) else value
