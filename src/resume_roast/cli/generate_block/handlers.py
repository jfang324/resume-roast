"""`generate-block` command: bare handler function, wired by the registry."""

import time

from rich.console import Console

from resume_roast.cli.utils import model_label, stream_to_console, summary_line
from resume_roast.integrations.conversation import Conversation
from resume_roast.integrations.errors import ApiError, AuthenticationError
from resume_roast.integrations.llm_client import LlmClient
from resume_roast.integrations.nvidia.client import NvidiaClient
from resume_roast.persistence.credentials.store import CredentialsStore
from resume_roast.persistence.paths import storage_dir
from resume_roast.persistence.settings.store import SettingsStore
from resume_roast.prompts.generate_block.builder import GenerateBlockPromptBuilder
from resume_roast.prompts.generate_block.input.parser import GenerateBlockParser
from resume_roast.prompts.generate_block.input.state import GenerateBlockState

_TEMPERATURE = 0.5
_USER_PROMPT = "> "


def generate_block() -> None:
    """Interview the user about a role or project, then generate a resume block.

    Supports ``/generate <optional notes>`` to produce a resume block and
    plain text for conversational information gathering.
    """
    api_key = _require_api_key()
    settings = SettingsStore(storage_dir()).load_or_create()

    client: LlmClient = NvidiaClient(api_key=api_key, model=settings.model)
    parser = GenerateBlockParser()
    state = GenerateBlockState(parser)
    builder = GenerateBlockPromptBuilder(state)

    conversation = Conversation.start(client, builder.build_system(), temperature=_TEMPERATURE)

    console = Console(highlight=False)
    started = time.perf_counter()
    label = model_label(settings.model)

    console.print(
        "Tell me about a role or project you've worked on. I'll ask questions to gather "
        "details, then generate a resume block when you type /generate.\n"
        "Type /help to see available commands."
    )

    try:
        while True:
            raw = input(_USER_PROMPT).strip()
            parsed = state.parse(raw)

            if parsed is None:
                console.print("(unrecognised command)", style="dim")
                continue
            if parsed[0] == "exit":
                break
            if parsed[0] == "help":
                console.print(
                    "Available commands:\n"
                    "  /generate <notes>  Generate a resume block\n"
                    "  /exit              End the session\n"
                    "  /help              Show this message\n"
                    "\n"
                    "Or just type naturally and I'll ask questions.",
                    style="dim",
                )
                continue

            user_text = builder.build_turn_message(parsed)
            if _stream_exchange(conversation, console, user_text, label):
                state.commit(parsed)
    except (EOFError, KeyboardInterrupt):
        console.print()

    elapsed_seconds = time.perf_counter() - started
    console.print(
        summary_line(settings.model, conversation.total_usage, elapsed_seconds), style="dim"
    )


def _stream_exchange(
    conversation: Conversation, console: Console, message: str, label: str
) -> bool:
    """Stream one assistant reply to *message*.

    Returns ``True`` on success, ``False`` on a transient API error
    (which is reported to the user so they can retry).
    """
    console.print(f"{label}{_USER_PROMPT}", end="", style="bold")
    try:
        stream_to_console(conversation.send_stream(message), console)
    except ApiError as exc:
        console.print(f"\n{exc} — try again.", style="red")
        return False
    console.print()
    if conversation.last_finish_reason == "length":
        console.print("(reply cut off at the length limit)", style="dim")
    return True


def _require_api_key() -> str:
    credentials = CredentialsStore(storage_dir()).load()
    if credentials.nvidia_api_key is None:
        raise AuthenticationError(
            "No NVIDIA API key configured. Run: resume-roast config credentials"
        )
    return credentials.nvidia_api_key
