import click
import utilities_common.cli as clicommon
from show.main import run_command

###############################################################################
#
# 'show ldp' cli stanza
#
###############################################################################


@click.group(cls=clicommon.AliasedGroup)
def ldp():
    """Show LDP information"""
    pass


# 'neighbor' subcommand ("show ldp neighbor")
@ldp.command(context_settings=dict(max_content_width=120))
@click.option('--router_id', type=str, help="Show information for router ID ROUTER-ID")
@click.option('--json', is_flag=True, help="JSON output")
@click.option('--verbose', is_flag=True, help="Enable verbose output")
def neighbor(verbose, router_id, json):
    """
    Show LDP neighbor information.
    """

    cmd = 'sudo docker exec bgp /opt/framewave/bin/show-ldp-neighbor'

    if router_id:
        cmd += str(router_id)
    if json:
        cmd += " --json"
    run_command(cmd, display_cmd=verbose)


# 'labels' subcommand ("show ldp labels")
@ldp.command(context_settings=dict(max_content_width=120))
@click.argument('prefix', metavar='[PREFIX]', nargs=1, required=False)
@click.option('--upstream', is_flag=True, help="Show upstream label information")
@click.option('--downstream', is_flag=True, help="Show downstream label information")
@click.option('--downstream-detailed',
              is_flag=True,
              help="Show detailed downstream label information (overrides --upstream and --downstream)")
@click.option('--json', is_flag=True, help="JSON output")
@click.option('--verbose', is_flag=True, help="Enable verbose output")
def labels(prefix, verbose, upstream, downstream, downstream_detailed, json):
    """
    Show LDP labels information.\n
         PREFIX    Show detailed information for the specified PREFIX\n
    """

    cmd = 'sudo docker exec bgp /opt/framewave/bin/show-ldp-labels'
    if prefix is not None:
        cmd += " --prefix" + str(ifname)
    if downstream_detailed:
      cmd += " --detailed-downstream"
    else:
      if upstream:
          cmd += " --upstream"
      if downstream:
          cmd += " --downstream"
    if json:
        cmd += " --json"
    run_command(cmd, display_cmd=verbose)
