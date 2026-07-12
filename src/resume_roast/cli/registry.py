"""Declares the CLI's command tree and builds the subcommand registry."""

import typer

from resume_roast.cli.config import handlers as config
from resume_roast.cli.guards import guarded
from resume_roast.cli.show import handlers as show
from resume_roast.cli.types import Group

SUBCOMMAND_GROUPS: tuple[Group, ...] = (
    Group(
        name="config",
        help="Manage settings and credentials.",
        handlers=(config.credentials, config.settings),
    ),
    Group(
        name="show",
        help="Display saved settings and credentials.",
        handlers=(show.credentials, show.settings),
    ),
)


def build_subcommand_registry() -> typer.Typer:
    """Assemble the CLI's command tree from every group in SUBCOMMAND_GROUPS."""
    registry = typer.Typer(no_args_is_help=True)
    for group in SUBCOMMAND_GROUPS:
        group_cli = typer.Typer(no_args_is_help=True, help=group.help)
        for handler in group.handlers:
            group_cli.command()(guarded(handler))
        registry.add_typer(group_cli, name=group.name)
    return registry
