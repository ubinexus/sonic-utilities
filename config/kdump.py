import sys

import click
from utilities_common.cli import AbbreviationGroup, pass_db


#
# 'kdump' group ('sudo config kdump ...')
#
@click.group(cls=AbbreviationGroup, name="kdump")
def kdump():
    """Configure the KDUMP mechanism"""
    pass


def check_kdump_table_existence(kdump_table):
    """Checks whether the 'KDUMP' table is configured in Config DB.

    Args:
      kdump_table: A dictionary represents the key-value pair in sub-table
      of 'KDUMP'.

    Returns:
      None.
    """
    if not kdump_table:
        click.echo("Unable to retrieve 'KDUMP' table from Config DB.")
        sys.exit(1)

    if "config" not in kdump_table:
        click.echo("Unable to retrieve key 'config' from KDUMP table.")
        sys.exit(2)


#
# 'disable' command ('sudo config kdump disable')
#
@kdump.command(name="disable", short_help="Disable the KDUMP mechanism")
@pass_db
def kdump_disable(db):
    """Disable the KDUMP mechanism"""
    kdump_table = db.cfgdb.get_table("KDUMP")
    check_kdump_table_existence(kdump_table)

    db.cfgdb.mod_entry("KDUMP", "config", {"enabled": "false"})
    click.echo("KDUMP configuration changes may require a reboot to take effect.")
    click.echo("Save SONiC configuration using 'config save' before issuing the reboot command.")


#
# 'enable' command ('sudo config kdump enable')
#
@kdump.command(name="enable", short_help="Enable the KDUMP mechanism")
@pass_db
def kdump_enable(db):
    """Enable the KDUMP mechanism"""
    kdump_table = db.cfgdb.get_table("KDUMP")
    check_kdump_table_existence(kdump_table)

    db.cfgdb.mod_entry("KDUMP", "config", {"enabled": "true"})
    click.echo("KDUMP configuration changes may require a reboot to take effect.")
    click.echo("Save SONiC configuration using 'config save' before issuing the reboot command.")


#
# 'memory' command ('sudo config kdump memory ...')
#
@kdump.command(name="memory", short_help="Configure the memory for KDUMP mechanism")
@click.argument('kdump_memory', metavar='<kdump_memory>', required=True)
@pass_db
def kdump_memory(db, kdump_memory):
    """Reserve memory for kdump capture kernel"""
    kdump_table = db.cfgdb.get_table("KDUMP")
    check_kdump_table_existence(kdump_table)

    db.cfgdb.mod_entry("KDUMP", "config", {"memory": kdump_memory})
    click.echo("KDUMP configuration changes may require a reboot to take effect.")
    click.echo("Save SONiC configuration using 'config save' before issuing the reboot command.")


#
# 'num_dumps' command ('sudo config kdump num_dumps ...')
#
@kdump.command(name="num_dumps", short_help="Configure the maximum dump files of KDUMP mechanism")
@click.argument('kdump_num_dumps', metavar='<kdump_num_dumps>', required=True, type=int)
@pass_db
def kdump_num_dumps(db, kdump_num_dumps):
    """Set maximum number of dump files for kdump"""
    kdump_table = db.cfgdb.get_table("KDUMP")
    check_kdump_table_existence(kdump_table)

    db.cfgdb.mod_entry("KDUMP", "config", {"num_dumps": kdump_num_dumps})


#
# 'num_dumps' command ('sudo config kdump remote ssh -c ... -k ...')
# 'num_dumps' command ('sudo config kdump remote disable ...')
#
@kdump.command(name="remote", short_help="Configure remote KDUMP mechanism")
@click.argument("action", type=click.Choice(["ssh", "disable"]))
@click.option("-c", "--connection-string", help="SSH user and host", required=false)
@click.option("-k", "--private-key", help="Path to private key", default="/root/.ssh/kdump_id_rsa", required=false)
@pass_db
def kdump_remote(action, connection_string, private_key):
    """Configure remote KDUMP mechanism"""
    kdump_table = db.cfgdb.get_table("KDUMP")
    check_kdump_table_existence(kdump_table)

    
    if action == "ssh":
        if connection_string is not None:
            db.cfgdb.mod_entry("KDUMP", "config", {"connection_string": connection_string})

        if private_key is not None:
            db.cfgdb.mod_entry("KDUMP", "config", {"private_key": private_key})

        if connection_string is None or private_key is None:
            click.echo("Error: Both --connection_string and --private-key are required for SSH configuration.")
            sys.exit(1)
        # Enable (uncomment) SSH comand in config file
        pass
    elif action == "disable":
        # Execute disable command
        pass

    click.echo("KDUMP configuration changes may require a reboot to take effect.")    
    click.echo("Save SONiC configuration using 'config save' before issuing the reboot command.")

