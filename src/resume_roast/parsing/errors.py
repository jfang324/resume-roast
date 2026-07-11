"""Shared errors for the resume parsing pipeline."""

from __future__ import annotations


class ParsingError(Exception):
    """Base for all resume-parsing failures."""


class InvalidPdfError(ParsingError):
    """The file cannot be opened as a readable PDF."""


class NoTextLayerError(ParsingError):
    """The PDF opened but contains no extractable text (likely a scan)."""


class UnsupportedLayoutError(ParsingError):
    """The PDF uses a layout the parser cannot order (multi-column)."""


class UnsupportedFormatError(ParsingError):
    """No extractor is registered for the file's extension."""


class UnknownNodeIdError(ParsingError):
    """A node id does not exist in the given document tree."""
