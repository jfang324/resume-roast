"""Rich-console implementation of the interview service's renderer protocol."""

from collections.abc import Mapping
from contextlib import AbstractContextManager

from rich.console import Console

from resume_roast.cli.utils import spinner, summary_line
from resume_roast.integrations.types import Usage
from resume_roast.prompts.interview.competencies import COMPETENCIES
from resume_roast.prompts.interview.output.schema import Verdict

_VERDICT_COLORS = {"hire": "green", "maybe": "yellow", "dont_hire": "red"}

_SCORE_BAR_WIDTH = 50


class ConsoleInterviewRenderer:
    """Renders interview session output to a rich console.

    Parameters
    ----------
    console
        Destination for all output.
    model
        Full model id, for the session metrics line.
    debug
        When False, the model's thoughts are dropped instead of shown.
    """

    def __init__(self, console: Console, model: str, *, debug: bool) -> None:
        self._console = console
        self._model = model
        self._debug = debug

    def busy(self, message: str) -> AbstractContextManager[object]:
        """Show the animated spinner while a blocking call runs."""
        return spinner(message)

    def show_start(self, total_questions: int) -> None:
        """Announce the interview and how the candidate interacts with it."""
        self._console.print(
            f"\n[bold]Interview started — {total_questions} questions planned[/bold]"
        )
        self._console.print("Type your answers when prompted. Enter /exit to end early.\n")

    def show_question(self, index: int, question: str) -> None:
        """Present base question number ``index`` (0-based) to the candidate."""
        self._console.print(f"\n[bold]Q{index + 1}:[/bold] {question}")

    def show_follow_up(self, question: str) -> None:
        """Present a follow-up question to the candidate."""
        self._console.print(f"\n{question}")

    def show_status(self, message: str, *, ok: bool) -> None:
        """Report a tool step's outcome as transient chrome."""
        mark = "✓" if ok else "✗"
        self._console.print(f"[dim]{mark} {message}[/dim]")

    def show_thought(self, thought: str) -> None:
        """Surface the model's reasoning in debug runs; drop it otherwise."""
        if self._debug:
            self._console.print(f"[dim]thought: {thought}[/dim]")

    def show_report(self, verdict: Verdict, scores: Mapping[str, float], max_per_comp: int) -> None:
        """Render the final interview report."""
        self._console.rule("\nINTERVIEW REPORT")
        self._console.print()

        for c in COMPETENCIES:
            score = scores.get(c.id, 0)
            filled = int(_SCORE_BAR_WIDTH * score / max_per_comp) if max_per_comp > 0 else 0
            bar = "█" * filled + "░" * (_SCORE_BAR_WIDTH - filled)
            self._console.print(f"{c.label:30} {score:<4}/{max_per_comp:<2}  {bar}")

        self._console.print()
        color = _VERDICT_COLORS.get(verdict.verdict, "white")
        self._console.print(f"Overall Rating: [bold]{verdict.overall_rating:.1f}/10[/bold]")
        self._console.print(f"Verdict: [bold {color}]{verdict.verdict.upper()}[/bold {color}]")
        self._console.print()

        if verdict.strengths:
            self._console.print("[bold green]Strengths:[/bold green]")
            for s in verdict.strengths:
                self._console.print(f"  + {s}")

        if verdict.growth_areas:
            self._console.print()
            self._console.print("[bold yellow]Growth Areas:[/bold yellow]")
            for g in verdict.growth_areas:
                self._console.print(f"  - {g}")

        self._console.print()
        self._console.print(verdict.summary)

    def show_metrics(self, usage: Usage, latency_seconds: float) -> None:
        """Print the metrics footprint of the whole session."""
        self._console.print(
            summary_line(self._model, usage, latency_seconds),
            style="dim",
        )

    def show_interrupt(self) -> None:
        """Close the session's output after EOF or a keyboard interrupt."""
        self._console.print()

    def show_abort(self) -> None:
        """Report an interview that ended before any question was answered."""
        self._console.print("Interview aborted before any questions were answered.")
