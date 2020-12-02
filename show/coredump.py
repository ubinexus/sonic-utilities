import os
import click
import utilities_common.cli as clicommon
from swsssdk import ConfigDBConnector

#
# 'coredumpctl' group ("show coredump")
#

@click.group(cls=clicommon.AliasedGroup, name="coredump")
def coredump():
    """Show core dump events encountered"""
    pass

# 'config' subcommand ("show coredump config")
@coredump.command('config')
@click.option('--verbose', is_flag=True, help="Enable verbose output")
def core_config(verbose):
    """ Show coredump configuration """
    # Default admin mode
    admin_mode = True
    # Obtain config from Config DB
    config_db = ConfigDBConnector()
    if config_db is not None:
        config_db.connect()
        table_data = config_db.get_table('COREDUMP')
        if table_data is not None:
            config_data = table_data.get('config')
            if config_data is not None:
                admin_mode = config_data.get('enabled')
                if admin_mode is not None and admin_mode.lower() == 'false':
                    admin_mode = False

    # Core dump administrative mode
    if admin_mode:
        click.echo('Coredump : %s' % 'Enabled')
    else:
        click.echo('Coredump : %s' % 'Disabled')

# 'list' subcommand ("show coredump list")
@coredump.command('list')
@click.argument('pattern', required=False)
@click.option('--verbose', is_flag=True, help="Enable verbose output")
def core_list(verbose, pattern):
    """ List available coredumps """

    if not os.geteuid()==0:
        click.echo("Note: To list all the core files please run the command with root privileges\n")

    if os.path.exists("/usr/bin/coredumpctl"):
        cmd = "coredumpctl list"
        if pattern is not None:
            cmd = cmd + " " + pattern
        clicommon.run_command(cmd, display_cmd=verbose)
    else:
        exit("Note: Install systemd-coredump package to run this command")

# 'info' subcommand ("show coredump info")
@coredump.command('info')
@click.argument('pattern', required=False)
@click.option('--verbose', is_flag=True, help="Enable verbose output")
def core_info(verbose, pattern):
    """ Show information about one or more coredumps """

    if not os.geteuid()==0:
        click.echo("Note: To view all the core files please run the command with root privileges\n")

    if os.path.exists("/usr/bin/coredumpctl"):
        cmd = "coredumpctl info"
        if pattern is not None:
            cmd = cmd + " " + pattern
        clicommon.run_command(cmd, display_cmd=verbose)
    else:
        exit("Note: Install systemd-coredump package to run this command")

