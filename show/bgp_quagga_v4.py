import click
from show.main import get_bgp_summary_extended, ip, multi_instance_bgp_summary, run_command
from show.multi_npu import multi_npu_process_options
from show.multi_npu import multi_npu_platform



###############################################################################
#
# 'show ip bgp' cli stanza
#
###############################################################################


@ip.group()
def bgp():
    """Show IPv4 BGP (Border Gateway Protocol) information"""
    pass


# 'summary' subcommand ("show ip bgp summary")
@bgp.command()
@mutli_npu_options
def summary(namespace, display_opt):
    """Show summarized information of IPv4 BGP state"""
    if multi_npu_platform():
        multi_instance_bgp_summary(namespace, display_opt)
        return
    try:
        device_output = run_command('sudo vtysh -c "show ip bgp summary"', return_cmd=True)
        get_bgp_summary_extended(device_output)
    except Exception:
        run_command('sudo vtysh -c "show ip bgp summary"')


# 'neighbors' subcommand ("show ip bgp neighbors")
@bgp.command()
@click.argument('ipaddress', required=False)
@click.argument('info_type', type=click.Choice(['routes', 'advertised-routes', 'received-routes']), required=False)
def neighbors(ipaddress, info_type):
    """Show IP (IPv4) BGP neighbors"""

    command = 'sudo vtysh -c "show ip bgp neighbor'

    if ipaddress is not None:
        command += ' {}'.format(ipaddress)

        # info_type is only valid if ipaddress is specified
        if info_type is not None:
            command += ' {}'.format(info_type)

    command += '"'

    run_command(command)
