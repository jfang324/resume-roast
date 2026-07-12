"""Shared errors raised by every document parser."""


class ExtractionError(Exception):
    """Base for all document extraction failures."""


class UnreadableDocumentError(ExtractionError):
    """A document file is missing, corrupt, or encrypted."""
