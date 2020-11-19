import click
import utilities_common.cli as clicommon
from show.main import run_command

###############################################################################
#
# 'show bfd' cli stanza
#
###############################################################################


@click.group(cls=clicommon.AliasedGroup)
def bfd():
    """Show bfd information"""
    pass

#
# 'bfd session' subcommand ("show bfd session")
#

@bfd.command(context_settings=dict(max_content_width=120))
@click.argument('peer-addr', metavar='[PEER-ADDR]', nargs=1, required=False)
@click.option('--vrf', type=str, help="Show information for VRF VRF-NAME")
@click.option('--ipv4', is_flag=True, help="Show BFD IPv4 information")
@click.option('--ipv6', is_flag=True, help="Show BFD IPv6 information")
@click.option('--json', is_flag=True, help="JSON output")
@click.option('--verbose', is_flag=True, help="Enable verbose output")
def session(peer_addr, verbose, vrf, ipv4, ipv6, json):
    """
    Show bfd session information.
        PEER-ADDR    Show detailed information for the specified PEER-ADDR\n

    """

    cmd = 'sudo docker exec bgp /opt/framewave/bin/show-bfd-session'

    if peer_addr is not None:
        cmd += " "+ str(peer_addr)
    if vrf is not None:
        cmd += " --vrf " + str(vrf)
    if ipv4:
        cmd += " --ipv4"
    if ipv6:
        cmd += " --ipv6"
    if json:
        cmd += " --json"
    run_command(cmd, display_cmd=verbose)
