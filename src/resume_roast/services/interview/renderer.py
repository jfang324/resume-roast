"""Display port for interview sessions; the console implementation lives in the CLI layer."""

from collections.abc import Mapping
from contextlib import AbstractContextManager
from typing import Protocol

from resume_roast.integrations.types import Usage
from resume_roast.prompts.interview.output.schema import Verdict


class InterviewRenderer(Protocol):
    """Renders interview output; implementations own all display concerns."""

    def busy(self, message: str) -> AbstractContextManager[object]:
        """Return a context manager showing transient busy state around a blocking call."""
        ...

    def show_start(self, total_questions: int) -> None:
        """Announce the interview and how the candidate interacts with it."""
        ...

    def show_question(self, index: int, question: str) -> None:
        """Present base question number ``index`` (0-based) to the candidate."""
        ...

    def show_follow_up(self, question: str) -> None:
        """Present a follow-up question to the candidate."""
        ...

    def show_status(self, message: str, *, ok: bool) -> None:
        """Report a tool step's outcome as transient chrome."""
        ...

    def show_thought(self, thought: str) -> None:
        """Surface the model's reasoning; implementations may drop it."""
        ...

    def show_report(self, verdict: Verdict, scores: Mapping[str, float], max_per_comp: int) -> None:
        """Render the final interview report."""
        ...

    def show_metrics(self, usage: Usage, latency_seconds: float) -> None:
        """Print the metrics footprint of the whole session."""
        ...

    def show_interrupt(self) -> None:
        """Close the session's output after EOF or a keyboard interrupt."""
        ...

    def show_abort(self) -> None:
        """Report an interview that ended before any question was answered."""
        ...
