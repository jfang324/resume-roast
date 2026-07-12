"""Errors raised by API clients, split by what the user can do about them."""


class ApiError(Exception):
    """Base for all API failures."""


class AuthenticationError(ApiError):
    """The API key is missing or rejected; fixed by `resume-roast config credentials`."""


class TransientError(ApiError):
    """A rate limit, connection failure, or server error; fixed by trying again."""


class EmptyResponseError(ApiError):
    """The API returned a completion with no content."""


class TruncatedResponseError(ApiError):
    """The model hit the completion-token limit before finishing its response."""
