"""`refine` command: bare handler function, wired by the registry."""

from rich.console import Console

from resume_roast.cli.chat_renderer import ConsoleRenderer
from resume_roast.cli.input_provider import ConsoleInputProvider
from resume_roast.cli.utils import USER_PROMPT, build_client, model_label
from resume_roast.services.refine.service import run


def refine(bullet: str) -> None:
    """Coach a single resume bullet through a back-and-forth chat.

    Supports ``/replace <new text>`` to commit a new version of the bullet,
    ``/generate <optional notes>`` to produce a candidate rewrite, and plain
    text for conversational coaching.
    """
    client, settings = build_client()
    console = Console(highlight=False)
    label = model_label(settings.model)
    renderer = ConsoleRenderer(console, label, settings.model)
    input_provider = ConsoleInputProvider()

    # Echo the bullet as the user's first turn, then let the service drive.
    console.print(f"{USER_PROMPT}{bullet}")
    run(client, bullet, renderer, input_provider)
