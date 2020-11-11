import click
import utilities_common.cli as clicommon
from natsort import natsorted
from swsssdk import ConfigDBConnector
from swsssdk import SonicV2Connector
from tabulate import tabulate

#
# 'vxlan' command ("show vxlan")
#
@click.group(cls=clicommon.AliasedGroup)
def vxlan():
    """Show vxlan related information"""
    pass

@vxlan.command()
@click.argument('vxlan_name', required=True)
def name(vxlan_name):
    """Show vxlan name <vxlan_name> information"""
    config_db = ConfigDBConnector()
    config_db.connect()
    header = ['vxlan tunnel name', 'source ip', 'destination ip', 'tunnel map name', 'tunnel map mapping(vni -> vlan)']

    # Fetching data from config_db for VXLAN TUNNEL
    vxlan_data = config_db.get_entry('VXLAN_TUNNEL', vxlan_name)

    table = []
    if vxlan_data:
        r = []
        r.append(vxlan_name)
        r.append(vxlan_data.get('src_ip'))
        r.append(vxlan_data.get('dst_ip'))
        vxlan_map_keys = config_db.keys(config_db.CONFIG_DB,
                                        'VXLAN_TUNNEL_MAP{}{}{}*'.format(config_db.KEY_SEPARATOR, vxlan_name, config_db.KEY_SEPARATOR))
        if vxlan_map_keys:
            vxlan_map_mapping = config_db.get_all(config_db.CONFIG_DB, vxlan_map_keys[0])
            r.append(vxlan_map_keys[0].split(config_db.KEY_SEPARATOR, 2)[2])
            r.append("{} -> {}".format(vxlan_map_mapping.get('vni'), vxlan_map_mapping.get('vlan')))
        table.append(r)

    click.echo(tabulate(table, header))

@vxlan.command()
def tunnel_cfg():
    """Show vxlan tunnel information"""
    config_db = ConfigDBConnector()
    config_db.connect()
    header = ['vxlan tunnel name', 'source ip', 'destination ip', 'tunnel map name', 'tunnel map mapping(vni -> vlan)']

    # Fetching data from config_db for VXLAN TUNNEL
    vxlan_data = config_db.get_table('VXLAN_TUNNEL')
    vxlan_keys = natsorted(list(vxlan_data.keys()))

    table = []
    for k in vxlan_keys:
        r = []
        r.append(k)
        r.append(vxlan_data[k].get('src_ip'))
        r.append(vxlan_data[k].get('dst_ip'))
        vxlan_map_keys = config_db.keys(config_db.CONFIG_DB,
                                        'VXLAN_TUNNEL_MAP{}{}{}*'.format(config_db.KEY_SEPARATOR, k, config_db.KEY_SEPARATOR))
        if vxlan_map_keys:
            vxlan_map_mapping = config_db.get_all(config_db.CONFIG_DB, vxlan_map_keys[0])
            r.append(vxlan_map_keys[0].split(config_db.KEY_SEPARATOR, 2)[2])
            r.append("{} -> {}".format(vxlan_map_mapping.get('vni'), vxlan_map_mapping.get('vlan')))
        table.append(r)

    click.echo(tabulate(table, header))

@vxlan.command()
def interface():
    """Show VXLAN VTEP Information"""

    config_db = ConfigDBConnector()
    config_db.connect()

    # Fetching VTEP keys from config DB
    click.secho('VTEP Information:\n', bold=True, underline=True)
    vxlan_table = config_db.get_table('VXLAN_TUNNEL')
    vxlan_keys = vxlan_table.keys()
    vtep_sip = '0.0.0.0'
    if vxlan_keys is not None:
      for key in natsorted(vxlan_keys):
          key1 = key.split('|',1)
          vtepname = key1.pop();
          if 'src_ip' in vxlan_table[key]:
            vtep_sip = vxlan_table[key]['src_ip']
          if vtep_sip is not '0.0.0.0':
             output = '\tVTEP Name : ' + vtepname + ', SIP  : ' + vxlan_table[key]['src_ip']
          else:
             output = '\tVTEP Name : ' + vtepname 

          click.echo(output)

    if vtep_sip is not '0.0.0.0':
       vxlan_table = config_db.get_table('VXLAN_EVPN_NVO')
       vxlan_keys = vxlan_table.keys()
       if vxlan_keys is not None:
         for key in natsorted(vxlan_keys):
             key1 = key.split('|',1)
             vtepname = key1.pop();
             output = '\tNVO Name  : ' + vtepname + ',  VTEP : ' + vxlan_table[key]['source_vtep']
             click.echo(output)

       vxlan_keys = config_db.keys('CONFIG_DB', "LOOPBACK_INTERFACE|*")
       loopback = 'Not Configured'
       if vxlan_keys is not None:
         for key in natsorted(vxlan_keys):
             key1 = key.split('|',2)
             if len(key1) == 3 and key1[2] == vtep_sip+'/32':
                loopback = key1[1]
                break
         output = '\tSource interface  : ' + loopback 
         if vtep_sip != '0.0.0.0':
            click.echo(output)

@vxlan.command()
@click.argument('count', required=False)
def vlanvnimap(count):
    """Show VLAN VNI Mapping Information"""

    header = ['VLAN', 'VNI']
    body = []

    config_db = ConfigDBConnector()
    config_db.connect()

    if count is not None:
      vxlan_keys = config_db.keys('CONFIG_DB', "VXLAN_TUNNEL_MAP|*")

      if not vxlan_keys:
        vxlan_count = 0
      else:
        vxlan_count = len(vxlan_keys)

      output = 'Total count : '
      output += ('%s \n' % (str(vxlan_count)))
      click.echo(output)
    else:
       vxlan_table = config_db.get_table('VXLAN_TUNNEL_MAP')
       vxlan_keys = vxlan_table.keys()
       num=0
       if vxlan_keys is not None:
         for key in natsorted(vxlan_keys):
             body.append([vxlan_table[key]['vlan'], vxlan_table[key]['vni']])
             num += 1
       click.echo(tabulate(body, header, tablefmt="grid"))
       output = 'Total count : '
       output += ('%s \n' % (str(num)))
       click.echo(output)

@vxlan.command()
def vrfvnimap():
    """Show VRF VNI Mapping Information"""

    header = ['VRF', 'VNI']
    body = []

    config_db = ConfigDBConnector()
    config_db.connect()

    vrf_table = config_db.get_table('VRF')
    vrf_keys = vrf_table.keys()
    num=0
    if vrf_keys is not None:
      for key in natsorted(vrf_keys):
          if ('vni' in vrf_table[key]):
              body.append([key, vrf_table[key]['vni']])
              num += 1
    click.echo(tabulate(body, header, tablefmt="grid"))
    output = 'Total count : '
    output += ('%s \n' % (str(num)))
    click.echo(output)

@vxlan.command()
@click.argument('count', required=False)
def tunnel(count):
    """Show All VXLAN Tunnels Information"""

    if (count is not None) and (count != 'count'):
        click.echo("Unacceptable argument {}".format(count))
        return

    header = ['SIP', 'DIP', 'Creation Source', 'OperStatus']
    body = []
    db = SonicV2Connector(host='127.0.0.1')
    db.connect(db.STATE_DB) 

    vxlan_keys = db.keys(db.STATE_DB, 'VXLAN_TUNNEL_TABLE|*')

    if vxlan_keys is not None:
        vxlan_count = len(vxlan_keys)
    else:
        vxlan_count = 0

    if (count is not None):
        output = 'Total count : '
        output += ('%s \n' % (str(vxlan_count)))
        click.echo(output)
    else: 
        num = 0
        if vxlan_keys is not None:
           for key in natsorted(vxlan_keys):
                vxlan_table = db.get_all(db.STATE_DB, key);
                if vxlan_table is None:
                   continue
                body.append([vxlan_table['src_ip'], vxlan_table['dst_ip'], vxlan_table['tnl_src'], 'oper_' + vxlan_table['operstatus']])
                num += 1
        click.echo(tabulate(body, header, tablefmt="grid"))
        output = 'Total count : '
        output += ('%s \n' % (str(num)))
        click.echo(output)

@vxlan.command()
@click.argument('remote_vtep_ip', required=True)
@click.argument('count', required=False)
def remote_vni(remote_vtep_ip, count):
    """Show Vlans extended to the remote VTEP"""

    if (remote_vtep_ip != 'all') and (clicommon.is_ipaddress(remote_vtep_ip ) is False):
        click.echo("Remote VTEP IP {} invalid format".format(remote_vtep_ip))
        return
  
    header = ['VLAN', 'RemoteVTEP', 'VNI']
    body = []
    db = SonicV2Connector(host='127.0.0.1')
    db.connect(db.APPL_DB) 

    if(remote_vtep_ip == 'all'):
      vxlan_keys = db.keys(db.APPL_DB, 'VXLAN_REMOTE_VNI_TABLE:*')
    else:
      vxlan_keys = db.keys(db.APPL_DB, 'VXLAN_REMOTE_VNI_TABLE:*' + remote_vtep_ip + '*')

    if count is not None:
      if not vxlan_keys:
        vxlan_count = 0
      else:
        vxlan_count = len(vxlan_keys)

      output = 'Total count : '
      output += ('%s \n' % (str(vxlan_count)))
      click.echo(output)
    else:
      num = 0
      if vxlan_keys is not None:
        for key in natsorted(vxlan_keys):
            key1 = key.split(':')
            rmtip = key1.pop();
            #if remote_vtep_ip != 'all' and rmtip != remote_vtep_ip:
            #   continue
            vxlan_table = db.get_all(db.APPL_DB, key);
            if vxlan_table is None:
             continue
            body.append([key1.pop(), rmtip, vxlan_table['vni']])
            num += 1
      click.echo(tabulate(body, header, tablefmt="grid"))
      output = 'Total count : '
      output += ('%s \n' % (str(num)))
      click.echo(output)

@vxlan.command()
@click.argument('remote_vtep_ip', required=True)
@click.argument('count', required=False)
def remote_mac(remote_vtep_ip, count):
    """Show MACs pointing to the remote VTEP"""

    if (remote_vtep_ip != 'all') and (clicommon.is_ipaddress(remote_vtep_ip ) is False): 
        click.echo("Remote VTEP IP {} invalid format".format(remote_vtep_ip))
        return

    header = ['VLAN', 'MAC', 'RemoteVTEP', 'VNI', 'Type']
    body = []
    db = SonicV2Connector(host='127.0.0.1')
    db.connect(db.APPL_DB) 

    vxlan_keys = db.keys(db.APPL_DB, 'VXLAN_FDB_TABLE:*')

    if ((count is not None) and (remote_vtep_ip == 'all')):
      if not vxlan_keys:
        vxlan_count = 0
      else:
        vxlan_count = len(vxlan_keys)

      output = 'Total count : '
      output += ('%s \n' % (str(vxlan_count)))
      click.echo(output)
    else:
      num = 0
      if vxlan_keys is not None:
        for key in natsorted(vxlan_keys):
            key1 = key.split(':',2)
            mac = key1.pop();
            vlan = key1.pop();
            vxlan_table = db.get_all(db.APPL_DB, key);
            if vxlan_table is None:
             continue
            rmtip = vxlan_table['remote_vtep']
            if remote_vtep_ip != 'all' and rmtip != remote_vtep_ip:
               continue
            if count is None:
               body.append([vlan, mac, rmtip, vxlan_table['vni'], vxlan_table['type']])
            num += 1
      if count is None:
         click.echo(tabulate(body, header, tablefmt="grid"))
      output = 'Total count : '
      output += ('%s \n' % (str(num)))
      click.echo(output)

#Neigh Suppress
@click.group('neigh-suppress')
def neigh_suppress():
    """ show neigh_suppress """
    pass
@neigh_suppress.command('all')
def neigh_suppress_all():
    """ Show neigh_suppress all """

    header = ['VLAN', 'STATUS', 'ASSOCIATED_NETDEV']
    body = []

    config_db = ConfigDBConnector()
    config_db.connect()

    vxlan_table = config_db.get_table('VXLAN_TUNNEL_MAP')
    suppress_table = config_db.get_table('SUPPRESS_VLAN_NEIGH')
    vxlan_keys = vxlan_table.keys()
    num=0
    if vxlan_keys is not None:
      for key in natsorted(vxlan_keys):
          key1 = vxlan_table[key]['vlan']
          netdev = vxlan_keys[0][0]+"-"+key1[4:]
          if key1 not in suppress_table:
              supp_str = "Not Configured"
          else:
              supp_str = "Configured"
          body.append([vxlan_table[key]['vlan'], supp_str, netdev])
          num += 1
    click.echo(tabulate(body, header, tablefmt="grid"))
    output = 'Total count : '
    output += ('%s \n' % (str(num)))
    click.echo(output)

@neigh_suppress.command('vlan')
@click.argument('vid', metavar='<vid>', required=True, type=int)
def neigh_suppress_vlan(vid):
    """ Show neigh_suppress vlan"""
    header = ['VLAN', 'STATUS', 'ASSOCIATED_NETDEV']
    body = []

    config_db = ConfigDBConnector()
    config_db.connect()

    vxlan_table = config_db.get_table('VXLAN_TUNNEL_MAP')
    suppress_table = config_db.get_table('SUPPRESS_VLAN_NEIGH')
    vlan = 'Vlan{}'.format(vid)
    vxlan_keys = vxlan_table.keys()

    if vxlan_keys is not None:
      for key in natsorted(vxlan_keys):
          key1 = vxlan_table[key]['vlan']
          if(key1 == vlan):
                netdev = vxlan_keys[0][0]+"-"+key1[4:]
                if key1 in suppress_table:
                    supp_str = "Configured"
                    body.append([vxlan_table[key]['vlan'], supp_str, netdev])
                    click.echo(tabulate(body, header, tablefmt="grid"))
                    return
    print(vlan + " is not configured in vxlan tunnel map table")
