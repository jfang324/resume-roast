"""Error boundary wrapped around every CLI handler at registration time."""

import functools
from typing import Any

import typer

from resume_roast.cli.types import Handler
from resume_roast.persistence.errors import PersistenceError


def guarded(handler: Handler) -> Handler:
    """Wrap a handler so a PersistenceError becomes a one-line error + exit 1.

    Centralizes the "storage failure -> user-facing error" boundary here
    instead of repeating a try/except in every handler. The closure keeps
    the handler's signature intact (via functools.wraps), which Typer
    inspects to build the command's options.
    """

    @functools.wraps(handler)
    def wrapper(*args: Any, **kwargs: Any) -> None:
        try:
            handler(*args, **kwargs)
        except PersistenceError as exc:
            typer.echo(f"Error: {exc}", err=True)
            raise typer.Exit(code=1) from exc

    return wrapper
