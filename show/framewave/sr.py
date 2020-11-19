import click
import utilities_common.cli as clicommon
from show.main import run_command

###############################################################################
#
# 'show segment-routing' cli stanza
#
###############################################################################


@click.group(cls=clicommon.AliasedGroup, name='segment-routing')
def segment_routing():
    """Show segment routing information"""
    pass


# 'node' command ("show segment-routing node")
@segment_routing.group(context_settings=dict(max_content_width=120))
def node():
    """Show node information"""
    pass


# 'all' subcommand ("show segment-routing node all")
@node.command(context_settings=dict(max_content_width=120), name="all")
@click.option('--json', is_flag=True, help="JSON output")
@click.option('--verbose', is_flag=True, help="Enable verbose output")
def all_nodes(json, verbose):
    """Show all nodes"""

    cmd = 'sudo docker exec bgp /opt/framewave/bin/show-segment-routing node'

    if json:
        cmd += " --json"

    run_command(cmd, display_cmd=verbose)


# 'local' subcommand ("show segment-routing node local")
@node.command(context_settings=dict(max_content_width=120))
@click.option('--json', is_flag=True, help="JSON output")
@click.option('--verbose', is_flag=True, help="Enable verbose output")
def local(json, verbose):
    """Show local node information"""

    cmd = 'sudo docker exec bgp /opt/framewave/bin/show-segment-routing node local'

    if json:
        cmd += " --json"

    run_command(cmd, display_cmd=verbose)


# 'isis' subcommand ("show segment-routing node isis ROUTER-ID")
@node.command(context_settings=dict(max_content_width=120), short_help="Show ISIS node information.")
@click.argument('router_id', metavar='[ROUTER-ID]', nargs=1, required=True)
@click.option('--json', is_flag=True, help="JSON output")
@click.option('--verbose', is_flag=True, help="Enable verbose output")
def isis(router_id, json, verbose):
    """
    ROUTER-ID     Show detailed information for the specified ROUTER-ID\n
    """

    cmd = 'sudo docker exec bgp /opt/framewave/bin/show-segment-routing node isis'

    if router_id:
        cmd += " " + router_id

    if json:
        cmd += " --json"

    run_command(cmd, display_cmd=verbose)


# 'prefix_sid' subcommand ("show segment-routing prefix-sid")
@segment_routing.command(context_settings=dict(max_content_width=120))
@click.option('--json', is_flag=True, help="JSON output")
@click.option('--verbose', is_flag=True, help="Enable verbose output")
def prefix_sid(json, verbose):
    """Show prefix SID information"""

    cmd = 'sudo docker exec bgp /opt/framewave/bin/show-segment-routing prefix-sid'

    if json:
        cmd += " --json"

    run_command(cmd, display_cmd=verbose)


# 'xc' subcommand ("show segment-routing xc")
@segment_routing.command(context_settings=dict(max_content_width=120))
@click.argument('dst_sid', metavar='[DEST-SID]', nargs=1, required=False)
@click.option('--json', is_flag=True, help="JSON output")
@click.option('--verbose', is_flag=True, help="Enable verbose output")
def xc(dst_sid, json, verbose):
    """
    Show cross-connect information
    DEST-SID      Show detailed information for the specified destination SID\n
    """

    cmd = 'sudo docker exec bgp /opt/framewave/bin/show-segment-routing xc'
    if dst_sid is not None:
        cmd += " " + str(dst_sid)
    if json:
        cmd += " --json"

    run_command(cmd, display_cmd=verbose)
