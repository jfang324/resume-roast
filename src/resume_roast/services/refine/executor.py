"""Refine's command executor: the feature vocabulary and the session's bullet state."""

from collections.abc import Mapping
from functools import partial

from resume_roast.prompts.refine.builder import (
    build_chat_message,
    build_generate_message,
    build_replace_message,
)
from resume_roast.services.chat.command_executor import CommandExecutor
from resume_roast.services.chat.types import CommandSpec, Outcome, SendTurn
from resume_roast.services.refine.constants import COMMANDS
from resume_roast.services.refine.enums import RefineCommand


class RefineCommandExecutor(CommandExecutor[RefineCommand]):
    """Owns the refine vocabulary and the session's current bullet.

    ``/replace`` adopts its argument as the current bullet — but only once
    the turn it drives lands, via the outcome's commit callback, so a failed
    exchange leaves the bullet untouched.
    """

    def __init__(self, initial_bullet: str) -> None:
        self.current_bullet = initial_bullet

    @property
    def commands(self) -> Mapping[RefineCommand, CommandSpec]:
        """``/replace <text>`` and ``/generate [notes]``."""
        return COMMANDS

    def chat(self, text: str) -> Outcome:
        """Wrap a conversational turn with the current bullet as context."""
        return SendTurn(build_chat_message(self.current_bullet, text))

    def command(self, command: RefineCommand, arg: str | None) -> Outcome:
        """Build the turn for ``/replace`` or ``/generate``."""
        if command is RefineCommand.REPLACE and arg is not None:
            return SendTurn(build_replace_message(arg), partial(self._adopt_bullet, arg))

        if command is RefineCommand.GENERATE:
            return SendTurn(build_generate_message(self.current_bullet, arg))

        msg = f"Unhandled command: {command!r}"  # REPLACE without arg is policy-filtered
        raise ValueError(msg)

    def _adopt_bullet(self, new_bullet: str) -> None:
        """Commit ``/replace``'s argument once the turn it drives lands."""
        self.current_bullet = new_bullet
