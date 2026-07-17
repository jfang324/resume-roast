"""Display helpers shared across subcommand groups."""

from collections.abc import Iterable, Mapping, Sequence

from rich.console import Console, RenderableType
from rich.live import Live
from rich.padding import Padding
from rich.spinner import Spinner
from rich.text import Text

from resume_roast.integrations.errors import AuthenticationError
from resume_roast.integrations.llm_client import LlmClient
from resume_roast.integrations.nvidia.client import NvidiaClient
from resume_roast.integrations.nvidia.pricing import estimate_cost
from resume_roast.integrations.types import Usage
from resume_roast.persistence.credentials.store import CredentialsStore
from resume_roast.persistence.paths import storage_dir
from resume_roast.persistence.settings.store import SettingsStore
from resume_roast.persistence.settings.types import Settings

NOT_SET = "(not set)"
"""Shown wherever an optional value has nothing saved."""

USER_PROMPT = "> "
"""Prompt prefix for interactive user input and echoed user turns."""


def build_client() -> tuple[LlmClient, Settings]:
    """Load credentials and settings and return a ready-to-use client pair."""
    credentials = CredentialsStore(storage_dir()).load()
    if credentials.nvidia_api_key is None:
        raise AuthenticationError(
            "No NVIDIA API key configured. Run: resume-roast config credentials"
        )
    settings = SettingsStore(storage_dir()).load_or_create()
    return NvidiaClient(api_key=credentials.nvidia_api_key, model=settings.model), settings


_MESSAGE_SECONDS = 5.0
"""How long each spinner message stays up before rotating to the next."""


def display_value(value: str | tuple[str, ...]) -> str:
    """Render a setting value for prompts and display."""
    return ", ".join(value) if isinstance(value, tuple) else value


def print_highlighted_lines(text: str, console: Console, styles: Mapping[str, str]) -> None:
    """Print `text`, filling the background of prefix-matched lines to full width.

    `styles` maps a line prefix to a Rich style; a line starting with a prefix
    is padded out to the terminal width so its background spans the whole row —
    and every wrapped row — where a bare style colors only the characters.
    Off a terminal the fill would only add trailing whitespace, so every line
    prints plain. `Text` (never markup) keeps bracketed titles intact.
    """
    for line in text.splitlines():
        style = next((s for prefix, s in styles.items() if line.startswith(prefix)), None)
        if style is not None and console.is_terminal:
            console.print(Padding(Text(line), (0, 0), style=style))
        else:
            console.print(Text(line), soft_wrap=True)


_MODEL_LABEL_MAX = 20


def model_label(model: str) -> str:
    name = model.rsplit("/", 1)[-1]
    if len(name) > _MODEL_LABEL_MAX:
        return f"{name[: _MODEL_LABEL_MAX - 1]}…"
    return name


def stream_to_console(chunks: Iterable[str], console: Console) -> None:
    for chunk in chunks:
        console.print(chunk, end="", markup=False, highlight=False, soft_wrap=True)


def summary_line(model: str, usage: Usage | None, latency_seconds: float) -> str:
    parts: list[str] = []
    if usage is not None:
        parts.append(f"{usage.prompt_tokens:,} input tokens")
        parts.append(f"{usage.completion_tokens:,} output tokens")
        cost = estimate_cost(usage, model)
        if cost is not None:
            parts.append(f"~${cost:.4f}")
    parts.append(f"{latency_seconds:.1f}s")
    return " · ".join(parts)


class RotatingSpinner(Spinner):
    """A spinner that cycles through its messages on a fixed cadence.

    ``Live``'s refresh thread re-renders continuously and passes the clock
    into ``render``; deriving the message from that clock is what lets it
    rotate while the caller sits blocked on a slow API call.
    """

    def __init__(self, name: str, messages: Sequence[Text], *, style: str) -> None:
        super().__init__(name, text=messages[0], style=style)
        self._messages = messages
        self._first_render_time: float | None = None

    def render(self, time: float) -> RenderableType:
        """Render the animation frame and message due at `time`."""
        if self._first_render_time is None:
            self._first_render_time = time
        elapsed = time - self._first_render_time
        self.text = self._messages[int(elapsed / _MESSAGE_SECONDS) % len(self._messages)]
        return super().render(time)


def spinner(message: str, *more: str) -> Live:
    """Return an animated status spinner to use as a context manager.

    Cycles through the given messages every few seconds, wrapping around.
    Drawn on stderr so stdout stays pipeable, and erased when the context
    exits; on non-terminal output nothing is drawn at all. Dimmed throughout
    to read as transient chrome, like the post-roast stats line.
    """
    texts = [Text(text, style="dim") for text in (message, *more)]
    rotating = RotatingSpinner("dots", texts, style="dim")
    return Live(rotating, console=Console(stderr=True), transient=True, refresh_per_second=12.5)
