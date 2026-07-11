"""Types describing the CLI's command tree."""

from dataclasses import dataclass
from typing import Any, Protocol


class Handler(Protocol):
    """A bare subcommand handler.

    Registration relies on `__name__` for the command's name and the
    docstring for its help text, so a handler must be a named callable —
    a plain function qualifies; an anonymous callable does not.
    """

    __name__: str

    def __call__(self, *args: Any, **kwargs: Any) -> None: ...


@dataclass(frozen=True)
class Group:
    """A named subcommand group and the bare handler functions it exposes."""

    name: str
    help: str
    handlers: tuple[Handler, ...]
