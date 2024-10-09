import click
import os
import sys
from swsscommon.swsscommon import ConfigDBConnector


# Simulate the AbbreviationGroup from utilities_common.cli
class AbbreviationGroup(click.Group):
    def get_command(self, ctx, cmd_name):
        # Fallback to default command if abbreviation not found
        return super().get_command(ctx, cmd_name)



#
# 'memory-stats' group ('sudo config memory-stats ...')
#
@click.group(cls=AbbreviationGroup, name="memory-stats")
def memory_stats():
    """Configure the Memory Statistics feature"""
    pass


def check_memory_stats_table_existence(memory_stats_table):
    """Checks whether the 'MEMORY_STATISTICS' table is configured in Config DB."""
    if not memory_stats_table:
        click.echo("Unable to retrieve 'MEMORY_STATISTICS' table from Config DB.")
        sys.exit(1)

    if "memory_statistics" not in memory_stats_table:
        click.echo("Unable to retrieve key 'memory_statistics' from MEMORY_STATISTICS table.")
        sys.exit(2)


#
# 'enable' command ('sudo config memory-stats enable')
#
@memory_stats.command(name="enable", short_help="Enable the Memory Statistics feature")
def memory_stats_enable():
    """Enable the Memory Statistics feature"""
    db = ConfigDBConnector()
    db.connect()

    memory_stats_table = db.get_table("MEMORY_STATISTICS")
    check_memory_stats_table_existence(memory_stats_table)

    # Set enabled to true and disabled to false
    db.mod_entry("MEMORY_STATISTICS", "memory_statistics", {"enabled": "true", "disabled": "false"})
    click.echo("Memory Statistics feature enabled.")
    click.echo("Save SONiC configuration using 'config save' to persist the changes.")


#
# 'disable' command ('sudo config memory-stats disable')
#
@memory_stats.command(name="disable", short_help="Disable the Memory Statistics feature")
def memory_stats_disable():
    """Disable the Memory Statistics feature"""
    db = ConfigDBConnector()
    db.connect()

    memory_stats_table = db.get_table("MEMORY_STATISTICS")
    check_memory_stats_table_existence(memory_stats_table)

    # Set enabled to false and disabled to true
    db.mod_entry("MEMORY_STATISTICS", "memory_statistics", {"enabled": "false", "disabled": "true"})
    click.echo("Memory Statistics feature disabled.")
    click.echo("Save SONiC configuration using 'config save' to persist the changes.")


#
# 'retention-period' command ('sudo config memory-stats retention-period ...')
#
@memory_stats.command(name="retention-period", short_help="Configure the retention period for Memory Statistics")
@click.argument('retention_period', metavar='<retention_period>', required=True, type=int)
def memory_stats_retention_period(retention_period):
    """Set the retention period for Memory Statistics"""
    db = ConfigDBConnector()
    db.connect()


    memory_stats_table = db.get_table("MEMORY_STATISTICS")
    check_memory_stats_table_existence(memory_stats_table)

    db.mod_entry("MEMORY_STATISTICS", "memory_statistics", {"retention_time": retention_period})
    click.echo(f"Memory Statistics retention period set to {retention_period} days.")
    click.echo("Save SONiC configuration using 'config save' to persist the changes.")


#
# 'sampling-interval' command ('sudo config memory-stats sampling-interval ...')
#
@memory_stats.command(name="sampling-interval", short_help="Configure the sampling interval for Memory Statistics")
@click.argument('sampling_interval', metavar='<sampling_interval>', required=True, type=int)
def memory_stats_sampling_interval(sampling_interval):
    """Set the sampling interval for Memory Statistics"""
    db = ConfigDBConnector()
    db.connect()

    memory_stats_table = db.get_table("MEMORY_STATISTICS")
    check_memory_stats_table_existence(memory_stats_table)

    db.mod_entry("MEMORY_STATISTICS", "memory_statistics", {"sampling_interval": sampling_interval})
    click.echo(f"Memory Statistics sampling interval set to {sampling_interval} minutes.")
    click.echo("Save SONiC configuration using 'config save' to persist the changes.")


if __name__ == "__main__":
    memory_stats()