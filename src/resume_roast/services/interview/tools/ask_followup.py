"""Ask-followup tool: present the interviewer's question and collect the answer.

The one tool backed by human I/O rather than an LLM program — stateless,
with the session's ports injected per call. Cap policy and /exit handling
stay with the FSM, as they do for every tool.
"""

from resume_roast.services.chat.input_provider import InputProvider
from resume_roast.services.interview.renderer import InterviewRenderer


def ask_followup(
    renderer: InterviewRenderer,
    input_provider: InputProvider,
    question: str,
) -> str:
    """Present *question* to the candidate and return their stripped answer."""
    renderer.show_follow_up(question)

    return input_provider.get_input().strip()
