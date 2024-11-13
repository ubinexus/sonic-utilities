import click
from swsscommon.swsscommon import ConfigDBConnector

# Default values
DEFAULT_SAMPLING_INTERVAL = 5
DEFAULT_RETENTION_PERIOD = 15

def update_memory_statistics_status(status, db):
    """Updates the status of the memory statistics feature in the config DB."""
    try:
        db.mod_entry("MEMORY_STATISTICS", "memory_statistics", {"enabled": status})
        click.echo(f"Memory statistics feature {'enabled' if status == 'true' else 'disabled'} successfully.")
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


@click.command()
def memory_statistics_disable():
    """Disable memory statistics."""
    db = ConfigDBConnector()
    db.connect()
    success, error = update_memory_statistics_status("false", db)
    if not success:
        click.echo(error, err=True)  # Handle error if unsuccessful


@click.command()
@click.argument("retention_period", type=int, required=False, default=DEFAULT_RETENTION_PERIOD)
def memory_statistics_retention_period(retention_period):
    """Set retention period for memory statistics."""
    if not (1 <= retention_period <= 30):
        click.echo("Error: Retention period must be between 1 and 30.", err=True)
        return False, "Invalid retention period value"
    
    db = ConfigDBConnector()
    db.connect()
    try:
        db.mod_entry("MEMORY_STATISTICS", "memory_statistics", {"retention_period": retention_period})
        click.echo(f"Retention period set to {retention_period} successfully.")
        return True, None  # Success: return True and no error
    except Exception as e:
        return False, f"Error setting retention period: {e}"  # Failure: return False and the error message


@click.command()
@click.argument("sampling_interval", type=int, required=False, default=DEFAULT_SAMPLING_INTERVAL)
def memory_statistics_sampling_interval(sampling_interval):
    """Set sampling interval for memory statistics."""
    if not (3 <= sampling_interval <= 15):
        click.echo("Error: Sampling interval must be between 3 and 15.", err=True)
        return False, "Invalid sampling interval value"
    
    db = ConfigDBConnector()
    db.connect()
    try:
        db.mod_entry("MEMORY_STATISTICS", "memory_statistics", {"sampling_interval": sampling_interval})
        click.echo(f"Sampling interval set to {sampling_interval} successfully.")
        return True, None  # Success: return True and no error
    except Exception as e:
        return False, f"Error setting sampling interval: {e}"  # Failure: return False and the error message


def get_memory_statistics_table(db):
    """Retrieve MEMORY_STATISTICS table from config DB."""
    return db.get_table("MEMORY_STATISTICS")


def check_memory_statistics_table_existence(table):
    """Check if MEMORY_STATISTICS table exists in the given table."""
    return "memory_statistics" in table
