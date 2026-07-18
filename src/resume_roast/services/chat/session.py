"""The interactive session loop for conversational subcommands.

`ChatSession` owns the input loop and orchestrates the command pipeline —
lexing via `InputParser`, semantics via a feature's `CommandExecutor` — and
the `Conversation`. All I/O goes through ports: display via `ChatRenderer`,
input via `InputProvider`.
"""

import time
from enum import Enum

from resume_roast.integrations.conversation import Conversation
from resume_roast.integrations.errors import TransientError
from resume_roast.services.chat.command_executor import CommandExecutor
from resume_roast.services.chat.input_parser import InputParser
from resume_roast.services.chat.input_provider import InputProvider
from resume_roast.services.chat.renderer import ChatRenderer
from resume_roast.services.chat.types import EndSession, Invalid, SendTurn, ShowHelp


class ChatSession[C: Enum]:
    """One interactive chat session, driven turn by turn until exit.

    Reads user turns, routes them through the parser and the feature's
    executor, and acts on the outcome — streaming `SendTurn` text as an LLM
    exchange. A turn's commit closure runs only once its exchange lands, so
    a failed turn leaves the feature state and transcript untouched.

    Parameters
    ----------
    conversation
        The running conversation every turn is sent through.
    parser
        Lexes raw input into commands and chat text.
    executor
        The feature's command semantics: vocabulary, help, turn building.
    renderer
        Where replies and session chrome are rendered.
    input_provider
        Where user turns are read from.
    """

    def __init__(
        self,
        conversation: Conversation,
        parser: InputParser,
        executor: CommandExecutor[C],
        renderer: ChatRenderer,
        input_provider: InputProvider,
    ) -> None:
        self._conversation = conversation
        self._parser = parser
        self._executor = executor
        self._renderer = renderer
        self._input = input_provider

    def run(self, opening: str | None = None) -> None:
        """Drive the session: an optional opening turn, then read turns until exit.

        Non-transient API errors — a rejected key, a malformed request —
        propagate to the command's error boundary, ending the session, since
        retrying won't help.
        """
        try:
            if opening is not None:
                self._exchange(opening)

            while True:
                raw = self._input.get_input().strip()

                match self._executor.execute(self._parser.parse(raw)):
                    case Invalid():
                        self._renderer.show_usage_hint()

                    case EndSession():
                        break

                    case ShowHelp(text):
                        self._renderer.show_help(text)

                    case SendTurn(text, commit):
                        if self._exchange(text) and commit is not None:
                            commit()  # only persist the turn once it lands

        except (EOFError, KeyboardInterrupt):
            self._renderer.show_interrupt()

    def _exchange(self, message: str) -> bool:
        """Stream one assistant reply to *message*, then report its metrics.

        Returns ``True`` on success and ``False`` on a transient API error
        (reported so the user can retry the same turn against an unchanged
        conversation).
        """
        started = time.perf_counter()
        try:
            reply = self._conversation.send_stream(message)
            self._renderer.show_reply(reply)

        except TransientError as exc:
            self._renderer.show_transient_error(exc)

            return False

        if not reply.exhausted:
            # A renderer that stops early would silently lose the assistant
            # turn — fail loudly instead, this is a programming error.
            msg = "ChatRenderer.show_reply must drain the reply stream to exhaustion."
            raise RuntimeError(msg)

        self._renderer.show_metrics(
            reply.usage,
            reply.finish_reason,
            time.perf_counter() - started,
        )

        return True
