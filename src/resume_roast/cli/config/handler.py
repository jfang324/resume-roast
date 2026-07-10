"""Commands under `resume-roast config`."""

from dataclasses import replace

import typer

from resume_roast.persistence.config_store import SETTING_SPECS, Config, ConfigStore, SettingSpec
from resume_roast.persistence.credentials_store import (
    CREDENTIAL_SPECS,
    Credentials,
    CredentialsStore,
    mask_secret,
)
from resume_roast.persistence.errors import PersistenceError
from resume_roast.persistence.paths import storage_dir

_NOT_SET = "(not set)"

config_cli = typer.Typer(no_args_is_help=True)


@config_cli.command("credentials")
def credentials() -> None:
    """Select and save one of the supported API keys."""
    typer.echo("Select a credential to set:")
    for index, spec in enumerate(CREDENTIAL_SPECS, start=1):
        typer.echo(f"  {index}. {spec.label}")
    typer.echo("  0. Cancel")

    choice: int = typer.prompt("Enter a number", type=int)
    if choice == 0:
        typer.echo("Cancelled.")
        return
    if choice < 1 or choice > len(CREDENTIAL_SPECS):
        typer.echo("Error: invalid selection", err=True)
        raise typer.Exit(1)
    spec = CREDENTIAL_SPECS[choice - 1]

    raw_value = typer.prompt(spec.label, hide_input=True, confirmation_prompt=True)
    value = raw_value.strip()
    if not value:
        typer.echo("Error: API key cannot be empty", err=True)
        raise typer.Exit(1)

    store = CredentialsStore(storage_dir())
    try:
        store.save(Credentials(**{spec.key: value}))
    except PersistenceError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(1) from exc

    typer.echo(f"Saved {spec.label} {mask_secret(value)} to {store.path}")


def _current_display(spec: SettingSpec, current: Config) -> str:
    value = getattr(current, spec.key)
    if value is None:
        return _NOT_SET
    if spec.multi:
        return ", ".join(value)
    return value


def _select_single(spec: SettingSpec) -> str | None:
    """Prompt a single-select menu; return the chosen value, or None to keep current."""
    choice: int = typer.prompt("Enter a number", type=int)
    if choice == 0:
        return None
    if choice < 1 or choice > len(spec.choices):
        typer.echo("Error: invalid selection", err=True)
        raise typer.Exit(1)
    return spec.choices[choice - 1]


def _select_multi(spec: SettingSpec) -> tuple[str, ...] | None:
    """Prompt the ensemble menu; return the chosen tuple, or None to keep current."""
    raw = typer.prompt("Enter numbers separated by commas (0 to keep current)")
    if raw.strip() == "0":
        return None

    selected: list[str] = []
    for token in (t.strip() for t in raw.split(",")):
        if not token.lstrip("-").isdigit():
            typer.echo("Error: invalid selection", err=True)
            raise typer.Exit(1)
        number = int(token)
        if number < 1 or number > len(spec.choices):
            typer.echo("Error: invalid selection", err=True)
            raise typer.Exit(1)
        value = spec.choices[number - 1]
        if value not in selected:
            selected.append(value)
    return tuple(selected)


@config_cli.command("settings")
def settings() -> None:
    """Walk through each setting, selecting values from numbered menus."""
    store = ConfigStore(storage_dir())
    current = store.load()

    updates = Config()
    for spec in SETTING_SPECS:
        typer.echo(f"{spec.label} [current: {_current_display(spec, current)}]:")
        for index, choice in enumerate(spec.choices, start=1):
            typer.echo(f"  {index}. {choice}")
        typer.echo("  0. Keep current")

        value = _select_multi(spec) if spec.multi else _select_single(spec)
        if value is None:
            continue
        updates = replace(updates, **{spec.key: value})

    if updates == Config():
        typer.echo("No changes.")
        return

    try:
        store.save(updates)
    except PersistenceError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(1) from exc

    typer.echo(f"Saved settings to {store.path}")
