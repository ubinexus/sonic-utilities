import click
import utilities_common.cli as clicommon
from show.main import run_command

###############################################################################
#
# 'show lacp' cli stanza
#
###############################################################################


@click.group(cls=clicommon.AliasedGroup)
def lacp():
    """Show LACP information"""
    pass


# 'state' subcommand ("show lacp state")
@lacp.command(context_settings=dict(max_content_width=120))
@click.option('--json', is_flag=True, help="JSON output")
@click.option('--verbose', is_flag=True, help="Enable verbose output")
def state(verbose, json):
    """
    Show LACP general information.
    """

    cmd = 'sudo docker exec bgp /opt/framewave/bin/show-lacp'

    if json:
        cmd += " --json"
    run_command(cmd, display_cmd=verbose)


# 'interface' subcommand ("show lacp interface")
@lacp.command(context_settings=dict(max_content_width=120))
@click.argument('ifname', metavar='[IF-NAME]', nargs=1, required=False)
@click.option('--json', is_flag=True, help="JSON output")
@click.option('--verbose', is_flag=True, help="Enable verbose output")
def interface(ifname, verbose, json):
    """
    Show LACP interface information.\n
         IF-NAME    Show detailed information for the specified IF-NAME\n
    """

    cmd = 'sudo docker exec bgp /opt/framewave/bin/show-lacp-interface'
    if ifname is not None:
        cmd += " " + str(ifname)

    if json:
        cmd += " --json"
    run_command(cmd, display_cmd=verbose)


# 'bundle' subcommand ("show lacp bundle")
@lacp.command(context_settings=dict(max_content_width=120))
@click.argument('bundle-id', metavar='[BUNDLE-ID]', nargs=1, required=False)
@click.option('--mc-lag', is_flag=True, help="Show LACP bundle MC-LAG")
@click.option('--json', is_flag=True, help="JSON output")
@click.option('--verbose', is_flag=True, help="Enable verbose output")
def bundle(bundle_id, mc_lag, verbose, json):
    """
    Show LACP bundle information.\n
         BUNDLE-ID    Show detailed information for the specified BUNDLE-ID\n
    """

    cmd = 'sudo docker exec bgp /opt/framewave/bin/show-lacp-bundle'
    if bundle_id is not None:
        cmd += " " + str(bundle_id)
    if mc_lag:
        cmd += " --mc-lag"
    if json:
        cmd += " --json"
    run_command(cmd, display_cmd=verbose)
