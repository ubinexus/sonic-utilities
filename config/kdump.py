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


def echo_reboot_warning():
    """Prints the warning message about reboot requirements."""
    click.echo("KDUMP configuration changes may require a reboot to take effect.")
    click.echo("Save SONiC configuration using 'config save' before issuing the reboot command.")
#
# 'disable' command ('sudo config kdump disable')
#


@kdump.command(name="disable", help="Disable the KDUMP mechanism")
@pass_db
def kdump_disable(db):
    """Disable the KDUMP mechanism"""
    kdump_table = db.cfgdb.get_table("KDUMP")
    check_kdump_table_existence(kdump_table)

    db.cfgdb.mod_entry("KDUMP", "config", {"enabled": "false"})
    echo_reboot_warning()

#
# 'enable' command ('sudo config kdump enable')
#


@kdump.command(name="enable", help="Enable the KDUMP mechanism")
@pass_db
def kdump_enable(db):
    """Enable the KDUMP mechanism"""
    kdump_table = db.cfgdb.get_table("KDUMP")
    check_kdump_table_existence(kdump_table)

    db.cfgdb.mod_entry("KDUMP", "config", {"enabled": "true"})
    echo_reboot_warning()

#
# 'memory' command ('sudo config kdump memory ...')
#


@kdump.command(name="memory", help="Configure the memory for KDUMP mechanism")
@click.argument('kdump_memory', metavar='<kdump_memory>', required=True)
@pass_db
def kdump_memory(db, kdump_memory):
    """Reserve memory for kdump capture kernel"""
    kdump_table = db.cfgdb.get_table("KDUMP")
    check_kdump_table_existence(kdump_table)

    db.cfgdb.mod_entry("KDUMP", "config", {"memory": kdump_memory})
    echo_reboot_warning()

#
# 'num_dumps' command ('sudo config kdump num_dumps ...')
#


@kdump.command(name="num_dumps", help="Configure the maximum dump files of KDUMP mechanism")
@click.argument('kdump_num_dumps', metavar='<kdump_num_dumps>', required=True, type=int)
@pass_db
def kdump_num_dumps(db, kdump_num_dumps):
    """Set maximum number of dump files for kdump"""
    kdump_table = db.cfgdb.get_table("KDUMP")
    check_kdump_table_existence(kdump_table)

    db.cfgdb.mod_entry("KDUMP", "config", {"num_dumps": kdump_num_dumps})
    echo_reboot_warning()


@kdump.command(name ="remote", help="Configure the remote enable/disable for KDUMP mechanism")
@click.argument('action', metavar='<enable/disable>', required=True, type=click.STRING)  # Corrected this line
@pass_db
def remote(db,action):
    """Enable or disable remote kdump feature"""
    kdump_table = db.cfgdb.get_table("KDUMP")
    check_kdump_table_existence(kdump_table)

    # Get the current status of the remote feature as string
    current_status = kdump_table["config"].get("remote", "false").lower()

    if action.lower() == 'enable':
        if current_status == "true":
            click.echo("Remote kdump feature is already enabled.")
        else:
            db.cfgdb.mod_entry("KDUMP", "config", {"remote": "true"})
            click.echo("Remote kdump feature enabled.")
            echo_reboot_warning()
    elif action.lower() == 'disable':
        if current_status == "false":
            click.echo("Remote kdump feature is already disabled.")
        else:
            db.cfgdb.mod_entry("KDUMP", "config", {"remote": "false"})
            click.echo("Remote kdump feature disabled.")
            echo_reboot_warning()
    else:
        click.echo("Invalid action. Use 'enable' or 'disable'.")
