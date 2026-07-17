"""Session constants for the generate-block service."""

from resume_roast.services.chat.enums import ArgPolicy
from resume_roast.services.chat.types import CommandSpec
from resume_roast.services.generate_block.enums import GenerateBlockCommand

TEMPERATURE: float = 0.5

COMMANDS: dict[GenerateBlockCommand, CommandSpec] = {
    GenerateBlockCommand.GENERATE: CommandSpec(
        ArgPolicy.OPTIONAL, "Generate a resume block", "<notes>"
    ),
}
"""The generate-block vocabulary; the ``/help`` text is generated from it."""

HELP_EPILOGUE = "Or just type naturally and I'll ask questions."
