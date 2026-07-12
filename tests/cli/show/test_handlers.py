"""Tests for `resume-roast show`."""

import dataclasses
from pathlib import Path

import pytest
from typer.testing import CliRunner

from resume_roast.cli.registry import build_subcommand_registry
from resume_roast.persistence.credentials.store import CredentialsStore
from resume_roast.persistence.credentials.types import Credentials
from resume_roast.persistence.settings.store import SettingsStore
from resume_roast.persistence.settings.types import MODELS, PERSONAS, Settings

app = build_subcommand_registry()
runner = CliRunner()

_TEST_KEY = "sk-ant-test-9876"


@pytest.fixture(autouse=True)
def _isolated_storage_dir(  # pyright: ignore[reportUnusedFunction]
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> Path:
    monkeypatch.setattr("resume_roast.cli.show.handlers.storage_dir", lambda: tmp_path)
    return tmp_path


def test_show_credentials_reports_not_set_when_nothing_saved() -> None:
    result = runner.invoke(app, ["show", "credentials"])

    assert result.exit_code == 0
    assert "NVIDIA API key: (not set)" in result.output


def test_show_credentials_creates_missing_file(tmp_path: Path) -> None:
    result = runner.invoke(app, ["show", "credentials"])

    assert result.exit_code == 0
    assert CredentialsStore(tmp_path).path.exists()


def test_show_credentials_masks_saved_key(tmp_path: Path) -> None:
    CredentialsStore(tmp_path).save(Credentials(nvidia_api_key=_TEST_KEY))

    result = runner.invoke(app, ["show", "credentials"])

    assert result.exit_code == 0
    assert "****9876" in result.output
    assert _TEST_KEY not in result.output


def test_show_settings_displays_defaults_when_nothing_saved() -> None:
    result = runner.invoke(app, ["show", "settings"])

    assert result.exit_code == 0
    defaults = Settings()
    assert f"Model: {defaults.model}" in result.output
    assert f"Persona: {defaults.persona}" in result.output
    assert f"Level: {defaults.level}" in result.output
    assert f"Feedback model: {defaults.feedback_model}" in result.output
    assert f"Ensemble models: {', '.join(defaults.ensemble_models)}" in result.output


def test_show_settings_creates_missing_file_with_defaults(tmp_path: Path) -> None:
    result = runner.invoke(app, ["show", "settings"])

    assert result.exit_code == 0
    store = SettingsStore(tmp_path)
    assert store.path.exists()
    assert store.load() == Settings()


def test_show_settings_displays_saved_values(tmp_path: Path) -> None:
    saved = dataclasses.replace(
        Settings(), persona=PERSONAS[1], ensemble_models=(MODELS[0], MODELS[1])
    )
    SettingsStore(tmp_path).save(saved)

    result = runner.invoke(app, ["show", "settings"])

    assert result.exit_code == 0
    assert f"Persona: {PERSONAS[1]}" in result.output
    assert f"Ensemble models: {MODELS[0]}, {MODELS[1]}" in result.output


def test_show_settings_reports_storage_failure(tmp_path: Path) -> None:
    SettingsStore(tmp_path).path.write_text("not json", encoding="utf-8")

    result = runner.invoke(app, ["show", "settings"])

    assert result.exit_code == 1
    assert "Error" in result.output
    assert "Traceback" not in result.output


def test_show_group_shows_help_without_subcommand() -> None:
    result = runner.invoke(app, ["show"])

    # no_args_is_help prints help and exits with Click's usage-error code (2),
    # not 0 — this isn't the same code path as an explicit `--help`.
    assert result.exit_code == 2
    assert "credentials" in result.output
    assert "settings" in result.output
