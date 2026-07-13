"""Tests for the plain-text report rendering."""

from resume_roast.prompts.evaluate.output.rendering import render_report
from resume_roast.prompts.evaluate.output.schema import (
    CATEGORY_NAMES,
    CategoryReview,
    Example,
    RoastReport,
    Suggestion,
)


def _review(name: str, *, with_suggestion: bool) -> CategoryReview:
    suggestions = (
        (
            Suggestion(
                recommendation="Quantify your impact",
                examples=(
                    Example(quote="Used Python", rewrite="Built a Python ETL pipeline"),
                    Example(quote="Team player", rewrite="Led a team of [X] engineers"),
                ),
            ),
        )
        if with_suggestion
        else ()
    )
    return CategoryReview(score=5, findings=f"{name} needs work.", suggestions=suggestions)


def _report() -> RoastReport:
    return RoastReport(
        overall="A promising draft undermined by vague bullets.",
        overall_score=6,
        categories={
            name: _review(name, with_suggestion=name == "Content") for name in CATEGORY_NAMES
        },
        strengths=("Concise single page", "Strong verbs"),
        weaknesses=("No metrics anywhere",),
    )


def test_renders_underlined_plaintext_sections() -> None:
    rendered = render_report(_report())

    assert "[Overall Assessment]\n" in rendered
    assert "Overall: 6/10" in rendered
    assert "[Content — 5/10]\nContent needs work." in rendered
    assert "#" not in rendered  # no Markdown, no Rich markup


def test_renders_every_category_in_order() -> None:
    rendered = render_report(_report())

    positions = [rendered.index(f"[{name} — 5/10]") for name in CATEGORY_NAMES]
    assert positions == sorted(positions)


def test_renders_suggestions_under_their_category() -> None:
    rendered = render_report(_report())

    content_start = rendered.index("[Content — 5/10]")
    block = rendered[content_start:]
    assert "Content needs work." in block
    assert "Suggestions:\n- Quantify your impact" in block
    assert "  - Used Python\n  + Built a Python ETL pipeline" in block
    assert "  - Team player\n  + Led a team of [X] engineers" in block


def test_prefixes_every_line_of_a_multi_line_quote_and_rewrite() -> None:
    report = RoastReport(
        overall="x",
        overall_score=5,
        categories={
            name: CategoryReview(
                score=5,
                findings="Fine.",
                suggestions=(
                    Suggestion(
                        recommendation="Consolidate the skills section",
                        examples=(
                            Example(
                                quote="Languages: Python, Go\nTools: Git, Docker",
                                rewrite="Languages: Python, Go\nTools: Git, Docker, AWS",
                            ),
                        ),
                    ),
                )
                if name == "Content"
                else (),
            )
            for name in CATEGORY_NAMES
        },
        strengths=("x",),
        weaknesses=("x",),
    )

    rendered = render_report(report)

    # Both lines of the quote carry the removal prefix, both lines of the
    # rewrite the addition prefix — no line renders bare.
    assert "  - Languages: Python, Go\n  - Tools: Git, Docker\n" in rendered
    assert "  + Languages: Python, Go\n  + Tools: Git, Docker, AWS" in rendered


def test_renders_a_bare_recommendation_with_no_examples() -> None:
    report = RoastReport(
        overall="x",
        overall_score=8,
        categories={
            name: CategoryReview(
                score=8,
                findings="Fine.",
                suggestions=(
                    Suggestion(recommendation="Add a LinkedIn URL to the header", examples=()),
                )
                if name == "Polish"
                else (),
            )
            for name in CATEGORY_NAMES
        },
        strengths=("x",),
        weaknesses=("x",),
    )

    rendered = render_report(report)

    assert "Suggestions:\n- Add a LinkedIn URL to the header" in rendered
    # No dangling example indentation under a bare recommendation.
    assert "Add a LinkedIn URL to the header\n  " not in rendered


def test_renders_an_additive_example_without_a_quote() -> None:
    report = RoastReport(
        overall="x",
        overall_score=1,
        categories={
            name: CategoryReview(
                score=0,
                findings="Missing.",
                suggestions=(
                    Suggestion(
                        recommendation="Add an Education section",
                        examples=(Example(quote="", rewrite="BSc, [University], 2024"),),
                    ),
                )
                if name == "Clarity"
                else (),
            )
            for name in CATEGORY_NAMES
        },
        strengths=("x",),
        weaknesses=("x",),
    )

    rendered = render_report(report)

    assert "- Add an Education section\n  + BSc, [University], 2024" in rendered
    assert "  - BSc" not in rendered  # no removal line when there is no quote


def test_omits_the_suggestions_label_when_a_category_has_none() -> None:
    rendered = render_report(_report())

    clarity_start = rendered.index("[Clarity — 5/10]")
    polish_start = rendered.index("[Polish — 5/10]")
    block = rendered[clarity_start:polish_start]
    assert "Clarity needs work." in block
    assert "Suggestions:" not in block


def test_renders_good_and_bad_bullets_right_after_the_overall_assessment() -> None:
    rendered = render_report(_report())

    assert "[What's Good]\n- Concise single page\n- Strong verbs" in rendered
    assert "[What's Bad]\n- No metrics anywhere" in rendered
    assert (
        rendered.index("[Overall Assessment]")
        < rendered.index("[What's Good]")
        < rendered.index("[What's Bad]")
        < rendered.index("[Content — 5/10]")
    )
