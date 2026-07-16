"""`refine` command: bare handler function, wired by the registry."""

from rich.console import Console

from resume_roast.cli.chat import USER_PROMPT, run_chat_loop, stream_exchange
from resume_roast.cli.refine.constants import HELP, TEMPERATURE
from resume_roast.cli.utils import build_client, model_label
from resume_roast.integrations.conversation import Conversation
from resume_roast.prompts.refine.builder import RefinePromptBuilder
from resume_roast.prompts.refine.input.parser import RefineParser
from resume_roast.prompts.refine.input.state import RefineState


def refine(bullet: str) -> None:
    """Coach a single resume bullet through a back-and-forth chat.

    Supports ``/replace <new text>`` to commit a new version of the bullet,
    ``/generate <optional notes>`` to produce a candidate rewrite, and plain
    text for conversational coaching.
    """
    client, settings = build_client()

    state = RefineState(RefineParser(), bullet)
    builder = RefinePromptBuilder(state)

    conversation = Conversation(client, builder.build_system(), temperature=TEMPERATURE)

    console = Console(highlight=False)
    label = model_label(settings.model)

    # First turn — send the initial bullet
    console.print(f"{USER_PROMPT}{bullet}")
    stream_exchange(conversation, console, builder.build_first_message(), label, settings.model)

    run_chat_loop(conversation, console, state, builder, label, settings.model, HELP)
