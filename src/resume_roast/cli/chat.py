"""Shared interactive chat loop for conversational subcommands (refine, generate-block).

Both chat features share the same shape: seed a `Conversation`, then read user
turns until exit, streaming each turn as an LLM exchange. The per-feature parts —
the welcome text, any opening turn, the command vocabulary — stay in the handler;
everything below is common.
"""

from typing import Protocol

from rich.console import Console

from resume_roast.cli.utils import stream_to_console
from resume_roast.integrations.conversation import Conversation
from resume_roast.integrations.errors import AuthenticationError, TransientError
from resume_roast.persistence.credentials.store import CredentialsStore
from resume_roast.persistence.paths import storage_dir

USER_PROMPT = "> "


class ChatState(Protocol):
    """Parses raw user input and commits a successfully-sent turn."""

    def parse(self, raw: str) -> tuple[str, ...] | None: ...

    def commit(self, parsed: tuple[str, ...]) -> None: ...


class TurnBuilder(Protocol):
    """Builds the user-turn text for a parsed command."""

    def build_turn_message(self, parsed: tuple[str, ...]) -> str: ...


def require_api_key() -> str:
    """Return the stored NVIDIA API key, or raise if none is configured."""
    credentials = CredentialsStore(storage_dir()).load()
    if credentials.nvidia_api_key is None:
        raise AuthenticationError(
            "No NVIDIA API key configured. Run: resume-roast config credentials"
        )
    return credentials.nvidia_api_key


def run_chat_loop(
    conversation: Conversation,
    console: Console,
    state: ChatState,
    builder: TurnBuilder,
    label: str,
    help_text: str,
) -> None:
    """Read user turns until exit, dispatching each to the LLM.

    Handles the shared command vocabulary — unrecognised input, ``/exit``, and
    ``/help`` — and streams every other turn as an LLM exchange. A turn is
    committed to *state* only once its exchange lands, so a failed turn leaves
    the session state and transcript untouched.
    """
    try:
        while True:
            raw = input(USER_PROMPT).strip()
            parsed = state.parse(raw)

            if parsed is None:
                console.print("(unrecognised command)", style="dim")
                continue
            if parsed[0] == "exit":
                break
            if parsed[0] == "help":
                console.print(help_text, style="dim")
                continue

            user_text = builder.build_turn_message(parsed)
            if stream_exchange(conversation, console, user_text, label):
                state.commit(parsed)  # only persist the turn once it lands
    except (EOFError, KeyboardInterrupt):
        console.print()


def stream_exchange(conversation: Conversation, console: Console, message: str, label: str) -> bool:
    """Stream one assistant reply to *message*.

    Returns ``True`` on success and ``False`` on a transient API error (reported
    so the user can retry the same turn against an unchanged conversation).
    Non-transient API errors — a rejected key, a malformed request — propagate to
    the command's error boundary, ending the session, since retrying won't help.
    """
    console.print(f"{label}{USER_PROMPT}", end="", style="bold")
    try:
        stream_to_console(conversation.send_stream(message), console)
    except TransientError as exc:
        console.print(f"\n{exc} — try again.", style="red")
        return False
    console.print()
    if conversation.last_finish_reason == "length":
        console.print("(reply cut off at the length limit)", style="dim")
    return True
