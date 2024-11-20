import sys
import socket
import json
import click
import syslog
import utilities_common.cli as clicommon
import pytest
from click.testing import CliRunner
from your_module import Dict2Obj  # Make sure Dict2Obj is imported correctly

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

def send_data(command, data, quiet=False):
    """Function to send data to the server."""
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
    """Fetch memory statistics configuration from the database."""
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
    """Format field values for display."""
    if field_name == "enabled":
        return "True" if value.lower() == "true" else "False"
    return value if value != "Unknown" else "Not configured"


def clean_and_print(data):
    """Clean and print memory statistics data."""
    if isinstance(data, dict):
        memory_stats = data.get("data", "")
        cleaned_output = memory_stats.replace("\n", "\n").strip()
        print(f"Memory Statistics:\n{cleaned_output}")
    else:
        print("Error: Invalid data format.")


@click.group()
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
