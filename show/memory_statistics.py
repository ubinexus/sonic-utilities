import click
from tabulate import tabulate
import utilities_common.cli as clicommon
from swsscommon.swsscommon import ConfigDBConnector

# 'memory-statistics' group (show memory-statistics ...)
@click.group(cls=clicommon.AliasedGroup, name="memory-statistics")
def memory_statistics():
    """Show memory statistics configuration and logs"""
    pass

# Set `cli` as an alias to `memory_statistics` for test compatibility
cli = memory_statistics

# MockConfigDBConnector class to simulate ConfigDB interactions for testing
class MockConfigDBConnector:
    def __init__(self, data=None):
        # Set initial data for the mock database
        self.data = data if data else {}

    def connect(self):
        # Simulate the connect method without actual DB connection
        pass

    def get_table(self, table_name):
        # Return the simulated table data
        return self.data.get(table_name, {})

def get_memory_statistics_config(field_name, db_connector=None):
    """Fetches the configuration of memory_statistics from `CONFIG_DB`."""
    field_value = "Unknown"
    db_connector = db_connector or ConfigDBConnector()
    db_connector.connect()
    memory_statistics_table = db_connector.get_table("MEMORY_STATISTICS")
    if (memory_statistics_table and
            "memory_statistics" in memory_statistics_table and
            field_name in memory_statistics_table["memory_statistics"]):
        field_value = memory_statistics_table["memory_statistics"][field_name]
    return field_value

@memory_statistics.command(name="config", short_help="Show the configuration of memory statistics")
@click.pass_context
def config(ctx, db_connector=None):
    """Displays the memory statistics configuration."""
    db_connector = db_connector or ConfigDBConnector()
    db_connector.connect()

    admin_mode = "Disabled"
    admin_enabled = get_memory_statistics_config("enabled", db_connector=db_connector)
    if admin_enabled == "true":
        admin_mode = "Enabled"

    click.echo("Memory Statistics administrative mode: {}".format(admin_mode))

    retention_time = get_memory_statistics_config("retention_time", db_connector=db_connector)
    click.echo("Memory Statistics retention time (days): {}".format(retention_time))

    sampling_interval = get_memory_statistics_config("sampling_interval", db_connector=db_connector)
    click.echo("Memory Statistics sampling interval (minutes): {}".format(sampling_interval))

def fetch_memory_statistics(starting_time=None, ending_time=None, select=None, db_connector=None):
    """Fetch memory statistics from the database."""
    db_connector = db_connector or ConfigDBConnector()
    db_connector.connect()
    memory_statistics_table = db_connector.get_table("MEMORY_STATISTICS")
    filtered_statistics = []

    for key, entry in memory_statistics_table.items():
        if (not starting_time or entry.get("time") >= starting_time) and \
           (not ending_time or entry.get("time") <= ending_time):
            filtered_statistics.append(entry)

    return filtered_statistics

@memory_statistics.command(name="logs", short_help="Show memory statistics logs with optional filtering")
@click.argument('starting_time', required=False)
@click.argument('ending_time', required=False)
@click.argument('additional_options', required=False, nargs=-1)
@click.pass_context
def show_memory_statistics_logs(ctx, starting_time, ending_time, additional_options, db_connector=None):
    """Show memory statistics logs with optional filtering by time and select."""
    db_connector = db_connector or ConfigDBConnector()
    db_connector.connect()
    
    memory_statistics = fetch_memory_statistics(starting_time, ending_time, additional_options, db_connector=db_connector)

    if not memory_statistics:
        click.echo("No memory statistics available for the given parameters.")
        return

    headers = ["Time", "Statistic", "Value"]
    table_data = [[entry.get("time"), entry.get("statistic"), entry.get("value")] for entry in memory_statistics]

    click.echo(tabulate(table_data, headers=headers, tablefmt="grid"))

# Example test functions using MockConfigDBConnector
def test_memory_statistics_config():
    # Prepare mock data
    mock_data = {
        "MEMORY_STATISTICS": {
            "memory_statistics": {
                "enabled": "true",
                "retention_time": "10",
                "sampling_interval": "15"
            }
        }
    }
    mock_db = MockConfigDBConnector(data=mock_data)

    # Call the config function with the mock database
    config(db_connector=mock_db)

def test_memory_statistics_logs():
    # Prepare mock data with some example log entries
    mock_data = {
        "MEMORY_STATISTICS": {
            "log1": {"time": "2024-11-04 10:00:00", "statistic": "Usage", "value": "512 MB"},
            "log2": {"time": "2024-11-04 10:05:00", "statistic": "Usage", "value": "514 MB"},
        }
    }
    mock_db = MockConfigDBConnector(data=mock_data)

    # Call the logs function with the mock database
    show_memory_statistics_logs(db_connector=mock_db)