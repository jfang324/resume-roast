"""Session constants for the interview service."""

from resume_roast.services.interview.types import Limits

LIMITS = Limits()
"""The FSM's runaway-loop bounds; see `Limits` for the rationale per bound."""

MAX_SCORE_PER_QUESTION: int = 10
"""Top score one competency can earn from a single answered question — the
evaluate tool's 1-10 scale. Progress caps and the verdict's normalized
per-question scores both derive from it."""

PLANNING_TEMPERATURE: float = 0.7
"""Question planning samples freely — varied, resume-specific questions."""

TURN_TEMPERATURE: float = 0.0
"""Every other turn decodes greedily: tool calls and verdicts should be repeatable."""
