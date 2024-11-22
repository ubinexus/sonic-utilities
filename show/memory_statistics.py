import sys
import socket
import json
import click
import syslog
from click_default_group import DefaultGroup
from difflib import get_close_matches
import utilities_common.cli as clicommon


class Dict2Obj:
    """Converts dictionaries or lists into objects with attribute-style access.
    Recursively transforms dictionaries and lists to allow accessing nested
    structures as attributes. Supports nested dictionaries and lists of dictionaries.
    """

    def __init__(self, d):
        """Initializes the Dict2Obj object.

        Parameters:
            d (dict or list): The dictionary or list to be converted into an object.
        """
        if not isinstance(d, (dict, list)):
            raise ValueError("Input should be a dictionary or a list")

        if isinstance(d, dict):
            for key, value in d.items():
                if isinstance(value, (list, tuple)):
                    setattr(
                        self,
                        key,
                        [Dict2Obj(x) if isinstance(x, dict) else x for x in value],
                    )
                else:
                    setattr(
                        self, key, Dict2Obj(value) if isinstance(value, dict) else value
                    )
        elif isinstance(d, list):
            self.items = [Dict2Obj(x) if isinstance(x, dict) else x for x in d]

    def to_dict(self):
        """Converts the object back to a dictionary format."""
        result = {}
        if hasattr(self, "items"):
            return [x.to_dict() if isinstance(x, Dict2Obj) else x for x in self.items]

        for key in self.__dict__:
            value = getattr(self, key)
            if isinstance(value, Dict2Obj):
                result[key] = value.to_dict()
            elif isinstance(value, list):
                result[key] = [v.to_dict() if isinstance(v, Dict2Obj) else v for v in value]
            else:
                result[key] = value
        return result

    def __repr__(self):
        """Provides a string representation of the object for debugging."""
        return f"<{self.__class__.__name__} {self.to_dict()}>"


syslog.openlog(ident="memory_statistics_cli", logoption=syslog.LOG_PID)


@click.group(cls=DefaultGroup, default="show", default_if_no_args=True)
@click.pass_context
def cli(ctx):
    """Main entry point for the SONiC CLI.

    Parameters:
        ctx (click.Context): The Click context that holds configuration data
        and other CLI-related information.
    """
    ctx.ensure_object(dict)

    if clicommon:
        try:
            ctx.obj["db_connector"] = clicommon.get_db_connector()
        except AttributeError:
            error_msg = (
                "Error: 'utilities_common.cli' does not have 'get_db_connector' function."
            )
            click.echo(error_msg, err=True)
            syslog.syslog(syslog.LOG_ERR, error_msg)
            sys.exit(1)
    else:
        ctx.obj["db_connector"] = None


def validate_command(command, valid_commands):
    """Validates the user's command input against a list of valid commands.

    Parameters:
        command (str): The command entered by the user.
        valid_commands (list): List of valid command strings.

    Raises:
        click.UsageError: If the command is invalid, with suggestions for the closest valid command.
    """
    match = get_close_matches(command, valid_commands, n=1, cutoff=0.6)
    if match:
        error_msg = f"Error: No such command '{command}'. Did you mean '{match[0]}'?"
        syslog.syslog(syslog.LOG_ERR, error_msg)
        raise click.UsageError(error_msg)
    else:
        error_msg = f"Error: No such command '{command}'."
        syslog.syslog(syslog.LOG_ERR, error_msg)
        raise click.UsageError(error_msg)


# ------------------- Integration of show memory-stats Command -------------------


@cli.group()
@click.pass_context
def show(ctx):
    """Displays various information about the system using the 'show' subcommand.

    Parameters:
        ctx (click.Context): The Click context that holds configuration data and other CLI-related information.
    """
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
    """Displays memory statistics.

    Fetches and shows memory statistics based on the provided time range and metric.
    If no time range or metric is specified, defaults are used.

    Parameters:
        ctx (click.Context): The Click context holding configuration and command info.
        from_keyword (str): Expected keyword 'from' indicating the start of the time range.
        from_time (str): The start time for the data retrieval.
        to_keyword (str): Expected keyword 'to' indicating the end of the time range.
        to_time (str): The end time for the data retrieval.
        select_keyword (str): Expected keyword 'select' to indicate a specific metric.
        select_metric (str): The specific metric to retrieve data for.
    """
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


def clean_and_print(data):
    """Formats and prints memory statistics in a user-friendly format.

    If the data is received in a valid format, it extracts the relevant memory
    statistics and prints them. Otherwise, it prints an error message.

    Parameters:
        data (dict): Dictionary containing the memory statistics to display.
    """
    if isinstance(data, dict):
        memory_stats = data.get("data", "")

        cleaned_output = memory_stats.replace("\n", "\n").strip()
        print(f"Memory Statistics:\n{cleaned_output}")
    else:
        print("Error: Invalid data format.")


def send_data(command, data, quiet=False):
    """Sends a command and data to the memory statistics service.
    Connects to the UNIX socket, sends the JSON-encoded command and data,
    and returns the response. If the service is unavailable, it handles the error.

    Parameters:
        command (str): The command name to be sent to the server.
        data (dict): Data payload containing parameters for the command.
        quiet (bool): If True, suppresses output on exceptions.

    Returns:
        response (Dict2Obj): Parsed response from the server.

    Raises:
        click.Abort: If there are issues connecting to the server or receiving data.
    """
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


# ------------------- Integration of show memory-statistics config -------------------


@show.group(name="memory-statistics")
@click.pass_context
def memory_statistics(ctx):
    """Displays memory statistics configuration information."""
    pass


def get_memory_statistics_config(field_name, db_connector):
    """Fetches memory statistics configuration field value.
    Parameters:
        field_name (str): Name of the configuration field to retrieve.
        db_connector: Database connector to fetch data from.
    Returns:
        str: Value of the field or "Unknown" if not found.
    """
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
    """Formats field values for consistent output.
    Parameters:
        field_name (str): The field name.
        value (str): The field value to format.
    Returns:
        str: Human-readable formatted field value.
    """
    if field_name == "enabled":
        return "True" if value.lower() == "true" else "False"
    return value if value != "Unknown" else "Not configured"


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


# --------------------------------------------------------------------------------


def main():
    """Entry point for the CLI application."""
    cli()


if __name__ == '__main__':
    valid_commands = ['show', 'memory-stats', 'memory-statistics']
    user_input = sys.argv[1:]
    if user_input:
        command = user_input[0]
        if command not in valid_commands:
            validate_command(command, valid_commands)
    cli()