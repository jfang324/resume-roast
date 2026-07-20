"""Declares the CLI's command tree and builds the subcommand registry."""

import typer

from resume_roast.cli.config import handlers as config
from resume_roast.cli.evaluate.handlers import evaluate
from resume_roast.cli.generate_block.handlers import generate_block
from resume_roast.cli.guards import guarded
from resume_roast.cli.interview.handlers import interview
from resume_roast.cli.refine.handlers import refine
from resume_roast.cli.show import handlers as show
from resume_roast.cli.types import Group, Handler
from resume_roast.logging_config import configure_logging

TOP_LEVEL_HANDLERS: tuple[Handler, ...] = (evaluate, refine, generate_block, interview)

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


def _configure_logging(
    debug: bool = typer.Option(
        False,
        "--debug",
        help="Write full debug logs to ~/.resume-roast/logs/debug.log; "
        "includes raw prompts and responses containing resume content.",
    ),
) -> None:
    """Root callback: configure logging before any command runs."""
    configure_logging(debug)


def build_subcommand_registry() -> typer.Typer:
    """Assemble the CLI's command tree from every registered handler and group."""
    registry = typer.Typer(no_args_is_help=True)
    registry.callback()(_configure_logging)
    for handler in TOP_LEVEL_HANDLERS:
        registry.command()(guarded(handler))

    for group in SUBCOMMAND_GROUPS:
        group_cli = typer.Typer(no_args_is_help=True, help=group.help)
        for handler in group.handlers:
            group_cli.command()(guarded(handler))

        registry.add_typer(group_cli, name=group.name)

    return registry
