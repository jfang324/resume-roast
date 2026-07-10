"""Tests for the `show` command group."""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from resume_roast.cli import cli
from resume_roast.persistence.config_store import Config, ConfigStore
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


def test_show_settings_displays_saved_values(resume_roast_home: Path) -> None:
    ConfigStore(resume_roast_home).save(
        Config(
            model="nvidia/nemotron-3-super-120b-a12b",
            persona="recruiter",
            level="entry",
            feedback_model="meta/llama-3.1-8b-instruct",
            ensemble_models=(
                "nvidia/nemotron-3-super-120b-a12b",
                "meta/llama-4-maverick-17b-128e-instruct",
            ),
        )
    )

    result = runner.invoke(cli, ["show", "settings"])

    assert result.exit_code == 0
    assert result.stdout == (
        "Model: nvidia/nemotron-3-super-120b-a12b\n"
        "Persona: recruiter\n"
        "Level: entry\n"
        "Feedback model: meta/llama-3.1-8b-instruct\n"
        "Ensemble models: nvidia/nemotron-3-super-120b-a12b, "
        "meta/llama-4-maverick-17b-128e-instruct\n"
    )


def test_show_settings_reports_not_set_when_missing() -> None:
    result = runner.invoke(cli, ["show", "settings"])

    assert result.exit_code == 0
    assert result.stdout == (
        "Model: (not set)\n"
        "Persona: (not set)\n"
        "Level: (not set)\n"
        "Feedback model: (not set)\n"
        "Ensemble models: (not set)\n"
    )


def test_show_group_shows_help_without_subcommand() -> None:
    result = runner.invoke(cli, ["show"])

    assert "credentials" in result.stdout
    assert "List every" in result.stdout
