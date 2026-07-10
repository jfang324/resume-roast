"""Wires the resume-roast Typer application from group-level Typer instances."""

import typer

from resume_roast.cli.config.handler import config_cli
from resume_roast.cli.show.handler import show_cli

cli = typer.Typer(no_args_is_help=True)
cli.add_typer(config_cli, name="config", help="Manage settings and credentials.")
cli.add_typer(show_cli, name="show", help="Display saved settings and credentials.")
