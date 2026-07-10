"""Tests for the `config` command group."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from resume_roast.cli import cli
from resume_roast.persistence.credentials_store import Credentials, CredentialsStore

TEST_KEY = "nvapi-test-9876"
NVIDIA_CHOICE = "1"

runner = CliRunner()


def test_config_credentials_saves_prompted_key(resume_roast_home: Path) -> None:
    result = runner.invoke(
        cli,
        ["config", "credentials"],
        input=f"{NVIDIA_CHOICE}\n{TEST_KEY}\n{TEST_KEY}\n",
    )

    assert result.exit_code == 0
    assert "1. NVIDIA API key" in result.stdout
    credentials_path = resume_roast_home / "credentials.json"
    assert json.loads(credentials_path.read_text(encoding="utf-8")) == {"nvidia_api_key": TEST_KEY}


def test_config_credentials_masks_key_in_output() -> None:
    result = runner.invoke(
        cli,
        ["config", "credentials"],
        input=f"{NVIDIA_CHOICE}\n{TEST_KEY}\n{TEST_KEY}\n",
    )

    combined = result.stdout + result.stderr
    assert "****9876" in combined
    assert TEST_KEY not in combined


def test_config_credentials_rejects_blank_key(resume_roast_home: Path) -> None:
    result = runner.invoke(cli, ["config", "credentials"], input=f"{NVIDIA_CHOICE}\n   \n   \n")

    assert result.exit_code == 1
    assert result.stderr.strip() != ""
    assert not (resume_roast_home / "credentials.json").exists()


def test_config_credentials_rejects_out_of_range_selection(resume_roast_home: Path) -> None:
    result = runner.invoke(cli, ["config", "credentials"], input="9\n")

    assert result.exit_code == 1
    assert result.stderr.strip() != ""
    assert not (resume_roast_home / "credentials.json").exists()


def test_config_credentials_cancels_without_saving(resume_roast_home: Path) -> None:
    result = runner.invoke(cli, ["config", "credentials"], input="0\n")

    assert result.exit_code == 0
    assert "0. Cancel" in result.stdout
    assert "Traceback" not in result.stdout
    assert not (resume_roast_home / "credentials.json").exists()


def test_config_credentials_overwrites_existing_key(resume_roast_home: Path) -> None:
    CredentialsStore(resume_roast_home).save(
        Credentials(nvidia_api_key="nvapi-old-0000")  # pragma: allowlist secret
    )
    new_key = "nvapi-new-1111"

    result = runner.invoke(
        cli, ["config", "credentials"], input=f"{NVIDIA_CHOICE}\n{new_key}\n{new_key}\n"
    )

    assert result.exit_code == 0
    assert CredentialsStore(resume_roast_home).load() == Credentials(nvidia_api_key=new_key)


def test_config_credentials_reports_storage_failure(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    blocked_path = tmp_path / "not-a-dir"
    blocked_path.write_text("blocked", encoding="utf-8")
    monkeypatch.setenv("RESUME_ROAST_HOME", str(blocked_path))

    result = runner.invoke(
        cli,
        ["config", "credentials"],
        input=f"{NVIDIA_CHOICE}\n{TEST_KEY}\n{TEST_KEY}\n",
    )

    assert result.exit_code == 1
    assert "Traceback" not in result.stdout
    assert "Traceback" not in result.stderr
    error_lines = [line for line in result.stderr.splitlines() if line.strip()]
    assert len(error_lines) == 1


def test_config_group_shows_help_without_subcommand() -> None:
    result = runner.invoke(cli, ["config"])

    assert "credentials" in result.stdout
