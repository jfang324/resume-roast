"""`refine` command: bare handler function, wired by the registry."""

import time

from rich.console import Console

from resume_roast.cli.utils import model_label, stream_to_console, summary_line
from resume_roast.integrations.conversation import Conversation
from resume_roast.integrations.errors import ApiError, AuthenticationError
from resume_roast.integrations.llm_client import LlmClient
from resume_roast.integrations.nvidia.client import NvidiaClient
from resume_roast.integrations.types import Message
from resume_roast.persistence.credentials.store import CredentialsStore
from resume_roast.persistence.paths import storage_dir
from resume_roast.persistence.settings.store import SettingsStore
from resume_roast.prompts.refine.builder import RefinePromptBuilder
from resume_roast.prompts.refine.input.parser import RefineParser
from resume_roast.prompts.refine.input.state import RefineState

_TEMPERATURE = 0.5
_USER_PROMPT = "> "


def refine(bullet: str) -> None:
    """Coach a single resume bullet through a back-and-forth chat.

    Supports ``/replace <new text>`` to commit a new version of the bullet,
    ``/generate <optional notes>`` to produce a candidate rewrite, and plain
    text for conversational coaching.
    """
    api_key = _require_api_key()
    settings = SettingsStore(storage_dir()).load_or_create()

    client: LlmClient = NvidiaClient(api_key=api_key, model=settings.model)
    parser = RefineParser()
    state = RefineState(parser, bullet)
    builder = RefinePromptBuilder(state)

    conversation = Conversation.start(client, builder.build_system(), temperature=_TEMPERATURE)
    conversation.messages.append(Message(role="system", content=builder.build_initial_block()))

    console = Console(highlight=False)
    started = time.perf_counter()
    label = model_label(settings.model)

    # First turn — send the initial bullet
    console.print(f"{_USER_PROMPT}{bullet}")
    _stream_exchange(conversation, console, bullet, label)

    # Subsequent turns
    try:
        while True:
            raw = input(_USER_PROMPT).strip()
            parsed = state.parse(raw)

            if parsed is None:
                console.print("(unrecognised command)", style="dim")
                continue
            if parsed[0] == "exit":
                break

            cmd = parsed[0]
            block = builder.build_turn_block(parsed)
            conversation.messages.append(Message(role="system", content=block))

            if cmd == "replace":
                user_text = "I've updated my bullet."
            elif cmd == "generate":
                user_text = "Generate a candidate."
            else:
                user_text = parsed[1] if len(parsed) > 1 else raw

            if not _stream_exchange(conversation, console, user_text, label):
                conversation.messages.pop()  # roll back the system block
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
