import click
import json
import re
from natsort import natsorted
from tabulate import tabulate
from natsort import natsorted
from tabulate import tabulate
from show.main import *

def parse_bgp_summary(summ):
    """turn output of show ip bgp summary to a list"""
    ls = summ.splitlines()
    bgpinfo = []
    # Read until the table header
    n = len(ls)
    li = 0
    while li < n:
        l = ls[li]
        if l.startswith('Neighbor        '): break
        if l.startswith('No IPv'):  # eg. No IPv6 neighbor is configured
            return bgpinfo
        if l.endswith('> exit'):  # last command in the lines
            return bgpinfo
        li += 1
    # Read and store the table header
    if li >= n:
        raise ValueError('No table header found')
    hl = ls[li]
    li += 1
    ht = re.split('\s+', hl.rstrip())
    hn = len(ht)
    # Read rows in the table
    while li < n:
        l = ls[li]
        li += 1
        if l == '': break
        # Handle line wrap
        # ref: bgp_show_summary in https://github.com/Azure/sonic-quagga/blob/debian/0.99.24.1/bgpd/bgp_vty.c
        if ' ' not in l:
            # Read next line
            if li >= n:
                raise ValueError('Unexpected line wrap')
            l += ls[li]
            li += 1
        # Note: State/PfxRcd field may be 'Idle (Admin)'
        lt = re.split('\s+', l.rstrip(), maxsplit=hn - 1)
        if len(lt) != hn:
            raise ValueError('Unexpected row in the table')
        dic = dict(zip(ht, lt))
        bgpinfo.append(dic)
    return bgpinfo


def run_command_save(command, display_cmd=False):
    """run a command and save the output"""
    if display_cmd:
        click.echo(click.style("Command: ", fg='cyan') + click.style(command, fg='green'))
    try:
        proc = subprocess.Popen(command,
                                stdout=subprocess.PIPE,
                                shell=True,
                                stderr=subprocess.STDOUT)
        stdout = proc.communicate()[0]
        proc.wait()
        result = stdout.rstrip('\n')
    except OSError, e:
        raise OSError("Error running command")
    return (result)

###############################################################################
#
# 'show ip bgp' cli stanza
#
###############################################################################


@ip.group(cls=AliasedGroup, default_if_no_args=False)
def bgp():
    """Show IPv4 BGP (Border Gateway Protocol) information"""
    pass

#
# 'bgp' group ("show ip bgp ...")
#
@bgp.group(cls=AliasedGroup, default_if_no_args=False, invoke_without_command=True)
@click.pass_context
# 'summary' subcommand ("show ip bgp summary")
def summary(ctx):
    if ctx.invoked_subcommand is None:
        """Show summarized information of IPv4 BGP state"""
        run_command('sudo vtysh -c "show ip bgp summary"')

# 'enhanced' subcommand ("show ip bgp summary enhanced")
@summary.command()
def enhanced():
    """Show BGP summary with Devicename and advertised-routes"""
    # get bgp summary table from cli and save as dictionary
    bgpsum_cmd = 'sudo vtysh -c "show ip bgp summary"'
    bgpsum_output = run_command_save(bgpsum_cmd)
    parse_bgp_sum_output = parse_bgp_summary(bgpsum_output)
    # only preform the following if there is data from BGP summary
    if len(parse_bgp_sum_output) > 0:
        bgpsum_dict = {}
        for item in parse_bgp_sum_output:
            bgpsum_dict[item['Neighbor']] = {'V': item['V'],
                                             'AS': item['AS'],
                                             'MsgRcvd': item['MsgRcvd'],
                                             'MsgSent': item['MsgSent'],
                                             'TblVer': item['TblVer'],
                                             'InQ': item['InQ'],
                                             'OutQ': item['OutQ'],
                                             'Up/Down': item['Up/Down'],
                                             'State/PfxRcd': item['State/PfxRcd']}
        # create a list of BGP neighbor
        neighborIP = bgpsum_dict.keys()
        neighbor_adv_dict = {}
        # get advestise prefix per neighbor
        for item in neighborIP:
            pfxadv = run_command_save('sudo vtysh -c "show ip bgp nei {0} advertised-routes" | grep Total'.format(item))
            no_pfxadv = re.findall('[0-9]+', pfxadv, flags=re.I)[0]
            neighbor_adv_dict[item] = {'PfxAdv': no_pfxadv}
        # get BGP neighbor name
        bgp_neighbor_cmd = 'sonic-cfggen -d --var-json "BGP_NEIGHBOR"'
        p = subprocess.Popen(bgp_neighbor_cmd, shell=True, stdout=subprocess.PIPE)
        bgp_neighbor_dict = json.loads(p.stdout.read())

        header = ['NeighborIP', 'V', 'AS', 'MsgRcvd', 'MsgSent', 'TblVer', 'InQ', 'OutQ', 'Up/Down', 'State/PfxRcd',
                  'PfxAdv', 'Device']
        body = []

        for neighborIP in natsorted(bgpsum_dict):
            body.append([neighborIP,
                         bgpsum_dict[neighborIP]['V'],
                         bgpsum_dict[neighborIP]['AS'],
                         bgpsum_dict[neighborIP]['MsgRcvd'],
                         bgpsum_dict[neighborIP]['MsgSent'],
                         bgpsum_dict[neighborIP]['TblVer'],
                         bgpsum_dict[neighborIP]['InQ'],
                         bgpsum_dict[neighborIP]['OutQ'],
                         bgpsum_dict[neighborIP]['Up/Down'],
                         bgpsum_dict[neighborIP]['State/PfxRcd'],
                         neighbor_adv_dict[neighborIP]['PfxAdv'],
                         bgp_neighbor_dict[neighborIP]['name']
                         ])
        click.echo(tabulate(body, header))
    else:
        click.echo('No bgp summary data')

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
