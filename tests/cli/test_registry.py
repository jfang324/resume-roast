"""Group-level behavior the subcommand registry gives every command group."""

import pytest
from typer.testing import CliRunner

from resume_roast.cli.registry import build_subcommand_registry

app = build_subcommand_registry()
runner = CliRunner()


@pytest.mark.parametrize(
    ("group", "subcommands"),
    [
        ("config", ("credentials", "settings")),
        ("show", ("credentials", "settings")),
    ],
)
def test_a_bare_group_prints_its_help(group: str, subcommands: tuple[str, ...]) -> None:
    result = runner.invoke(app, [group])

    # no_args_is_help prints help and exits with Click's usage-error code (2),
    # not 0 — this isn't the same code path as an explicit `--help`.
    assert result.exit_code == 2
    for name in subcommands:
        assert name in result.output
