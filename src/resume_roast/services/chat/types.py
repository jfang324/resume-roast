"""Types for the chat command pipeline: parsed input, vocabulary, and outcomes."""

from collections.abc import Callable
from dataclasses import dataclass

from resume_roast.services.chat.enums import ArgPolicy

# ── Parsed input ─────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class Command:
    """A slash command: ``/name arg`` — ``arg`` is None when absent."""

    name: str
    arg: str | None = None


@dataclass(frozen=True)
class ChatText:
    """A plain conversational turn."""

    text: str


type UserInput = Command | ChatText


# ── Vocabulary ───────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class CommandSpec:
    """One feature command: how it behaves and how ``/help`` documents it.

    The spec is the single source of truth for a command — the executor
    validates against `policy` and generates the help line from `description`
    and `arg_hint`, so the vocabulary and its documentation cannot drift.
    """

    policy: ArgPolicy
    description: str
    arg_hint: str | None = None
    """Placeholder shown after the name in the help usage column, e.g. ``<text>``."""


# ── Outcomes ─────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class SendTurn:
    """Send *text* as the user turn; call *commit* once the exchange lands.

    *commit* carries the state change a successful send earns (e.g. adopting
    a replaced bullet); None when the command changes nothing.
    """

    text: str
    commit: Callable[[], None] | None = None


@dataclass(frozen=True)
class ShowHelp:
    """Print the feature's command help."""

    text: str


@dataclass(frozen=True)
class EndSession:
    """Leave the session loop."""


@dataclass(frozen=True)
class Invalid:
    """Unusable input — empty, unknown command, or missing required argument."""


type Outcome = SendTurn | ShowHelp | EndSession | Invalid
