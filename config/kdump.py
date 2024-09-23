import sys
import click
from utilities_common.db import ConfigDBConnector
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


# 'remote' command ('sudo config kdump remote ...')
@kdump.command('remote')
@click.argument('action', metavar='<enable/disable>', required=True)
def remote(action):
    """Enable or disable remote kdump feature"""
    config_db = ConfigDBConnector()
    if config_db is not None:
        config_db.connect()

        # Get the current status of the remote feature
        current_status = config_db.get_entry("KDUMP", "config").get("remote", False)

        if action.lower() == 'enable':
            if current_status:
                click.echo("Remote kdump feature is already enabled.")
            else:
                config_db.mod_entry("KDUMP", "config", {"remote": True})
                click.echo("Remote kdump feature enabled.")
        elif action.lower() == 'disable':
            if not current_status:
                click.echo("Remote kdump feature is already disabled.")
            else:
                config_db.mod_entry("KDUMP", "config", {"remote": False})
                click.echo("Remote kdump feature disabled.")
        else:
            click.echo("Invalid action. Use 'enable' or 'disable'.")


@kdump.command(name="add", help="Add SSH key or path for remote KDUMP configuration")
@click.argument('option', metavar='<option>', required=True, type=click.Choice(['ssh_key', 'ssh_path']))
@click.argument('value', metavar='<value>', required=True, help="USER@IP_SSH_SERVER")
@pass_db
def add(db, option, value):
    """Add SSH key or path for remote KDUMP configuration"""
    kdump_table = db.cfgdb.get_table("KDUMP")
    check_kdump_table_existence(kdump_table)

    # Check if remote is enabled
    remote_config = kdump_table.get("config", {})
    remote_enabled = remote_config.get("remote", "false") == "true"

    if not remote_enabled:
        click.echo("Remote KDUMP is not enabled. Please enable remote KDUMP first.")
        sys.exit(3)

    # Update the database with the new SSH key or path
    if option == 'ssh_key':
        db.cfgdb.mod_entry("KDUMP", "config", {"SSH_KEY": value})
    elif option == 'ssh_path':
        db.cfgdb.mod_entry("KDUMP", "config", {"SSH_PATH": value})

    echo_reboot_warning()


@kdump.command(name="remove", help="Remove SSH connection string or SSH key path.")
@click.argument('item', type=click.Choice(['ssh_string', 'ssh_path']))
@pass_db
def remove_kdump_item(db, item):
    """Remove SSH connection string or SSH key path for kdump"""
    kdump_table = db.cfgdb.get_table("KDUMP")
    check_kdump_table_existence(kdump_table)

    # Check if the item is already configured
    existing_value = kdump_table.get("config", {}).get(item)
    if not existing_value:
        click.echo(f"Error: {item} is not configured.")
        return

    # Remove item from config_db
    db.cfgdb.mod_entry("KDUMP", "config", {item: ""})
    click.echo(f"{item} removed successfully.")
    echo_reboot_warning()
