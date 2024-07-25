import sys
import click
import re

from utilities_common.cli import AbbreviationGroup, pass_db
from pathlib import Path
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

    if action.lower() == 'disable':
        ssh_string = kdump_table.get("config", {}).get("ssh_string", None)
        ssh_key = kdump_table.get("config", {}).get("ssh_key", None)

        if ssh_string or ssh_key:
            click.echo("Error: Remove SSH_string and SSH_key from Config DB before disabling Kdump Remote Mode.")
            return

    remote = 'true' if action.lower() == 'enable' else 'false'
    db.cfgdb.mod_entry("KDUMP", "config", {"remote": remote})

    def uncomment_ssh(match):
        return match.group(0)[1:]  # Remove the leading '#'
    def comment_ssh(match):
        return f'#{match.group(0)}'  # Add a leading '#'

    if action.lower() == 'enable':
        file_path = Path('/etc/default/kdump-tools')
        try:
            # Read the content of the file
            content = file_path.read_text()
            new_content = re.sub(r"^#SSH", uncomment_ssh, content, flags=re.MULTILINE)
            new_content = re.sub(r"^#SSH_KEY", uncomment_ssh, new_content, flags=re.MULTILINE)
            click.echo("Updated /etc/default/kdump-tools: SSH and SSH_KEY commented out.")
        except Exception as e:
            click.echo(f"Error updating /etc/default/kdump-tools: {e}")

    elif action.lower() == 'disable':
        file_path = Path('/etc/default/kdump-tools')
        try:
            # Read the content of the file
            content = file_path.read_text()
            new_content = re.sub(r"^SSH", comment_ssh, content, flags=re.MULTILINE)
            new_content = re.sub(r"^SSH_KEY", comment_ssh, new_content, flags=re.MULTILINE)
            click.echo("Updated /etc/default/kdump-tools: SSH and SSH_KEY commented .")
        except Exception as e:
            click.echo(f"Error updating /etc/default/kdump-tools: {e}")

    echo_reboot_warning()

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

    # Check if the item is already added
    existing_value = kdump_table.get("config", {}).get(item)
    if existing_value:
        click.echo(f"Error: {item} is already added.")
        return

    # Add item to config_db
    db.cfgdb.mod_entry("KDUMP", "config", {item: value})

    # Retrieve updated values from config_db
    # kdump_table = db.cfgdb.get_table("KDUMP")
    # ssh_string = kdump_table.get("config", {}).get("ssh_string", "")
    # ssh_path = kdump_table.get("config", {}).get("ssh_path", "")

    # file_path = Path('/etc/default/kdump-tools')
    # try:
    #     # Read the content of the file
    #     content = file_path.read_text()

    #     # Define replacement functions with capture groups
    #     def replace_ssh(match):
    #         return f'SSH="{ssh_string}"' if ssh_string else match.group(0)

    #     def replace_ssh_key(match):
    #         return f'SSH_KEY="{ssh_path}"' if ssh_path else match.group(0)

    #     # Apply replacements using capture groups
    #     new_content = re.sub(r"^\s*#?\s*SSH\s*=\s*.*$", replace_ssh, content, flags=re.MULTILINE)
    #     new_content = re.sub(r"^\s*#?\s*SSH_KEY\s*=\s*.*$", replace_ssh_key, new_content, flags=re.MULTILINE)

    #     # Write the updated content back to the file
    #     file_path.write_text(new_content)
    #     click.echo("Updated /etc/default/kdump-tools with new SSH settings.")
    # except Exception as e:
    #     click.echo(f"Error updating /etc/default/kdump-tools: {e}")
    echo_reboot_warning()


@kdump.command(name="remove", short_help="Remove SSH connection string or SSH key path.")
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

    # Retrieve updated values from config_db
    # kdump_table = db.cfgdb.get_table("KDUMP")

    # file_path = Path('/etc/default/kdump-tools')
    # try:
    #     # Read the content of the file
    #     content = file_path.read_text()

    #     # Define replacement functions with capture groups
    #     def replace_ssh(match):
    #         return 'SSH=""' if item == "ssh_string" else match.group(0)

    #     def replace_ssh_key(match):
    #         return 'SSH_KEY=""' if item == "ssh_path" else match.group(0)

    #     # Apply replacements using capture groups
    #     new_content = re.sub(r"^\s*#?\s*SSH\s*=\s*.*$", replace_ssh, content, flags=re.MULTILINE)
    #     new_content = re.sub(r"^\s*#?\s*SSH_KEY\s*=\s*.*$", replace_ssh_key, new_content, flags=re.MULTILINE)

    #     # Write the updated content back to the file
    #     file_path.write_text(new_content)
    #     click.echo("Updated /etc/default/kdump-tools with empty SSH settings.")
    # except Exception as e:
    #     click.echo(f"Error updating /etc/default/kdump-tools: {e}")

    click.echo(f"{item} removed successfully.")
    echo_reboot_warning()
