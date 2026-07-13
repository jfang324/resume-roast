"""Renders a structured roast report with git-diff-style highlighting."""

from resume_roast.prompts.evaluate.schema import CategoryReview, Example, RoastReport

DIFF_REMOVAL_PREFIX = "  - "
DIFF_ADDITION_PREFIX = "  + "
"""Line prefixes marking diff hunks; the handler colors lines that start with these."""


def render_report(report: RoastReport) -> str:
    """Render `report` as a plain-text string with diff lines prefixed for ANSI coloring."""
    sections: list[str] = [
        _section("Overall Assessment", f"{report.overall}\n\nOverall: {report.overall_score}/10"),
        _section("What's Good", _bullets(report.strengths)),
        _section("What's Bad", _bullets(report.weaknesses)),
    ]
    sections.extend(
        _section(f"{name} — {review.score}/10", _category_body(review))
        for name, review in report.categories.items()
    )
    return "\n\n".join(sections)


def _category_body(review: CategoryReview) -> str:
    """Render a category's findings, then its suggestions when it has any."""
    if not review.suggestions:
        return review.findings
    recommendations = "\n\n".join(
        f"- {s.recommendation}{_examples_block(s.examples)}" for s in review.suggestions
    )
    return f"{review.findings}\n\nSuggestions:\n{recommendations}"


def _examples_block(examples: tuple[Example, ...]) -> str:
    """Render examples as indented diff hunks."""
    if not examples:
        return ""
    return "\n" + "\n".join(_example(e) for e in examples)


def _example(example: Example) -> str:
    """Render one example as a diff hunk, prefixing every line so multi-line
    quotes and rewrites color fully, not just their first line."""
    additions = _prefix_lines(example.rewrite, DIFF_ADDITION_PREFIX)
    if not example.quote:
        return additions
    return f"{_prefix_lines(example.quote, DIFF_REMOVAL_PREFIX)}\n{additions}"


def _prefix_lines(text: str, prefix: str) -> str:
    """Prefix every line of `text`, so each renders as its own diff line."""
    return "\n".join(f"{prefix}{line}" for line in text.splitlines())


def _section(title: str, body: str) -> str:
    """Render one section: a bracketed title, then its body."""
    return f"[{title}]\n{body}"


def _bullets(items: tuple[str, ...]) -> str:
    """Render one bullet line per item."""
    return "\n".join(f"- {item}" for item in items)
