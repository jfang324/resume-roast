"""Errors raised by API clients, split by what the user can do about them."""

from resume_roast.integrations.types import Usage


class ApiError(Exception):
    """Base for all API failures."""

    usage: Usage | None = None
    """Tokens billed before this failure, when a retry loop tracked them.

    ``structured_completion`` sets this before it gives up, so a caller that
    catches the error and falls back can still record the cost of the
    attempts that were made. None when nothing tracked usage.
    """


class AuthenticationError(ApiError):
    """The API key is missing or rejected; fixed by `resume-roast config credentials`."""


class TransientError(ApiError):
    """A rate limit, connection failure, or server error; fixed by trying again."""


class EmptyResponseError(ApiError):
    """The API returned a completion with no content."""


class MalformedResponseError(ApiError):
    """The response text does not satisfy the caller's expected structure.

    The message is written for the model, naming the offending field and the
    rule it broke — retry loops send it back verbatim as feedback.
    """


class TruncatedResponseError(ApiError):
    """The model hit the completion-token limit before finishing its response."""
