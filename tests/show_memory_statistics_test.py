import sys
import socket
import json
import click
import syslog
from difflib import get_close_matches
import utilities_common.cli as clicommon
import pytest
from click.testing import CliRunner
from unittest.mock import patch


class Dict2Obj:
    """Converts dictionaries or lists into objects with attribute-style access."""

    def __init__(self, d):
        if isinstance(d, dict):
            for key, value in d.items():
                if isinstance(value, (list, tuple)):
                    setattr(self, key, [Dict2Obj(x) if isinstance(x, dict) else x for x in value])
                else:
                    setattr(self, key, Dict2Obj(value) if isinstance(value, dict) else value)
        elif isinstance(d, list):
            self.items = [Dict2Obj(x) if isinstance(x, dict) else x for x in d]
        else:
            raise ValueError("Input should be a dictionary or a list")

    def to_dict(self):
        if hasattr(self, "items"):
            return [x.to_dict() if isinstance(x, Dict2Obj) else x for x in self.items]

        result = {}
        for key, value in self.__dict__.items():
            if isinstance(value, Dict2Obj):
                result[key] = value.to_dict()
            elif isinstance(value, list):
                result[key] = [v.to_dict() if isinstance(v, Dict2Obj) else v for v in value]
            else:
                result[key] = value
        return result

    def __repr__(self):
        return f"<{self.__class__.__name__} {self.to_dict()}>"


# Mock Click group CLI
@click.group()
@click.pass_context
def cli(ctx):
    """Main entry point for the SONiC CLI."""
    print("CLI initialized!")  # Debugging line
    ctx.ensure_object(dict)
    if clicommon:
        try:
            ctx.obj["db_connector"] = clicommon.get_db_connector()
        except AttributeError:
            error_msg = "Error: 'utilities_common.cli' does not have 'get_db_connector' function."
            click.echo(error_msg, err=True)
            syslog.syslog(syslog.LOG_ERR, error_msg)
            sys.exit(1)
    else:
        ctx.obj["db_connector"] = None


@cli.group()
@click.pass_context
def show(ctx):
    """Displays various information about the system."""
    pass


@show.command(name="memory-stats")
@click.argument("from_keyword", required=False)
@click.argument("from_time", required=False)
@click.argument("to_keyword", required=False)
@click.argument("to_time", required=False)
@click.argument("select_keyword", required=False)
@click.argument("select_metric", required=False)
@click.pass_context
def memory_stats(ctx, from_keyword, from_time, to_keyword, to_time, select_keyword, select_metric):
    """Displays memory statistics."""
    if from_keyword and from_keyword != "from":
        raise click.UsageError("Expected 'from' keyword as the first argument.")
    if to_keyword and to_keyword != "to":
        raise click.UsageError("Expected 'to' keyword before the end time.")
    if select_keyword and select_keyword != "select":
        raise click.UsageError("Expected 'select' keyword before the metric name.")
    click.echo("Memory Statistics fetched successfully.")


@show.group(name="memory-statistics")
@click.pass_context
def memory_statistics(ctx):
    """Displays memory statistics configuration information."""
    pass


@memory_statistics.command(name="config", short_help="Show the configuration of memory statistics")
@click.pass_context
def config(ctx):
    """Displays the configuration settings for memory statistics."""
    click.echo("Enabled\nRetention Time (days)\nSampling Interval (minutes)")


@pytest.fixture
def runner():
    """Fixture to set up the Click test runner."""
    return CliRunner()


@patch("utilities_common.cli.get_db_connector", return_value={"dummy_key": "dummy_value"})
def test_memory_stats_valid(mock_get_db_connector, runner):
    """Test valid memory-stats command."""
    result = runner.invoke(
        cli,
        [
            'show', 'memory-stats', 'from', "'2023-11-01'",
            'to', "'2023-11-02'", 'select', "'used_memory'"
        ]
    )
    print(result.output)  # Debugging line to print output
    assert result.exit_code == 0
    assert "CLI initialized!" in result.output
    assert "Memory Statistics fetched successfully." in result.output


@patch("utilities_common.cli.get_db_connector", return_value={"dummy_key": "dummy_value"})
def test_memory_stats_invalid_from_keyword(mock_get_db_connector, runner):
    """Test memory-stats command with invalid 'from' keyword."""
    result = runner.invoke(cli, ['show', 'memory-stats', 'from_invalid', "'2023-11-01'"])
    print(result.output)  # Debugging line to print output
    assert result.exit_code != 0
    assert "UsageError" in result.output or "Expected 'from' keyword as the first argument." in result.output


@patch("utilities_common.cli.get_db_connector", return_value={"dummy_key": "dummy_value"})
def test_memory_statistics_config(mock_get_db_connector, runner):
    """Test the memory-statistics config command."""
    result = runner.invoke(cli, ['show', 'memory-statistics', 'config'])
    print(result.output)  # Debugging line to print output
    assert result.exit_code == 0
    assert "Enabled" in result.output
    assert "Retention Time (days)" in result.output
    assert "Sampling Interval (minutes)" in result.output
