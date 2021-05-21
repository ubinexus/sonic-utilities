#!/usr/sbin/env python

import click
import swsssdk
import ipaddress


CFG_PORTCHANNEL_PREFIX = "PortChannel"
CFG_PORTCHANNEL_PREFIX_LEN = 11
CFG_PORTCHANNEL_MAX_VAL = 9999
CFG_PORTCHANNEL_NAME_TOTAL_LEN_MAX = 15
CFG_PORTCHANNEL_NO="<0-9999>"

def mclag_domain_id_valid(domain_id):
    """Check if the domain id is in acceptable range (between 1 and 4095)
    """

    if domain_id<1 or domain_id>4095:
        return False

    return True

def is_portchannel_name_valid(portchannel_name):
    """Port channel name validation
    """
    # Return True if Portchannel name is PortChannelXXXX (XXXX can be 0-9999)
    if portchannel_name[:CFG_PORTCHANNEL_PREFIX_LEN] != CFG_PORTCHANNEL_PREFIX :
        return False
    if (portchannel_name[CFG_PORTCHANNEL_PREFIX_LEN:].isdigit() is False or
          int(portchannel_name[CFG_PORTCHANNEL_PREFIX_LEN:]) > CFG_PORTCHANNEL_MAX_VAL) :
        return False
    if len(portchannel_name) > CFG_PORTCHANNEL_NAME_TOTAL_LEN_MAX:
        return False
    return True

def is_ipv4_addr_valid(addr):
    v4_invalid_list = [ipaddress.IPv4Address(str('0.0.0.0')), ipaddress.IPv4Address(str('255.255.255.255'))]
    try:
        ip = ipaddress.ip_address(str(addr))
        if (ip.version == 4):
            if (ip.is_reserved):
                click.echo ("{} Not Valid, Reason: IPv4 reserved address range.".format(addr))
                return False
            elif (ip.is_multicast):
                click.echo ("{} Not Valid, Reason: IPv4 Multicast address range.".format(addr))
                return False
            elif (ip in v4_invalid_list):
                click.echo ("{} Not Valid.".format(addr))
                return False
            else:
                return True

        else:
            click.echo ("{} Not Valid, Reason: Not an IPv4 address".format(addr))
            return False

    except ValueError:
        return False



def check_if_interface_is_valid(db, interface_name):
    from main import interface_name_is_valid
    if interface_name_is_valid(db,interface_name) is False:
        ctx.fail("Interface name is invalid. Please enter a valid interface name!!")


######
#
# 'mclag' group ('config mclag ...')
#
@click.group()
@click.pass_context
def mclag(ctx):
    config_db = swsssdk.ConfigDBConnector()
    config_db.connect()
    ctx.obj = {'db': config_db}


#mclag domain add 
@mclag.command('add')
@click.argument('domain_id', metavar='<domain_id>', required=True, type=int)
@click.argument('local_ip', metavar='<local_ip>', required=True)
@click.argument('peer_ip', metavar='<peer_ip>', required=True)
@click.argument('peer_link', metavar='<peer_link>', required=False)
@click.pass_context
def add_mclag_domain(ctx, domain_id, local_ip, peer_ip, peer_link):
    """Add MCLAG Domain"""

    if not mclag_domain_id_valid(domain_id):
        ctx.fail("{} invalid domain ID, valid range is 1 to 4095".format(domain_id))  
    if not is_ipv4_addr_valid(local_ip, True):
        ctx.fail("{} invalid local ip address".format(local_ip))  
    if not is_ipv4_addr_valid(peer_ip, True):
        ctx.fail("{} invalid peer ip address".format(peer_ip))  

    db = ctx.obj['db']
    fvs = {}
    fvs['local_ip'] = str(local_ip)
    fvs['peer_ip'] = str(peer_ip)
    if peer_link is not None:
        if (peer_link.startswith("Ethernet") is False) and (peer_link.startswith("PortChannel") is False):
            ctx.fail("peer link is invalid, should be Ethernet interface or portChannel !!")
        if (peer_link.startswith("Ethernet") is True) and (check_if_interface_is_valid(db, peer_link) is False):
            ctx.fail("peer link Ethernet interface name is invalid. it is not present in port table of configDb!!")
        if (peer_link.startswith("PortChannel")) and (is_portchannel_name_valid(peer_link) is False):
            ctx.fail("peer link PortChannel interface name is invalid !!")
        fvs['peer_link'] = str(peer_link)
    mclag_domain_keys = db.get_table('MC_LAG').keys()
    if len(mclag_domain_keys) == 0:
        db.set_entry('MC_LAG', domain_id, fvs)
    else:
        if domain_id in mclag_domain_keys:
            db.mod_entry('MC_LAG', domain_id, fvs)
        else: 
            ctx.fail("only one mclag Domain can be configured. Already one domain {} configured ".format(mclag_domain_keys[0]))  

#mclag domain delete
#MCLAG Domain del involves deletion of associated MCLAG Ifaces also
@mclag.command('del')
@click.argument('domain_id', metavar='<domain_id>', required=True, type=int)
@click.pass_context
def del_mclag_domain(ctx, domain_id):
    """Delete MCLAG Domain"""

    if not mclag_domain_id_valid(domain_id):
        ctx.fail("{} invalid domain ID, valid range is 1 to 4095".format(domain_id))  

    db = ctx.obj['db']
    entry = db.get_entry('MC_LAG', domain_id)
    if entry is None:
        ctx.fail("MCLAG Domain {} not configured ".format(domain_id))  
        return

    #delete mclag domain
    db.set_entry('MC_LAG', domain_id, None)

#mclag interface config
@mclag.group('interface')
@click.pass_context
def mclag_interface(ctx):
    pass

@mclag_interface.command('add')
@click.argument('domain_id', metavar='<domain_id>', required=True)
@click.argument('mclag_interface', metavar='<mclag_interface>', required=True)
@click.pass_context
def add_mclag_interface(ctx, domain_id, mclag_interface):
    """Add member MCLAG interfaces from MCLAG Domain"""
    db = ctx.obj['db']
    old_portchannel = db.get_entry('MC_LAG', domain_id).get('mclag_interface')
    old_portchannel_list = str(old_portchannel).split(",")
    portchannel_list = mclag_interface.split(",")
    mclag_domain_keys = db.get_table('MC_LAG').keys()
    if len(mclag_domain_keys) != 0:
        if domain_id not in mclag_domain_keys:
            ctx.fail("only one mclag Domain can be configured. Already one domain {} configured ".format(mclag_domain_keys[0]))
            return
    for portchannel_name in portchannel_list:
        if is_portchannel_name_valid(portchannel_name) != True:
            ctx.fail("{} is invalid!, name should have prefix '{}' and suffix '{}'" .format(portchannel_name, CFG_PORTCHANNEL_PREFIX, CFG_PORTCHANNEL_NO))
        if portchannel_name not in old_portchannel_list:
            old_portchannel_list.append(portchannel_name)
    if len(old_portchannel_list) != 0:
        old_portchannel_list.sort()
        num = 1
        mclag_intf_names = ""
        for name_add in old_portchannel_list:
            if num == 1:
                 mclag_intf_names = name_add
            else:
                 mclag_intf_names = mclag_intf_names + "," + name_add
            num = num + 1
        db.set_entry('MC_LAG', domain_id, {'mclag_interface':mclag_intf_names} )

@mclag_interface.command('del')
@click.argument('domain_id', metavar='<domain_id>', required=True)
@click.argument('mclag_interface', metavar='<mclag_interface>', required=True)
@click.pass_context
def del_mclag_interface(ctx, domain_id, mclag_interface):
    """Delete member MCLAG interfaces from MCLAG Domain"""
    db = ctx.obj['db']
    entry = db.get_entry('MC_LAG', domain_id)
    if entry is None:
        ctx.fail("MCLAG Domain {} not configured ".format(domain_id))  
        return
    #split comma seperated portchannel names
    old_portchannel = db.get_entry('MC_LAG', domain_id).get('mclag_interface')
    old_portchannel_list = str(old_portchannel).split(",")
    portchannel_list = mclag_interface.split(",")
    for portchannel_name in portchannel_list:
        if is_portchannel_name_valid(portchannel_name) != True:
            ctx.fail("{} is invalid!, name should have prefix '{}' and suffix '{}'" .format(portchannel_name, CFG_PORTCHANNEL_PREFIX, CFG_PORTCHANNEL_NO))
        if portchannel_name  in old_portchannel_list:
            old_portchannel_list.remove(portchannel_name)
    if len(old_portchannel_list) != 0:
        old_portchannel_list.sort()
        num = 1
        mclag_intf_names = ""
        for name_add in old_portchannel_list:
            if num == 1:
                 mclag_intf_names = name_add
            else:
                 mclag_intf_names = mclag_intf_names + "," + name_add
            num = num + 1
        db.set_entry('MC_LAG', domain_id, {'mclag_interface':mclag_intf_names} )
    else:
        db.set_entry('MC_LAG', domain_id, {'mclag_interface':None} )

#config commit
@mclag.command('config-commit')
@click.pass_context
def config_mclag_commit(ctx):
    """Configure MCLAG commit"""
    db = ctx.obj['db']
    from main import execute_systemctl

    services_to_restart = [
        'iccpd'
    ]

    execute_systemctl(services_to_restart, "restart")

#######
