
import click
import utilities_common.cli as clicommon
from show.main import run_command

###############################################################################
#
# 'show bgp' cli stanza
#
###############################################################################


@click.group(cls=clicommon.AliasedGroup)
def bgp():
    """Show BGP information"""
    pass

# Commented out until a decision is made if it's required and support added to query missing fields is in place
# # 'summary' subcommand ("show ip bgp summary")
# @bgp.command(context_settings=dict(max_content_width=120))
# @multi_asic_util.multi_asic_click_options
# def summary(namespace, display):
#     """
#     Show BGP summary information.\n
#     """
#     bgp_summary = bgp_framewave_util.get_bgp_framewave_summary_from_all_bgp_instances(namespace, display)
#     bgp_framewave_util.display_bgp_framewave_summary(bgp_summary=bgp_summary)


# 'ip' subcommand ("show bgp ip")
@bgp.command(context_settings=dict(max_content_width=120))
@click.argument('args', metavar='[PREFIX] [...]', nargs=-1, required=False)
@click.option('--ipv4', is_flag=True, help="Show only BGP IPv4 unicast prefixes")
@click.option('--ipv6', is_flag=True, help="Show only BGP IPv6 unicast prefixes")
@click.option('--vrf', type=str, help="Show information for VRF VRF-NAME")
@click.option('--json', is_flag=True, help="JSON output")
@click.option('--verbose', is_flag=True, help="Enable verbose output")
def ip(args, verbose, ipv4, ipv6, vrf, json):
    """
    Show BGP NLRI Prefix information.\n
         PREFIX      Show detailed information for the specified IP-PREFIX\n
    """

    cmd = 'sudo docker exec bgp /opt/framewave/bin/show-bgp'
    for arg in args:
        cmd += " " + str(arg)
    if ipv4:
        cmd += " --ipv4"
    if ipv6:
        cmd += " --ipv6"
    if vrf is not None:
        cmd += " --vrf " + str(vrf)
    if json:
        cmd += " --json"
    run_command(cmd, display_cmd=verbose)


# Autocomplete function for the counters argument
def ac_counters(ctx, args, incomplete):
    arg_string = ['counters']
    return [elem for elem in arg_string if incomplete in elem]


# 'neighbor' subcommand ("show bgp neighbor")
@bgp.command(context_settings=dict(max_content_width=120))
@click.argument('address', metavar='[IP-ADDRESS]', nargs=1, required=False)
@click.argument('counters', metavar='[counters]', nargs=1, required=False, autocompletion=ac_counters)
@click.option('--vrf', type=str, help="Show information for VRF VRF-NAME")
@click.option('--json', is_flag=True, help="JSON output")
@click.option('--verbose', is_flag=True, help="Enable verbose output")
def neighbor(address, verbose, counters, vrf, json):
    """
    Show BGP neighbor information.\n
         IP-ADDRESS  Show detailed information for the specified IP-ADDRESS\n
         counters    Show counters info for specified neighbor\n
    """

    cmd = 'sudo docker exec bgp /opt/framewave/bin/show-bgp-neighbors'
    if address is not None:
        cmd += " address " + str(address)

    if counters is not None:
        if str(counters) == 'counters':
            cmd += " --counters"
        else:
            print("Usage: show bgp neighbor [IP-ADDRESS] [counters]\n\n"
                  "Error: Got unexpected extra argument: (" + str(counters) + ")")
            return

    if vrf is not None:
        cmd += " --vrf " + str(vrf)
    if json:
        cmd += " --json"
    run_command(cmd, display_cmd=verbose)


# 'neighbor_routes' subcommand ("show bgp neighbor routes")
@bgp.command(context_settings=dict(max_content_width=120))
@click.argument('route_type', type=click.Choice(['advertised', 'received']), nargs=1, required=True)
@click.argument('peer', metavar='[PEER-ADDRESS] ', nargs=1, required=False)
@click.option('--addr-type', type=click.Choice(['ipv4', 'ipv6', 'vpnv4', 'vpnv6'],
                                                case_sensitive=False),
              help="Show BGP neighbor routes from specified address type")
@click.option('--vrf', type=str, help="Show information for VRF VRF-NAME")
@click.option('--json', is_flag=True, help="JSON output")
@click.option('--verbose', is_flag=True, help="Enable verbose output")
def neighbor_routes(route_type, peer, verbose, vrf, addr_type, json):
    """
    Show BGP neighbor route information.\n
       advertised | received    Route type to display\n
       PEER-ADDRESS             Show detailed information for the specified PEER-ADDRESS\n
    """

    cmd = 'sudo docker exec bgp /opt/framewave/bin/show-bgp-neighbors-routes'
    if route_type is not None:
        cmd += " " + str(route_type)
    if peer is not None:
        cmd += " " + str(peer)
    if vrf is not None:
        cmd += " --vrf " + str(vrf)
    if addr_type is not None:
        cmd += " --" + str(addr_type)
    if json:
        cmd += " --json"
    run_command(cmd, display_cmd=verbose)


# 'l3vpn' subcommand ("show bgp l3vpn")
@bgp.command(context_settings=dict(max_content_width=120))
@click.argument('prefix', metavar='[PREFIX]', nargs=1, required=False)
@click.option('--vpnv4', is_flag=True, help="Show only BGP VPNv4 unicast prefixes.")
@click.option('--vpnv6', is_flag=True, help="Show only BGP VPNv6 unicast prefixes.")
@click.option('--json', is_flag=True, help="JSON output")
@click.option('--verbose', is_flag=True, help="Enable verbose output")
def l3vpn(prefix, verbose, vpnv4, vpnv6, json):
    """
    Show BGP NLRI L3VPN information.\n
       IP-PREFIX     Show detailed information for the specified IP-PREFIX\n
    """

    cmd = 'sudo docker exec bgp /opt/framewave/bin/show-bgp-l3vpn'
    if prefix is not None:
        cmd += " " + str(prefix)
    if vpnv4:
        cmd += " --vpnv4"
    elif vpnv6:
        cmd += " --vpnv6"
    if json:
        cmd += " --json"
    run_command(cmd, display_cmd=verbose)
