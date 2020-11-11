import click
import utilities_common.cli as clicommon

#
# 'vxlan' group ('config vxlan ...')
#
@config.group()
@click.pass_context
def vxlan(ctx):
    config_db = ConfigDBConnector()
    config_db.connect()
    ctx.obj = {'db': config_db}

@vxlan.command('add')
@click.argument('vxlan_name', metavar='<vxlan_name>', required=True)
@click.argument('src_ip', metavar='<src_ip>', required=True)
@click.pass_context
def add_vxlan(ctx, vxlan_name, src_ip):
    """Add VXLAN"""
    if not clicommon.is_ip4_addr_valid(src_ip, True):
        ctx.fail("{} invalid src ip address".format(src_ip))  
    db = ctx.obj['db']

    vxlan_keys = db.keys('CONFIG_DB', "VXLAN_TUNNEL|*")
    if not vxlan_keys:
      vxlan_count = 0
    else:
      vxlan_count = len(vxlan_keys)

    if(vxlan_count > 0):
        ctx.fail("VTEP already configured.")  

    fvs = {'src_ip': src_ip}
    db.set_entry('VXLAN_TUNNEL', vxlan_name, fvs)

@vxlan.command('del')
@click.argument('vxlan_name', metavar='<vxlan_name>', required=True)
@click.pass_context
def del_vxlan(ctx, vxlan_name):
    """Del VXLAN"""
    db = ctx.obj['db']

    vxlan_keys = db.keys('CONFIG_DB', "VXLAN_EVPN_NVO|*")
    if not vxlan_keys:
      vxlan_count = 0
    else:
      vxlan_count = len(vxlan_keys)

    if(vxlan_count > 0):
        ctx.fail("Please delete the EVPN NVO configuration.")  

    vxlan_keys = db.keys('CONFIG_DB', "VXLAN_TUNNEL_MAP|*")
    if not vxlan_keys:
      vxlan_count = 0
    else:
      vxlan_count = len(vxlan_keys)

    if(vxlan_count > 0):
        ctx.fail("Please delete all VLAN VNI mappings.")  

    db.set_entry('VXLAN_TUNNEL', vxlan_name, None)

@vxlan.group('evpn_nvo')
@click.pass_context
def vxlan_evpn_nvo(ctx):
    pass

@vxlan_evpn_nvo.command('add')
@click.argument('nvo_name', metavar='<nvo_name>', required=True)
@click.argument('vxlan_name', metavar='<vxlan_name>', required=True)
@click.pass_context
def add_vxlan_evpn_nvo(ctx, nvo_name, vxlan_name):
    """Add NVO"""
    db = ctx.obj['db']
    vxlan_keys = db.keys('CONFIG_DB', "VXLAN_EVPN_NVO|*")
    if not vxlan_keys:
      vxlan_count = 0
    else:
      vxlan_count = len(vxlan_keys)

    if(vxlan_count > 0):
        ctx.fail("EVPN NVO already configured")  

    if len(db.get_entry('VXLAN_TUNNEL', vxlan_name)) == 0:
        ctx.fail("VTEP {} not configured".format(vxlan_name))

    fvs = {'source_vtep': vxlan_name}
    db.set_entry('VXLAN_EVPN_NVO', nvo_name, fvs)

@vxlan_evpn_nvo.command('del')
@click.argument('nvo_name', metavar='<nvo_name>', required=True)
@click.pass_context
def del_vxlan_evpn_nvo(ctx, nvo_name):
    """Del NVO"""
    db = ctx.obj['db']
    vxlan_keys = db.keys('CONFIG_DB', "VXLAN_TUNNEL_MAP|*")
    if not vxlan_keys:
      vxlan_count = 0
    else:
      vxlan_count = len(vxlan_keys)

    if(vxlan_count > 0):
        ctx.fail("Please delete all VLAN VNI mappings.")  
    db.set_entry('VXLAN_EVPN_NVO', nvo_name, None)

@vxlan.group('map')
@click.pass_context
def vxlan_map(ctx):
    pass

@vxlan_map.command('add')
@click.argument('vxlan_name', metavar='<vxlan_name>', required=True)
@click.argument('vlan', metavar='<vlan_id>', required=True)
@click.argument('vni', metavar='<vni>', required=True)
@click.pass_context
def add_vxlan_map(ctx, vxlan_name, vlan, vni):
    """Add VLAN-VNI map entry"""
    if not vlan.isdigit():
        ctx.fail("Invalid vlan {}. Only valid vlan is accepted".format(vni))
    if clicommon.is_vlanid_in_range(int(vlan)) is False:
        ctx.fail(" Invalid Vlan Id , Valid Range : 1 to 4094 ")
    if not vni.isdigit():
        ctx.fail("Invalid VNI {}. Only valid VNI is accepted".format(vni))
    if clicommon.vni_id_is_valid(int(vni)) is False:
        ctx.fail("Invalid VNI {}. Valid range [1 to 16777215].".format(vni))

    db = ctx.obj['db']
    vlan_name = "Vlan" + vlan

    if len(db.get_entry('VXLAN_TUNNEL', vxlan_name)) == 0:
        ctx.fail("VTEP {} not configured".format(vxlan_name))

    if len(db.get_entry('VLAN', vlan_name)) == 0:
        ctx.fail("{} not configured".format(vlan_name))

    vxlan_table = db.get_table('VXLAN_TUNNEL_MAP')
    vxlan_keys = vxlan_table.keys()
    if vxlan_keys is not None:
      for key in vxlan_keys:
        if (vxlan_table[key]['vlan'] == vlan_name):
           ctx.fail(" Vlan Id already mapped ")
        if (vxlan_table[key]['vni'] == vni):
           ctx.fail(" VNI Id already mapped ")

    fvs = {'vni': vni,
           'vlan' : vlan_name}
    mapname = vxlan_name + '|' + 'map_' + vni + '_' + vlan_name
    db.set_entry('VXLAN_TUNNEL_MAP', mapname, fvs)

@vxlan_map.command('del')
@click.argument('vxlan_name', metavar='<vxlan_name>', required=True)
@click.argument('vlan', metavar='<vlan_id>', required=True)
@click.argument('vni', metavar='<vni>', required=True)
@click.pass_context
def del_vxlan_map(ctx, vxlan_name, vlan, vni):
    """Del VLAN-VNI map entry"""
    if not vlan.isdigit():
        ctx.fail("Invalid vlan {}. Only valid vlan is accepted".format(vni))
    if clicommon.is_vlanid_in_range(int(vlan)) is False:
        ctx.fail(" Invalid Vlan Id , Valid Range : 1 to 4094 ")
    if not vni.isdigit():
        ctx.fail("Invalid VNI {}. Only valid VNI is accepted".format(vni))
    if clicommon.vni_id_is_valid(int(vni)) is False:
        ctx.fail("Invalid VNI {}. Valid range [1 to 16777215].".format(vni))

    db = ctx.obj['db']
    if len(db.get_entry('VXLAN_TUNNEL', vxlan_name)) == 0:
        ctx.fail("VTEP {} not configured".format(vxlan_name))
    found = 0
    vrf_table = db.get_table('VRF')
    vrf_keys = vrf_table.keys()
    if vrf_keys is not None:
      for vrf_key in vrf_keys:
        if ('vni' in vrf_table[vrf_key] and vrf_table[vrf_key]['vni'] == vni):
           found = 1
           break

    if (found == 1):
        ctx.fail("VNI mapped to vrf {}, Please remove VRF VNI mapping".format(vrf_key))

    mapname = vxlan_name + '|' + 'map_' + vni + '_' + vlan
    db.set_entry('VXLAN_TUNNEL_MAP', mapname, None)
    mapname = vxlan_name + '|' + 'map_' + vni + '_Vlan' + vlan
    db.set_entry('VXLAN_TUNNEL_MAP', mapname, None)

@vxlan.group('map_range')
@click.pass_context
def vxlan_map_range(ctx):
    pass

@vxlan_map_range.command('add')
@click.argument('vxlan_name', metavar='<vxlan_name>', required=True)
@click.argument('vlan_start', metavar='<vlan_start>', required=True, type=int)
@click.argument('vlan_end', metavar='<vlan_end>', required=True, type=int)
@click.argument('vni_start', metavar='<vni_start>', required=True, type=int)
@click.pass_context
def add_vxlan_map_range(ctx, vxlan_name, vlan_start, vlan_end, vni_start):
    """Add Range of vlan-vni mappings"""
    if clicommon.is_vlanid_in_range(vlan_start) is False:
        ctx.fail(" Invalid Vlan Id , Valid Range : 1 to 4094 ")
    if clicommon.is_vlanid_in_range(vlan_end) is False:
        ctx.fail(" Invalid Vlan Id , Valid Range : 1 to 4094 ")
    if (vlan_start > vlan_end):
       ctx.fail("vlan_end should be greater or equal to vlan_start")
    if clicommon.vni_id_is_valid(vni_start) is False:
        ctx.fail("Invalid VNI {}. Valid range [1 to 16777215].".format(vni_start))
    if clicommon.vni_id_is_valid(vni_start+vlan_end-vlan_start) is False:
        ctx.fail("Invalid VNI End {}. Valid range [1 to 16777215].".format(vni_start))

    db = ctx.obj['db']
    if len(db.get_entry('VXLAN_TUNNEL', vxlan_name)) == 0:
        ctx.fail("VTEP {} not configured".format(vxlan_name))
    vlan_end = vlan_end + 1
    vxlan_table = db.get_table('VXLAN_TUNNEL_MAP')
    vxlan_keys = vxlan_table.keys()

    for vid in range (vlan_start, vlan_end):
       vlan_name = 'Vlan{}'.format(vid)
       vnid = vni_start+vid-vlan_start
       vni_name = '{}'.format(vnid)
       match_found = 'no'
       if len(db.get_entry('VLAN', vlan_name)) == 0:
         click.echo("{} not configured".format(vlan_name))
         continue
       if vxlan_keys is not None:
          for key in vxlan_keys:
            if (vxlan_table[key]['vlan'] == vlan_name):
              print(vlan_name + " already mapped")
              match_found = 'yes'
              break
            if (vxlan_table[key]['vni'] == vni_name):
              print("VNI:" + vni_name + " already mapped ")
              match_found = 'yes'
              break
       if (match_found == 'yes'):
         continue
       fvs = {'vni': vni_name,
              'vlan' : vlan_name}
       mapname = vxlan_name + '|' + 'map_' + vni_name + '_' + vlan_name
       db.set_entry('VXLAN_TUNNEL_MAP', mapname, fvs)

@vxlan_map_range.command('del')
@click.argument('vxlan_name', metavar='<vxlan_name>', required=True)
@click.argument('vlan_start', metavar='<vlan_start>', required=True, type=int)
@click.argument('vlan_end', metavar='<vlan_end>', required=True, type=int)
@click.argument('vni_start', metavar='<vni_start>', required=True, type=int)
@click.pass_context
def del_vxlan_map_range(ctx, vxlan_name, vlan_start, vlan_end, vni_start):
    """Del Range of vlan-vni mappings"""
    if clicommon.is_vlanid_in_range(vlan_start) is False:
        ctx.fail(" Invalid Vlan Id , Valid Range : 1 to 4094 ")
    if clicommon.is_vlanid_in_range(vlan_end) is False:
        ctx.fail(" Invalid Vlan Id , Valid Range : 1 to 4094 ")
    if (vlan_start > vlan_end):
       ctx.fail("vlan_end should be greater or equal to vlan_start")
    if clicommon.vni_id_is_valid(vni_start) is False:
        ctx.fail("Invalid VNI {}. Valid range [1 to 16777215].".format(vni_start))
    if clicommon.vni_id_is_valid(vni_start+vlan_end-vlan_start) is False:
        ctx.fail("Invalid VNI End {}. Valid range [1 to 16777215].".format(vni_start))

    db = ctx.obj['db']
    if len(db.get_entry('VXLAN_TUNNEL', vxlan_name)) == 0:
        ctx.fail("VTEP {} not configured".format(vxlan_name))

    vlan_end = vlan_end + 1
    for vid in range (vlan_start, vlan_end):
       vlan_name = 'Vlan{}'.format(vid)
       vnid = vni_start+vid-vlan_start
       vni_name = '{}'.format(vnid)
       if clicommon.is_vni_vrf_mapped(ctx, vni_name) is False:
           print "Skipping Vlan {} VNI {} mapped delete. ".format(vlan_name, vni_name)
           continue

       mapname = vxlan_name + '|' + 'map_' + vni_name + '_' + vlan_name
       db.set_entry('VXLAN_TUNNEL_MAP', mapname, None)

#######
#
# 'neigh_suppress' group ('config neigh_suppress...')
#
@config.group()
@click.pass_context
def neigh_suppress(ctx):
    """ Neighbour Suppress VLAN-related configuration """
    config_db = ConfigDBConnector()
    config_db.connect()
    ctx.obj = {'db': config_db}

@neigh_suppress.command('enable')
@click.argument('vid', metavar='<vid>', required=True, type=int)
@click.pass_context
def enable_neigh_suppress(ctx, vid):
    db = ctx.obj['db']
    if clicommon.is_vlanid_in_range(vid) is False:
        ctx.fail(" Invalid Vlan Id , Valid Range : 1 to 4094 ")
    vlan = 'Vlan{}'.format(vid)
    if len(db.get_entry('VLAN', vlan)) == 0:
        click.echo("{} doesn't exist".format(vlan))
        return
    fvs = {'suppress': "on"}
    db.set_entry('SUPPRESS_VLAN_NEIGH', vlan, fvs)

@neigh_suppress.command('disable')
@click.argument('vid', metavar='<vid>', required=True, type=int)
@click.pass_context
def disable_neigh_suppress(ctx, vid):
    db = ctx.obj['db']
    if clicommon.is_vlanid_in_range(vid) is False:
        ctx.fail(" Invalid Vlan Id , Valid Range : 1 to 4094 ")
    vlan = 'Vlan{}'.format(vid)
    db.set_entry('SUPPRESS_VLAN_NEIGH', vlan, None)
#######
#
# 'neigh_suppress' group ('config neigh_suppress...')
#
@config.group()
@click.pass_context
def neigh_suppress(ctx):
    """ Neighbour Suppress VLAN-related configuration """
    config_db = ConfigDBConnector()
    config_db.connect()
    ctx.obj = {'db': config_db}

@neigh_suppress.command('enable')
@click.argument('vid', metavar='<vid>', required=True, type=int)
@click.pass_context
def enable_neigh_suppress(ctx, vid):
    db = ctx.obj['db']
    if clicommon.is_vlanid_in_range(vid) is False:
        ctx.fail(" Invalid Vlan Id , Valid Range : 1 to 4094 ")
    vlan = 'Vlan{}'.format(vid)
    if len(db.get_entry('VLAN', vlan)) == 0:
        click.echo("{} doesn't exist".format(vlan))
        return
    fvs = {'suppress': "on"}
    db.set_entry('SUPPRESS_VLAN_NEIGH', vlan, fvs)

@neigh_suppress.command('disable')
@click.argument('vid', metavar='<vid>', required=True, type=int)
@click.pass_context
def disable_neigh_suppress(ctx, vid):
    db = ctx.obj['db']
    if clicommon.is_vlanid_in_range(vid) is False:
        ctx.fail(" Invalid Vlan Id , Valid Range : 1 to 4094 ")
    vlan = 'Vlan{}'.format(vid)
    db.set_entry('SUPPRESS_VLAN_NEIGH', vlan, None)
