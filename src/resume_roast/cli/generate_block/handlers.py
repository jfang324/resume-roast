"""`generate-block` command: bare handler function, wired by the registry."""

import time

from rich.console import Console

from resume_roast.cli.chat import require_api_key, run_chat_loop
from resume_roast.cli.utils import model_label, summary_line
from resume_roast.integrations.conversation import Conversation
from resume_roast.integrations.llm_client import LlmClient
from resume_roast.integrations.nvidia.client import NvidiaClient
from resume_roast.persistence.paths import storage_dir
from resume_roast.persistence.settings.store import SettingsStore
from resume_roast.prompts.generate_block.builder import GenerateBlockPromptBuilder
from resume_roast.prompts.generate_block.input.parser import GenerateBlockParser
from resume_roast.prompts.generate_block.input.state import GenerateBlockState

_TEMPERATURE = 0.5

_WELCOME = (
    "Tell me about a role or project you've worked on. I'll ask questions to gather "
    "details, then generate a resume block when you type /generate.\n"
    "Type /help to see available commands."
)

_HELP = (
    "Available commands:\n"
    "  /generate <notes>  Generate a resume block\n"
    "  /exit              End the session\n"
    "  /help              Show this message\n"
    "\n"
    "Or just type naturally and I'll ask questions."
)


def generate_block() -> None:
    """Interview the user about a role or project, then generate a resume block.

    Supports ``/generate <optional notes>`` to produce a resume block and
    plain text for conversational information gathering.
    """
    api_key = require_api_key()
    settings = SettingsStore(storage_dir()).load_or_create()

    client: LlmClient = NvidiaClient(api_key=api_key, model=settings.model)
    state = GenerateBlockState(GenerateBlockParser())
    builder = GenerateBlockPromptBuilder()

    conversation = Conversation.start(client, builder.build_system(), temperature=_TEMPERATURE)

    console = Console(highlight=False)
    started = time.perf_counter()
    label = model_label(settings.model)

    console.print(_WELCOME)

    run_chat_loop(conversation, console, state, builder, label, _HELP)

    elapsed_seconds = time.perf_counter() - started
    console.print(
        summary_line(settings.model, conversation.total_usage, elapsed_seconds), style="dim"
    )
