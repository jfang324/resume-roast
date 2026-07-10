"""Tests for the `show` command group."""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from resume_roast.cli import cli
from resume_roast.persistence.credentials_store import Credentials, CredentialsStore

TEST_KEY = "nvapi-test-9876"

runner = CliRunner()


def test_show_credentials_displays_masked_value_not_full_key(resume_roast_home: Path) -> None:
    CredentialsStore(resume_roast_home).save(Credentials(nvidia_api_key=TEST_KEY))

    result = runner.invoke(cli, ["show", "credentials"])

    assert result.exit_code == 0
    combined = result.stdout + result.stderr
    assert "****9876" in combined
    assert TEST_KEY not in combined


def test_show_credentials_reports_not_set_when_missing() -> None:
    result = runner.invoke(cli, ["show", "credentials"])

    assert result.exit_code == 0
    assert "NVIDIA API key: (not set)" in result.stdout


def test_show_group_shows_help_without_subcommand() -> None:
    result = runner.invoke(cli, ["show"])

    assert "credentials" in result.stdout
