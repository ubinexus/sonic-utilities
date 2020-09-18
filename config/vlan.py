import click

import utilities_common.cli as clicommon
from .utils import log

#
# 'vlan' group ('config vlan ...')
#
@click.group(cls=clicommon.AbbreviationGroup, name='vlan')
def vlan():
    """VLAN-related configuration tasks"""
    pass

@vlan.command('add')
@click.argument('vid', metavar='<vid>', required=True, type=int)
@clicommon.pass_db
def add_vlan(db, vid):
    """Add VLAN"""

    ctx = click.get_current_context()

    if not clicommon.is_vlanid_in_range(vid):
        ctx.fail("Invalid VLAN ID {} (1-4094)".format(vid))

    vlan = 'Vlan{}'.format(vid)
    if clicommon.check_if_vlanid_exist(db.cfgdb, vlan):
        ctx.fail("{} already exists".format(vlan))

    db.cfgdb.set_entry('VLAN', vlan, {'vlanid': vid})

@vlan.command('del')
@click.argument('vid', metavar='<vid>', required=True, type=int)
@clicommon.pass_db
def del_vlan(db, vid):
    """Delete VLAN"""

    log.log_info("'vlan del {}' executing...".format(vid))

    ctx = click.get_current_context()

    if not clicommon.is_vlanid_in_range(vid):
        ctx.fail("Invalid VLAN ID {} (1-4094)".format(vid))

    vlan = 'Vlan{}'.format(vid)
    if clicommon.check_if_vlanid_exist(db.cfgdb, vlan) == False:
        ctx.fail("{} does not exist".format(vlan))

    keys = [ (k, v) for k, v in db.cfgdb.get_table('VLAN_MEMBER') if k == 'Vlan{}'.format(vid) ]
    for k in keys:
        db.cfgdb.set_entry('VLAN_MEMBER', k, None)
    db.cfgdb.set_entry('VLAN', 'Vlan{}'.format(vid), None)

#
# 'member' group ('config vlan member ...')
#
@vlan.group(cls=clicommon.AbbreviationGroup, name='member')
def vlan_member():
    pass

@vlan_member.command('add')
@click.argument('vid', metavar='<vid>', required=True, type=int)
@click.argument('port', metavar='port', required=True)
@click.option('-u', '--untagged', is_flag=True)
@clicommon.pass_db
def add_vlan_member(db, vid, port, untagged):
    """Add VLAN member"""

    ctx = click.get_current_context()

    log.log_info("'vlan member add {} {}' executing...".format(vid, port))

    if not clicommon.is_vlanid_in_range(vid):
        ctx.fail("Invalid VLAN ID {} (1-4094)".format(vid))

    vlan = 'Vlan{}'.format(vid)
    if clicommon.check_if_vlanid_exist(db.cfgdb, vlan) == False:
        ctx.fail("{} does not exist".format(vlan))

    if clicommon.get_interface_naming_mode() == "alias":
        alias = port
        iface_alias_converter = clicommon.InterfaceAliasConverter(db)
        port = iface_alias_converter.alias_to_name(alias)
        if port is None:
            ctx.fail("cannot find port name for alias {}".format(alias))

    if clicommon.is_port_mirror_dst_port(db.cfgdb, port):
        ctx.fail("{} is configured as mirror destination port".format(port))

    if clicommon.is_port_vlan_member(db.cfgdb, port, vlan):
        ctx.fail("{} is already a member of {}".format(port, vlan))

    if clicommon.is_valid_port(db.cfgdb, port):
        is_port = True
    elif clicommon.is_valid_portchannel(db.cfgdb, port):
        is_port = False
    else:
        ctx.fail("{} does not exist".format(port))

    if (is_port and clicommon.is_port_router_interface(db.cfgdb, port)) or \
       (not is_port and clicommon.is_pc_router_interface(db.cfgdb, port)):
        ctx.fail("{} is a router interface!".format(port))

    db.cfgdb.set_entry('VLAN_MEMBER', (vlan, port), {'tagging_mode': "untagged" if untagged else "tagged" })

@vlan_member.command('del')
@click.argument('vid', metavar='<vid>', required=True, type=int)
@click.argument('port', metavar='<port>', required=True)
@clicommon.pass_db
def del_vlan_member(db, vid, port):
    """Delete VLAN member"""

    ctx = click.get_current_context()

    log.log_info("'vlan member del {} {}' executing...".format(vid, port))

    if not clicommon.is_vlanid_in_range(vid):
        ctx.fail("Invalid VLAN ID {} (1-4094)".format(vid))

    vlan = 'Vlan{}'.format(vid)
    if clicommon.check_if_vlanid_exist(db.cfgdb, vlan) == False:
        ctx.fail("{} does not exist".format(vlan))

    if clicommon.get_interface_naming_mode() == "alias":
        alias = port
        iface_alias_converter = clicommon.InterfaceAliasConverter(db)
        port = iface_alias_converter.alias_to_name(alias)
        if port is None:
            ctx.fail("cannot find port name for alias {}".format(alias))

    if not clicommon.is_port_vlan_member(db.cfgdb, port, vlan):
        ctx.fail("{} is not a member of {}".format(port, vlan))

    db.cfgdb.set_entry('VLAN_MEMBER', (vlan, port), None)

@vlan.group(cls=clicommon.AbbreviationGroup, name='dhcp_relay')
def vlan_dhcp_relay():
    pass

@vlan_dhcp_relay.command('add')
@click.argument('vid', metavar='<vid>', required=True, type=int)
@click.argument('dhcp_relay_destination_ip', metavar='<dhcp_relay_destination_ip>', required=True)
@clicommon.pass_db
def add_vlan_dhcp_relay_destination(db, vid, dhcp_relay_destination_ip):
    """ Add a destination IP address to the VLAN's DHCP relay """

    ctx = click.get_current_context()

    if not clicommon.is_ipaddress(dhcp_relay_destination_ip):
        ctx.fail('{} is invalid IP address'.format(dhcp_relay_destination_ip))

    vlan_name = 'Vlan{}'.format(vid)
    vlan = db.cfgdb.get_entry('VLAN', vlan_name)
    if len(vlan) == 0:
        ctx.fail("{} doesn't exist".format(vlan_name))

    dhcp_relay_dests = vlan.get('dhcp_servers', [])
    if dhcp_relay_destination_ip in dhcp_relay_dests:
        click.echo("{} is already a DHCP relay destination for {}".format(dhcp_relay_destination_ip, vlan_name))
        return

    dhcp_relay_dests.append(dhcp_relay_destination_ip)
    vlan['dhcp_servers'] = dhcp_relay_dests
    db.cfgdb.set_entry('VLAN', vlan_name, vlan)
    click.echo("Added DHCP relay destination address {} to {}".format(dhcp_relay_destination_ip, vlan_name))
    try:
        click.echo("Restarting DHCP relay service...")
        clicommon.run_command("systemctl restart dhcp_relay", display_cmd=False)
    except SystemExit as e:
        ctx.fail("Restart service dhcp_relay failed with error {}".format(e))

@vlan_dhcp_relay.command('del')
@click.argument('vid', metavar='<vid>', required=True, type=int)
@click.argument('dhcp_relay_destination_ip', metavar='<dhcp_relay_destination_ip>', required=True)
@clicommon.pass_db
def del_vlan_dhcp_relay_destination(db, vid, dhcp_relay_destination_ip):
    """ Remove a destination IP address from the VLAN's DHCP relay """

    ctx = click.get_current_context()

    if not clicommon.is_ipaddress(dhcp_relay_destination_ip):
        ctx.fail('{} is invalid IP address'.format(dhcp_relay_destination_ip))

    vlan_name = 'Vlan{}'.format(vid)
    vlan = db.cfgdb.get_entry('VLAN', vlan_name)
    if len(vlan) == 0:
        ctx.fail("{} doesn't exist".format(vlan_name))

    dhcp_relay_dests = vlan.get('dhcp_servers', [])
    if not dhcp_relay_destination_ip in dhcp_relay_dests:
        ctx.fail("{} is not a DHCP relay destination for {}".format(dhcp_relay_destination_ip, vlan_name))

    dhcp_relay_dests.remove(dhcp_relay_destination_ip)
    if len(dhcp_relay_dests) == 0:
        del vlan['dhcp_servers']
    else:
        vlan['dhcp_servers'] = dhcp_relay_dests
    db.cfgdb.set_entry('VLAN', vlan_name, vlan)
    click.echo("Removed DHCP relay destination address {} from {}".format(dhcp_relay_destination_ip, vlan_name))
    try:
        click.echo("Restarting DHCP relay service...")
        clicommon.run_command("systemctl restart dhcp_relay", display_cmd=False)
    except SystemExit as e:
        ctx.fail("Restart service dhcp_relay failed with error {}".format(e))

def vlan_id_is_valid(vid):
    """Check if the vlan id is in acceptable range (between 1 and 4094)
    """

    if vid>0 and vid<4095:
        return True

    return False

# Validate VLAN range.
#
def vlan_range_validate(vid1, vid2):
    vlan1 = 'Vlan{}'.format(vid1)
    vlan2 = 'Vlan{}'.format(vid2)

    if vlan_id_is_valid(vid1) is False:
        ctx.fail("{} is not within allowed range of 1 through 4094".format(vlan1))
    if vlan_id_is_valid(vid2) is False:
        ctx.fail("{} is not within allowed range of 1 through 4094".format(vlan2))

    if vid2 <= vid1:
        ctx.fail(" vid2 should be greater than vid1")

#
# 'range' group ('config vlan range ...')
#
@vlan.group('range')
@click.pass_context
def vlan_range(ctx):
    """VLAN-range related configuration tasks"""
    pass

@vlan_range.command('add')
@click.argument('vid1', metavar='<vid1>', required=True, type=int)
@click.argument('vid2', metavar='<vid2>', required=True, type=int)
@click.option('-w', "--warning", is_flag=True, help='warnings are not suppressed')
@clicommon.pass_db
def add_vlan_range(db, vid1, vid2, warning):

    vlan_range_validate(vid1, vid2)

    vid2 = vid2+1

    warning_vlans_list = []
    curr_vlan_count = 0
    clients = db.cfgdb.get_redis_client(db.cfgdb.CONFIG_DB)
    pipe = clients.pipeline()
    for vid in range (vid1, vid2):
        vlan = 'Vlan{}'.format(vid)

        if len(db.cfgdb.get_entry('VLAN', vlan)) != 0:
            if warning is True:
                warning_vlans_list.append(vid)
            continue

        pipe.hmset('VLAN|{}'.format(vlan),  {'vlanid': vid})
        curr_vlan_count += 1
    pipe.execute()
    # Log warning messages if 'warning' option is enabled
    if warning is True:
        if len(warning_vlans_list) != 0:
            logging.warning('VLANs already existing: {}'.format(get_hyphenated_string(warning_vlans_list)))

@vlan_range.command('del')
@click.argument('vid1', metavar='<vid1>', required=True, type=int)
@click.argument('vid2', metavar='<vid2>', required=True, type=int)
@click.option('-w', "--warning", is_flag=True, help='warnings are not suppressed')
@clicommon.pass_db
def del_vlan_range(db, vid1, vid2, warning):

    vlan_range_validate(vid1, vid2)

    vid2 = vid2+1

    warning_vlans_list = []
    warning_membership_list = []
    warning_ip_list = []
    client = db.cfgdb.get_redis_client(db.cfgdb.CONFIG_DB)
    pipe = client.pipeline()

    cur, vlan_member_keys = client.scan(cursor=0, match='*VLAN_MEMBER*', count=50)
    while cur != 0:
        cur, keys = client.scan(cursor=cur, match='*VLAN_MEMBER*', count=50)
        vlan_member_keys.extend(keys)
    
    cur, vlan_temp_member_keys = client.scan(cursor=0, match='*VLAN_MEMBER*', count=50)
    while cur != 0:
        cur, keys = client.scan(cursor=cur, match='*VLAN_MEMBER*', count=50)
        vlan_temp_member_keys.extend(keys)

    cur, vlan_ip_keys = client.scan(cursor=0, match='*VLAN_INTERFACE*', count=50)
    while cur != 0:
        cur, keys = client.scan(cursor=cur, match='*VLAN_INTERFACE*', count=50)
        vlan_ip_keys.extend(keys)

    # Fetch the interfaces from config_db associated with *VLAN_MEMBER*
    stored_intf_list = []
    if vlan_temp_member_keys is not None:
        for x in range(len(vlan_temp_member_keys)):
            member_list = vlan_temp_member_keys[x].split('|',2)
            stored_intf_list.append(str(member_list[2]))

    stored_intf_list = list(set(stored_intf_list))
    list_length = len(stored_intf_list)

    # Fetch VLAN participation list for each interface 
    vid = range(vid1, vid2)
    if vlan_temp_member_keys is not None and list_length != 0:
        for i in range(list_length):
            stored_vlan_list = []
            for x in list(vlan_temp_member_keys):
                member_list = x.split('|',2)
                fetched_vlan = int(re.search(r'\d+', member_list[1]).group())
                if stored_intf_list[i] == str(member_list[2]):
                    if fetched_vlan in vid:
                        stored_vlan_list.append(fetched_vlan)
                        vlan_temp_member_keys.remove(x)

            if len(stored_vlan_list) != 0:
                warning_string = str(stored_intf_list[i]) + ' is member of ' + get_hyphenated_string(stored_vlan_list)
                warning_membership_list.append(warning_string)

    if vlan_ip_keys is None and vlan_member_keys is None:
        for vid in range(vid1, vid2):
            vlan = 'Vlan{}'.format(vid)
            if len(db.cfgdb.get_entry('VLAN', vlan)) == 0:
                if warning is True:
                    warning_vlans_list.append(vid)
                continue

            pipe.delete('VLAN|{}'.format(vlan))
        pipe.execute()
    else:
        if vlan_ip_keys is not None:
            for v in vlan_ip_keys:
                pipe.hgetall(v)
            pipe.execute()
        if vlan_member_keys is not None:
            for v in vlan_member_keys:
                pipe.hgetall(v)
            pipe.execute()
        for vid in range(vid1, vid2):
            vlan_member_configured = False
            ip_configured = False
            vlan = 'Vlan{}'.format(vid)

            if len(db.cfgdb.get_entry('VLAN', vlan)) == 0:
                if warning is True:
                    warning_vlans_list.append(vid)
                continue

            if vlan_member_keys is not None:
                for x in range(len(vlan_member_keys)):
                    vlan_member_configured = False
                    member_list = vlan_member_keys[x].split('|',2)
                    fetched_vlan = int(re.search(r'\d+', member_list[1]).group())
                    if(fetched_vlan == vid):
                        if "Ethernet" or "PortChannel" in str(member_list[2]):
                            vlan_member_configured = True
                            break

                if vlan_member_configured is True:
                    continue

            if vlan_ip_keys is not None:
                for x in range(len(vlan_ip_keys)):
                    ip_configured = False
                    member_list = vlan_ip_keys[x].split('|',2)
                    fetched_vlan = int(re.search(r'\d+', member_list[1]).group())
                    if(fetched_vlan == vid):
                        if warning is True:
                            warning_ip_list.append(vid)
                        ip_configured = True
                        break

                if ip_configured is True:
                    continue

            vlan = 'Vlan{}'.format(vid)
            pipe.delete('VLAN|{}'.format(vlan))
        pipe.execute()

    # Log warning messages if 'warning' option is enabled
    if warning is True and len(warning_vlans_list) != 0:
        logging.warning('Non-existent VLANs: {}'.format(get_hyphenated_string(warning_vlans_list)))
    if warning is True and len(warning_membership_list) != 0:
        logging.warning('Remove VLAN membership before removing VLAN: {}'.format(warning_membership_list))
    if warning is True and len(warning_ip_list) != 0:
        warning_string = 'Vlans configured with IP: ' + get_hyphenated_string(warning_ip_list)
        logging.warning('Remove IP configuration before removing VLAN: {}'.format(warning_string))

#
# 'member range' group ('config vlan member range ...')
#
@vlan_member.group('range')
@click.pass_context
def vlan_member_range(ctx):
    """VLAN member range related configuration tasks"""
    pass

#
# Returns VLAN data in a format required to perform redisDB operations.
#
def vlan_member_data(member_list):
    vlan_data = {}
    for key in member_list:
        value = member_list[key]
        if type(value) is list:
            vlan_data[key+'@'] = ','.join(value)
        else:
            vlan_data[key] = str(value)
    return vlan_data

def interface_name_is_valid(config_db, interface_name):
    """Check if the interface name is valid
    """
    # If the input parameter config_db is None, derive it from interface.
    # In single ASIC platform, get_port_namespace() returns DEFAULT_NAMESPACE.
    if config_db is None:
        namespace = get_port_namespace(interface_name)
        if namespace is None:
            return False
        config_db = ConfigDBConnector(use_unix_socket_path=True, namespace=namespace)

    config_db.connect()
    port_dict = config_db.get_table('PORT')
    port_channel_dict = config_db.get_table('PORTCHANNEL')
    sub_port_intf_dict = config_db.get_table('VLAN_SUB_INTERFACE')

    if clicommon.get_interface_naming_mode() == "alias":
        interface_name = interface_alias_to_name(config_db, interface_name)

    if interface_name is not None:
        if not port_dict:
            click.echo("port_dict is None!")
            raise click.Abort()
        for port_name in port_dict.keys():
            if interface_name == port_name:
                return True
        if port_channel_dict:
            for port_channel_name in port_channel_dict.keys():
                if interface_name == port_channel_name:
                    return True
        if sub_port_intf_dict:
            for sub_port_intf_name in sub_port_intf_dict.keys():
                if interface_name == sub_port_intf_name:
                    return True
    return False

@vlan_member_range.command('add')
@click.argument('vid1', metavar='<vid1>', required=True, type=int)
@click.argument('vid2', metavar='<vid2>', required=True, type=int)
@click.argument('interface_name', metavar='<interface_name>', required=True)
@click.option('-u', '--untagged', is_flag=True)
@click.option('-w', "--warning", is_flag=True, help='warnings are not suppressed')
@clicommon.pass_db
def add_vlan_member_range(db, vid1, vid2, interface_name, untagged, warning):
    vlan_range_validate(vid1, vid2)
    ctx = click.get_current_context()

    if clicommon.get_interface_naming_mode() == "alias":
        interface_name = interface_alias_to_name(interface_name)
        if interface_name is None:
            ctx.fail("'interface_name' is None!")

    if interface_name_is_valid(db.cfgdb, interface_name) is False:
        ctx.fail("Interface name is invalid!!")

    vid2 = vid2+1
    vlan_count = vid2-vid1
    if untagged is True and (vlan_count >= 2):
        ctx.fail("Same interface {} cannot be untagged member of more than one VLAN".format(interface_name))

    warning_vlans_list = []
    warning_membership_list = []
    clients = db.cfgdb.get_redis_client(db.cfgdb.CONFIG_DB)
    pipe = clients.pipeline()

    # Validate if interface has IP configured
    # in physical and port channel tables
    for k,v in db.cfgdb.get_table('INTERFACE').iteritems():
        if k == interface_name:
            ctx.fail(" {} has ip address configured".format(interface_name))

    for k,v in db.cfgdb.get_table('PORTCHANNEL_INTERFACE').iteritems():
        if k == interface_name:
            ctx.fail(" {} has ip address configured".format(interface_name))

    for k,v in db.cfgdb.get_table('PORTCHANNEL_MEMBER'):
        if v == interface_name:
            ctx.fail(" {} is configured as a port channel member".format(interface_name))

    for vid in range(vid1, vid2):
        vlan_name = 'Vlan{}'.format(vid)
        vlan = db.cfgdb.get_entry('VLAN', vlan_name)

        if len(vlan) == 0:
            if warning is True:
                warning_vlans_list.append(vid)
            continue

        members = vlan.get('members', [])
        if interface_name in members:
            if warning is True:
                warning_membership_list.append(vid)
            if clicommon.get_interface_naming_mode() == "alias":
                interface_name = interface_name_to_alias(interface_name)
                if interface_name is None:
                    ctx.fail("'interface_name' is None!")
                continue
            else:
                continue

        members.append(interface_name)
        vlan['members'] = members
        pipe.hmset('VLAN|{}'.format(vlan_name), vlan_member_data(vlan))
        pipe.hmset('VLAN_MEMBER|{}'.format(vlan_name+'|'+interface_name), {'tagging_mode': "untagged" if untagged else "tagged" })
    # If port is being made L2 port, enable STP
    pipe.execute()
    # Log warning messages if 'warning' option is enabled
    if warning is True and len(warning_vlans_list) != 0:
        logging.warning('Non-existent VLANs: {}'.format(get_hyphenated_string(warning_vlans_list)))
    if warning is True and len(warning_membership_list) != 0:
        if(len(warning_membership_list) == 1):
            vlan_string = 'Vlan: '
        else:
            vlan_string = 'Vlans: '
        warning_string = str(interface_name) + ' is already a member of ' + vlan_string + get_hyphenated_string(warning_membership_list)
        logging.warning('Membership exists already: {}'.format(warning_string))

@vlan_member_range.command('del')
@click.argument('vid1', metavar='<vid1>', required=True, type=int)
@click.argument('vid2', metavar='<vid2>', required=True, type=int)
@click.argument('interface_name', metavar='<interface_name>', required=True)
@click.option('-w', "--warning", is_flag=True, help='warnings are not suppressed')
@clicommon.pass_db
def del_vlan_member_range(db, vid1, vid2, interface_name, warning):
    vlan_range_validate(vid1, vid2)
    ctx = click.get_current_context()

    if clicommon.get_interface_naming_mode() == "alias":
        interface_name = interface_alias_to_name(interface_name)
        if interface_name is None:
            ctx.fail("'interface_name' is None!")

    if interface_name_is_valid(db.cfgdb, interface_name) is False:
        ctx.fail("Interface name is invalid!!")

    vid2 = vid2+1

    warning_vlans_list = []
    warning_membership_list = []
    clients = db.cfgdb.get_redis_client(db.cfgdb.CONFIG_DB)
    pipe = clients.pipeline()

    for vid in range(vid1, vid2):
        vlan_name = 'Vlan{}'.format(vid)
        vlan = db.cfgdb.get_entry('VLAN', vlan_name)

        if len(vlan) == 0:
            if warning is True:
                warning_vlans_list.append(vid)
            continue

        members = vlan.get('members', [])
        if interface_name not in members:
            if warning is True:
                warning_membership_list.append(vid)
            if clicommon.get_interface_naming_mode() == "alias":
                interface_name = interface_name_to_alias(interface_name)
                if interface_name is None:
                    ctx.fail("'interface_name' is None!")
                continue
            else:
                continue

        members.remove(interface_name)
        if len(members) == 0:
            pipe.hdel('VLAN|{}'.format(vlan_name), 'members@')
        else:
            vlan['members'] = members
            pipe.hmset('VLAN|{}'.format(vlan_name), vlan_member_data(vlan))

        pipe.delete('VLAN_MEMBER|{}'.format(vlan_name+'|'+interface_name))
        pipe.delete('STP_VLAN_INTF|{}'.format(vlan_name + '|' + interface_name))
    pipe.execute()
    # Log warning messages if 'warning' option is enabled
    if warning is True and len(warning_vlans_list) != 0:
        logging.warning('Non-existent VLANs: {}'.format(get_hyphenated_string(warning_vlans_list)))
    if warning is True and len(warning_membership_list) != 0:
        if(len(warning_membership_list) == 1):
            vlan_string = 'Vlan: '
        else:
            vlan_string = 'Vlans: '
        warning_string = str(interface_name) + ' is not a member of ' + vlan_string + get_hyphenated_string(warning_membership_list)
        logging.warning('Non-existent membership: {}'.format(warning_string))
