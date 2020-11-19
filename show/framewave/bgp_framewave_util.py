import json

import click
import utilities_common.cli as clicommon
import utilities_common.multi_asic as multi_asic_util
import utilities_common.bgp_util as bgp_util
from natsort import natsorted
from sonic_py_common import multi_asic
from tabulate import tabulate
from utilities_common import constants


def run_bgp_framewave_command(show_cmd, bgp_namespace=multi_asic.DEFAULT_NAMESPACE):
    bgp_instance_id = ' '
    output = None
    if bgp_namespace is not multi_asic.DEFAULT_NAMESPACE:
        bgp_instance_id = " -n {} ".format(multi_asic.get_asic_id_from_name(bgp_namespace))

    cmd = 'sudo docker exec bgp{} /opt/framewave/bin/{}'.format(bgp_instance_id, show_cmd)

    try:
        output = clicommon.run_command(cmd, return_cmd=True)
    except Exception:
        ctx = click.get_current_context()
        ctx.fail("Unable to get summary from bgp".format(bgp_instance_id))

    return output


def get_bgp_framewave_summary_from_all_bgp_instances(namespace, display):

    device = multi_asic_util.MultiAsic(display, namespace)
    ctx = click.get_current_context()

    show_cmd = "show-bgp-neighbors --json"

    bgp_summary = {}
    cmd_output_json = {}
    for ns in device.get_ns_list_based_on_options():
        cmd_output = run_bgp_framewave_command(show_cmd, ns)
        try:
            cmd_output_json = json.loads(cmd_output)
        except ValueError:
            ctx.fail("bgp summary from bgp container not in json format")

        device.current_namespace = ns

        process_bgp_summary_framewave_json(bgp_summary, cmd_output_json, device)
    return bgp_summary


def display_bgp_framewave_summary(bgp_summary):
    '''
    Display the json output in the format display by framewave

    Args:
        bgp_summary ([dict]): [Bgp summary from all bgp instances in ]

    '''
    headers = ["Neighbor", "V", "AS", "MsgRcvd", "MsgSent", "TblVer",
               "InQ", "OutQ", "Up/Down", "State/PfxRcd", "NeighborName"]

    try:
        click.echo("\nIP Unicast Summary:")
        # display the bgp instance information
        for router_info in bgp_summary['router_info']:
            for k in router_info.keys():
                v = router_info[k]
                instance = "{}: ".format(k) if k is not "" else ""
                click.echo(
                    "{}BGP router identifier {}, local AS number {} vrf-id {}" .format(
                        instance, v['router_id'], v['as'], v['vrf']))
                click.echo("BGP table version {}".format(v['tbl_ver']))

        click.echo("RIB entries {}, using {} bytes of memory"
                   .format(bgp_summary['ribCount'], bgp_summary['ribMemory']))
        click.echo(
            "Peers {}, using {} KiB of memory" .format(
                bgp_summary['peerCount'],
                bgp_summary['peerMemory']))
        click.echo("Peer groups {}, using {} bytes of memory" .format(
            bgp_summary['peerGroupCount'], bgp_summary['peerGroupMemory']))
        click.echo("\n")

        click.echo(tabulate(natsorted(bgp_summary['peers']), headers=headers))
        click.echo("\nTotal number of neighbors {}".
                   format(len(bgp_summary['peers'])))
    except KeyError as e:
        ctx = click.get_current_context()
        ctx.fail("{} missing in the bgp_summary".format(e.args[0]))

def process_bgp_summary_framewave_json(bgp_summary, cmd_output, device):
    '''
    This function process the framewave output in json format from a bgp
    instance and stores the need values in the a bgp_summary

    '''
    static_neighbors, dynamic_neighbors = bgp_util.get_bgp_neighbors_dict(
        device.current_namespace)
    try:
        bgp_summary['peerMemory'] = bgp_summary.get(
            'peerMemory', 0) + 0
        bgp_summary['ribCount'] = bgp_summary.get(
            'ribCount', 0) + 0
        bgp_summary['ribMemory'] = bgp_summary.get(
            'ribMemory', 0) + 0
        bgp_summary['peerGroupCount'] = bgp_summary.get(
            'peerGroupCount', 0) + 0
        bgp_summary['peerGroupMemory'] = bgp_summary.get(
            'peerGroupMemory', 0) + 0

        # store instance level field is seperate dict
        router_info = dict()
        router_info['router_id'] = "1.2.3.4"
        router_info['vrf'] = 0
        router_info['as'] = 100
        router_info['tbl_ver'] = 1
        bgp_summary.setdefault('router_info', []).append(
            {device.current_namespace: router_info})

        for peer in cmd_output:

            # add all the router level fields
            bgp_summary['peerCount'] = bgp_summary.get(
                'peerCount', 0) + 1

            peers = []
            # if display option is 'frontend', internal bgp neighbors will not
            # be displayed
            if device.skip_display(constants.BGP_NEIGH_OBJ, peer['remote-address']):
                continue

            peers.append(peer['remote-address'])
            if ":" in peer['remote-address']:
                peers.append("6")
            else:
                peers.append("4")
            peers.append(peer['remote-as'])
            peers.append(peer['in-total-messages'])
            peers.append(peer['out-total-messages'])
            peers.append(0)
            peers.append(0)
            peers.append(0)
            peers.append(peer['fsm-established-time'])
            if peer['state'] == 'established':
                peers.append(peer['in-prefixes'])
            else:
                peers.append(peer['state'])

            # Get the bgp neighbour name and store it
            neigh_name = bgp_util.get_bgp_neighbor_ip_to_name(
                peer['remote-address'], static_neighbors, dynamic_neighbors)
            peers.append(neigh_name)

            bgp_summary.setdefault('peers', []).append(peers)
    except KeyError as e:
        ctx = click.get_current_context()
        ctx.fail("{} missing in the bgp_summary".format(e.args[0]))
