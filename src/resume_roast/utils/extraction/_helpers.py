"""Shared helpers for document-format parsers."""


def none_when_blank(value: str | None) -> str | None:
    """Return None for missing or whitespace-only strings; pass through otherwise.

    Shared across every document parser because PDF and DOCX both store absent
    metadata values as empty strings.
    """
    if value is None or not value.strip():
        return None

    return value
