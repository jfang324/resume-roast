"""Command execution for chat sessions: a feature's vocabulary and semantics.

Raw input arrives already lexed (see `input_parser.py`) as a `Command` or
`ChatText`. What a command *means* is a feature's business: each chat feature
subclasses `CommandExecutor`, declaring its vocabulary and turning parsed
input into an `Outcome` the session loop acts on. The shared base handles
everything vocabulary-independent — the ``/exit`` and ``/help`` built-ins,
unknown names, argument policy, and the generated help text.
"""

from abc import ABC, abstractmethod
from collections.abc import Mapping
from enum import Enum

from resume_roast.services.chat.enums import ArgPolicy
from resume_roast.services.chat.types import (
    ChatText,
    Command,
    CommandSpec,
    EndSession,
    Invalid,
    Outcome,
    ShowHelp,
    UserInput,
)

_HELP_USAGE_WIDTH = 19
"""Width of the usage column in the generated help text."""


class CommandExecutor[C: Enum](ABC):
    """Turns parsed input into session outcomes; owns a feature's vocabulary.

    Subclasses declare the vocabulary as an enum-keyed spec table (`commands`)
    and implement the two feature hooks (`chat`, `command`). The shared
    `execute` handles the built-ins and validation, so the `command` hook only
    ever sees a member of the vocabulary enum whose argument satisfies its
    policy; ``/help`` output is generated from the table, so it cannot drift
    from the vocabulary.
    """

    @property
    @abstractmethod
    def commands(self) -> Mapping[C, CommandSpec]:
        """The feature's command vocabulary, beyond the shared built-ins."""

    @property
    def help_text(self) -> str:
        """The ``/help`` output, generated from `commands`."""
        lines = ["Available commands:"]
        for command, spec in self.commands.items():
            usage = f"/{command.value}"

            if spec.arg_hint is not None:
                usage += f" {spec.arg_hint}"

            lines.append(f"  {usage:<{_HELP_USAGE_WIDTH}}{spec.description}")

        lines.append(f"  {'/exit':<{_HELP_USAGE_WIDTH}}End the session")
        lines.append(f"  {'/help':<{_HELP_USAGE_WIDTH}}Show this message")
        text = "\n".join(lines)

        if self.help_epilogue:
            text = f"{text}\n\n{self.help_epilogue}"

        return text

    @property
    def help_epilogue(self) -> str:
        """Free text appended after the command list; empty unless overridden."""
        return ""

    def execute(self, parsed: UserInput | None) -> Outcome:
        """Validate *parsed* against the vocabulary and produce its outcome."""
        match parsed:
            case None:
                return Invalid()

            case ChatText(text):
                return self.chat(text)

            case Command("exit", None):
                return EndSession()

            case Command("help", None):
                return ShowHelp(self.help_text)

            case Command(name, arg):
                command = self._member(name)

                if command is None:
                    return Invalid()

                if self.commands[command].policy is ArgPolicy.REQUIRED and arg is None:
                    return Invalid()

                return self.command(command, arg)

    def _member(self, name: str) -> C | None:
        """Return the vocabulary member the user typed as ``/name``, or None."""
        return next((c for c in self.commands if c.value == name), None)

    @abstractmethod
    def chat(self, text: str) -> Outcome:
        """Produce the outcome for a plain conversational turn."""

    @abstractmethod
    def command(self, command: C, arg: str | None) -> Outcome:
        """Produce the outcome for a validated feature command."""
