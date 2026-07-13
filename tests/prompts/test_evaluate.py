"""Tests for the evaluate prompt builder."""

import pytest

from resume_roast.persistence.settings.types import LEVELS, PERSONAS
from resume_roast.prompts.evaluate.builder import build_evaluate_prompt
from resume_roast.prompts.evaluate.output.schema import CATEGORY_NAMES
from resume_roast.prompts.system_prompt import LEVEL_CONTEXT, PERSONA_PROMPTS
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
    unwrapped = " ".join(prompt.system.split())
    assert "Never invent metrics, technologies, or claims" in unwrapped


def test_system_calibrates_document_statistics(prompt: Prompt) -> None:
    unwrapped = " ".join(prompt.system.split())
    assert "400-700 words" in unwrapped


def test_system_warns_about_extraction_artifacts(prompt: Prompt) -> None:
    unwrapped = " ".join(prompt.system.split())
    assert "The Markdown extraction preserves" in unwrapped
    assert "Never report a section as missing" in unwrapped


def test_system_covers_chronology(prompt: Prompt) -> None:
    unwrapped = " ".join(prompt.system.split())
    assert "employment gaps" in unwrapped


def test_system_puts_competence_above_categories(prompt: Prompt) -> None:
    unwrapped = " ".join(prompt.system.split())
    assert "convey competence" in unwrapped
    assert "never an average of category scores" in unwrapped
    assert "Categories are not equally weighted" in unwrapped


def test_system_frames_guidance_as_judgment_not_checklist(prompt: Prompt) -> None:
    unwrapped = " ".join(prompt.system.split())
    assert "not a checklist" in unwrapped
    assert "rules of thumb" in unwrapped


def test_system_locks_output_to_json(prompt: Prompt) -> None:
    unwrapped = " ".join(prompt.system.split())
    assert "one raw JSON object" in unwrapped
    assert "a 100-point scale is never used" in unwrapped
    assert '"overall_score": <n>' in prompt.system
    for name in CATEGORY_NAMES:
        assert f'"{name}": {{"score": <n>, "findings":' in prompt.system
    assert '"suggestions"' in prompt.system


def test_user_message_closes_with_the_output_contract(prompt: Prompt) -> None:
    assert prompt.user is not None
    unwrapped = " ".join(prompt.user.split())
    assert unwrapped.endswith("in the Output Format section — nothing else.")
    assert "single raw JSON object" in unwrapped
    # The task restatement comes after the resume and statistics, not before.
    assert prompt.user.index("<resume>") < prompt.user.index("Respond with the single raw JSON")


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
