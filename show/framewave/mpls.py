import click
import utilities_common.cli as clicommon
from show.main import run_command

###############################################################################
#
# 'show mpls' cli stanza
#
###############################################################################


@click.group(cls=clicommon.AliasedGroup, name='mpls')
def mpls():
    """Display MPLS information."""

# 'forwarding' command ("show mpls forwarding")
@mpls.group(context_settings=dict(max_content_width=120))
def forwarding():
    """Display MPLS forwarding information."""
    pass


# 'all' subcommand ("show mpls forwarding all")
@forwarding.command(context_settings=dict(max_content_width=120))
@click.option('--json', is_flag=True, help="JSON output")
@click.option('--verbose', is_flag=True, help="Enable verbose output")
def all(json, verbose):
    """Show all MPLS cross-connects."""

    cmd = 'sudo docker exec bgp /opt/framewave/bin/show-mpls-forwarding'

    if json:
        cmd += " --json"

    run_command(cmd, display_cmd=verbose)


# 'incoming-label' subcommand ("show mpls forwarding incoming-label")
@forwarding.command(context_settings=dict(max_content_width=120),
          short_help="Show MPLS forwarding information for the specified INCOMING LABEL.",
          name='incoming-label')
@click.argument('label', metavar='[LABEL]', nargs=1, required=True)
@click.option('--json', is_flag=True, help="JSON output")
@click.option('--verbose', is_flag=True, help="Enable verbose output")
def incoming_label(label, json, verbose):
    """
    LABEL     Show MPLS forwarding information for the specified INCOMING LABEL.\n
    """

    cmd = 'sudo docker exec bgp /opt/framewave/bin/show-mpls-forwarding incoming-label'

    if label:
        cmd += " " + label

    if json:
        cmd += " --json"

    run_command(cmd, display_cmd=verbose)


# 'fec-type' subcommand ("show mpls forwarding fec-type")
@forwarding.command(context_settings=dict(max_content_width=120),
                  short_help="Show MPLS forwarding information for the specified FEC TYPE.",
                  name='fec-type')
@click.argument('type', metavar='[FEC-TYPE]', type=click.Choice(['sr-prefix', 'ldp']), nargs=1, required=True)
@click.option('--json', is_flag=True, help="JSON output")
@click.option('--verbose', is_flag=True, help="Enable verbose output")
def fec_type(type, json, verbose):
    """
    FEC-TYPE    Show MPLS forwarding information for the specified FEC TYPE.\n
    """

    cmd = 'sudo docker exec bgp /opt/framewave/bin/show-mpls-forwarding fec-type'

    if type:
        cmd += " " + type

    if json:
        cmd += " --json"

    run_command(cmd, display_cmd=verbose)
