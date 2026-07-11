"""Tests for `resume-roast config credentials`."""

from pathlib import Path

import pytest
from typer.testing import CliRunner

from resume_roast.cli.registry import build_subcommand_registry
from resume_roast.persistence.credentials.store import CredentialsStore

app = build_subcommand_registry()
runner = CliRunner()

_TEST_KEY = "sk-ant-test-9876"
_TEST_KEY_2 = "sk-ant-test-1234"


@pytest.fixture(autouse=True)
def _isolated_storage_dir(  # pyright: ignore[reportUnusedFunction]
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> Path:
    monkeypatch.setattr("resume_roast.cli.config.handlers.storage_dir", lambda: tmp_path)
    return tmp_path


def test_credentials_saves_prompted_key(tmp_path: Path) -> None:
    result = runner.invoke(app, ["config", "credentials"], input=f"{_TEST_KEY}\n")

    assert result.exit_code == 0
    store = CredentialsStore(tmp_path)
    assert store.load().nvidia_api_key == _TEST_KEY


def test_credentials_masks_key_in_output() -> None:
    result = runner.invoke(app, ["config", "credentials"], input=f"{_TEST_KEY}\n")

    assert "****9876" in result.output
    assert _TEST_KEY not in result.output


def test_credentials_blank_entry_keeps_existing_value(tmp_path: Path) -> None:
    runner.invoke(app, ["config", "credentials"], input=f"{_TEST_KEY}\n")

    result = runner.invoke(app, ["config", "credentials"], input="\n")

    assert result.exit_code == 0
    store = CredentialsStore(tmp_path)
    assert store.load().nvidia_api_key == _TEST_KEY


def test_credentials_overwrites_existing_key(tmp_path: Path) -> None:
    runner.invoke(app, ["config", "credentials"], input=f"{_TEST_KEY}\n")

    result = runner.invoke(app, ["config", "credentials"], input=f"{_TEST_KEY_2}\n")

    assert result.exit_code == 0
    store = CredentialsStore(tmp_path)
    assert store.load().nvidia_api_key == _TEST_KEY_2


def test_credentials_prompt_shows_current_status_on_rerun() -> None:
    runner.invoke(app, ["config", "credentials"], input=f"{_TEST_KEY}\n")

    result = runner.invoke(app, ["config", "credentials"], input="\n")

    assert "currently set" in result.output
    assert "****9876" in result.output


def test_credentials_leaves_unset_provider_reported_as_not_set() -> None:
    result = runner.invoke(app, ["config", "credentials"], input="\n")

    assert "not set" in result.output


def test_credentials_reports_storage_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    blocked_dir = tmp_path / "blocked"
    blocked_dir.write_text("not a directory", encoding="utf-8")
    monkeypatch.setattr("resume_roast.cli.config.handlers.storage_dir", lambda: blocked_dir)

    result = runner.invoke(app, ["config", "credentials"], input=f"{_TEST_KEY}\n")

    assert result.exit_code == 1
    assert "Error" in result.output
    assert "Traceback" not in result.output


def test_config_group_shows_help_without_subcommand() -> None:
    result = runner.invoke(app, ["config"])

    # no_args_is_help prints help and exits with Click's usage-error code (2),
    # not 0 — this isn't the same code path as an explicit `--help`.
    assert result.exit_code == 2
    assert "credentials" in result.output
