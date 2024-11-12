# config/memory_statistics.py
import click
from utilities_common.cli import AbbreviationGroup
from swsssdk import ConfigDBConnector


def update_memory_statistics_status(status, db):
    """Helper function to update the status of the Memory Statistics feature."""
    try:
        db.mod_entry("MEMORY_STATISTICS", "memory_statistics", {
            "enabled": status
        })
        click.echo(f"Memory Statistics feature {'enabled' if status == 'true' else 'disabled'} successfully.")
    except Exception as e:
        click.echo(f"Error {'enabling' if status == 'true' else 'disabling'} Memory Statistics feature: {e}", err=True)


@click.command()
def memory_statistics_enable():
    """Enable the Memory Statistics feature."""
    db = ConfigDBConnector()
    db.connect()
    update_memory_statistics_status("true", db)


@click.command()
def memory_statistics_disable():
    """Disable the Memory Statistics feature."""
    db = ConfigDBConnector()
    db.connect()
    update_memory_statistics_status("false", db)


@click.command()
@click.argument("retention_period", type=int)
def memory_statistics_retention_period(retention_period):
    """Set the retention period for Memory Statistics."""
    db = ConfigDBConnector()
    db.connect()
    try:
        db.mod_entry("MEMORY_STATISTICS", "memory_statistics", {
            "retention_period": retention_period
        })
        click.echo(f"Retention period set to {retention_period} successfully.")
    except Exception as e:
        click.echo(f"Error setting retention period: {e}", err=True)


@click.command()
@click.argument("sampling_interval", type=int)
def memory_statistics_sampling_interval(sampling_interval):
    """Set the sampling interval for Memory Statistics."""
    db = ConfigDBConnector()
    db.connect()
    try:
        db.mod_entry("MEMORY_STATISTICS", "memory_statistics", {
            "sampling_interval": sampling_interval
        })
        click.echo(f"Sampling interval set to {sampling_interval} successfully.")
    except Exception as e:
        click.echo(f"Error setting sampling interval: {e}", err=True)


def check_memory_statistics_table_existence(table):
    """Check if the MEMORY_STATISTICS table exists and contains memory_statistics key."""
    if "memory_statistics" in table:
        return True
    click.echo("Unable to retrieve key 'memory_statistics' from MEMORY_STATISTICS table.", err=True)
    return False


def get_memory_statistics_table(db):
    """Retrieve the MEMORY_STATISTICS table from ConfigDB."""
    return db.get_table("MEMORY_STATISTICS")
