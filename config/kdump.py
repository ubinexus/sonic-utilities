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


@kdump.command(name="disable", short_help="Disable the KDUMP mechanism")
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


@kdump.command(name="enable", short_help="Enable the KDUMP mechanism")
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


@kdump.command(name="memory", short_help="Configure the memory for KDUMP mechanism")
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


@kdump.command(name="num_dumps", short_help="Configure the maximum dump files of KDUMP mechanism")
@click.argument('kdump_num_dumps', metavar='<kdump_num_dumps>', required=True, type=int)
@pass_db
def kdump_num_dumps(db, kdump_num_dumps):
    """Set maximum number of dump files for kdump"""
    kdump_table = db.cfgdb.get_table("KDUMP")
    check_kdump_table_existence(kdump_table)

    db.cfgdb.mod_entry("KDUMP", "config", {"num_dumps": kdump_num_dumps})
    echo_reboot_warning()

#
# 'remote' command ('sudo config kdump remote ...')
#


@kdump.command(name="remote", short_help="Enable or Disable Kdump Remote")
@click.argument('action', required=True, type=click.Choice(['enable', 'disable'], case_sensitive=False))
@pass_db
def kdump_remote(db, action):
    """Enable or Disable Kdump Remote Mode"""
    kdump_table = db.cfgdb.get_table("KDUMP")
    check_kdump_table_existence(kdump_table)

    current_remote_status = kdump_table.get("config", {}).get("remote", "false").lower()

    if action.lower() == 'enable' and current_remote_status == 'true':
        click.echo("Error: Kdump Remote Mode is already enabled.")
        return
    elif action.lower() == 'disable' and current_remote_status == 'false':
        click.echo("Error: Kdump Remote Mode is already disabled.")
        return

    remote = 'true' if action.lower() == 'enable' else 'false'
    db.cfgdb.mod_entry("KDUMP", "config", {"remote": remote})
    echo_reboot_warning()

#
# 'add' command ('sudo config kdump add ...')
#


@kdump.command(name="add", short_help="Add SSH connection string or SSH key path for kdump.")
@click.argument('item', type=click.Choice(['ssh_string', 'ssh_path']))
@click.argument('value', metavar='<value>', required=True)
@pass_db
def add_kdump_item(db, item, value):
    """Add SSH connection string or SSH key path for kdump"""
    kdump_table = db.cfgdb.get_table("KDUMP")
    check_kdump_table_existence(kdump_table)

    # Check if remote mode is enabled
    remote_mode_enabled = kdump_table.get("config", {}).get("remote", "false").lower()
    if remote_mode_enabled != "true":
        click.echo("Error: Enable remote mode first.")
        return

    # Check if the item is already added
    existing_value = kdump_table.get("config", {}).get(item)
    if existing_value:
        click.echo(f"Error: {item} is already added.")
        return

    # Add item to config_db
    db.cfgdb.mod_entry("KDUMP", "config", {item: value})
    echo_reboot_warning()


@kdump.command(name="remove", short_help="Remove SSH connection string or SSH key path for kdump.")
@click.argument('item', type=click.Choice(['ssh_string', 'ssh_path']))
@pass_db
def remove_kdump_item(db, item):
    """Remove SSH connection string or SSH key path for kdump"""
    kdump_table = db.cfgdb.get_table("KDUMP")
    check_kdump_table_existence(kdump_table)

    # Check if remote mode is enabled
    remote_mode_enabled = kdump_table.get("config", {}).get("remote", "false").lower()
    if remote_mode_enabled != "true":
        click.echo("Error: Enable remote mode first.")
        return

    # Check if the item is already configured
    existing_value = kdump_table.get("config", {}).get(item)
    if not existing_value:
        click.echo(f"Error: {item} is not configured.")
        return

    # Remove item from config_db
    db.cfgdb.mod_entry("KDUMP", "config", {item: ""})
    click.echo(f"{item} removed successfully.")
    echo_reboot_warning()
