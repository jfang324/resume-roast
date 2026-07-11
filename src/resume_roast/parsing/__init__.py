"""Resume parsing pipeline: PDF -> addressable Document tree."""

from resume_roast.parsing.errors import (
    InvalidPdfError,
    NoTextLayerError,
    ParsingError,
    UnknownNodeIdError,
    UnsupportedFormatError,
    UnsupportedLayoutError,
)
from resume_roast.parsing.models import (
    BBox,
    Block,
    Bullet,
    Document,
    Entry,
    Extraction,
    Extractor,
    Line,
    Node,
    Paragraph,
    Section,
    Style,
)
from resume_roast.parsing.pdf import PyMuPdfExtractor
from resume_roast.parsing.pipeline import EXTRACTORS, extract_resume, parse_resume
from resume_roast.parsing.render import render_tree
from resume_roast.parsing.tree import ancestors, find_node, node_path, walk

__all__ = [
    "EXTRACTORS",
    "BBox",
    "Block",
    "Bullet",
    "Document",
    "Entry",
    "Extraction",
    "Extractor",
    "InvalidPdfError",
    "Line",
    "NoTextLayerError",
    "Node",
    "Paragraph",
    "ParsingError",
    "PyMuPdfExtractor",
    "Section",
    "Style",
    "UnknownNodeIdError",
    "UnsupportedFormatError",
    "UnsupportedLayoutError",
    "ancestors",
    "extract_resume",
    "find_node",
    "node_path",
    "parse_resume",
    "render_tree",
    "walk",
]
