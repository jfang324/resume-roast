# SPEC-006: PDF Parsing Pipeline (`evaluate`)

---
**Status**: pending
**Created**: 2026-07-10
**TDD**: required
**Coverage target**: repo default (`fail_under = 85` in `pyproject.toml`)
**Commit(s)**: <!-- Populated on completion. One `- hash (description)` per commit. -->

## Summary

`resume-roast` has nothing that can read a resume yet. This spec adds the
first stage of the parsing pipeline: a new `parsing/` domain that turns a
**single-column, born-digital PDF** into an immutable, addressable tree —
`Document → Section → Entry → (Paragraph | Bullet)` — where every node
carries the style and geometry metadata (font, size, bold/italic, bounding
box, page) needed by later specs for formatting-preserving re-rendering, and
every node carries a **stable opaque ID** plus a derivable **positional
path** so the future TUI can display the tree and address individual nodes
for editing. The pipeline is two pure stages behind one facade:
an `Extractor` protocol implementation turns the file into styled `Line`s —
PyMuPDF's `PyMuPdfExtractor` is the only registered one, keeping the
extraction library swappable behind the protocol — and `treeify.py`
builds the tree from those lines using style and whitespace heuristics
(largest style cluster = body text; larger-font lines = section headings;
a line preceded by more than a line-break's worth of vertical whitespace =
an entry heading, regardless of its own style; marker-prefixed lines =
bullets) — no hardcoded section-name dictionaries. Real resumes routinely
have no stylistic distinction between a job title and body text, so
entries are detected from surrounding whitespace rather than boldness.
Unsupported inputs fail **loudly** with
typed errors — multi-column layouts, PDFs with no text layer (scans), and
unopenable/password-protected files are rejected with a clear message, never
parsed into silently-wrong output. Nothing is persisted: the tree is an
in-memory value. The user-visible surface is one new root-level CLI
command, `resume-roast evaluate <path>`, which parses the resume and prints
the tree with node IDs — the manual verification surface for the parser, a
preview of the TUI's tree view, and the command a later spec extends with
the AI evaluation results.

### Existing Code

- `src/resume_roast/cli/runner.py` — wires group Typer instances via
  `cli.add_typer(...)`; gains one line merging the new `evaluate`
  command's Typer instance at the root level.
- `src/resume_roast/cli/config/handler.py` /
  `src/resume_roast/cli/show/handler.py` — the group-handler convention the
  new `cli/evaluate/handler.py` follows: module-level `<name>_cli = typer.Typer()`,
  `@<group>_cli.command(...)`-decorated functions, domain errors reported as
  one-line stderr `Error: ...` + `raise typer.Exit(1)`.
- `src/resume_roast/persistence/errors.py` — the pattern (domain base error +
  specific subclasses) that `parsing/errors.py` mirrors. **Not imported** —
  parsing is not persistence; it gets its own error family.
- `src/resume_roast/persistence/credentials_store/parser.py` — the reference
  for INV-002's ingestion-seam shape: one module owns all raw-untyped access
  and returns typed models. `parsing/pdf.py` plays this role for raw PyMuPDF
  payloads.
- `tests/conftest.py` — root conftest (currently `store_dir`); gains the
  `make_pdf` factory fixture because both `tests/parsing/` and `tests/cli/`
  need it.
- `tests/cli/conftest.py` — autouse `resume_roast_home` fixture; reused
  as-is (the parse command does no storage I/O, but the fixture is harmless
  and stays autouse).
- `pyproject.toml` — gains the `pymupdf` dependency (see Constraints).

## Module Decomposition

- **New files**:
  - `src/resume_roast/parsing/__init__.py` — package root re-exporting the
    public surface: `parse_resume`, the node types, `Line`/`Style`/`BBox`/
    `Extraction`, the `Extractor` protocol and `PyMuPdfExtractor`, the
    errors, and `walk`/`find_node`/`node_path`/`ancestors`.
  - `src/resume_roast/parsing/errors.py` — `ParsingError` base +
    `InvalidPdfError`, `NoTextLayerError`, `UnsupportedLayoutError`,
    `UnsupportedFormatError`, `UnknownNodeIdError`.
  - `src/resume_roast/parsing/models.py` — `Style`, `BBox`, `Line`,
    `Extraction`, the `Extractor` protocol, and the tree node types
    `Document`, `Section`, `Entry`, `Paragraph`, `Bullet` (+ `Block`/`Node`
    type aliases).
  - `src/resume_roast/parsing/pdf.py` — `PyMuPdfExtractor`, the `Extractor`
    implementation for `.pdf`: PyMuPDF extraction, line assembly, unicode
    normalization, same-row merging, multi-column/no-text/unopenable
    rejection. The **only** module that imports `pymupdf` or touches its
    raw dict payloads.
  - `src/resume_roast/parsing/treeify.py` — `build_tree(lines, *, source,
    page_count) -> Document`: style clustering, heading tiers, bullet and
    paragraph assembly, pre-order ID assignment.
  - `src/resume_roast/parsing/tree.py` — addressing helpers over a built
    tree: `walk`, `find_node`, `node_path`, `ancestors`.
  - `src/resume_roast/parsing/pipeline.py` — `parse_resume(path) ->
    Document` facade: extractor dispatch by file extension (`EXTRACTORS`
    registry, `.pdf` only today) then `build_tree`.
  - `src/resume_roast/cli/evaluate/__init__.py` /
    `src/resume_roast/cli/evaluate/handler.py` — the root-level `evaluate`
    command.
  - `tests/parsing/__init__.py`, `tests/parsing/test_pdf.py`,
    `tests/parsing/test_treeify.py`, `tests/parsing/test_tree.py`,
    `tests/parsing/test_pipeline.py`, `tests/cli/test_evaluate.py` — see
    Test Plan.
- **Modified files**:
  - `src/resume_roast/cli/runner.py` — one `cli.add_typer(evaluate_cli)`
    line (no `name`, so the command merges into the root level).
  - `pyproject.toml` — add `pymupdf` to `[project] dependencies`.
  - `tests/conftest.py` — add the `make_pdf` factory fixture.
- **Renames / moves**: none.
- **Explicit non-goals** (required):
  - **No multi-column support.** Two-column layouts are *detected and
    rejected* (`UnsupportedLayoutError`), not parsed. Column-aware reading
    order is a future spec; the loud failure is this spec's contract.
  - **No OCR / scanned PDFs.** A PDF with no extractable text raises
    `NoTextLayerError`. OCR is out of scope indefinitely.
  - **No formats other than PDF.** The `Extractor` protocol, the `Line`
    list, and the tree are the format-agnostic seams a future DOCX
    extractor plugs into; only the `.pdf` registry entry exists today. The
    `evaluate <path>` command dispatches by file extension through
    `EXTRACTORS`, so a future format needs a registry entry and zero CLI
    changes.
  - **No semantic fields.** No interpretation of dates, employers, job
    titles, contact info, or skill lists. Nodes are structural (section /
    entry / paragraph / bullet) with raw text plus style metadata only.
  - **No persistence.** The tree is in-memory only — no serialization, no
    files written, no `persistence/` involvement. A later spec owns
    save/load if the TUI needs it.
  - **No editing operations.** Node IDs and paths make nodes *addressable*;
    the edit-operation vocabulary (replace/insert/delete/move) is a later
    spec.
  - **No TUI, no AI.** This spec ends at "parse and print".
  - **No span-level styling.** Blocks carry one dominant style each (the
    style of their longest fragment). Mixed inline styling within a block
    ("**bold** inside a bullet") is recorded nowhere in v1.
  - **No tables, images, hyperlinks, headers/footers heuristics.** Table
    cells parse as whatever lines they yield; images are ignored.
  - **No heuristic tuning loop.** The classification thresholds below are
    v1 constants. Known v1 limitations (each documented in Edge cases): a
    multi-line section or entry heading becomes multiple sections/entries;
    an all-bold resume gets no entry tier; a three-level heading hierarchy
    flattens into the two supported tiers.
  - **No golden-resume corpus.** Tests use synthetic PDFs generated by
    PyMuPDF itself. A real-resume corpus with visual round-trip diffing
    belongs to the future re-rendering spec.

## Design Principles Referenced

- [DP-001: Test Behavior, Not Implementation](../docs/design-principles/dp-001-test-behavior-not-implementation.md)
  — treeify scenarios drive the public `build_tree` with `Line` values and
  assert the resulting tree; pdf scenarios drive `PyMuPdfExtractor.extract`
  with real PDF files and assert `Line`s or typed errors; CLI scenarios
  drive `CliRunner`
  and assert exit codes/output. No test reaches into clustering internals.
- [DP-002: Economical Test Code](../docs/design-principles/dp-002-economical-test-code.md)
  — bullet markers, malformed-file cases, and unknown-ID cases are
  parametrized; a single `make_pdf` factory fixture and a single `Line`
  factory helper serve all scenarios.
- [DP-003: Thin CLI Handlers](../docs/design-principles/dp-003-thin-cli-handlers.md)
  — the `evaluate` command is one `parse_resume` call, pure tree-to-text
  rendering (presentation, explicitly within DP-003's remit), and the
  standard error-mapping convention. All real work lives in `parsing/`.

## Invariants Referenced

- [INV-002: JSON Never Crosses a Boundary Untyped](../docs/invariants/inv-002-json-never-crosses-a-boundary-untyped.md)
  — applied to this domain's equivalent ingestion: the raw
  `page.get_text("dict")` payload is untyped external data exactly like raw
  JSON from a file. `parsing/pdf.py` is the single ingestion seam — the only
  module that touches the raw payload — and it returns typed
  `Line`/`Extraction` models; every documented bad input (unopenable file,
  garbage bytes, password-protected, no text layer, multi-column) raises a
  typed `ParsingError`, never an unguarded `KeyError`/`TypeError`. Enforced
  by the `test_extract_rejects_*` scenarios plus `pyright --strict`.

## Pre-implementation Self-Check

- DP-001 — every scenario exercises a public function (`extract`,
  `build_tree`, the `tree.py` helpers, `parse_resume`, or the CLI)
  and asserts observable results (returned models, raised typed errors,
  exit codes, rendered text); expected values are literals.
- DP-002 — parametrized markers/bad-files/unknown-IDs; one PDF factory
  fixture in the root conftest shared by parsing and CLI tests; one local
  `Line` factory helper in `test_treeify.py` shared with `test_tree.py`
  only if extracted to a tiny shared helper — otherwise duplicated
  three-line factories are acceptable per DP-002's "fitting fixture" test.
- DP-003 — `cli/evaluate/handler.py` contains only: one `parse_resume` call,
  the `_render` presentation helper, and `ParsingError → Error: ... /
  exit 1` mapping. It imports nothing from `pymupdf` and does no I/O beyond
  reading the argument path via `parse_resume`.
- INV-002 — raw PyMuPDF dicts never escape `pdf.py` (its return type is
  `Extraction`); rejection scenarios cover each documented malformed input.

## Test Plan (written first)

### `tests/parsing/test_treeify.py`

Scenarios construct `Line` values directly via a module-level factory
helper with keyword defaults (body style: 11.0pt, not bold) — no PDFs
needed; `build_tree` is pure.

- `test_build_tree_promotes_larger_font_lines_to_section_headings` — lines:
  22pt name, 11pt contact line (small gap), 14pt "EXPERIENCE", 11pt body
  (small gap); tree has sections `["Jordan Diaz", "EXPERIENCE"]` (both
  larger-than-body tiers are section tier), with the contact text under
  the first section.
- `test_build_tree_puts_leading_body_text_in_untitled_section` — body lines
  before any heading; `sections[0].heading is None` and holds them.
- `test_build_tree_starts_new_entry_on_large_gap_without_bold` — within a
  section, entirely without bold anywhere: a first job title (small gap
  after the section heading) with a paragraph and bullets, then a second
  job title preceded by a gap over threshold; the first job's content
  lands in an `Entry` with `heading is None`, the second job's line starts
  `Entry(heading="...")` — proving entries are detected from whitespace,
  not boldness (this is the spec's Acceptance Example above, pinned as a
  test).
- `test_build_tree_keeps_first_entry_in_section_untitled` — a section
  heading immediately followed by a body line with only a small
  (continuation-sized) gap; that content lands in `Entry(heading=None)` —
  pins the documented v1 limitation that a section's first record stays
  untitled.
- `test_build_tree_treats_bold_as_irrelevant_to_entry_detection` — the same
  shape as `test_build_tree_starts_new_entry_on_large_gap_without_bold` but
  with every line bold: identical output — proves bold no longer
  influences entry detection in either direction (replaces the old
  "all-bold disables the entry tier" behavior entirely).
- `test_build_tree_strips_bullet_markers` — parametrized over every marker
  in `BULLET_MARKERS`; a line `"{marker} Did a thing"` becomes
  `Bullet(marker="{marker}", text="Did a thing")`.
- `test_build_tree_merges_indented_bullet_continuation_lines` — bullet line
  followed by a continuation line (x0 aligned with the bullet's text,
  vertical gap under threshold) yields one `Bullet` with joined text and a
  union bbox.
- `test_build_tree_merges_adjacent_body_lines_and_dehyphenates` —
  parametrized over two body lines with gap under threshold:
  (`"a devel-"`, `"oper of things"`) → one `Paragraph` containing
  `"developer"` (syllable hyphen dropped), and (`"uses state-of-the-"`,
  `"art tooling"`) → one `Paragraph` containing `"state-of-the-art"`
  (compound hyphen kept).
- `test_build_tree_starts_new_entry_instead_of_splitting_paragraph_on_large_gap`
  — two body lines with gap over threshold, no bullets, no section
  boundary → the first stands alone in an `Entry(heading=None)`, the
  second starts its own `Entry(heading=...)` holding no blocks — this
  supersedes the old "splits into two sibling Paragraphs" behavior, since
  a large gap now always means "new record", not "new paragraph in the
  same record".
- `test_build_tree_assigns_preorder_node_ids` — for a known two-section
  tree, IDs are exactly `n1` (document), `n2`/`n3`/`n4`… in pre-order
  (section, its entries, each entry's blocks, next section…).
- `test_build_tree_records_style_and_provenance_on_nodes` — a block's
  `style`/`bbox`/`page` equal the dominant source line's style, the union
  of merged bboxes, and the first line's page; a section heading node
  carries its heading line's style/bbox/page.
- `test_build_tree_returns_empty_document_for_no_lines` — `build_tree([],
  source="x.pdf", page_count=1)` → `Document` with `sections == ()` and id
  `n1` (the pipeline never produces this — `extract` raises first — but the
  pure function's behavior is pinned).

### `tests/parsing/test_tree.py`

Builds one small tree via `build_tree` (not hand-assembled nodes) and
exercises the helpers.

- `test_walk_yields_nodes_in_preorder` — `[n.id for n in walk(doc)]` ==
  `["n1", "n2", ...]` in document order.
- `test_find_node_returns_node_by_id` — `find_node(doc, "n3")` is the same
  object `walk` yields third.
- `test_node_path_returns_bracketed_path` — parametrized:
  (`"n1"`, `"doc"`), a section id → `"sections[i]"`, an entry id →
  `"sections[i].entries[j]"`, a block id →
  `"sections[i].entries[j].blocks[k]"` (0-based indices).
- `test_ancestors_returns_chain_from_document` — for a block id,
  `ancestors(doc, block_id)` is `(document, its_section, its_entry)` in
  that order; for `"n1"` it is `()`.
- `test_helpers_raise_unknown_node_id` — parametrized over `find_node`,
  `node_path`, and `ancestors` with `"n999"`; each raises
  `UnknownNodeIdError` naming the id.

### `tests/parsing/test_pdf.py`

Scenarios call `PyMuPdfExtractor().extract` and use the `make_pdf` factory
fixture (root conftest) to generate synthetic PDFs in `tmp_path`. Fixture
bullets use the ASCII `"- "` marker (the base-14
fonts used for generation cannot encode `•`); unicode markers are covered in
the treeify scenarios above.

- `test_extract_returns_styled_lines_in_reading_order` — one page with a
  14pt Helvetica-Bold heading and two 11pt Helvetica body lines; `extract`
  returns `page_count == 1` and `Line`s in top-to-bottom order with the
  expected text, `style.size` (±0.5), `style.bold` flags, and `page == 1`.
- `test_extract_orders_lines_across_pages` — text on pages 1 and 2 of a
  two-page PDF; `page_count == 2`, page-2 lines carry `page == 2` and sort
  after every page-1 line.
- `test_extract_merges_same_row_title_and_date` — "Software Engineer" at
  the left margin and "2020 – 2023" right-aligned at the same baseline
  become **one** `Line` reading `"Software Engineer  2020 – 2023"`, and no
  `UnsupportedLayoutError` is raised — right-aligned dates are single-column
  content, not a second column.
- `test_extract_normalizes_ligatures` — inserted text containing the `ﬁ`
  ligature (U+FB01) extracts with `"fi"` in the line text.
- `test_extract_rejects_two_column_layout` — two parallel text columns
  (≥ 6 lines each, separated by a wide gutter, both spanning the page) →
  `UnsupportedLayoutError` whose message names page 1.
- `test_extract_rejects_pdf_without_text_layer` — a PDF with one empty page
  → `NoTextLayerError` naming the file.
- `test_extract_rejects_unopenable_file` — parametrized: a nonexistent
  path; a `.pdf` file containing garbage bytes; a password-protected PDF
  (`user_pw` set at save) → each raises `InvalidPdfError` naming the path.

### `tests/parsing/test_pipeline.py`

- `test_parse_resume_returns_document_for_single_column_pdf` — the
  canonical fixture resume (see the CLI Acceptance Example below) parsed
  end-to-end: `parse_resume` returns a `Document` with
  `source == "resume.pdf"`, `page_count == 1`, section headings
  `["Jordan Diaz", "EXPERIENCE"]`, one bold-line entry under "EXPERIENCE"
  holding two `Bullet`s with markers stripped.
- `test_parse_resume_rejects_unregistered_extension` — parametrized: a
  `.docx` path and a suffixless path → `UnsupportedFormatError` naming the
  extension (or its absence); no extractor runs.
- `test_parse_resume_uses_injected_extractor` — a hand-written stub
  extractor (plain class whose `extract` returns a canned `Extraction`)
  passed via the `extractor` keyword; the returned `Document` is built
  from the stub's lines — proves callers depend only on the `Extractor`
  protocol, not on PyMuPDF.

### `tests/cli/test_evaluate.py`

- `test_evaluate_renders_node_tree` — canonical fixture resume; exit 0 and
  stdout equals exactly the rendered block in the handler's first
  Acceptance Example (exact match, not containment, so a wrong indent,
  wrong ID order, or missing node fails).
- `test_evaluate_reports_error_for_unreadable_file` — parametrized:
  nonexistent path, a two-column fixture, and a `.docx` path; each exits 1
  with a one-line `Error: ...` on stderr (naming the path, the page for
  the layout case, or the extension for the format case), no traceback,
  nothing on stdout.
- `test_root_help_lists_evaluate` — `resume-roast` with no arguments exits
  0 and the help output contains the `evaluate` command's help-summary
  text (`"Parse a resume"`), not a bare `"evaluate"` substring — proving
  the command merged into the root level.

**Constraints**:

- Every Acceptance Example in *Changes Required* maps to at least one
  scenario above.
- INV-002 → the three `test_extract_rejects_*` scenarios (typed errors at
  the ingestion seam, never unguarded exceptions).
- Red/green evidence: separate `test:` then `feat:` commits on the branch
  (`make check-tdd` enforces the ordering).
- Immediately after test bodies are authored — before any production code —
  run the [Local Test Quality check](../docs/checks/local-test-quality.md)
  against DP-001/DP-002; waivers recorded in *Footnotes*.

**Red/green record**: n/a — separate `test:`/`feat:` commits.

## Execution Order

0. [Spec review](../docs/checks/spec-review.md) (optional, at user's
   discretion) — findings resolved by the author before implementation.
1. `poetry add pymupdf` (tests import it for fixture generation); commit as
   `chore: add pymupdf dependency`.
2. Author all test files (`tests/parsing/*`, `tests/cli/test_evaluate.py`, the
   `make_pdf` fixture in `tests/conftest.py`); observe red locally
   (`poetry run pytest`).
3. **Run Local Test Quality check** — validate the new test code against
   DP-001/DP-002 before any production code.
4. Commit as `test: add failing tests for the PDF parsing pipeline`.
5. Implement `parsing/errors.py`, `models.py`, `treeify.py`, `tree.py`
   (pure modules first); observe treeify/tree tests green.
6. Implement `parsing/pdf.py` and `pipeline.py`; observe pdf/pipeline tests
   green.
7. Implement `cli/evaluate/handler.py` + the `runner.py` mount; observe
   CLI tests green.
8. `make check` clean (ruff format/check, pyright strict).
9. Commit as `feat: add PDF parsing pipeline and evaluate command`.
10. Manual smoke test (see Definition of Done).

## Changes Required

### `src/resume_roast/parsing/errors.py`

- **Interface**:

  ```python
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
  ```

- **Behavior**: pure error taxonomy, mirroring `persistence/errors.py`'s
  base-plus-specifics shape in a separate family (parsing failures are not
  persistence failures; the CLI catches `ParsingError`).
- **Acceptance Examples**: n/a — exercised through `pdf.py`/`tree.py`.
- **Data flow / Edge cases / Strategy**: n/a — declarations only.
- **Tests**: covered by every rejection scenario.

### `src/resume_roast/parsing/models.py`

- **Interface**:

  ```python
  @dataclass(frozen=True)
  class Style:
      font: str
      size: float
      bold: bool
      italic: bool

  @dataclass(frozen=True)
  class BBox:
      x0: float
      y0: float
      x1: float
      y1: float

  @dataclass(frozen=True)
  class Line:
      text: str
      style: Style
      bbox: BBox
      page: int  # 1-based

  @dataclass(frozen=True)
  class Extraction:
      lines: tuple[Line, ...]
      page_count: int

  @dataclass(frozen=True)
  class Paragraph:
      id: str
      text: str
      style: Style
      bbox: BBox
      page: int

  @dataclass(frozen=True)
  class Bullet:
      id: str
      text: str      # marker stripped
      marker: str    # the glyph that introduced the bullet, e.g. "•"
      style: Style
      bbox: BBox
      page: int

  type Block = Paragraph | Bullet

  @dataclass(frozen=True)
  class Entry:
      id: str
      heading: str | None
      style: Style | None   # heading line's style; None when heading is None
      bbox: BBox | None
      page: int | None
      blocks: tuple[Block, ...]

  @dataclass(frozen=True)
  class Section:
      id: str
      heading: str | None
      style: Style | None
      bbox: BBox | None
      page: int | None
      entries: tuple[Entry, ...]

  @dataclass(frozen=True)
  class Document:
      id: str
      source: str        # file name, e.g. "resume.pdf"
      page_count: int
      sections: tuple[Section, ...]

  type Node = Document | Section | Entry | Paragraph | Bullet

  class Extractor(Protocol):
      """Extraction stage for one resume file format."""

      def extract(self, path: Path) -> Extraction: ...
  ```

- **Behavior**: pure data. Everything is frozen with `tuple` children —
  the tree is an immutable value; future edit specs produce new trees via
  `dataclasses.replace`. `Line`/`Extraction` are the typed seam between
  `pdf.py` and `treeify.py` (and the entry point a future DOCX extractor
  targets).
- **Acceptance Examples**: n/a — exercised through the builders below.
- **Data flow**: `pdf.py` produces `Extraction`; `treeify.py` consumes
  `Line`s and produces `Document`; `tree.py` and the CLI consume `Document`.
- **Edge cases**: `heading is None` means "untitled" (preamble section /
  anonymous entry) and implies `style`/`bbox`/`page` are also `None` for
  that node — there is no heading line to take provenance from. This is
  intentional, not an omission: on Section/Entry these fields mean
  *heading-line provenance* specifically, never a derived summary of
  children — a best-effort style taken from the first child would silently
  hand a future re-renderer body style where it expects heading style.
  Consumers needing an untitled node's location or extent derive it from
  descendants (first block's `page`, union of block bboxes); a dedicated
  extent helper belongs to the first spec that needs one.
- **Strategy**: node IDs are plain `str` (`"n1"`…) assigned by `treeify`;
  models never generate IDs. Every node type has an `id` as its first
  field so `Node` can be handled uniformly (`node.id` is total across the
  union). `Extractor` is a structural `typing.Protocol` — implementations
  (PyMuPDF today, others after a library migration) conform by matching
  the signature, no inheritance.
- **Tests**: covered via treeify/tree/pdf scenarios; no direct model tests.

### `src/resume_roast/parsing/pdf.py`

- **Interface**:

  ```python
  class PyMuPdfExtractor:
      """Extractor implementation backed by PyMuPDF."""

      def extract(self, path: Path) -> Extraction: ...
  ```

  Satisfies the `Extractor` protocol (verified by `pyright --strict` at
  its `EXTRACTORS` registration). Module constants (named, tunable):
  `GUTTER_MIN_WIDTH = 24.0`,
  `MIN_SIDE_FRACTION = 0.30`, `MIN_SIDE_LINES = 5`,
  `MIN_LINES_FOR_COLUMN_CHECK = 10`, `ROW_OVERLAP_FRACTION = 0.5`.

- **Behavior**: opens the file with `pymupdf.open`; any open failure
  (missing file, not a PDF, corrupt) and `doc.needs_pass` raise
  `InvalidPdfError` naming the path. For each page,
  `page.get_text("dict")` is parsed into `Line`s: text blocks only, one
  `Line` per PyMuPDF line, text = concatenated span texts normalized with
  NFKC (folds ligatures like `ﬁ`), style = the dominant span's (most
  characters) font/size, `bold = bool(flags & 16) or "bold" in
  font.lower()`, `italic = bool(flags & 2)`; whitespace-only lines are
  dropped. Lines are sorted by `(page, y0, x0)` and **same-row fragments
  merged**: consecutive lines whose vertical overlap is ≥
  `ROW_OVERLAP_FRACTION` of the shorter line's height are joined
  left-to-right with two spaces (union bbox, dominant-fragment style) — this
  is how "title ......... right-aligned date" rows stay one line. Before
  merging, each page with ≥ `MIN_LINES_FOR_COLUMN_CHECK` lines is checked
  for a column gutter: compute the union of all line x-intervals; if an
  interior coverage gap of width ≥ `GUTTER_MIN_WIDTH` exists such that each
  side holds ≥ `MIN_SIDE_LINES` lines **and** ≥ `MIN_SIDE_FRACTION` of the
  page's lines, raise `UnsupportedLayoutError` naming the page. (Right-
  aligned dates usually survive this: a date column runs one line per
  entry — 8 dates on a 30-line page is 27%, under the 30% threshold — and
  any full-width line, like a summary paragraph, closes the gutter
  entirely.) If, after all pages, no line has non-blank text,
  raise `NoTextLayerError` suggesting the file may be a scan. Returns
  `Extraction(lines, page_count)`.
- **Acceptance Examples**:

  ```text
  Input:  PyMuPdfExtractor().extract(path to a one-page PDF: "EXPERIENCE" at 14pt Helvetica-Bold,
          "Built a parser" at 11pt Helvetica below it)
  Output: Extraction(page_count=1, lines=(
            Line(text="EXPERIENCE", style=Style(font="Helvetica-Bold", size≈14, bold=True, italic=False), page=1),
            Line(text="Built a parser", style=Style(font="Helvetica", size≈11, bold=False, italic=False), page=1)))
  ```

  ```text
  Input:  PyMuPdfExtractor().extract(path to a two-column PDF: 8 lines at x∈[72,280],
          8 lines at x∈[330,540], all vertically interleaved)
  Output: raises UnsupportedLayoutError("... page 1 ... multi-column ...")
  ```

  ```text
  Input:  PyMuPdfExtractor().extract(Path("missing.pdf"))
  Output: raises InvalidPdfError naming missing.pdf
  ```

- **Data flow**: `Path → pymupdf document → raw dict payload → Line
  assembly → column check → same-row merge → Extraction`. Reached only
  through the `EXTRACTORS` registry entry in `pipeline.py` (and tests).
- **Edge cases**: empty pages contribute no lines but still count in
  `page_count`; span `size` is kept raw (binning is treeify's concern);
  encrypted-but-openable PDFs (`needs_pass` false) parse normally; a page
  under `MIN_LINES_FOR_COLUMN_CHECK` lines skips the gutter check (too
  little text to misorder badly). The column thresholds are v1 estimates
  deliberately biased toward **false positives**: an unusually dense date
  column that still trips the check yields a loud, recoverable
  `UnsupportedLayoutError`, whereas a missed two-column layout would yield
  silently garbled text — the strictly worse failure. Expect
  `MIN_SIDE_FRACTION`/`GUTTER_MIN_WIDTH` to be tuned against real resumes
  at the manual smoke test; each tune is a one-constant amendment.
- **Strategy**: `import pymupdf` (the modern module name, not `fitz`).
  This module is the **only** place raw PyMuPDF payloads exist; the
  `get_text("dict")` result is immediately narrowed (`cast` to
  `dict[str, Any]` and defensive `.get` access) and converted to typed
  models — any `cast`/`type: ignore` needed to satisfy `pyright --strict`
  against PyMuPDF's incomplete typing is confined here (INV-002 seam).
- **Tests**: the `test_extract_*` scenarios.

### `src/resume_roast/parsing/treeify.py`

- **Interface**:

  ```python
  def build_tree(lines: Sequence[Line], *, source: str, page_count: int) -> Document: ...
  ```

  Module constants: `STYLE_SIZE_BIN = 0.5`, `SECTION_SIZE_DELTA = 1.0`,
  `BREAK_GAP_FACTOR = 0.5`, `BULLET_X_TOLERANCE = 2.0`,
  `BULLET_MARKERS = ("•", "◦", "▪", "▫", "‣", "·", "∙", "⁃", "●", "○",
  "■", "□", "◆", "◇", "▶", "➤", "→", "✓", "✔", "-", "–", "—", "*")`.

- **Behavior**: classifies each line in one reading-order pass, using two
  independent signals — **style** (for sections) and **the vertical gap to
  the previous line** (for entries) — then groups. **Classification**:
  style key = `(round(size / STYLE_SIZE_BIN) * STYLE_SIZE_BIN, bold)`; the
  *body style* is the key with the most total characters, and the median
  height of body-style lines is the unit the gap signal is measured
  against. A line is a **bullet** if its text starts with a
  `BULLET_MARKERS` glyph followed by whitespace or an invisible Unicode
  format character (e.g. a zero-width space); else a **section heading**
  if its size bin ≥ body bin + `SECTION_SIZE_DELTA` — bold is irrelevant
  here, since many real templates size section headings up without
  bolding them; else an **entry heading** if its lead-in gap
  (`this.bbox.y0 - previous_line.bbox.y1`, the immediately preceding line
  in reading order, same page; undefined for the first line of the
  document counts as "no", i.e. not an entry heading) is ≥
  `BREAK_GAP_FACTOR` × the median body-line height — bold and size are
  irrelevant here too, since a real job/project title is frequently
  identical in style to body text, and only the surrounding whitespace
  marks it as a new record; else **body**. This replaces the earlier
  "bold at body size" entry rule entirely: real resumes commonly have no
  stylistic distinction whatsoever between a job title and its body text,
  so style cannot be the signal for entries the way it still is for
  sections. **Grouping**: each section-heading line starts a `Section`
  (heading = line text); body/bullet/entry content before the first
  section heading forms `Section(heading=None)`. Within a section, each
  entry-heading line starts an `Entry` (heading = line text); content
  before the first forms `Entry(heading=None)` — in particular, a
  section's first record commonly stays untitled, since the gap right
  after a section heading is ordinarily the same small size as any other
  continuation gap (see Edge cases). Sections/entries with no content
  still appear (empty `entries`/`blocks`). Consecutive body lines (lines
  that are neither bullets, section headings, nor entry headings — i.e.
  their lead-in gap is below the entry threshold) merge into one
  `Paragraph` while on the same page; joining de-hyphenates: when the
  previous fragment ends with `-` and the next starts lowercase, the
  pieces join without a space — dropping the hyphen when the fragment's
  final token contains no earlier hyphen (`devel-` + `oper` →
  `developer`, syllable hyphenation), keeping it when one exists
  (`state-of-the-` + `art` → `state-of-the-art`, a compound broken at a
  real hyphen). All other joins use a single space. A bullet line always
  starts a new `Bullet` (marker stripped along with following whitespace
  or invisible format characters), regardless of its lead-in gap;
  subsequent body lines merge into it under the same gap rule while their
  `x0` ≥ the bullet text's x0 − `BULLET_X_TOLERANCE`. Merged blocks take
  the union bbox, the dominant fragment's style, and the first fragment's
  page. **IDs**: assigned pre-order over the finished structure — `n1` is
  the document, then each section, its entries, and each entry's blocks
  in document order.
- **Acceptance Examples**:

  ```text
  Input:  build_tree([Line("Jordan Diaz", 22pt, y0=60,y1=88), Line("jordan@example.com", 11pt, y0=92,y1=104),
                      Line("EXPERIENCE", 14pt, y0=150,y1=166), Line("Engineer — Acme", 11pt, y0=170,y1=182),
                      Line("- Shipped it", 11pt, y0=196,y1=208), Line("Engineer — Beta", 11pt, y0=250,y1=262)],
                      source="resume.pdf", page_count=1)
          (no line is bold; entry detection relies entirely on the gap signal;
          body-line height is 12pt throughout, so the entry threshold is 6pt)
  Output: Document(n1, sections=(
            Section(n2, "Jordan Diaz", entries=(Entry(n3, None, blocks=(Paragraph(n4, "jordan@example.com"),)),)),
            Section(n5, "EXPERIENCE", entries=(
              Entry(n6, None, blocks=(Paragraph(n7, "Engineer — Acme"), Bullet(n8, "Shipped it", marker="-"))),
              Entry(n9, "Engineer — Beta", blocks=()),
            ))))
  ```

  The first job ("Engineer — Acme") stays untitled — its 4pt gap after
  "EXPERIENCE" is ordinary continuation spacing, under the 6pt threshold —
  while the second job ("Engineer — Beta"), preceded by a 42pt gap, clears
  the threshold and correctly starts its own `Entry`, entirely without any
  bold text anywhere in the input.

  ```text
  Input:  two body lines, gap < threshold, texts "a devel-" / "oper of things"
  Output: one Paragraph with text "a developer of things"
  ```

  ```text
  Input:  two body lines, gap < threshold, texts "uses state-of-the-" / "art tooling"
  Output: one Paragraph with text "uses state-of-the-art tooling"
  ```

- **Data flow**: pure function; consumes `Line`s from any extractor,
  produces the `Document` consumed by `tree.py` and the CLI.
- **Edge cases**: empty `lines` → `Document` with no sections; multi-line
  section/entry headings become sibling sections/entries (v1 limitation,
  accepted); **a section's first record is commonly left untitled** —
  the gap between a section heading and its first entry is ordinarily the
  same small "next line" spacing as any continuation gap, not a
  deliberate break, so it does not clear `BREAK_GAP_FACTOR` (a known v1
  gap: only the second-and-later records in a section reliably get their
  own titled `Entry`; a future spec may add a positional signal — e.g.
  "immediately followed by a bullet run" — to close this); a section with
  multiple gap-separated paragraphs and no bullets between them (rare in
  practice) over-segments — each such paragraph becomes its own titled
  `Entry`, with that paragraph's full text as the heading, rather than
  staying grouped as sibling paragraphs in one entry, since nothing but
  the gap distinguishes "new paragraph" from "new record" once style is
  out of the picture (accepted v1 limitation); a
  bullet marker with no following whitespace (e.g. "-dash-led word") is
  body text, not a bullet; the 0.5pt style bin absorbs PyMuPDF's
  sub-point size jitter (10.96 and 11.03 both bin to 11.0), and two
  readings straddling a bin boundary (10.74 vs 10.76) merely split one
  cluster — harmless, since section classification needs only the
  ≥ `SECTION_SIZE_DELTA` separation between body and heading sizes, not
  exact cluster membership; a bold, all-caps, or otherwise
  distinctively-styled resume works the same as a plain one now, since
  neither section nor entry classification depends on bold.
- **Strategy**: classification thresholds are module constants — future
  tuning specs change one number, not logic. Entry classification and the
  paragraph continuation/split decision are the same comparison viewed
  from two sides (lead-in gap below `BREAK_GAP_FACTOR` × median height
  means "merge/continue", at or above means "this is a new record") — one
  threshold, not two independent ones, so they cannot disagree. Pre-order
  IDs are assigned bottom-up-safe: allocate counters while walking the
  grouped structure in document order before freezing dataclasses
  (implementation may build mutable intermediates; the public output is
  frozen).
- **Tests**: the `test_build_tree_*` scenarios.

### `src/resume_roast/parsing/tree.py`

- **Interface**:

  ```python
  def walk(document: Document) -> Iterator[Node]: ...
  def find_node(document: Document, node_id: str) -> Node: ...
  def node_path(document: Document, node_id: str) -> str: ...
  def ancestors(document: Document, node_id: str) -> tuple[Node, ...]: ...
  ```

- **Behavior**: `walk` yields the document, then each section, its entries,
  and their blocks, pre-order (so yielded IDs are `n1, n2, …` in sequence
  for a freshly built tree). `find_node` returns the node with the given
  id; `node_path` returns `"doc"` for the document,
  `"sections[i]"`, `"sections[i].entries[j]"`, or
  `"sections[i].entries[j].blocks[k]"` (0-based) for descendants.
  `ancestors` returns the chain of containing nodes from the document down
  to the node's direct parent, exclusive of the node itself (`()` for the
  document) — the primitive a future verify-style tool uses to fetch "the
  block/section this node came from" by ID. All lookups raise
  `UnknownNodeIdError` naming the id when absent. IDs are the
  canonical address (stable across edits within a session); paths are
  **always derived, never stored**, so they cannot drift when a future spec
  inserts or removes nodes.
- **Acceptance Examples**:

  ```text
  Input:  node_path(doc, "n7")   (doc from the treeify example above)
  Output: "sections[1].entries[0].blocks[0]"
  ```

  ```text
  Input:  find_node(doc, "n99")
  Output: raises UnknownNodeIdError("no node with id 'n99'")
  ```

- **Data flow**: read-only helpers over a built `Document`; the TUI's and
  future edit-operation specs' addressing primitives.
- **Edge cases**: `walk` on an empty document yields just the document;
  lookups are O(n) over `walk` — fine at resume scale, no index caching.
- **Strategy**: implement `find_node`/`node_path`/`ancestors` on top of a
  single private pre-order traversal that tracks the path and ancestor
  chain, so the four functions cannot disagree.
- **Tests**: the `test_walk_*` / `test_find_node_*` / `test_node_path_*` /
  `test_ancestors_*` / `test_helpers_raise_*` scenarios.

### `src/resume_roast/parsing/pipeline.py`

- **Interface**:

  ```python
  EXTRACTORS: Mapping[str, Extractor] = {".pdf": PyMuPdfExtractor()}

  def parse_resume(path: Path, *, extractor: Extractor | None = None) -> Document: ...
  ```

- **Behavior**: resolves the extractor — the `extractor` argument when
  given, else `EXTRACTORS[path.suffix.lower()]`, raising
  `UnsupportedFormatError` naming the extension when no entry exists —
  runs it, then `build_tree(extraction.lines, source=path.name,
  page_count=extraction.page_count)`. No other error handling —
  extraction errors propagate typed.
- **Acceptance Examples**:

  ```text
  Input:  parse_resume(Path(".../resume.pdf"))   (canonical fixture resume)
  Output: Document(source="resume.pdf", page_count=1,
                   sections=("Jordan Diaz", "EXPERIENCE" — as in the treeify example))
  ```

  ```text
  Input:  parse_resume(Path("resume.docx"))
  Output: raises UnsupportedFormatError naming ".docx"
  ```

- **Data flow**: the app-facing seam. CLI/TUI/future agent code depends on
  `parse_resume` and the `Extractor` protocol only — never on PyMuPDF — so
  migrating extraction libraries later means writing one new `Extractor`
  and swapping a registry entry, with no caller changes.
- **Edge cases**: extension matching is case-insensitive (`.PDF` parses);
  a path with no suffix raises `UnsupportedFormatError`; the `extractor`
  keyword bypasses the registry (tests, future per-format options).
- **Strategy**: `EXTRACTORS` is a plain module-level mapping — a future
  format adds one entry, nothing more.
- **Tests**: the `test_parse_resume_*` scenarios.

### `src/resume_roast/parsing/__init__.py`

- **Change**: re-export the public surface (`parse_resume`, `EXTRACTORS`,
  node types and aliases, `Line`/`Style`/`BBox`/`Extraction`, `Extractor`,
  `PyMuPdfExtractor`, all errors, `walk`, `find_node`, `node_path`,
  `ancestors`). Handlers and future TUI code import only from the package
  root, mirroring `persistence`'s package-root convention.
- **Tests**: exercised transitively by every import.

### `src/resume_roast/cli/evaluate/handler.py`

- **Interface**:

  ```python
  evaluate_cli = typer.Typer()

  @evaluate_cli.command("evaluate")
  def evaluate(path: Path) -> None:
      """Parse a resume and display its node tree."""
      ...
  ```

  Module constant: `TEXT_PREVIEW_LENGTH = 60`.

- **Behavior**: calls `parse_resume(path)`; on `ParsingError`, prints
  `Error: {message}` to stderr and exits 1 (the exact convention of the
  existing handlers' `PersistenceError` mapping). On success, prints one
  line per node from `walk(document)`, indented two spaces per depth:
  the document as `{id} [document] {source} — {page_count} page(s),
  {len(sections)} section(s)`; sections/entries as `{id} [section|entry]
  {heading or "(untitled)"}`; blocks as `{id} [paragraph|bullet] {text}`.
  Every node line whose `page` is not `None` gains a ` (p{page})` suffix —
  untitled sections/entries have no page and thus no suffix — so multi-page
  resumes show where each node lives. Heading and block text longer than
  `TEXT_PREVIEW_LENGTH` renders as the first `TEXT_PREVIEW_LENGTH - 1`
  characters plus `…`; the page suffix is appended after truncation and is
  never truncated. Exit 0.
- **Acceptance Examples**:

  ```text
  Input:  resume-roast evaluate resume.pdf   (canonical fixture: 22pt name,
          11pt contact line, 14pt-bold EXPERIENCE, 11pt-bold entry line,
          two "- " bullets)
  Output: exit 0; stdout ==
          n1 [document] resume.pdf — 1 page(s), 2 section(s)
            n2 [section] Jordan Diaz (p1)
              n3 [entry] (untitled)
                n4 [paragraph] jordan@example.com | 555-0100 (p1)
            n5 [section] EXPERIENCE (p1)
              n6 [entry] Software Engineer — Acme Corp (p1)
                n7 [bullet] Shipped the roasting pipeline (p1)
                n8 [bullet] Cut parse latency by 40% (p1)
  ```

  ```text
  Input:  resume-roast evaluate missing.pdf
  Output: exit 1; stderr "Error: ..." (one line, names missing.pdf); empty stdout
  ```

- **Data flow**: one `parse_resume` call → private `_render(document) ->
  list[str]` → `typer.echo`. No storage access, no other I/O.
- **Edge cases**: rendering is pure presentation over `walk`; depth is
  derived from node type (document 0, section 1, entry 2, block 3).
- **Strategy**: `path: Path` is a plain Typer argument (no `exists=True`) —
  missing files flow through `InvalidPdfError` so all failures share the
  `Error:`/exit-1 shape rather than Typer's exit-2 usage error. The handler
  imports from `resume_roast.parsing` only, never `pymupdf` (DP-003).
- **Tests**: the `test_evaluate_*` scenarios and the root-help scenario.

### `src/resume_roast/cli/runner.py`

- **Change**: import `evaluate_cli` and add `cli.add_typer(evaluate_cli)`
  after the existing mounts — no `name`, so Typer merges the sub-app's
  single command into the root level and the invocation is
  `resume-roast evaluate <path>` (not a nested group). Nothing else.
- **Tests**: exercised by every `tests/cli/test_evaluate.py` scenario;
  `test_root_help_lists_evaluate` specifically pins the root-level merge.

### `pyproject.toml`

- **Change**: add `"pymupdf (>=1.26,<2.0)"` to `[project] dependencies`
  (via `poetry add pymupdf`). No other sections change.
- **Tests**: n/a — every parsing test imports it transitively.

### `tests/conftest.py`

- **Change**: add a `make_pdf` factory fixture: returns a callable taking a
  sequence of text placements `(text, x, y, size, fontname)` (base-14 names:
  `"helv"`, `"hebo"`, …) plus optional `filename`/`page_count`/`user_pw`
  keyword options, builds the PDF with PyMuPDF into `tmp_path`, and returns
  its `Path`. Shared by `tests/parsing/` and `tests/cli/test_evaluate.py`; the
  existing `store_dir` fixture is untouched.
- **Tests**: it is test infrastructure; validated by its consumers.

## Definition of Done — Hard Gates

All of these must be true for this spec to be marked completed:

- [ ] All tests pass (`make test`), existing suites untouched and green.
- [ ] Coverage target met (repo default, `fail_under = 85`).
- [ ] `make check` passes (ruff format/check, pyright strict).
- [ ] `make check-tdd` passes (`test:` commit precedes `feat:` commit).
- [ ] Every Acceptance Example above has a corresponding passing test.
- [ ] INV-002 enforcement tests pass (the `test_extract_rejects_*`
      scenarios — every documented bad input raises a typed `ParsingError`).
- [ ] Manual smoke test: `resume-roast evaluate` against a **real**
      single-column resume PDF renders a plausible tree (name/contact
      section, section headings detected, bullets stripped); against a real
      two-column resume it prints the one-line layout error and exits 1;
      the root `resume-roast --help` lists `evaluate` alongside the
      existing groups.

## Advisory Reports

Available at the user's discretion; findings go to
`reports/{check-name}-006.md` and do not block closure:

- [Spec Review](../docs/checks/spec-review.md) — recommended before
  implementation; the classification thresholds and the tree/addressing
  contract are load-bearing for the future TUI and worth adversarial eyes.
- [Local Test Quality](../docs/checks/local-test-quality.md) — mandatory at
  Execution Order step 3 (not advisory).
- [Dead Code](../docs/checks/dead-code.md) — run at green.
- [Local Doc Drift](../docs/checks/local-doc-drift.md) — run at green;
  `docs/development.md` may want an `evaluate` mention.
- [Code Review](../docs/checks/code-review.md) — run before closure.
- [Workflow Conformance](../docs/checks/workflow-conformance.md) — run
  before closure.

## Constraints

- **`pymupdf` is the single new dependency this spec approves** (runtime
  dependency; also used by tests to generate fixtures). PyMuPDF is
  AGPL-3.0 — acknowledged and accepted by the user for this project at spec
  time. No other new dependencies.
- `pymupdf` may be imported **only** by `src/resume_roast/parsing/pdf.py`
  and the `make_pdf` fixture in `tests/conftest.py`. Any
  `cast`/`type: ignore` needed for PyMuPDF's incomplete typing is confined
  to those two files.
- The extraction library is swappable by design: everything outside
  `parsing/` reaches the parser through `parse_resume` (via the package
  root), and everything inside `parsing/` except `pdf.py` depends on the
  `Extractor` protocol and the typed `Line`/`Extraction` models, never on
  PyMuPDF types. Migrating libraries later must require only a new
  `Extractor` implementation and an `EXTRACTORS` entry.
- All heuristic thresholds and the bullet-marker set are module-level named
  constants in `pdf.py`/`treeify.py` — no magic numbers inline.
- All tree/model types are frozen dataclasses with `tuple` children; the
  public API exposes no mutable structures.
- Node IDs are session-scoped: stable for the lifetime of a parsed
  `Document` value, **not** stable across re-parses of the same file.
  Positional paths are always derived by `node_path`, never stored on
  nodes.
- The parsing domain does no persistence: nothing under
  `src/resume_roast/persistence/` is imported by `parsing/` or
  `cli/evaluate/`, and no file is ever written.
- Unsupported input never yields a partial tree — `extract` raises before
  `build_tree` runs; wrong-but-confident output is the failure mode this
  spec exists to prevent.
- Existing modules other than `cli/runner.py`, `pyproject.toml`, and
  `tests/conftest.py` are untouched. Completed specs (SPEC-001 through
  SPEC-005) are immutable — not edited.

## Dependencies

- SPEC-004 — provides the group-Typer wiring convention and `runner.py`
  mount point the new `evaluate` command registers against.

## Footnotes

### Manual Corrections

Populated after agent completes implementation. Each entry documents
something the agent got wrong and how it was manually corrected. This serves
as training signal for future specs.
