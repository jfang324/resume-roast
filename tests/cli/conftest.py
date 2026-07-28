"""Shared fixtures for the CLI end-to-end tests.

Every CLI test runs against a throwaway storage directory. `storage_dir` is
imported by name into four modules, so all four bindings are redirected here
rather than per-test-file — a command that later reaches for storage through a
module its own test never patched still cannot touch the real `~/.resume-roast`.
"""

# The PDF fixture drives PyMuPDF's partially annotated document-building API.
# pyright: reportUnknownMemberType=false, reportUnknownArgumentType=false

from pathlib import Path

import pymupdf
import pytest

from resume_roast.persistence.credentials.store import CredentialsStore
from resume_roast.persistence.credentials.types import Credentials

_STORAGE_DIR_BINDINGS = (
    "resume_roast.cli.utils.storage_dir",
    "resume_roast.cli.config.handlers.storage_dir",
    "resume_roast.cli.interview.handlers.storage_dir",
    "resume_roast.cli.show.handlers.storage_dir",
)


@pytest.fixture(autouse=True)
def isolated_storage_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    for binding in _STORAGE_DIR_BINDINGS:
        monkeypatch.setattr(binding, lambda: tmp_path)
    return tmp_path


@pytest.fixture
def saved_key(isolated_storage_dir: Path) -> None:
    """Put a usable NVIDIA key on disk so a command gets past its auth guard."""
    CredentialsStore(isolated_storage_dir).save(
        Credentials(nvidia_api_key="nv-key")  # pragma: allowlist secret
    )


@pytest.fixture
def sample_pdf(isolated_storage_dir: Path) -> Path:
    """Build a minimal two-line resume PDF, enough for extraction to yield Markdown."""
    path = isolated_storage_dir / "sample.pdf"
    with pymupdf.open() as doc:
        page = doc.new_page()
        page.insert_text((72, 80), "Jane Doe", fontsize=20)
        page.insert_text((72, 120), "Engineer at Acme Corp", fontsize=11)
        doc.save(path)
    return path
