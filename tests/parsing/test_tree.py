"""Tests for resume_roast.parsing.tree addressing helpers."""

from __future__ import annotations

from collections.abc import Callable

import pytest

from resume_roast.parsing import Document, Line
from resume_roast.parsing.errors import UnknownNodeIdError
from resume_roast.parsing.tree import ancestors, find_node, node_path, walk

LineFactory = Callable[..., Line]


def test_walk_yields_nodes_in_preorder(doc: Document) -> None:
    assert [node.id for node in walk(doc)] == ["n1", "n2", "n3", "n4", "n5", "n6", "n7"]


def test_find_node_returns_node_by_id(doc: Document) -> None:
    third = list(walk(doc))[2]

    assert find_node(doc, "n3") is third


@pytest.mark.parametrize(
    ("node_id", "expected"),
    [
        ("n1", "doc"),
        ("n2", "sections[0]"),
        ("n3", "sections[0].entries[0]"),
        ("n4", "sections[0].entries[0].blocks[0]"),
    ],
)
def test_node_path_returns_bracketed_path(doc: Document, node_id: str, expected: str) -> None:
    assert node_path(doc, node_id) == expected


def test_ancestors_returns_chain_from_document(doc: Document) -> None:
    assert ancestors(doc, "n4") == (doc, doc.sections[0], doc.sections[0].entries[0])
    assert ancestors(doc, "n1") == ()


@pytest.mark.parametrize(
    "helper",
    [find_node, node_path, ancestors],
    ids=["find_node", "node_path", "ancestors"],
)
def test_helpers_raise_unknown_node_id(
    doc: Document, helper: Callable[[Document, str], object]
) -> None:
    with pytest.raises(UnknownNodeIdError, match="n999"):
        helper(doc, "n999")
