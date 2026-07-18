"""Refine's session entry point.

Mirrors `services/evaluate/service.py`: the CLI handler wires credentials and display,
`run()` owns the feature's orchestration — composing the command pipeline and
the generic `ChatSession` around refine's executor.
"""

from resume_roast.integrations.conversation import Conversation
from resume_roast.integrations.llm_client import LlmClient
from resume_roast.prompts.refine.builder import build_first_message, build_system
from resume_roast.services.chat.input_parser import InputParser
from resume_roast.services.chat.input_provider import InputProvider
from resume_roast.services.chat.renderer import ChatRenderer
from resume_roast.services.chat.session import ChatSession
from resume_roast.services.refine.constants import TEMPERATURE
from resume_roast.services.refine.executor import RefineCommandExecutor


def run(
    client: LlmClient, bullet: str, renderer: ChatRenderer, input_provider: InputProvider
) -> None:
    """Coach *bullet* through an interactive chat session rendered on *renderer*."""
    parser = InputParser()
    executor = RefineCommandExecutor(bullet)
    conversation = Conversation(client, build_system(), temperature=TEMPERATURE)
    session = ChatSession(conversation, parser, executor, renderer, input_provider)
    session.run(opening=build_first_message(bullet))
