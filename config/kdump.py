import sys
import click
import re
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

    # Fetch the current remote status
    current_remote_status = kdump_table.get("config", {}).get("remote", "false").lower()

    if action.lower() == 'enable':
        if current_remote_status == 'true':
            # Check if SSH is already uncommented
            with open('/etc/default/kdump-tools', 'r') as file:
                content = file.read()

            if re.search(r'^\s*SSH\s*=', content, re.MULTILINE):
                click.echo("Error: Kdump Remote Mode is already enabled.")
                return

            # Uncomment SSH in /etc/default/kdump-tools
            with open('/etc/default/kdump-tools', 'r') as file:
                lines = file.readlines()

            with open('/etc/default/kdump-tools', 'w') as file:
                for line in lines:
                    if line.strip().startswith('#SSH'):
                        file.write(line.lstrip('#'))
                    else:
                        file.write(line)

            click.echo("Kdump Remote Mode enabled.")
        else:
            # Enable remote mode
            remote = 'true'
            db.cfgdb.mod_entry("KDUMP", "config", {"remote": remote})
            echo_reboot_warning()

    elif action.lower() == 'disable':
        if current_remote_status == 'false':
            click.echo("Error: Kdump Remote Mode is already disabled.")
            return

        # Disable remote mode
        remote = 'false'
        db.cfgdb.mod_entry("KDUMP", "config", {"remote": remote})

        # Comment out SSH and SSH_KEY in /etc/default/kdump-tools
        try:
            # Read the current content of the file
            with open('/etc/default/kdump-tools', 'r') as file:
                lines = file.readlines()

            # Prepare new content
            new_lines = []
            ssh_commented = False
            ssh_key_commented = False

            for line in lines:
                if line.strip().startswith('SSH'):
                    new_lines.append(f"#{line}")
                    ssh_commented = True
                elif line.strip().startswith('SSH_KEY'):
                    new_lines.append(f"#{line}")
                    ssh_key_commented = True
                else:
                    new_lines.append(line)

            # If SSH or SSH_KEY were not present, add commented lines at the end
            if not ssh_commented:
                new_lines.append("#SSH=\n")
            if not ssh_key_commented:
                new_lines.append("#SSH_KEY=\n")

            # Write the updated content back to the file
            with open('/etc/default/kdump-tools', 'w') as file:
                file.writelines(new_lines)

            click.echo("Kdump Remote Mode disabled. SSH settings commented out.")
        except Exception as e:
            click.echo(f"Error updating /etc/default/kdump-tools: {e}")

#
# 'add' command ('sudo config kdump add ...')
#


@kdump.command(name="add", short_help="Add SSH connection string or SSH key path.")
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

    # Add item to config_db
    db.cfgdb.mod_entry("KDUMP", "config", {item: value})
    click.echo(f"{item} added to configuration.")

    # Check if both parameters are added
    ssh_string = kdump_table.get("config", {}).get("ssh_string")
    ssh_path = kdump_table.get("config", {}).get("ssh_path")

    # If both are present, update the file
    if ssh_string and ssh_path:
        try:
            # Read the current content of the file
            with open('/etc/default/kdump-tools', 'r') as file:
                lines = file.readlines()

            # Prepare new content
            new_lines = []
            ssh_string_added = False
            ssh_path_added = False

            for line in lines:
                if line.strip().startswith('#SSH') or line.strip().startswith('SSH'):
                    new_lines.append(f"SSH={ssh_string}\n")
                    ssh_string_added = True
                elif line.strip().startswith('#SSH_KEY') or line.strip().startswith('SSH_KEY'):
                    new_lines.append(f"SSH_KEY={ssh_path}\n")
                    ssh_path_added = True
                else:
                    new_lines.append(line)

            # If either SSH or SSH_KEY was not found, add them at the end of the file
            if not ssh_string_added:
                new_lines.append(f"SSH={ssh_string}\n")
            if not ssh_path_added:
                new_lines.append(f"SSH_KEY={ssh_path}\n")

            # Write the updated content back to the file
            with open('/etc/default/kdump-tools', 'w') as file:
                file.writelines(new_lines)

            click.echo("Updated /etc/default/kdump-tools with new SSH settings.")
        except Exception as e:
            click.echo(f"Error updating /etc/default/kdump-tools: {e}")

    echo_reboot_warning()


@kdump.command(name="remove", short_help="Remove SSH connection string or SSH key path for kdump.")
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
