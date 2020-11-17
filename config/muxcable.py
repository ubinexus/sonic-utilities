import json
import os
import sys

import click
from sonic_py_common import multi_asic, device_info
from swsscommon import swsscommon
from swsssdk import ConfigDBConnector
from tabulate import tabulate
import utilities_common.cli as clicommon

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

# Helper functions


def get_value_for_key_in_dict(dict, port, key, table_name):
    value = dict.get(key, None)
    if value is None:
        click.echo("could not retrieve key {} value for port {} inside table {}".format(key, port, table_name))
        sys.exit(1)
    return value

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


def lookup_statedb_and_update_configdb(per_npu_statedb, config_db, port, state_value, port_status_dict):

    muxcable_statedb_dict = per_npu_statedb.get_all(per_npu_statedb.STATE_DB, 'MUX_CABLE_TABLE|{}'.format(port))

    state = get_value_for_key_in_dict(muxcable_statedb_dict, port, "state", "MUX_CABLE_TABLE")
    #click.echo("state_value = {} {}".format(state_value, state))
    if (state == "active" and state_value == "active") or (state == "active" and state_value == "auto") or (state == "standby" and state_value == "auto"):
        # status is already active, so right back ok
        # Nothing to do Since the state is not changing
        port_status_dict[port] = 'OK'
    elif state == "standby" and state_value == "active":
        config_db.set_entry("MUX_CABLE", port, {"state": "INPROGRESS"})
        # Change of status recived, right back inprogress
        port_status_dict[port] = 'INPROGRESS'
    else:
        # Everything else to be treated as failure
        port_status_dict[port] = 'FAILED'


# 'muxcable' command ("config muxcable mode <port|all> active|auto")
@muxcable.command()
@click.argument('state', metavar='<operation_status>', required=True, type=click.Choice(["active", "auto"]))
@click.argument('port', metavar='<port_name>', required=True, default=None)
@click.option('--json', 'json_output', required=False, is_flag=True, type=click.BOOL)
def mode(state, port, json_output):
    """Show muxcable summary information"""

    port_table_keys = {}
    y_cable_asic_table_keys = {}
    per_npu_configdb = {}
    per_npu_statedb = {}
    mux_tbl_cfg_db = {}

    # Getting all front asic namespace and correspding config and state DB connector

    namespaces = multi_asic.get_front_end_namespaces()
    for namespace in namespaces:
        asic_id = multi_asic.get_asic_index_from_namespace(namespace)
        # replace these with correct macros
        per_npu_configdb[asic_id] = ConfigDBConnector(use_unix_socket_path=True, namespace=namespace)
        per_npu_configdb[asic_id].connect()
        per_npu_statedb[asic_id] = swsscommon.SonicV2Connector(use_unix_socket_path=True, namespace=namespace)
        per_npu_statedb[asic_id].connect(per_npu_statedb[asic_id].STATE_DB)

        mux_tbl_cfg_db[asic_id] = per_npu_configdb[asic_id].get_table("MUX_CABLE")

        port_table_keys[asic_id] = per_npu_statedb[asic_id].keys(
            per_npu_statedb[asic_id].STATE_DB, 'MUX_CABLE_TABLE|*')

    if port is not None and port != "all":
        asic_index = platform_sfputil.get_asic_id_for_logical_port(port)
        if asic_index is None:
            click.echo("Got invalid asic index for port {}, cant retreive mux status".format(port))
            sys.exit(1)

        if per_npu_statedb[asic_index] is not None:
            y_cable_asic_table_keys = port_table_keys[asic_index]
            logical_key = "MUX_CABLE_TABLE"+"|"+port
            if logical_key in y_cable_asic_table_keys:
                port_status_dict = {}
                lookup_statedb_and_update_configdb(
                    per_npu_statedb[asic_index], per_npu_configdb[asic_index], port, state, port_status_dict)

                if json_output:
                    click.echo("{}".format(json.dumps(port_status_dict, indent=4)))
                else:
                    headers = ['port', 'state']
                    data = sorted([(k, v) for k, v in port_status_dict.items()])
                    click.echo(tabulate(data, headers=headers))

            else:
                click.echo("this is not a valid port present on mux_cable".format(port))
                sys.exit(1)
        else:
            click.echo("there is not a valid asic table for this asic_index".format(asic_index))
            sys.exit(1)

    elif port == "all" and port is not None:

        for namespace in namespaces:
            asic_id = multi_asic.get_asic_index_from_namespace(namespace)
            for key in port_table_keys[asic_id]:
                logical_port = key.split("|")[1]
                port_status_dict = {}
                lookup_statedb_and_update_configdb(
                    per_npu_statedb[asic_id], per_npu_configdb[asic_id], logical_port, state, port_status_dict)

                if json_output:
                    click.echo("{}".format(json.dumps(port_status_dict, indent=4)))
                else:
                    headers = ['port', 'state']
                    data = sorted([(k, v) for k, v in port_status_dict.items()])
                    click.echo(tabulate(data, headers=headers))
