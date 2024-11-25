# import click
# import syslog
# from show.memory_statistics import memory_statistics
# from unittest.mock import MagicMock

# # Constants for valid ranges
# MIN_RETENTION_PERIOD = 1
# MAX_RETENTION_PERIOD = 30
# MIN_SAMPLING_INTERVAL = 1
# MAX_SAMPLING_INTERVAL = 60

# # Create a mock_db for testing purposes (remove this when deploying to production)
# mock_db = MagicMock()


# # Function to set retention period
# @memory_statistics.command(name="retention-period", short_help="Configure the retention period for Memory Statistics")
# @click.argument('retention_period', metavar='<retention_period>', required=True, type=int)
# def memory_statistics_retention_period(retention_period):
#     """Set the retention period for Memory Statistics"""

#     # Validate retention period range
#     if retention_period < MIN_RETENTION_PERIOD or retention_period > MAX_RETENTION_PERIOD:
#         click.echo(
#             f"Error: Retention period must be between {MIN_RETENTION_PERIOD} and {MAX_RETENTION_PERIOD}.", err=True
#         )
#         syslog.syslog(
#             syslog.LOG_ERR,
#             f"Error: Retention period must be between {MIN_RETENTION_PERIOD} and {MAX_RETENTION_PERIOD}."
#         )
#         return

#     # Assuming mock_db.mod_entry is used for storing values in the database
#     try:
#         mock_db.mod_entry("MEMORY_STATISTICS", "memory_statistics", {"retention_period": retention_period})
#         click.echo(f"Retention period set to {retention_period} successfully.")
#         syslog.syslog(syslog.LOG_INFO, f"Retention period set to {retention_period} successfully.")

#         # Add reminder to save configuration
#         click.echo("Save SONiC configuration using 'config save' to persist the changes.")
#         syslog.syslog(syslog.LOG_INFO, "Save SONiC configuration using 'config save' to persist the changes.")
#     except Exception as e:
#         click.echo(f"Error setting retention period: {str(e)}", err=True)


# # Function to set sampling interval
# @memory_statistics.command(name="sampling-interval",
# short_help="Configure the sampling interval for Memory Statistics")
# @click.argument('sampling_interval', metavar='<sampling_interval>', required=True, type=int)
# def memory_statistics_sampling_interval(sampling_interval):
#     """Set the sampling interval for Memory Statistics"""

#     # Validate sampling interval range
#     if sampling_interval < MIN_SAMPLING_INTERVAL or sampling_interval > MAX_SAMPLING_INTERVAL:
#         click.echo(
#             f"Error: Sampling interval must be between {MIN_SAMPLING_INTERVAL} and {MAX_SAMPLING_INTERVAL}.", err=True
#         )
#         syslog.syslog(
#             syslog.LOG_ERR,
#             f"Error: Sampling interval must be between {MIN_SAMPLING_INTERVAL} and {MAX_SAMPLING_INTERVAL}."
#         )
#         return

#     try:
#         mock_db.mod_entry("MEMORY_STATISTICS", "memory_statistics", {"sampling_interval": sampling_interval})
#         click.echo(f"Sampling interval set to {sampling_interval} successfully.")
#         syslog.syslog(syslog.LOG_INFO, f"Sampling interval set to {sampling_interval} successfully.")

#         # Add reminder to save configuration
#         click.echo("Save SONiC configuration using 'config save' to persist the changes.")
#         syslog.syslog(syslog.LOG_INFO, "Save SONiC configuration using 'config save' to persist the changes.")
#     except Exception as e:
#         click.echo(f"Error setting sampling interval: {str(e)}", err=True)


# # Function to check existence of the memory statistics table
# def check_memory_statistics_table_existence(memory_statistics_table):
#     """Checks whether the 'MEMORY_STATISTICS' table is configured in Config DB."""
#     if not memory_statistics_table:
#         click.echo("Unable to retrieve 'MEMORY_STATISTICS' table from Config DB.", err=True)
#         return False
#     if "memory_statistics" not in memory_statistics_table:
#         click.echo("Unable to retrieve key 'memory_statistics' from MEMORY_STATISTICS table.", err=True)
#         return False
#     return True

import click
import syslog
from swsscommon.swsscommon import ConfigDBConnector

# Default values
DEFAULT_SAMPLING_INTERVAL = 5
DEFAULT_RETENTION_PERIOD = 15


def log_to_syslog(message, level=syslog.LOG_INFO):
    """Log a message to syslog."""
    syslog.openlog("memory_statistics", syslog.LOG_PID | syslog.LOG_CONS, syslog.LOG_USER)
    syslog.syslog(level, message)


def update_memory_statistics_status(status, db):
    """Updates the status of the memory statistics feature in the config DB."""
    try:
        db.mod_entry("MEMORY_STATISTICS", "memory_statistics", {"enabled": status})
        msg = f"Memory statistics feature {'enabled' if status == 'true' else 'disabled'} successfully."
        click.echo(msg)
        log_to_syslog(msg)  # Log to syslog
        return True, None  # Success: return True and no error
    except Exception as e:
        error_msg = f"Error updating memory statistics status: {e}"
        click.echo(error_msg, err=True)
        log_to_syslog(error_msg, syslog.LOG_ERR)  # Log error to syslog
        return False, error_msg  # Failure: return False and the error message


@click.command()
def memory_statistics_enable():
    """Enable memory statistics."""
    db = ConfigDBConnector()
    db.connect()
    success, error = update_memory_statistics_status("true", db)
    if not success:
        click.echo(error, err=True)  # Handle error if unsuccessful
    else:
        success_msg = "Memory statistics enabled successfully."
        click.echo(success_msg)
        log_to_syslog(success_msg)  # Log to syslog
        reminder_msg = "Reminder: Please run 'config save' to persist changes."
        click.echo(reminder_msg)
        log_to_syslog(reminder_msg)  # Log to syslog


@click.command()
def memory_statistics_disable():
    """Disable memory statistics."""
    db = ConfigDBConnector()
    db.connect()
    success, error = update_memory_statistics_status("false", db)
    if not success:
        click.echo(error, err=True)  # Handle error if unsuccessful
    else:
        success_msg = "Memory statistics disabled successfully."
        click.echo(success_msg)
        log_to_syslog(success_msg)  # Log to syslog
        reminder_msg = "Reminder: Please run 'config save' to persist changes."
        click.echo(reminder_msg)
        log_to_syslog(reminder_msg)  # Log to syslog


@click.command()
@click.argument("retention_period", type=int, required=False, default=DEFAULT_RETENTION_PERIOD)
def memory_statistics_retention_period(retention_period):
    """Set retention period for memory statistics."""
    if not (1 <= retention_period <= 30):
        error_msg = "Error: Retention period must be between 1 and 30."
        click.echo(error_msg, err=True)
        log_to_syslog(error_msg, syslog.LOG_ERR)  # Log error to syslog
        return

    db = ConfigDBConnector()
    db.connect()
    try:
        db.mod_entry("MEMORY_STATISTICS", "memory_statistics", {"retention_period": retention_period})
        success_msg = f"Retention period set to {retention_period} successfully."
        click.echo(success_msg)
        log_to_syslog(success_msg)  # Log to syslog
    except Exception as e:
        error_msg = f"Error setting retention period: {e}"
        click.echo(error_msg, err=True)
        log_to_syslog(error_msg, syslog.LOG_ERR)  # Log error to syslog


@click.command()
@click.argument("sampling_interval", type=int, required=False, default=DEFAULT_SAMPLING_INTERVAL)
def memory_statistics_sampling_interval(sampling_interval):
    """Set sampling interval for memory statistics."""
    if not (3 <= sampling_interval <= 15):
        error_msg = "Error: Sampling interval must be between 3 and 15."
        click.echo(error_msg, err=True)
        log_to_syslog(error_msg, syslog.LOG_ERR)  # Log error to syslog
        return

    db = ConfigDBConnector()
    db.connect()
    try:
        db.mod_entry("MEMORY_STATISTICS", "memory_statistics", {"sampling_interval": sampling_interval})
        success_msg = f"Sampling interval set to {sampling_interval} successfully."
        click.echo(success_msg)
        log_to_syslog(success_msg)  # Log to syslog
    except Exception as e:
        error_msg = f"Error setting sampling interval: {e}"
        click.echo(error_msg, err=True)
        log_to_syslog(error_msg, syslog.LOG_ERR)  # Log error to syslog


def get_memory_statistics_table(db):
    """Retrieve MEMORY_STATISTICS table from config DB."""
    return db.get_table("MEMORY_STATISTICS")


def check_memory_statistics_table_existence(table):
    """Check if MEMORY_STATISTICS table exists in the given table."""
    return "memory_statistics" in table
