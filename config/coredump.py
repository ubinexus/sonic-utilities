import os
import click
import utilities_common.cli as clicommon
from swsssdk import ConfigDBConnector

@click.group(cls=clicommon.AbbreviationGroup, name="coredump")
def coredump():
    """ Configure coredump """
    if os.geteuid() != 0:
        exit("Root privileges are required for this operation")

@coredump.command()
@click.argument('disable', required=False)
def disable(disable):
    """Administratively Disable coredump generation"""
    config_db = ConfigDBConnector()
    config_db.connect()
    table = "COREDUMP"
    key = "config"
    config_db.set_entry(table, key, {"enabled": "false"})

@coredump.command()
@click.argument('enable', required=False)
def enable(enable):
    """Administratively Enable coredump generation"""
    config_db = ConfigDBConnector()
    config_db.connect()
    table = "COREDUMP"
    key = "config"
    config_db.set_entry(table, key, {"enabled": "true"})
