import click
from sonic_py_common import ConfigDBConnector


def update_memory_statistics_status(status, db):
    """Updates the status of the memory statistics feature in the config DB."""
    db.mod_entry("MEMORY_STATISTICS", "memory_statistics", {"enabled": status})
    click.echo(f"Memory statistics feature {'enabled' if status == 'true' else 'disabled'} successfully.")


@click.command()
def memory_statistics_enable():
    """Enable memory statistics."""
    db = ConfigDBConnector()
    db.connect()
    update_memory_statistics_status("true", db)


@click.command()
def memory_statistics_disable():
    """Disable memory statistics."""
    db = ConfigDBConnector()
    db.connect()
    update_memory_statistics_status("false", db)


@click.command()
@click.argument("retention_period", type=int)
def memory_statistics_retention_period(retention_period):
    """Set retention period for memory statistics."""
    db = ConfigDBConnector()
    db.connect()
    try:
        db.mod_entry("MEMORY_STATISTICS", "memory_statistics", {"retention_period": retention_period})
        click.echo(f"Retention period set to {retention_period} successfully.")
    except Exception as e:
        click.echo(f"Error setting retention period: {e}", err=True)


@click.command()
@click.argument("sampling_interval", type=int)
def memory_statistics_sampling_interval(sampling_interval):
    """Set sampling interval for memory statistics."""
    db = ConfigDBConnector()
    db.connect()
    try:
        db.mod_entry("MEMORY_STATISTICS", "memory_statistics", {"sampling_interval": sampling_interval})
        click.echo(f"Sampling interval set to {sampling_interval} successfully.")
    except Exception as e:
        click.echo(f"Error setting sampling interval: {e}", err=True)


def get_memory_statistics_table(db):
    """Retrieve MEMORY_STATISTICS table from config DB."""
    return db.get_table("MEMORY_STATISTICS")


def check_memory_statistics_table_existence(table):
    """Check if MEMORY_STATISTICS table exists in the given table."""
    return "memory_statistics" in table
