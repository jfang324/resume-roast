"""Tests for resume_roast.parsing.treeify.build_tree."""

from __future__ import annotations

from collections.abc import Callable

import pytest

from resume_roast.parsing import BBox, Bullet, Line, Paragraph
from resume_roast.parsing.treeify import BULLET_MARKERS, build_tree

LineFactory = Callable[..., Line]
SOURCE = "resume.pdf"


def test_build_tree_promotes_larger_font_lines_to_section_headings(
    make_line: LineFactory,
) -> None:
    lines = [
        make_line("Jordan Diaz", size=22.0, y0=60.0, y1=88.0),
        make_line("jordan@example.com", y0=92.0, y1=104.0),
        make_line("EXPERIENCE", size=14.0, bold=True, y0=150.0, y1=166.0),
        make_line("Built a parser", y0=170.0, y1=182.0),
    ]

    doc = build_tree(lines, source=SOURCE, page_count=1)

    assert [section.heading for section in doc.sections] == ["Jordan Diaz", "EXPERIENCE"]
    first_entry = doc.sections[0].entries[0]
    assert first_entry.heading is None
    assert first_entry.blocks[0].text == "jordan@example.com"


def test_build_tree_puts_leading_body_text_in_untitled_section(make_line: LineFactory) -> None:
    lines = [
        make_line("Objective: build great software.", y0=100.0, y1=112.0),
        make_line("EXPERIENCE", size=14.0, bold=True, y0=150.0, y1=166.0),
        make_line("Built a parser", y0=170.0, y1=182.0),
    ]

    doc = build_tree(lines, source=SOURCE, page_count=1)

    assert doc.sections[0].heading is None
    assert doc.sections[0].entries[0].blocks[0].text == "Objective: build great software."


def test_build_tree_starts_new_entry_on_large_gap_without_bold(make_line: LineFactory) -> None:
    lines = [
        make_line("EXPERIENCE", size=14.0, y0=100.0, y1=116.0),
        make_line("Engineer -- Acme", y0=120.0, y1=132.0),
        make_line("- Shipped it", y0=136.0, y1=148.0),
        make_line("Engineer -- Beta", y0=200.0, y1=212.0),
    ]

    doc = build_tree(lines, source=SOURCE, page_count=1)

    section = doc.sections[0]
    assert section.entries[0].heading is None
    assert section.entries[0].blocks[0].text == "Engineer -- Acme"
    assert section.entries[0].blocks[1].text == "Shipped it"
    assert section.entries[1].heading == "Engineer -- Beta"
    assert section.entries[1].blocks == ()


def test_build_tree_keeps_first_entry_in_section_untitled(make_line: LineFactory) -> None:
    lines = [
        make_line("EXPERIENCE", size=14.0, y0=100.0, y1=116.0),
        make_line("Some body text right after the heading.", y0=120.0, y1=132.0),
    ]

    doc = build_tree(lines, source=SOURCE, page_count=1)

    entry = doc.sections[0].entries[0]
    assert entry.heading is None
    assert entry.blocks[0].text == "Some body text right after the heading."


def test_build_tree_treats_bold_as_irrelevant_to_entry_detection(make_line: LineFactory) -> None:
    lines = [
        make_line("EXPERIENCE", size=14.0, bold=True, y0=100.0, y1=116.0),
        make_line("Engineer -- Acme", bold=True, y0=120.0, y1=132.0),
        make_line("- Shipped it", bold=True, y0=136.0, y1=148.0),
        make_line("Engineer -- Beta", bold=True, y0=200.0, y1=212.0),
    ]

    doc = build_tree(lines, source=SOURCE, page_count=1)

    section = doc.sections[0]
    assert section.entries[0].heading is None
    assert section.entries[0].blocks[0].text == "Engineer -- Acme"
    assert section.entries[0].blocks[1].text == "Shipped it"
    assert section.entries[1].heading == "Engineer -- Beta"
    assert section.entries[1].blocks == ()


@pytest.mark.parametrize("marker", BULLET_MARKERS)
def test_build_tree_strips_bullet_markers(make_line: LineFactory, marker: str) -> None:
    lines = [make_line(f"{marker} Did a thing")]

    doc = build_tree(lines, source=SOURCE, page_count=1)

    block = doc.sections[0].entries[0].blocks[0]
    assert isinstance(block, Bullet)
    assert block.marker == marker
    assert block.text == "Did a thing"


def test_build_tree_treats_zero_width_space_after_marker_as_bullet(
    make_line: LineFactory,
) -> None:
    lines = [make_line("●​ Led frontend development")]

    doc = build_tree(lines, source=SOURCE, page_count=1)

    block = doc.sections[0].entries[0].blocks[0]
    assert isinstance(block, Bullet)
    assert block.marker == "●"
    assert block.text == "Led frontend development"


def test_build_tree_merges_indented_bullet_continuation_lines(make_line: LineFactory) -> None:
    lines = [
        make_line("- Shipped the parser", x0=72.0, x1=250.0, y0=100.0, y1=112.0),
        make_line("and cut latency", x0=72.0, x1=220.0, y0=114.0, y1=126.0),
    ]

    doc = build_tree(lines, source=SOURCE, page_count=1)

    block = doc.sections[0].entries[0].blocks[0]
    assert isinstance(block, Bullet)
    assert block.text == "Shipped the parser and cut latency"
    assert block.bbox == BBox(x0=72.0, y0=100.0, x1=250.0, y1=126.0)


@pytest.mark.parametrize(
    ("first", "second", "expected"),
    [
        ("a devel-", "oper of things", "a developer of things"),
        ("uses state-of-the-", "art tooling", "uses state-of-the-art tooling"),
    ],
    ids=["syllable-hyphen-dropped", "compound-hyphen-kept"],
)
def test_build_tree_merges_adjacent_body_lines_and_dehyphenates(
    make_line: LineFactory, first: str, second: str, expected: str
) -> None:
    lines = [
        make_line(first, y0=100.0, y1=112.0),
        make_line(second, y0=114.0, y1=126.0),
    ]

    doc = build_tree(lines, source=SOURCE, page_count=1)

    block = doc.sections[0].entries[0].blocks[0]
    assert isinstance(block, Paragraph)
    assert block.text == expected


def test_build_tree_starts_new_entry_instead_of_splitting_paragraph_on_large_gap(
    make_line: LineFactory,
) -> None:
    lines = [
        make_line("First paragraph line.", y0=100.0, y1=112.0),
        make_line("Second paragraph line.", y0=140.0, y1=152.0),
    ]

    doc = build_tree(lines, source=SOURCE, page_count=1)

    entries = doc.sections[0].entries
    assert entries[0].heading is None
    assert entries[0].blocks[0].text == "First paragraph line."
    assert entries[1].heading == "Second paragraph line."
    assert entries[1].blocks == ()


def test_build_tree_assigns_preorder_node_ids(make_line: LineFactory) -> None:
    lines = [
        make_line("SECTION A", size=14.0, bold=True, y0=100.0, y1=116.0),
        make_line("Body under A.", y0=120.0, y1=132.0),
        make_line("SECTION B", size=14.0, bold=True, y0=160.0, y1=176.0),
        make_line("Body under B.", y0=180.0, y1=192.0),
    ]

    doc = build_tree(lines, source=SOURCE, page_count=1)

    assert doc.id == "n1"
    assert doc.sections[0].id == "n2"
    assert doc.sections[0].entries[0].id == "n3"
    assert doc.sections[0].entries[0].blocks[0].id == "n4"
    assert doc.sections[1].id == "n5"
    assert doc.sections[1].entries[0].id == "n6"
    assert doc.sections[1].entries[0].blocks[0].id == "n7"


def test_build_tree_records_style_and_provenance_on_nodes(make_line: LineFactory) -> None:
    heading = make_line(
        "EXPERIENCE", size=14.0, bold=True, x0=72.0, x1=180.0, y0=100.0, y1=116.0, page=2
    )
    first = make_line("Shipped the parser", x0=90.0, x1=200.0, y0=120.0, y1=132.0, page=2)
    second = make_line("with better latency", x0=72.0, x1=250.0, y0=134.0, y1=146.0, page=2)
    lines = [heading, first, second]

    doc = build_tree(lines, source=SOURCE, page_count=2)

    section = doc.sections[0]
    assert section.style == heading.style
    assert section.bbox == heading.bbox
    assert section.page == 2

    block = section.entries[0].blocks[0]
    assert block.style == first.style
    assert block.bbox == BBox(x0=72.0, y0=120.0, x1=250.0, y1=146.0)
    assert block.page == 2


def test_build_tree_returns_empty_document_for_no_lines() -> None:
    doc = build_tree([], source=SOURCE, page_count=1)

    assert doc.sections == ()
    assert doc.id == "n1"
