"""Generate-block's command executor: the feature vocabulary, stateless."""

from collections.abc import Mapping

from resume_roast.prompts.generate_block.builder import build_generate_message
from resume_roast.services.chat.command_executor import CommandExecutor
from resume_roast.services.chat.types import CommandSpec, Outcome, SendTurn
from resume_roast.services.generate_block.constants import COMMANDS, HELP_EPILOGUE
from resume_roast.services.generate_block.enums import GenerateBlockCommand


class GenerateBlockCommandExecutor(CommandExecutor[GenerateBlockCommand]):
    """Owns the generate-block vocabulary.

    Stateless — the block in progress lives entirely in the conversation
    history, so no command earns a commit closure.
    """

    @property
    def commands(self) -> Mapping[GenerateBlockCommand, CommandSpec]:
        """``/generate [notes]``."""
        return COMMANDS

    @property
    def help_epilogue(self) -> str:
        """Point out that plain conversation drives the information gathering."""
        return HELP_EPILOGUE

    def chat(self, text: str) -> Outcome:
        """Pass a conversational turn through untouched."""
        return SendTurn(text)

    def command(self, command: GenerateBlockCommand, arg: str | None) -> Outcome:
        """Build the ``/generate`` turn."""
        if command is GenerateBlockCommand.GENERATE:
            return SendTurn(build_generate_message(arg))
        msg = f"Unhandled command: {command!r}"  # single-member vocabulary
        raise ValueError(msg)
