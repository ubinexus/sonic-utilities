import sys
import socket
import json
import click
import syslog
from difflib import get_close_matches
import utilities_common.cli as clicommon
import pytest
from click.testing import CliRunner


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


syslog.openlog(ident="memory_statistics_cli", logoption=syslog.LOG_PID)


@click.group()
@click.pass_context
def cli(ctx):
    """Main entry point for the SONiC CLI."""
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


def validate_command(command, valid_commands):
    match = get_close_matches(command, valid_commands, n=1, cutoff=0.6)
    if match:
        error_msg = f"Error: No such command '{command}'. Did you mean '{match[0]}'?"
        syslog.syslog(syslog.LOG_ERR, error_msg)
        raise click.UsageError(error_msg)
    else:
        error_msg = f"Error: No such command '{command}'."
        syslog.syslog(syslog.LOG_ERR, error_msg)
        raise click.UsageError(error_msg)


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
    request_data = {"type": "system", "metric_name": None, "from": None, "to": None}

    if from_keyword:
        if from_keyword != "from":
            raise click.UsageError("Expected 'from' keyword as the first argument.")
        if to_keyword and to_keyword != "to":
            raise click.UsageError("Expected 'to' keyword before the end time.")
        if select_keyword and select_keyword != "select":
            raise click.UsageError("Expected 'select' keyword before the metric name.")

        request_data["from"] = from_time.strip("'\"")
        if to_time:
            request_data["to"] = to_time.strip("'\"")
        if select_metric:
            request_data["metric_name"] = select_metric.strip("'\"")

    try:
        response = send_data("memory_statistics_command_request_handler", request_data)

        if isinstance(response, Dict2Obj):
            clean_and_print(response.to_dict())
        else:
            error_msg = f"Error: Expected Dict2Obj, but got {type(response)}"
            syslog.syslog(syslog.LOG_ERR, error_msg)
            print(error_msg)

    except Exception as exc:
        error_msg = f"Error: {str(exc)}"
        syslog.syslog(syslog.LOG_ERR, error_msg)
        print(error_msg)


@show.group(name="memory-statistics")
@click.pass_context
def memory_statistics(ctx):
    """Displays memory statistics configuration information."""
    pass


@memory_statistics.command(name="config", short_help="Show the configuration of memory statistics")
@click.pass_context
def config(ctx):
    """Displays the configuration settings for memory statistics."""
    db_connector = ctx.obj.get('db_connector')
    if not db_connector:
        error_msg = "Error: Database connector is not initialized."
        click.echo(error_msg, err=True)
        syslog.syslog(syslog.LOG_ERR, error_msg)
        sys.exit(1)

    try:
        enabled = get_memory_statistics_config("enabled", db_connector)
        retention_time = get_memory_statistics_config("retention_period", db_connector)
        sampling_interval = get_memory_statistics_config("sampling_interval", db_connector)

        enabled_display = format_field_value("enabled", enabled)
        retention_display = format_field_value("retention_period", retention_time)
        sampling_display = format_field_value("sampling_interval", sampling_interval)

        click.echo(f"{'Configuration Field':<30}{'Value'}")
        click.echo("-" * 50)
        click.echo(f"{'Enabled':<30}{enabled_display}")
        click.echo(f"{'Retention Time (days)':<30}{retention_display}")
        click.echo(f"{'Sampling Interval (minutes)':<30}{sampling_display}")

    except Exception as e:
        error_msg = f"Error retrieving configuration: {str(e)}"
        click.echo(error_msg, err=True)
        syslog.syslog(syslog.LOG_ERR, error_msg)
        sys.exit(1)


def clean_and_print(data):
    if isinstance(data, dict):
        memory_stats = data.get("data", "")
        cleaned_output = memory_stats.replace("\n", "\n").strip()
        print(f"Memory Statistics:\n{cleaned_output}")
    else:
        print("Error: Invalid data format.")


def send_data(command, data, quiet=False):
    SERVER_ADDRESS = '/var/run/dbus/memstats.socket'
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        sock.connect(SERVER_ADDRESS)
    except socket.error as msg:
        error_msg = "Could not connect to the server. Please check if the memory stats service is running."
        syslog.syslog(syslog.LOG_ERR, error_msg)
        raise click.Abort(error_msg) from msg
    response = {}
    try:
        request = {"command": command, "data": data}
        sock.sendall(json.dumps(request).encode('utf-8'))
        res = sock.recv(40240).decode('utf-8')

        if res == '':
            sock.close()
            raise click.Abort("No response from the server. Please check the service and try again.")

        jdata = json.loads(res)
        if isinstance(jdata, dict):
            response = Dict2Obj(jdata)
        else:
            raise Exception("Unexpected response format from server")

        if not getattr(response, 'status', True):
            sock.close()
            raise click.Abort(getattr(response, 'msg', 'An error occurred'))

    except Exception as e:
        if quiet:
            sock.close()
            raise click.Abort(str(e))
        click.echo("Error: {}".format(str(e)))
        sock.close()
        sys.exit(1)

    sock.close()
    return response


def get_memory_statistics_config(field_name, db_connector):
    field_value = "Unknown"
    if not db_connector:
        return field_value

    memory_statistics_table = db_connector.get_table("MEMORY_STATISTICS")
    if (memory_statistics_table and
            "memory_statistics" in memory_statistics_table and
            field_name in memory_statistics_table["memory_statistics"]):
        field_value = memory_statistics_table["memory_statistics"][field_name]

    return field_value


def format_field_value(field_name, value):
    if field_name == "enabled":
        return "True" if value.lower() == "true" else "False"
    return value if value != "Unknown" else "Not configured"


# Test Cases

@pytest.fixture
def runner():
    """Fixture to set up the Click test runner."""
    return CliRunner()


def test_memory_stats_valid(runner):
    """Test valid memory-stats command."""
    result = runner.invoke(cli, ['show', 'memory-stats'])
    assert result.exit_code == 0
    assert "Memory Statistics" in result.output


def test_memory_stats_invalid(runner):
    """Test invalid memory-stats command."""
    result = runner.invoke(cli, ['show', 'memory-stats', 'invalid_command'])
    assert result.exit_code != 0
    assert "Error" in result.output


def test_memory_statistics_config(runner):
    """Test the memory-statistics config command."""
    result = runner.invoke(cli, ['show', 'memory-statistics', 'config'])
    assert result.exit_code == 0
    assert "Enabled" in result.output
