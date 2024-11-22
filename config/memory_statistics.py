import click
import syslog
from show.memory_statistics import memory_statistics
from unittest.mock import MagicMock

# Constants for valid ranges
MIN_RETENTION_PERIOD = 1
MAX_RETENTION_PERIOD = 30
MIN_SAMPLING_INTERVAL = 1
MAX_SAMPLING_INTERVAL = 60

# Create a mock_db for testing purposes (remove this when deploying to production)
mock_db = MagicMock()


# Function to set retention period
@memory_statistics.command(name="retention-period", short_help="Configure the retention period for Memory Statistics")
@click.argument('retention_period', metavar='<retention_period>', required=True, type=int)
def memory_statistics_retention_period(retention_period):
    """Set the retention period for Memory Statistics"""

    # Validate retention period range
    if retention_period < MIN_RETENTION_PERIOD or retention_period > MAX_RETENTION_PERIOD:
        click.echo(
            f"Error: Retention period must be between {MIN_RETENTION_PERIOD} and {MAX_RETENTION_PERIOD}.", err=True
        )
        syslog.syslog(
            syslog.LOG_ERR,
            f"Error: Retention period must be between {MIN_RETENTION_PERIOD} and {MAX_RETENTION_PERIOD}."
        )
        return

    # Assuming mock_db.mod_entry is used for storing values in the database
    try:
        # Mock DB interaction (replace with actual logic)
        mock_db.mod_entry("MEMORY_STATISTICS", "memory_statistics", {"retention_period": retention_period})
        click.echo(f"Retention period set to {retention_period} successfully.")
        syslog.syslog(syslog.LOG_INFO, f"Retention period set to {retention_period} successfully.")

        # Add reminder to save configuration
        click.echo("Save SONiC configuration using 'config save' to persist the changes.")
        syslog.syslog(syslog.LOG_INFO, "Save SONiC configuration using 'config save' to persist the changes.")
    except Exception as e:
        click.echo(f"Error setting retention period: {str(e)}", err=True)


# Function to set sampling interval
@memory_statistics.command(name="sampling-interval", short_help="Configure the sampling interval for Memory Statistics")
@click.argument('sampling_interval', metavar='<sampling_interval>', required=True, type=int)
def memory_statistics_sampling_interval(sampling_interval):
    """Set the sampling interval for Memory Statistics"""

    # Validate sampling interval range
    if sampling_interval < MIN_SAMPLING_INTERVAL or sampling_interval > MAX_SAMPLING_INTERVAL:
        click.echo(
            f"Error: Sampling interval must be between {MIN_SAMPLING_INTERVAL} and {MAX_SAMPLING_INTERVAL}.", err=True
        )
        syslog.syslog(
            syslog.LOG_ERR,
            f"Error: Sampling interval must be between {MIN_SAMPLING_INTERVAL} and {MAX_SAMPLING_INTERVAL}."
        )
        return

    try:
        # Mock DB interaction (replace with actual logic)
        mock_db.mod_entry("MEMORY_STATISTICS", "memory_statistics", {"sampling_interval": sampling_interval})
        click.echo(f"Sampling interval set to {sampling_interval} successfully.")
        syslog.syslog(syslog.LOG_INFO, f"Sampling interval set to {sampling_interval} successfully.")

        # Add reminder to save configuration
        click.echo("Save SONiC configuration using 'config save' to persist the changes.")
        syslog.syslog(syslog.LOG_INFO, "Save SONiC configuration using 'config save' to persist the changes.")
    except Exception as e:
        click.echo(f"Error setting sampling interval: {str(e)}", err=True)


# Function to check existence of the memory statistics table
def check_memory_statistics_table_existence(memory_statistics_table):
    """Checks whether the 'MEMORY_STATISTICS' table is configured in Config DB."""
    if not memory_statistics_table:
        click.echo("Unable to retrieve 'MEMORY_STATISTICS' table from Config DB.", err=True)
        return False
    if "memory_statistics" not in memory_statistics_table:
        click.echo("Unable to retrieve key 'memory_statistics' from MEMORY_STATISTICS table.", err=True)
        return False
    return True
