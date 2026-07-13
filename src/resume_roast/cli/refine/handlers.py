"""`refine` command: bare handler function, wired by the registry."""

from rich.console import Console

from resume_roast.cli.chat import USER_PROMPT, require_api_key, run_chat_loop, stream_exchange
from resume_roast.cli.utils import model_label
from resume_roast.integrations.conversation import Conversation
from resume_roast.integrations.llm_client import LlmClient
from resume_roast.integrations.nvidia.client import NvidiaClient
from resume_roast.persistence.paths import storage_dir
from resume_roast.persistence.settings.store import SettingsStore
from resume_roast.prompts.refine.builder import RefinePromptBuilder
from resume_roast.prompts.refine.input.parser import RefineParser
from resume_roast.prompts.refine.input.state import RefineState

_TEMPERATURE = 0.5

_HELP = (
    "Available commands:\n"
    "  /replace <text>    Replace the bullet with a new version\n"
    "  /generate <notes>  Generate a candidate rewrite\n"
    "  /exit              End the session\n"
    "  /help              Show this message"
)


def refine(bullet: str) -> None:
    """Coach a single resume bullet through a back-and-forth chat.

    Supports ``/replace <new text>`` to commit a new version of the bullet,
    ``/generate <optional notes>`` to produce a candidate rewrite, and plain
    text for conversational coaching.
    """
    api_key = require_api_key()
    settings = SettingsStore(storage_dir()).load_or_create()

    client: LlmClient = NvidiaClient(api_key=api_key, model=settings.model)
    state = RefineState(RefineParser(), bullet)
    builder = RefinePromptBuilder(state)

    conversation = Conversation.start(client, builder.build_system(), temperature=_TEMPERATURE)

    console = Console(highlight=False)
    label = model_label(settings.model)

    # First turn — send the initial bullet
    console.print(f"{USER_PROMPT}{bullet}")
    stream_exchange(conversation, console, builder.build_first_message(), label, settings.model)

    run_chat_loop(conversation, console, state, builder, label, settings.model, _HELP)
