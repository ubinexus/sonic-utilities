import os

import click
import utilities_common.cli as clicommon
from swsssdk import ConfigDBConnector


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
            click.echo("Unable to retrieve kdump table from CONFIG_DB.")
            return

        if "config" not in kdump_table:
            click.echo("Unable retrieve key `config` from kdump table.")
            return

        config_db.mod_entry("KDUMP", "config", {"enabled": "false"})


@kdump.command()
def enable():
    """Enable kdump feature"""
    config_db = ConfigDBConnector()
    if config_db:
        config_db.connect()
        kdump_table = config_db.get_table("KDUMP")
        if not kdump_table:
            click.echo("Unable to retrieve kdump table from CONFIG_DB.")
            return

        if "config" not in kdump_table:
            click.echo("Unable retrieve key `config` from kdump table.")
            return

        config_db.mod_entry("KDUMP", "config", {"enabled": "true"})


@kdump.command()
@click.argument('kdump_memory', metavar='<kdump_memory>', required=True)
def memory(kdump_memory):
    """Reserve memory for kdump capture kernel"""
    config_db = ConfigDBConnector()
    if config_db:
        config_db.connect()
        kdump_table = config_db.get_table("KDUMP")
        if not kdump_table:
            click.echo("Unable to retrieve kdump table from CONFIG_DB.")
            return

        if "config" not in kdump_table:
            click.echo("Unable retrieve key `config` from kdump table.")
            return

        config_db.mod_entry("KDUMP", "config", {"memory": kdump_memory})


@kdump.command('num-dumps')
@click.argument('kdump_num_dumps', metavar='<kdump_num_dumps>', required=True, type=int)
def num_dumps(kdump_num_dumps):
    """Set maximum number of dump files for kdump"""
    config_db = ConfigDBConnector()
    if config_db:
        config_db.connect()
        kdump_table = config_db.get_table("KDUMP")
        if not kdump_table:
            click.echo("Unable to retrieve kdump table from CONFIG_DB.")
            return

        if "config" not in kdump_table:
            click.echo("Unable retrieve key `config` from kdump table.")
            return

        config_db.mod_entry("KDUMP", "config", {"num_dumps": kdump_num_dumps})
