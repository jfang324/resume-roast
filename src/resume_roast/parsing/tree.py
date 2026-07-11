"""Read-only addressing helpers over a built Document tree."""

from __future__ import annotations

from collections.abc import Iterator

from resume_roast.parsing.errors import UnknownNodeIdError
from resume_roast.parsing.models import Document, Node


def _traverse(document: Document) -> Iterator[tuple[Node, str, tuple[Node, ...]]]:
    yield document, "doc", ()
    for si, section in enumerate(document.sections):
        section_path = f"sections[{si}]"
        yield section, section_path, (document,)
        for ei, entry in enumerate(section.entries):
            entry_path = f"{section_path}.entries[{ei}]"
            yield entry, entry_path, (document, section)
            for bi, block in enumerate(entry.blocks):
                block_path = f"{entry_path}.blocks[{bi}]"
                yield block, block_path, (document, section, entry)


def walk(document: Document) -> Iterator[Node]:
    """Yield every node in the tree, pre-order."""
    for node, _, _ in _traverse(document):
        yield node


def _find(document: Document, node_id: str) -> tuple[Node, str, tuple[Node, ...]]:
    for node, path, ancestor_chain in _traverse(document):
        if node.id == node_id:
            return node, path, ancestor_chain
    raise UnknownNodeIdError(f"no node with id {node_id!r}")


def find_node(document: Document, node_id: str) -> Node:
    """Return the node with the given id."""
    node, _, _ = _find(document, node_id)
    return node


def node_path(document: Document, node_id: str) -> str:
    """Return the bracketed positional path to the node with the given id."""
    _, path, _ = _find(document, node_id)
    return path


def ancestors(document: Document, node_id: str) -> tuple[Node, ...]:
    """Return the chain of containing nodes from the document to the node's parent."""
    _, _, ancestor_chain = _find(document, node_id)
    return ancestor_chain
