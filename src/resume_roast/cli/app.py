"""Builds the resume-roast Typer application and wires commands to it."""

import typer

from resume_roast.cli.config.handler import ConfigHandler
from resume_roast.cli.show.handler import ShowHandler

app = typer.Typer(no_args_is_help=True)

config_app = typer.Typer(no_args_is_help=True)
app.add_typer(config_app, name="config", help="Manage settings and credentials.")

config_handler = ConfigHandler()
config_app.command("credentials")(config_handler.credentials)

show_app = typer.Typer(no_args_is_help=True)
app.add_typer(show_app, name="show", help="Display saved settings and credentials.")

show_handler = ShowHandler()
show_app.command("credentials")(show_handler.credentials)
