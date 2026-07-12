"""Errors raised by the NVIDIA client, split by what the user can do about them."""


class NvidiaError(Exception):
    """Base for all NVIDIA API failures."""


class AuthenticationError(NvidiaError):
    """The API key is missing or rejected; fixed by `resume-roast config credentials`."""


class TransientError(NvidiaError):
    """A rate limit, connection failure, or server error; fixed by trying again."""


class EmptyResponseError(NvidiaError):
    """The API returned a completion with no content."""


class TruncatedResponseError(NvidiaError):
    """The model hit the completion-token limit before finishing its response."""
