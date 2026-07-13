"""Summing token usage across the attempts of a single request."""

from collections.abc import Sequence

from resume_roast.integrations.types import Usage


def total_usage(usages: Sequence[Usage]) -> Usage | None:
    """Sum token counts across attempts, or None when no attempt reported any."""
    if not usages:
        return None
    return Usage(
        prompt_tokens=sum(usage.prompt_tokens for usage in usages),
        completion_tokens=sum(usage.completion_tokens for usage in usages),
        total_tokens=sum(usage.total_tokens for usage in usages),
    )
