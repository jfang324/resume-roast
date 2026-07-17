"""Session constants for the refine service."""

from resume_roast.services.chat.enums import ArgPolicy
from resume_roast.services.chat.types import CommandSpec
from resume_roast.services.refine.enums import RefineCommand

TEMPERATURE: float = 0.5

COMMANDS: dict[RefineCommand, CommandSpec] = {
    RefineCommand.REPLACE: CommandSpec(
        ArgPolicy.REQUIRED, "Replace the bullet with a new version", "<text>"
    ),
    RefineCommand.GENERATE: CommandSpec(
        ArgPolicy.OPTIONAL, "Generate a candidate rewrite", "<notes>"
    ),
}
"""The refine vocabulary; the ``/help`` text is generated from it."""
