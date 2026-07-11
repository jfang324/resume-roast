"""Entry point for the console script and `python -m resume_roast`."""

from resume_roast.cli.registry import build_subcommand_registry


def main() -> None:
    """Build the subcommand registry and run it."""
    registry = build_subcommand_registry()
    registry()


if __name__ == "__main__":
    main()
