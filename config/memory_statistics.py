import click
from swsscommon.swsscommon import ConfigDBConnector
import syslog

# Default values
DEFAULT_SAMPLING_INTERVAL = 5
DEFAULT_RETENTION_PERIOD = 15
MIN_SAMPLING_INTERVAL = 3
MAX_SAMPLING_INTERVAL = 15
MIN_RETENTION_PERIOD = 1
MAX_RETENTION_PERIOD = 30
MEMORY_STATISTICS_TABLE = "MEMORY_STATISTICS"

def update_memory_statistics_status(status, db):
    """Updates the status of the memory statistics feature in the config DB."""
    try:
        db.mod_entry(MEMORY_STATISTICS_TABLE, "memory_statistics", {"enabled": status})
        click.echo(f"Memory statistics feature {'enabled' if status == 'true' else 'disabled'} successfully.")
        syslog.syslog(
            syslog.LOG_INFO,
            f"Memory statistics feature {'enabled' if status == 'true' else 'disabled'} successfully."
        )
        return True, None  # Success: return True and no error
    except Exception as e:
        return False, f"Error updating memory statistics status: {e}"  # Failure: return False and the error message


@click.command()
def memory_statistics_enable():
    """Enable memory statistics."""
    db = ConfigDBConnector()
    db.connect()
    success, error = update_memory_statistics_status("true", db)
    if not success:
        click.echo(error, err=True)  # Handle error if unsuccessful
        syslog.syslog(syslog.LOG_ERR, error)
    else:
        click.echo("Memory statistics enabled successfully.")
        syslog.syslog(syslog.LOG_INFO, "Memory statistics enabled successfully.")
        click.echo("Save SONiC configuration using 'config save' to persist the changes.")


@click.command()
def memory_statistics_disable():
    """Disable memory statistics."""
    db = ConfigDBConnector()
    db.connect()
    success, error = update_memory_statistics_status("false", db)
    if not success:
        click.echo(error, err=True)  # Handle error if unsuccessful
        syslog.syslog(syslog.LOG_ERR, error)
    else:
        click.echo("Memory statistics disabled successfully.")
        syslog.syslog(syslog.LOG_INFO, "Memory statistics disabled successfully.")
        click.echo("Save SONiC configuration using 'config save' to persist the changes.")


@click.command()
@click.argument("retention_period", type=int, required=True)
def memory_statistics_retention_period(retention_period):
    """Set the retention period for Memory Statistics."""
    if not (MIN_RETENTION_PERIOD <= retention_period <= MAX_RETENTION_PERIOD):
        click.echo(f"Error: Retention period must be between {MIN_RETENTION_PERIOD} and {MAX_RETENTION_PERIOD}.", err=True)
        syslog.syslog(syslog.LOG_ERR, f"Error: Retention period must be between {MIN_RETENTION_PERIOD} and {MAX_RETENTION_PERIOD}.")
        return

    db = ConfigDBConnector()
    db.connect()
    try:
        db.mod_entry(MEMORY_STATISTICS_TABLE, "memory_statistics", {"retention_period": retention_period})
        click.echo(f"Retention period set to {retention_period} successfully.")
        syslog.syslog(syslog.LOG_INFO, f"Retention period set to {retention_period} successfully.")
        click.echo("Save SONiC configuration using 'config save' to persist the changes.")
    except Exception as e:
        click.echo(f"Error setting retention period: {e}", err=True)
        syslog.syslog(syslog.LOG_ERR, f"Error setting retention period: {e}")


@click.command()
@click.argument("sampling_interval", type=int, required=True)
def memory_statistics_sampling_interval(sampling_interval):
    """Set the sampling interval for Memory Statistics."""
    if not (MIN_SAMPLING_INTERVAL <= sampling_interval <= MAX_SAMPLING_INTERVAL):
        click.echo(f"Error: Sampling interval must be between {MIN_SAMPLING_INTERVAL} and {MAX_SAMPLING_INTERVAL}.", err=True)
        syslog.syslog(syslog.LOG_ERR, f"Error: Sampling interval must be between {MIN_SAMPLING_INTERVAL} and {MAX_SAMPLING_INTERVAL}.")
        return

    db = ConfigDBConnector()
    db.connect()
    try:
        db.mod_entry(MEMORY_STATISTICS_TABLE, "memory_statistics", {"sampling_interval": sampling_interval})
        click.echo(f"Sampling interval set to {sampling_interval} successfully.")
        syslog.syslog(syslog.LOG_INFO, f"Sampling interval set to {sampling_interval} successfully.")
        click.echo("Save SONiC configuration using 'config save' to persist the changes.")
    except Exception as e:
        click.echo(f"Error setting sampling interval: {e}", err=True)
        syslog.syslog(syslog.LOG_ERR, f"Error setting sampling interval: {e}")


def get_memory_statistics_table(db):
    """Retrieve MEMORY_STATISTICS table from config DB."""
    return db.get_table(MEMORY_STATISTICS_TABLE)


def check_memory_statistics_table_existence(table):
    """Check if MEMORY_STATISTICS table exists in the given table."""
    if MEMORY_STATISTICS_TABLE not in table:
        click.echo(f"Unable to retrieve '{MEMORY_STATISTICS_TABLE}' table from Config DB.", err=True)
        return False
    return True
