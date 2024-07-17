import click

# from sonic_py_common import multi_asic
import utilities_common.cli as clicommon
from show.main import cli
import utilities_common.multi_asic as multi_asic_util
import utilities_common.bgp_util as bgp_util
import utilities_common.constants as constants


@cli.group(cls=clicommon.AliasedGroup)
def evpn():
    """Show BGP EVPN (Ethernet VPN) information"""
    pass


# 'es' subcommand ("show bgp evpn")
@evpn.command(name='es')
@click.option('--detail', is_flag=True, required=False)
@multi_asic_util.multi_asic_click_options
def es(detail, namespace, display):
    """Show summarized information of BGP EVPN ES state"""
    es_details = bgp_util.get_bgp_evpn_es_detais_from_all_bgp_instances(namespace, display, detail)
    if detail:
        bgp_util.display_bgp_evpn_es_detail(es_details)
    else:
        bgp_util.display_bgp_evpn_es(es_details)


# 'es-evi' subcommand ("show bgp evpn")
@evpn.command(name='es-evi')
@multi_asic_util.multi_asic_click_options
def es_evi(namespace, display):
    """Show summarized information of BGP EVPN ES state with VNI"""
    es_details = bgp_util.get_bgp_evpn_es_evi_detais_from_all_bgp_instances(namespace, display)
    bgp_util.display_bgp_evpn_es_evi(es_details)


# 'route' subcommand ("show bgp evpn")
@evpn.command(name='route')
@click.option('--type', required=False, type=int)
@multi_asic_util.multi_asic_click_options
def route(type, namespace, display):
    """
    Show summarized information of BGP EVPN routes
    Uses 'as is' format. TODO should be updated to JSON as soon as
        https://github.com/FRRouting/frr/issues/5325
        will be fixed
    """
    if type is not None:
        if type < 1 or type > 5:
            # Type-1 to Type-5 are valid BGP routes
            raise click.ClickException('Invalid route type')
    device = multi_asic_util.MultiAsic(display, namespace)
    vtysh_cmd = "show bgp l2vpn evpn route" + (" type {}".format(type) if type else "")

    cmd_output = {}

    for ns in device.get_ns_list_based_on_options():
        cmd_output = bgp_util.run_bgp_command(vtysh_cmd, ns, constants.RVTYSH_COMMAND)
        device.current_namespace = ns
        click.echo('\nNamespace: {}'.format(ns if ns else 'default'))
        click.echo(cmd_output)
