"""Tests for the evaluate prompt builder."""

import pytest

from resume_roast.persistence.settings.types import LEVELS, PERSONAS
from resume_roast.prompts.evaluate import build_evaluate_prompt
from resume_roast.prompts.levels import LEVEL_CONTEXT
from resume_roast.prompts.personas import PERSONA_PROMPTS
from resume_roast.prompts.types import Prompt
from resume_roast.utils.extraction.types import DocumentMetadata, PageMetadata, ParsedResume

_MARKDOWN = "# Jane Doe\n\n## Experience\n\n- Roasted resumes at Acme Corp"


def _parsed(markdown: str = _MARKDOWN) -> ParsedResume:
    page = PageMetadata(
        width=100.0,
        height=100.0,
        word_count=20,
        text_blocks=((0.0, 0.0, 50.0, 50.0),),
        image_count=1,
    )
    metadata = DocumentMetadata(
        page_count=1,
        creator=None,
        producer=None,
        created=None,
        modified=None,
        links=("https://github.com/janedoe",),
        pages=(page,),
    )
    return ParsedResume(markdown=markdown, metadata=metadata)


@pytest.fixture
def prompt() -> Prompt:
    return build_evaluate_prompt(_parsed(), persona="recruiter", level="mid")


def test_system_contains_selected_persona_and_level(prompt: Prompt) -> None:
    assert PERSONA_PROMPTS["recruiter"].prompt in prompt.system
    assert LEVEL_CONTEXT["mid"] in prompt.system


def test_system_contains_rubric_and_format_sections(prompt: Prompt) -> None:
    for heading in ("## Score Bands", "## Bullet Writing Principles", "## Output Format"):
        assert heading in prompt.system


def test_system_forbids_fabricated_rewrites(prompt: Prompt) -> None:
    assert "never invent metrics, technologies, or claims" in prompt.system


def test_resume_goes_delimited_into_user_not_system(prompt: Prompt) -> None:
    assert prompt.user is not None
    assert f"<resume>\n{_MARKDOWN}\n</resume>" in prompt.user
    assert _MARKDOWN not in prompt.system


def test_user_contains_document_statistics(prompt: Prompt) -> None:
    assert prompt.user is not None
    assert "- Pages: 1" in prompt.user
    assert "- Average words per page: 20" in prompt.user
    assert "- Text coverage: 25% of page area" in prompt.user
    assert "- Images: 1" in prompt.user
    assert "- Links: https://github.com/janedoe" in prompt.user


def test_every_settings_combination_builds() -> None:
    for persona in PERSONAS:
        for level in LEVELS:
            built = build_evaluate_prompt(_parsed(), persona=persona, level=level)
            assert PERSONA_PROMPTS[persona].label in built.system
