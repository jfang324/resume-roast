"""`generate-block` command: bare handler function, wired by the registry."""

from rich.console import Console

from resume_roast.cli.chat_renderer import ConsoleRenderer
from resume_roast.cli.generate_block.constants import WELCOME
from resume_roast.cli.input_provider import ConsoleInputProvider
from resume_roast.cli.utils import build_client, model_label
from resume_roast.services.generate_block.service import run


def generate_block() -> None:
    """Interview the user about a role or project, then generate a resume block.

    Supports ``/generate <optional notes>`` to produce a resume block and
    plain text for conversational information gathering.
    """
    client, settings = build_client()
    console = Console(highlight=False)
    label = model_label(settings.model)
    renderer = ConsoleRenderer(console, label, settings.model)
    input_provider = ConsoleInputProvider()

    console.print(WELCOME)
    run(client, renderer, input_provider)
