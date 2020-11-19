import click
import utilities_common.cli as clicommon
from show.main import run_command

###############################################################################
#
# 'show isis' cli stanza
#
###############################################################################


@click.group(cls=clicommon.AliasedGroup)
def isis():
    """Show IS-IS information"""
    pass


# 'state' subcommand ("show isis state")
@isis.command(context_settings=dict(max_content_width=120))
@click.option('--vrf', type=str, help="Show information for VRF VRF-NAME")
@click.option('--hostname', is_flag=True, help="Show IS-IS hostname")
@click.option('--level-1', is_flag=True, help="Show IS-IS level-1 information")
@click.option('--level-2', is_flag=True, help="Show IS-IS level-2 information")
@click.option('--json', is_flag=True, help="JSON output")
@click.option('--verbose', is_flag=True, help="Enable verbose output")
def state(verbose, level_1, level_2, vrf, hostname, json):
    """
    Show IS-IS state information.
    """

    cmd = 'sudo docker exec bgp /opt/framewave/bin/show-isis'

    if hostname:
        cmd += " --hostname"
    if level_1:
        cmd += " --level-1"
    if level_2:
        cmd += " --level-2"
    if vrf is not None:
        cmd += " --vrf " + str(vrf)
    if json:
        cmd += " --json"
    run_command(cmd, display_cmd=verbose)


# Autocomplete function for the statistics argument
def ac_stats(ctx, args, incomplete):
    arg_string = ['statistics']
    return [elem for elem in arg_string if incomplete in elem]


# 'interface' subcommand ("show isis interface")
@isis.command(context_settings=dict(max_content_width=120))
@click.argument('ifname', metavar='[IF-NAME]', nargs=1, required=False)
@click.argument('stats', metavar='[statistics]', nargs=1, required=False, autocompletion=ac_stats)
@click.option('--vrf', type=str, help="Show interfaces for VRF VRF-NAME")
@click.option('--level-1', is_flag=True, help="Show IS-IS interface level-1 information")
@click.option('--level-2', is_flag=True, help="Show IS-IS interface level-2 information")
@click.option('--json', is_flag=True, help="JSON output")
@click.option('--verbose', is_flag=True, help="Enable verbose output")
def interface(ifname, verbose, stats, vrf, level_1, level_2, json):
    """
    Show IS-IS interface information.\n
         IF-NAME    Show detailed information for the specified IF-NAME\n
         statistics Show IS-IS statistics for the specified interface\n
    """

    cmd = 'sudo docker exec bgp /opt/framewave/bin/show-isis-interface'
    if ifname is not None:
        cmd += " " + str(ifname)
    if stats is not None:
        if str(stats) == 'statistics':
            cmd += " --statistics"
        else:
            print("Usage: show isis interface [IF-NAME] [statistics]\n\n"
                  "Error: Got unexpected extra argument: (" + str(stats) + ")")
            return
    if vrf is not None:
        cmd += " --vrf " + str(vrf)
    if level_1:
        cmd += " --level-1"
    if level_2:
        cmd += " --level-2"
    if json:
        cmd += " --json"
    run_command(cmd, display_cmd=verbose)


# 'neighbors' subcommand ("show isis neighbors")
@isis.command(context_settings=dict(max_content_width=150))
@click.option('--vrf', type=str, help="Show neighbors for VRF VRF-NAME")
@click.option('--json', is_flag=True, help="JSON output")
@click.option('--verbose', is_flag=True, help="Enable verbose output")
def neighbors(verbose, vrf, json):
    """
    Show IS-IS neighbors information.
    """

    cmd = 'sudo docker exec bgp /opt/framewave/bin/show-isis-interface'
    cmd += " --neighbors "
    if vrf is not None:
        cmd += " --vrf " + str(vrf)
    if json:
        cmd += " --json"
    run_command(cmd, display_cmd=verbose)


# 'lsp' subcommand ("show isis lsp")
@isis.command(context_settings=dict(max_content_width=120))
@click.argument('lspid', metavar='[LSP-ID] ', nargs=1, required=False)
@click.option('--vrf', type=str, help="Show information for VRF VRF-NAME")
@click.option('--level-1', is_flag=True, help="Show IS-IS LSP level-1 information")
@click.option('--level-2', is_flag=True, help="Show IS-IS LSP level-2 information")
@click.option('--detail', is_flag=True, help="Show IS-IS detailed information for each LSP ID")
@click.option('--json', is_flag=True, help="JSON output")
@click.option('--verbose', is_flag=True, help="Enable verbose output")
def lsp(lspid, verbose, vrf, level_1, level_2, detail, json):
    """
    Show ISIS LSP information.\n
       LSP-ID            Show detailed information for the specified LSP-ID\n
    """

    cmd = 'sudo docker exec bgp /opt/framewave/bin/show-isis-lsp'
    if lspid is not None:
        cmd += " " + str(lspid)
    if vrf is not None:
        cmd += " --vrf " + str(vrf)
    if level_1:
        cmd += " --level-1"
    if level_2:
        cmd += " --level-2"
    if detail:
        cmd += " --detail"
    if json:
        cmd += " --json"
    run_command(cmd, display_cmd=verbose)
