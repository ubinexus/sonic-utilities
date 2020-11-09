import json
import os
import sys

import click
import utilities_common.cli as clicommon

from sonic_py_common import multi_asic, device_info
from swsscommon import swsscommon
from tabulate import tabulate

platform_sfputil = None

REDIS_TIMEOUT_MSECS = 0


# ==================== Methods for initialization ====================


# Loads platform specific sfputil module from source
def load_platform_sfputil():
    global platform_sfputil

    try:
        import sonic_platform_base.sonic_sfp.sfputilhelper
        platform_sfputil = sonic_platform_base.sonic_sfp.sfputilhelper.SfpUtilHelper()
    except Exception as e:
        click.echo("Failed to instantiate platform_sfputil due to {}".format(repr(e)))
        return -1


    return 0


#
# 'muxcable' command ("config muxcable")
#
@click.group(name='muxcable', cls=clicommon.AliasedGroup)
def muxcable():
    """SONiC command line - 'show muxcable' command"""

    if os.geteuid() != 0:
        click.echo("Root privileges are required for this operation")
        sys.exit(1)

    # Load platform-specific sfputil class
    err = load_platform_sfputil()
    if err != 0:
        sys.exit(2)

    # Load port info
    try:
        if multi_asic.is_multi_asic():
            # For multi ASIC platforms we pass DIR of port_config_file_path and the number of asics
            (platform_path, hwsku_path) = device_info.get_paths_to_platform_and_hwsku_dirs()

            # Load platform module from source
            platform_sfputil.read_all_porttab_mappings(hwsku_path, multi_asic.get_num_asics())
        else:
            # For single ASIC platforms we pass port_config_file_path and the asic_inst as 0
            port_config_file_path = device_info.get_path_to_port_config_file()
            platform_sfputil.read_porttab_mappings(port_config_file_path, 0)
    except Exception as e:
        log.log_error("Error reading port info (%s)" % str(e), True)
        sys.exit(3)

    return

# 'muxcable' command ("config muxcable mode <port> active|auto")
@muxcable.command()
@click.argument('port', metavar='<port_name>', required= False, default = None)
@click.argument('state', metavar='<operation_status>', required=True, type=click.Choice(["standby","active","auto"]))
@click.option('--json','json_flag', required=False, is_flag=True, type=click.BOOL)
def mode(state, port, json_flag):
    """Show muxcable summary information"""

    config_db = {}
    appl_db = {}
    y_cable_tbl = {}
    port_table_keys = {}
    y_cable_response_tbl = {}

    # Getting all front asic namespace and correspding config and state DB connector

    namespaces = multi_asic.get_front_end_namespaces()
    for namespace in namespaces:
        asic_id = multi_asic.get_asic_index_from_namespace(namespace)
        config_db[asic_id] = swsscommon.DBConnector("CONFIG_DB", REDIS_TIMEOUT_MSECS, True, namespace)
        appl_db[asic_id] = swsscommon.DBConnector("APPL_DB", REDIS_TIMEOUT_MSECS, True, namespace)
        y_cable_tbl[asic_id] = swsscommon.Table(config_db[asic_id], "MUX_CABLE")
        port_table_keys[asic_id] = y_cable_tbl[asic_id].getKeys()


    if port is not None:
        asic_index = platform_sfputil.get_asic_id_for_logical_port(port)
        click.echo("asic_index {} \n".format(asic_index))
        if asic_index is None:
            click.echo("Got invalid asic index for port {}, cant retreive mux status".format(port))
            return

        y_cable_asic_table = y_cable_tbl.get(asic_index, None)
        if y_cable_asic_table is not None:
            y_cable_asic_table_keys = y_cable_asic_table.getKeys()
            if port in y_cable_asic_table_keys:
                port_status_dict = {}
                (status, fvs) = y_cable_asic_table.get(str(port))
                if status is not True:
                    click.echo("could not retrieve port values for port".format(port))
                fvp = dict(fvs)
                status_value = fvp.get("status",None)
                if state == "active" and status_value == "active":
                    # status is already active, so right back ok
                    fvs = swsscommon.FieldValuePairs([('status', 'Ok')])
                    y_cable_tbl[asic_index].set(logical_port_name, fvs)
                    port_status_dict = {'status': 'Ok'}
                elif state == "active" and status_value == "standby":
                    # Change of status recived, right back inprogress
                    fvs = swsscommon.FieldValuePairs([('status', 'inprogress')])
                    y_cable_tbl[asic_index].set(logical_port_name, fvs)
                    port_status_dict = {'status': 'inprogress'}
                else:
                    #Everything else to be treated as failure
                    fvs = swsscommon.FieldValuePairs([('status', 'Failed')])
                    y_cable_tbl[asic_index].set(logical_port_name, fvs)
                    port_status_dict = {'status': 'Failed'}

                if json_flag:
                    click.echo("muxcable Ports status : \n {}".format(json.dumps(port_status_dict, indent=4)))
                else:
                    headers = ['port', 'status']
                    data = sorted([(k,v) for k,v in port_status_dict.items()])
                    click.echo(tabulate(data, headers=headers))

            else:
                click.echo("this is not a valid port present on mux_cable".format(port))
        else:
            click.echo("there is not a valid asic table for this asic_index".format(asic_index))


    else:

        for namespace in namespaces:
            asic_id = multi_asic.get_asic_index_from_namespace(namespace)
            for logical_port in port_table_keys[asic_id]:
                port_status_dict = {}
                (status, fvs) = y_cable_asic_table.get(str(logical_port))
                if status is not True:
                    click.echo("could not retrieve port values for port".format(logical_port))
                fvp = dict(fvs)
                status_value = fvp.get("status",None)
                if status == "active" and status_value == "active":
                    # status is already active, so right back ok
                    fvs = swsscommon.FieldValuePairs([('status', 'Ok')])
                    y_cable_tbl[asic_id].set(logical_port, fvs)
                    port_status_dict[logical_port] = {'status': 'Ok'}
                elif status == "active" and status_value == "standby":
                    # Change of status recived, right back inprogress
                    fvs = swsscommon.FieldValuePairs([('status', 'inprogress')])
                    y_cable_tbl[asic_id].set(logical_port, fvs)
                    port_status_dict[logical_port] = {'status': 'inprogress'}
                else:
                    #Everything else to be treated as failure
                    fvs = swsscommon.FieldValuePairs([('status', 'Failed')])
                    y_cable_tbl[asic_id].set(logical_port, fvs)
                    port_status_dict[logical_port] = {'status': 'Failed'}

                if json_flag:
                    click.echo("muxcable Ports status : \n {}".format(json.dumps(port_status_dict, indent=4)))
                else:
                    headers = ['port', 'status']
                    data = sorted([(k,v) for k,v in port_status_dict.items()])
                    click.echo(tabulate(data, headers=headers))


