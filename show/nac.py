import json
import os

import click
import utilities_common.cli as clicommon
from natsort import natsorted
from swsscommon.swsscommon import ConfigDBConnector, SonicV2Connector
from portconfig import get_child_ports
from tabulate import tabulate
import ast

#
# 'nac group ("show nac...")
#
@click.group(invoke_without_command=True)
@clicommon.pass_db
@click.pass_context
def nac(ctx, db):
    """Show NAC related information"""
    if ctx.invoked_subcommand is None:
        show_nac_global(db.cfgdb)


def show_nac_global(config_db):
    nac_info = config_db.get_table('NAC')
    global_admin_state = 'down'
    global_nac_type = 'port'
    global_auth_type = 'local'
    if nac_info:
        global_admin_state = nac_info['global']['admin_state']
        global_nac_type = nac_info['global']['nac_type']
        global_auth_type = nac_info['global']['auth_type']

    click.echo("\nNAC Global Information:")
    click.echo("  NAC Admin State:".ljust(30) + "{}".format(global_admin_state))
    click.echo("  NAC Type       :".ljust(30) + "{}".format(global_nac_type))
    click.echo("  NAC Authentication Type :".ljust(30) + "{}".format(global_auth_type))

#
# 'interface' command ("show nac interface <interface_name | all>")
#
@nac.command('interface')
@click.argument('interfacename', metavar='<interface_name>', required=True)
@clicommon.pass_db
def nac_interface(db, interfacename):
    """Show NAC interface information"""
    config_db = db.cfgdb

    nac_tbl = config_db.get_table('NAC')
    if not nac_tbl:
        click.echo("NAC feature not enabled. Enable feature to set NAC type.")
        return
    else:
        if nac_tbl['global']['admin_state'] == 'down':
            click.echo("NAC feature not enabled. Enable feature to configure NAC settings")
            return

    header = ['InterfaceName', 'NAC AdminState', 'Authorization State', 'Mapped Profile']
    body = []

    try:
        port_dict = config_db.get_table('PORT')
    except Exception as e:
        click.echo("PORT Table is not present in Config DB")
        raise click.Abort()

    try:
        nac_session_dict = config_db.get_table('NAC_SESSION')
    except Exception as e:
        click.echo("NAC_SESSION Table is not present in Config DB")
        raise click.Abort()

    ports = ast.literal_eval(json.dumps(port_dict))
    nac_sessions = ast.literal_eval(json.dumps(nac_session_dict))
    
    if interfacename != 'all':
        if interfacename in nac_sessions.keys():
            body.append([interfacename, nac_sessions[interfacename].get('admin_state'), nac_sessions[interfacename].get('nac_status'), ports[interfacename].get('nac')])
    else:
        for intf_name in nac_sessions.keys():
            if intf_name != 'all': #nac_sessions db table as well can have entry with nace 'all'
                body.append([intf_name, nac_sessions[intf_name].get('admin_state'), nac_sessions[intf_name].get('nac_status'), ports[intf_name].get('nac')])
    click.echo(tabulate(body, header, tablefmt="grid")) 
