#!/usr/sbin/env python

import click
import json
import os
import re
import subprocess
import sys

SONIC_CFGGEN_PATH = "/usr/local/bin/sonic-cfggen"
MINIGRAPH_PATH = "/etc/sonic/minigraph.xml"
MINIGRAPH_BGP_ASN_KEY = "minigraph_bgp_asn"
MINIGRAPH_BGP_SESSIONS = "minigraph_bgp"

BGP_ADMIN_STATE_YML_PATH = "/etc/sonic/bgp_admin.yml"

ANYDROP_FILE_NAME = "anydrop.json"

#
# Helper functions
#

# Print output information
def echo_info(prefix, content):
    click.echo(click.style('{}: '.format(prefix), fg='cyan') + click.style(content, fg='green'))

# Run bash command and print output to stdout
def run_command(command, pager=False, display_cmd=False, display_info=''):
    if display_info:
        echo_info('Doing task', display_info)

    if display_cmd == True:
        echo_info('Running command', command)

    p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)
    stdout = p.communicate()[0]
    p.wait()

    if len(stdout) > 0:
        if pager is True:
            click.echo_via_pager(p.stdout.read())
        else:
            click.echo(p.stdout.read())

    if p.returncode != 0:
        sys.exit(p.returncode)

# Run background bash command and return output
def run_bg_command(command):
    p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)
    stdout = p.communicate()[0]
    p.wait()
    return stdout

# Generate configurations and apply the configurations using swssconfig
def apply_swss_config(config, file_name):
    echo_info('Doing task', 'generate temporary configurations at {}'.format(file_name))
    file_path = '/tmp/{}'.format(file_name)
    with open(file_path, 'w') as output_file:
        json.dump(config, output_file, indent=4)
    # Copy the config file into swss docker
    command = 'docker cp {} swss:/tmp'.format(file_path)
    run_command(command, display_info='copy configurations into SwSS docker')
    # Apply the config file using swssconfig
    command = 'docker exec -it swss swssconfig {}'.format(file_path)
    run_command(command, display_info='apply configurations using swssconfig')

# Generate ANYDROP mirror session with a taget destination IP
def _generate_mirror_session(dst_ip_addr):
    RE_IFCONFIG_ETH0_IP = r'inet addr:([\d.]+)'

    ifconfig = run_bg_command('ifconfig eth0')
    src_ip_addr = re.findall(RE_IFCONFIG_ETH0_IP, ifconfig)[0]
    mirror_dict = {}
    mirror_dict['SRC_IP'] = src_ip_addr
    mirror_dict['DST_IP'] = dst_ip_addr
    mirror_dict['GRE_TYPE'] = '0x6558'
    mirror_dict['DSCP'] = '50'
    mirror_dict['TTL'] = '255'
    return {"MIRROR_SESSION_TABLE:ANYDROP": mirror_dict, "OP":"SET"}

# Generate ANYDROP rule that override the current DEFAULT_RULE
def _generate_acl_mirror_rule():
    try:
        aclshow = run_bg_command(['aclshow -a -r DEFAULT_RULE']).splitlines()[2].split()
    except IndexError:
        print "Error: could not locate DEFAULT_RULE"
        raise click.Abort
    table_name = aclshow[1]
    acl_dict = {}
    acl_dict['ETHER_TYPE'] = '0x0800'
    acl_dict['MIRROR_ACTION'] = 'ANYDROP'
    acl_dict['PRIORITY'] = int(aclshow[3]) + 1
    return {"ACL_RULE_TABLE:" + table_name + ":ANYDROP_RULE": acl_dict, "OP":"SET"}

# Remove ANYDROP mirror session
def _generate_mirror_session_del_rule():
    return {"MIRROR_SESSION_TABLE:ANYDROP": {}, "OP":"DEL"}

# Remove ANYDROP rule
def _generate_acl_del_rule():
    try:
        aclshow = run_bg_command(['aclshow -a -r ANYDROP_RULE']).splitlines()[2].split()
    except IndexError:
        print "Error: could not locate ANYDROP_RULE"
        raise click.Abort
    table_name = aclshow[1]
    return {"ACL_RULE_TABLE:" + table_name + ":ANYDROP_RULE": {}, "OP":"DEL"}

# Returns BGP ASN as a string
def _get_bgp_asn_from_minigraph():
    # Get BGP ASN from minigraph
    proc = subprocess.Popen([SONIC_CFGGEN_PATH, '-m', MINIGRAPH_PATH, '--var-json', MINIGRAPH_BGP_ASN_KEY],
                            stdout=subprocess.PIPE,
                            shell=False,
                            stderr=subprocess.STDOUT)
    stdout = proc.communicate()[0]
    proc.wait()
    return json.loads(stdout.rstrip('\n'))

# Returns True if a neighbor has the IP address <ipaddress>, False if not
def _is_neighbor_ipaddress(ipaddress):
    # Get BGP sessions from minigraph
    proc = subprocess.Popen([SONIC_CFGGEN_PATH, '-m', MINIGRAPH_PATH, '--var-json', MINIGRAPH_BGP_SESSIONS],
                            stdout=subprocess.PIPE,
                            shell=False,
                            stderr=subprocess.STDOUT)
    stdout = proc.communicate()[0]
    proc.wait()
    bgp_session_list = json.loads(stdout.rstrip('\n'))

    for session in bgp_session_list:
        if session['addr'] == ipaddress:
            return True

    return False

# Returns list of strings containing IP addresses of all BGP neighbors
def _get_all_neighbor_ipaddresses():
    # Get BGP sessions from minigraph
    proc = subprocess.Popen([SONIC_CFGGEN_PATH, '-m', MINIGRAPH_PATH, '--var-json', MINIGRAPH_BGP_SESSIONS],
                            stdout=subprocess.PIPE,
                            shell=False,
                            stderr=subprocess.STDOUT)
    stdout = proc.communicate()[0]
    proc.wait()
    bgp_session_list = json.loads(stdout.rstrip('\n'))

    bgp_neighbor_ip_list =[]

    for session in bgp_session_list:
        bgp_neighbor_ip_list.append(session['addr'])

    return bgp_neighbor_ip_list



# Returns string containing IP address of neighbor with hostname <hostname> or None if <hostname> not a neighbor
def _get_neighbor_ipaddress_by_hostname(hostname):
    # Get BGP sessions from minigraph
    proc = subprocess.Popen([SONIC_CFGGEN_PATH, '-m', MINIGRAPH_PATH, '--var-json', MINIGRAPH_BGP_SESSIONS],
                            stdout=subprocess.PIPE,
                            shell=False,
                            stderr=subprocess.STDOUT)
    stdout = proc.communicate()[0]
    proc.wait()
    bgp_session_list = json.loads(stdout.rstrip('\n'))

    for session in bgp_session_list:
        if session['name'] == hostname:
            return session['addr']

    return None

# Shut down BGP session by IP address and modify bgp_admin.yml accordingly
def _bgp_session_shutdown(bgp_asn, ipaddress, verbose):
    click.echo("Shutting down BGP session with neighbor {}...".format(ipaddress))

    # Shut down the BGP session
    command = "vtysh -c 'configure terminal' -c 'router bgp {}' -c 'neighbor {} shutdown'".format(bgp_asn, ipaddress)
    run_command(command, display_cmd=verbose)

    if os.path.isfile(BGP_ADMIN_STATE_YML_PATH):
        # Remove existing item in bgp_admin.yml about the admin state of this neighbor
        command = "sed -i \"/^\s*{}:/d\" {}".format(ipaddress, BGP_ADMIN_STATE_YML_PATH)
        run_command(command, display_cmd=verbose)

        # and add a new line mark it as off
        command = "echo \"  {}: off\" >> {}".format(ipaddress, BGP_ADMIN_STATE_YML_PATH)
        run_command(command, display_cmd=verbose)

# Start up BGP session by IP address and modify bgp_admin.yml accordingly
def _bgp_session_startup(bgp_asn, ipaddress, verbose):
    click.echo("Starting up BGP session with neighbor {}...".format(ipaddress))

    # Start up the BGP session
    command = "vtysh -c 'configure terminal' -c 'router bgp {}' -c 'no neighbor {} shutdown'".format(bgp_asn, ipaddress)
    run_command(command, display_cmd=verbose)

    if os.path.isfile(BGP_ADMIN_STATE_YML_PATH):
        # Remove existing item in bgp_admin.yml about the admin state of this neighbor
        command = "sed -i \"/^\s*{}:/d\" {}".format(ipaddress, BGP_ADMIN_STATE_YML_PATH)
        run_command(command, display_cmd=verbose)

        # and add a new line mark it as on
        command = "echo \"  {}: on\" >> {}".format(ipaddress, BGP_ADMIN_STATE_YML_PATH)
        run_command(command, display_cmd=verbose)


# This is our main entrypoint - the main 'config' command
@click.group()
def cli():
    """SONiC command line - 'config' command"""
    if os.geteuid() != 0:
        exit("Root privileges are required for this operation")

#
# 'everflow' group
#

@cli.group()
def everflow():
    """Everflow-related tasks"""
    pass

# 'acldrop' subcommand
@everflow.command()
@click.argument('dst_ip_addr', required=True)
def acldrop(dst_ip_addr):
    """Mirror ACL drop"""
    # Step 1: Create the mirror session
    mirror_session = _generate_mirror_session(dst_ip_addr)
    # Step 2: Create the ACL rule
    acl_rule = _generate_acl_mirror_rule()
    # Step 3: Apply configurations
    apply_swss_config([mirror_session, acl_rule], ANYDROP_FILE_NAME)

#
# 'no' group
#

@everflow.group()
def no():
    pass

# 'acldrop' subcommand
@no.command()
def acldrop():
    """Remove mirror ACL drop"""
    # Step 1: Create the ACL rule removal configuration
    acl_rule = _generate_acl_del_rule()
    # Step 2: Create the mirror session removal configuration
    mirror_session = _generate_mirror_session_del_rule()
    # Step 3: Apply configurations
    apply_swss_config([acl_rule, mirror_session], ANYDROP_FILE_NAME)

#
# 'bgp' group
#

@cli.group()
def bgp():
    """BGP-related configuration tasks"""
    pass

#
# 'shutdown' subgroup
#

@bgp.group()
def shutdown():
    """Shut down BGP session(s)"""
    pass

# 'all' subcommand
@shutdown.command()
@click.option('-v', '--verbose', is_flag=True, help="Enable verbose output")
def all(verbose):
    """Shut down all BGP sessions"""

    bgp_asn = _get_bgp_asn_from_minigraph()
    bgp_neighbor_ip_list = _get_all_neighbor_ipaddresses()

    for ipaddress in bgp_neighbor_ip_list:
        _bgp_session_shutdown(bgp_asn, ipaddress, verbose)

# 'neighbor' subcommand
@shutdown.command()
@click.argument('ipaddr_or_hostname', metavar='<ipaddr_or_hostname>', required=True)
@click.option('-v', '--verbose', is_flag=True, help="Enable verbose output")
def neighbor(ipaddr_or_hostname, verbose):
    """Shut down BGP session by neighbor IP address or hostname"""
    bgp_asn = _get_bgp_asn_from_minigraph()

    if _is_neighbor_ipaddress(ipaddr_or_hostname):
        ipaddress = ipaddr_or_hostname
    else:
        # If <ipaddr_or_hostname> is not the IP address of a neighbor, check to see if it's a hostname
        ipaddress = _get_neighbor_ipaddress_by_hostname(ipaddr_or_hostname)

    if ipaddress == None:
        print "Error: could not locate neighbor '{}'".format(ipaddr_or_hostname)
        raise click.Abort

    _bgp_session_shutdown(bgp_asn, ipaddress, verbose)


@bgp.group()
def startup():
    """Start up BGP session(s)"""
    pass

# 'all' subcommand
@startup.command()
@click.option('-v', '--verbose', is_flag=True, help="Enable verbose output")
def all(verbose):
    """Start up all BGP sessions"""
    bgp_asn = _get_bgp_asn_from_minigraph()
    bgp_neighbor_ip_list = _get_all_neighbor_ipaddresses()

    for ipaddress in bgp_neighbor_ip_list:
        _bgp_session_startup(bgp_asn, ipaddress, verbose)

# 'neighbor' subcommand
@startup.command()
@click.argument('ipaddr_or_hostname', metavar='<ipaddr_or_hostname>', required=True)
@click.option('-v', '--verbose', is_flag=True, help="Enable verbose output")
def neighbor(ipaddr_or_hostname, verbose):
    """Start up BGP session by neighbor IP address or hostname"""
    bgp_asn = _get_bgp_asn_from_minigraph()

    if _is_neighbor_ipaddress(ipaddr_or_hostname):
        ipaddress = ipaddr_or_hostname
    else:
        # If <ipaddr_or_hostname> is not the IP address of a neighbor, check to see if it's a hostname
        ipaddress = _get_neighbor_ipaddress_by_hostname(ipaddr_or_hostname)

    if ipaddress == None:
        print "Error: could not locate neighbor '{}'".format(ipaddr_or_hostname)
        raise click.Abort

    _bgp_session_startup(bgp_asn, ipaddress, verbose)

#
# 'interface' group
#

@cli.group()
def interface():
    """Interface-related configuration tasks"""
    pass

#
# 'shutdown' subcommand
#

@interface.command()
@click.argument('interface_name', metavar='<interface_name>', required=True)
@click.option('-v', '--verbose', is_flag=True, help="Enable verbose output")
def shutdown(interface_name, verbose):
    """Shut down interface"""
    command = "ip link set {} down".format(interface_name)
    run_command(command, display_cmd=verbose)

#
# 'startup' subcommand
#

@interface.command()
@click.argument('interface_name', metavar='<interface_name>', required=True)
@click.option('-v', '--verbose', is_flag=True, help="Enable verbose output")
def startup(interface_name, verbose):
    """Start up interface"""
    command = "ip link set {} up".format(interface_name)
    run_command(command, display_cmd=verbose)


if __name__ == '__main__':
    cli()
