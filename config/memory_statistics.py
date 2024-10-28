import click
from swsscommon.swsscommon import ConfigDBConnector


class AbbreviationGroup(click.Group):
    def get_command(self, ctx, cmd_name):
        return super().get_command(ctx, cmd_name)


@click.group(cls=AbbreviationGroup, name="memory-statistics")
def memory_statistics():
    """Configure the Memory Statistics feature"""
    pass


def check_memory_statistics_table_existence(memory_statistics_table):
    """Checks whether the 'MEMORY_STATISTICS' table is configured in Config DB."""
    if not memory_statistics_table:
        raise RuntimeError("Unable to retrieve 'MEMORY_STATISTICS' table from Config DB.")

    if "memory_statistics" not in memory_statistics_table:
        raise RuntimeError("Unable to retrieve key 'memory_statistics' from MEMORY_STATISTICS table.")


def get_memory_statistics_table(db):
    """Get the MEMORY_STATISTICS table from the database."""
    return db.get_table("MEMORY_STATISTICS")


@memory_statistics.command(name="enable", short_help="Enable the Memory Statistics feature")
def memory_statistics_enable():
    """Enable the Memory Statistics feature"""
    db = ConfigDBConnector()
    db.connect()

    memory_statistics_table = get_memory_statistics_table(db)
    check_memory_statistics_table_existence(memory_statistics_table)

    db.mod_entry("MEMORY_STATISTICS", "memory_statistics", {"enabled": "true", "disabled": "false"})
    click.echo("Memory Statistics feature enabled.")
    click.echo("Save SONiC configuration using 'config save' to persist the changes.")


@memory_statistics.command(name="disable", short_help="Disable the Memory Statistics feature")
def memory_statistics_disable():
    """Disable the Memory Statistics feature"""
    db = ConfigDBConnector()
    db.connect()

    memory_statistics_table = get_memory_statistics_table(db)
    check_memory_statistics_table_existence(memory_statistics_table)

    db.mod_entry("MEMORY_STATISTICS", "memory_statistics", {"enabled": "false", "disabled": "true"})
    click.echo("Memory Statistics feature disabled.")
    click.echo("Save SONiC configuration using 'config save' to persist the changes.")


@memory_statistics.command(name="retention-period", short_help="Configure the retention period for Memory Statistics")
@click.argument('retention_period', metavar='<retention_period>', required=True, type=int)
def memory_statistics_retention_period(retention_period):
    """Set the retention period for Memory Statistics"""
    db = ConfigDBConnector()
    db.connect()

    memory_statistics_table = get_memory_statistics_table(db)
    check_memory_statistics_table_existence(memory_statistics_table)

    db.mod_entry("MEMORY_STATISTICS", "memory_statistics", {"retention_time": retention_period})
    click.echo(f"Memory Statistics retention period set to {retention_period} days.")
    click.echo("Save SONiC configuration using 'config save' to persist the changes.")


@memory_statistics.command(name="sampling-interval", short_help="Configure the sampling interval for Memory Statistics")
@click.argument('sampling_interval', metavar='<sampling_interval>', required=True, type=int)
def memory_statistics_sampling_interval(sampling_interval):
    """Set the sampling interval for Memory Statistics"""
    db = ConfigDBConnector()
    db.connect()

    memory_statistics_table = get_memory_statistics_table(db)
    check_memory_statistics_table_existence(memory_statistics_table)

    db.mod_entry("MEMORY_STATISTICS", "memory_statistics", {"sampling_interval": sampling_interval})
    click.echo(f"Memory Statistics sampling interval set to {sampling_interval} minutes.")
    click.echo("Save SONiC configuration using 'config save' to persist the changes.")


if __name__ == "__main__":
    memory_statistics()
