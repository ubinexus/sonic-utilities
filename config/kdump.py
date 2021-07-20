import sys

import click
import utilities_common.cli as clicommon
from swsscommon.swsscommon import ConfigDBConnector


@click.group(cls=clicommon.AbbreviationGroup, name="kdump")
def kdump():
    """Modify configuration of kdump"""
    pass


@kdump.command()
def disable():
    """Disable kdump feature"""
    config_db = ConfigDBConnector()
    if config_db:
        config_db.connect()
        kdump_table = config_db.get_table("KDUMP")
        if not kdump_table:
            click.echo("Unable to retrieve KDUMP table from CONFIG DB.")
            sys.exit(1)

        if "config" not in kdump_table:
            click.echo("Unable to retrieve key 'config' from KDUMP table.")
            sys.exit(2)

        config_db.mod_entry("KDUMP", "config", {"enabled": "false"})
    else:
        click.echo("Unable to get an instance of 'ConfigDBConnector'.")
        sys.exit(3)


@kdump.command()
def enable():
    """Enable kdump feature"""
    config_db = ConfigDBConnector()
    if config_db:
        config_db.connect()
        kdump_table = config_db.get_table("KDUMP")
        if not kdump_table:
            click.echo("Unable to retrieve KDUMP table from CONFIG DB.")
            sys.exit(4)

        if "config" not in kdump_table:
            click.echo("Unable to retrieve key 'config' from KDUMP table.")
            sys.exit(5)

        config_db.mod_entry("KDUMP", "config", {"enabled": "true"})
    else:
        click.echo("Unable to get an instance of 'ConfigDBConnector'.")
        sys.exit(6)


@kdump.command()
@click.argument('kdump_memory', metavar='<kdump_memory>', required=True)
def memory(kdump_memory):
    """Reserve memory for kdump capture kernel"""
    config_db = ConfigDBConnector()
    if config_db:
        config_db.connect()
        kdump_table = config_db.get_table("KDUMP")
        if not kdump_table:
            click.echo("Unable to retrieve KDUMP table from CONFIG DB.")
            sys.exit(7)

        if "config" not in kdump_table:
            click.echo("Unable to retrieve key 'config' from KDUMP table.")
            sys.exit(8)

        config_db.mod_entry("KDUMP", "config", {"memory": kdump_memory})
    else:
        click.echo("Unable to get an instance of 'ConfigDBConnector'.")
        sys.exit(9)


@kdump.command('num-dumps')
@click.argument('kdump_num_dumps', metavar='<kdump_num_dumps>', required=True, type=int)
def num_dumps(kdump_num_dumps):
    """Set maximum number of dump files for kdump"""
    config_db = ConfigDBConnector()
    if config_db:
        config_db.connect()
        kdump_table = config_db.get_table("KDUMP")
        if not kdump_table:
            click.echo("Unable to retrieve KDUMP table from CONFIG DB.")
            sys.exit(10)

        if "config" not in kdump_table:
            click.echo("Unable to retrieve key 'config' from KDUMP table.")
            sys.exit(11)

        config_db.mod_entry("KDUMP", "config", {"num_dumps": kdump_num_dumps})
    else:
        click.echo("Unable to get an instance of 'ConfigDBConnector'.")
        sys.exit(12)
