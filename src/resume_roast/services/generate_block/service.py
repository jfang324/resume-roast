"""Generate-block's session entry point.

Mirrors `services/refine/service.py`: the CLI handler wires credentials and
display, `run()` owns the feature's orchestration.
"""

from resume_roast.integrations.conversation import Conversation
from resume_roast.integrations.llm_client import LlmClient
from resume_roast.prompts.generate_block.builder import build_system
from resume_roast.services.chat.input_parser import InputParser
from resume_roast.services.chat.input_provider import InputProvider
from resume_roast.services.chat.renderer import ChatRenderer
from resume_roast.services.chat.session import ChatSession
from resume_roast.services.generate_block.constants import TEMPERATURE
from resume_roast.services.generate_block.executor import GenerateBlockCommandExecutor


def run(client: LlmClient, renderer: ChatRenderer, input_provider: InputProvider) -> None:
    """Interview the user about a role, generating a resume block on ``/generate``."""
    parser = InputParser()
    executor = GenerateBlockCommandExecutor()
    conversation = Conversation(client, build_system(), temperature=TEMPERATURE)
    session = ChatSession(conversation, parser, executor, renderer, input_provider)
    session.run()
