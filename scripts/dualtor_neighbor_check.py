#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
dualtor_neighbor_check.py

This tool is designed to verify that, for dualtor SONiC, the neighbors learnt from
mux ports should have correct neighbor/route entry in ASIC.

Check steps:
1.
2.
3.
4.
5.
"""
import argparse
import functools
import ipaddress
import json
import logging
import sys
import syslog
import subprocess
import tabulate

from enum import Enum
from natsort import natsorted

from swsscommon import swsscommon
try:
    from sonic_py_common import swsssdk
except ImportError:
    from sonic_py_common import port_util


DB_READ_SCRIPT = """
-- this script is to read required tables from db:
-- APPL_DB:
--   - MUX_CABLE_TABLE
--   - HW_MUX_CABLE_TABLE
--   - NEIGH_TABLE
-- ASIC_DB:
--   - ASIC_STATE
--
-- KEYS - None
-- ARGV[1] - APPL_DB db index
-- ARGV[2] - APPL_DB mux cable table name
-- ARGV[3] - APPL_DB hardware mux cable table name
-- ARGV[4] - ASIC_DB db index
-- ARGV[5] - ASIC_DB asic state table name

local APPL_DB                   = 0
local APPL_DB_SEPARATOR         = ':'
local neighbor_table_name       = 'NEIGH_TABLE'
local mux_state_table_name      = 'MUX_CABLE_TABLE'
local hw_mux_state_table_name   = 'HW_MUX_CABLE_TABLE'
local ASIC_DB                   = 1
local ASIC_DB_SEPARATOR         = ':'
local asic_state_table_name     = 'ASIC_STATE'
local asic_route_key_prefix     = 'SAI_OBJECT_TYPE_ROUTE_ENTRY'
local asic_neigh_key_prefix     = 'SAI_OBJECT_TYPE_NEIGHBOR_ENTRY'
local asic_fdb_key_prefix       = 'SAI_OBJECT_TYPE_FDB_ENTRY'

if table.getn(ARGV) == 7 then
    APPL_DB                 = ARGV[1]
    APPL_DB_SEPARATOR       = ARGV[2]
    neighbor_table_name     = ARGV[3]
    mux_state_table_name    = ARGV[4]
    hw_mux_state_table_name = ARGV[5]
    ASIC_DB                 = ARGV[6]
    ASIC_DB_SEPARATOR       = ARGV[7]
    asic_state_table_name   = ARGV[8]
end

local neighbors             = {}
local mux_states            = {}
local hw_mux_states         = {}
local asic_fdb              = {}
local asic_route_table      = {}
local asic_neighbor_table   = {}

-- read from APPL_DB
redis.call('SELECT', APPL_DB)

-- read neighbors learnt from Vlan devices
local neighbor_table_vlan_prefix = neighbor_table_name .. APPL_DB_SEPARATOR .. 'Vlan'
local neighbor_keys = redis.call('KEYS', neighbor_table_vlan_prefix .. '*')
for i, neighbor_key in ipairs(neighbor_keys) do
    local second_separator_index = string.find(neighbor_key, APPL_DB_SEPARATOR, string.len(neighbor_table_vlan_prefix), true)
    if second_separator_index ~= nil then
        local neighbor_ip = string.sub(neighbor_key, second_separator_index + 1)
        local mac = string.lower(redis.call('HGET', neighbor_key, 'neigh'))
        neighbors[neighbor_ip] = mac
    end
end

-- read mux states
local mux_state_table_prefix = mux_state_table_name .. APPL_DB_SEPARATOR
local mux_cables = redis.call('KEYS', mux_state_table_prefix .. '*')
for i, mux_cable_key in ipairs(mux_cables) do
    local port_name = string.sub(mux_cable_key, string.len(mux_state_table_prefix) + 1)
    local mux_state = redis.call('HGET', mux_cable_key, 'state')
    if mux_state ~= nil then
        mux_states[port_name] = mux_state
    end
end

local hw_mux_state_table_prefix = hw_mux_state_table_name .. APPL_DB_SEPARATOR
local hw_mux_cables = redis.call('KEYS', hw_mux_state_table_prefix .. '*')
for i, hw_mux_cable_key in ipairs(hw_mux_cables) do
    local port_name = string.sub(hw_mux_cable_key, string.len(hw_mux_state_table_prefix) + 1)
    local mux_state = redis.call('HGET', hw_mux_cable_key, 'state')
    if mux_state ~= nil then
        hw_mux_states[port_name] = mux_state
    end
end

-- read from ASIC_DB
redis.call('SELECT', ASIC_DB)

-- read ASIC fdb entries
local fdb_prefix = asic_state_table_name .. ASIC_DB_SEPARATOR .. asic_fdb_key_prefix
local fdb_entries = redis.call('KEYS', fdb_prefix .. '*')
for i, fdb_entry in ipairs(fdb_entries) do
    local bridge_port_id = redis.call('HGET', fdb_entry, 'SAI_FDB_ENTRY_ATTR_BRIDGE_PORT_ID')
    local fdb_details = cjson.decode(string.sub(fdb_entry, string.len(fdb_prefix) + 2))
    local mac = string.lower(fdb_details['mac'])
    asic_fdb[mac] = bridge_port_id
end

-- read ASIC route table
local route_prefix = asic_state_table_name .. ASIC_DB_SEPARATOR .. asic_route_key_prefix
local route_entries = redis.call('KEYS', route_prefix .. '*')
for i, route_entry in ipairs(route_entries) do
    local route_details = string.sub(route_entry, string.len(route_prefix) + 2)
    table.insert(asic_route_table, route_details)
end

-- read ASIC neigh table
local neighbor_prefix = asic_state_table_name .. ASIC_DB_SEPARATOR .. asic_neigh_key_prefix
local neighbor_entries = redis.call('KEYS', neighbor_prefix .. '*')
for i, neighbor_entry in ipairs(neighbor_entries) do
    local neighbor_details = string.sub(neighbor_entry, string.len(neighbor_prefix) + 2)
    table.insert(asic_neighbor_table, neighbor_details)
end

local result = {}
result['neighbors']         = neighbors
result['mux_states']        = mux_states
result['hw_mux_states']     = hw_mux_states
result['asic_fdb']          = asic_fdb
result['asic_route_table']  = asic_route_table
result['asic_neigh_table']  = asic_neighbor_table

return redis.status_reply(cjson.encode(result))
"""


class LogOutput(Enum):
    """Enum to represent log output."""
    SYSLOG = "SYSLOG"
    STDOUT = "STDOUT"

    def __str__(self):
        return self.value


class SyslogLevel(Enum):
    """Class to represent syslog level."""
    ERROR = 3
    NOTICE = 5
    INFO = 6
    DEBUG = 7

    def __str__(self):
        return self.name


SYSLOG_LEVEL = SyslogLevel.INFO
WRITE_LOG_ERROR = None
WRITE_LOG_WARN = None
WRITE_LOG_INFO = None
WRITE_LOG_DEBUG = None


def parse_args():
    parser = argparse.ArgumentParser(
        description="Verify neighbors state is consistent with mux state."
    )
    parser.add_argument(
        "-o",
        "--log-output",
        type=LogOutput,
        choices=list(LogOutput),
        default=LogOutput.STDOUT,
        help="log output"
    )
    parser.add_argument(
        "-s",
        "--syslog-level",
        choices=["ERROR", "WARNING", "INFO", "DEBUG"],
        default=None,
        help="syslog level"
    )
    parser.add_argument(
        "-l",
        "--log-level",
        choices=["ERROR", "WARNING", "INFO", "DEBUG"],
        default=None,
        help="stdout log level"
    )
    args = parser.parse_args()

    if args.log_output == LogOutput.STDOUT:
        if args.log_level is None:
            args.log_level = logging.WARNING
        else:
            args.log_level = logging.getLevelName(args.log_level)

        if args.syslog_level is not None:
            parser.error("Received syslog level with log output to stdout.")
    if args.log_output == LogOutput.SYSLOG:
        if args.syslog_level is None:
            args.syslog_level = SyslogLevel.NOTICE
        else:
            args.syslog_level = SyslogLevel[args.syslog_level]

        if args.log_level is not None:
            parser.error("Received stdout log level with log output to syslog.")

    return args


def write_syslog(level, message, *args):
    if args:
        message %= args
    if level == SyslogLevel.ERROR:
        syslog.syslog(syslog.LOG_ERR, message)
    elif level == SyslogLevel.NOTICE:
        syslog.syslog(syslog.LOG_NOTICE, message)
    elif level == SyslogLevel.INFO:
        syslog.syslog(syslog.LOG_INFO, message)
    elif level == SyslogLevel.DEBUG:
        syslog.syslog(syslog.LOG_DEBUG, message)
    else:
        syslog.syslog(syslog.LOG_DEBUG, message)


def config_logging(args):
    """Configures logging based on arguments."""
    global SYSLOG_LEVEL
    global WRITE_LOG_ERROR
    global WRITE_LOG_WARN
    global WRITE_LOG_INFO
    global WRITE_LOG_DEBUG
    if args.log_output == LogOutput.STDOUT:
        logging.basicConfig(
            stream=sys.stdout,
            level=args.log_level,
            format="%(message)s"
        )
        WRITE_LOG_ERROR = logging.error
        WRITE_LOG_WARN = logging.warning
        WRITE_LOG_INFO = logging.info
        WRITE_LOG_DEBUG = logging.debug
    elif args.log_output == LogOutput.SYSLOG:
        SYSLOG_LEVEL = args.syslog_level
        WRITE_LOG_ERROR = functools.partial(write_syslog, SyslogLevel.ERROR)
        WRITE_LOG_WARN = functools.partial(write_syslog, SyslogLevel.NOTICE)
        WRITE_LOG_INFO = functools.partial(write_syslog, SyslogLevel.INFO)
        WRITE_LOG_DEBUG = functools.partial(write_syslog, SyslogLevel.DEBUG)


def run_command(cmd):
    """Runs a command and returns its output."""
    WRITE_LOG_DEBUG("Running command: %s", cmd)
    try:
        p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        (output, _) = p.communicate()
    except Exception as details:
        raise RuntimeError("Failed to run command: %s", details)
    WRITE_LOG_DEBUG("Command output: %s", output)
    WRITE_LOG_DEBUG("Command return code: %s", p.returncode)
    if p.returncode != 0:
        raise RuntimeError("Command failed with return code %s: %s" % (p.returncode, output))
    return output.decode()
    

def read_tables_from_db():
    """Reads required tables from db."""
    load_cmd = "sudo redis-cli SCRIPT LOAD \"%s\"" % DB_READ_SCRIPT
    script_sha1 = run_command(load_cmd).strip()
    WRITE_LOG_INFO("loaded script sha1: %s", script_sha1)

    run_cmd = "sudo redis-cli EVALSHA %s 0" % script_sha1
    result = run_command(run_cmd).strip()
    tables = json.loads(result)

    neighbors = tables["neighbors"]
    mux_states = tables["mux_states"]
    hw_mux_states = tables["hw_mux_states"]
    asic_fdb = {k:v.lstrip("oid:0x") for k,v in tables["asic_fdb"].items()}
    asic_route_table = tables["asic_route_table"]
    asic_neigh_table = tables["asic_neigh_table"]
    WRITE_LOG_DEBUG("neighbors: %s", json.dumps(neighbors, indent=4))
    WRITE_LOG_DEBUG("mux states: %s", json.dumps(mux_states, indent=4))
    WRITE_LOG_DEBUG("hw mux states: %s", json.dumps(hw_mux_states, indent=4))
    WRITE_LOG_DEBUG("ASIC FDB: %s", json.dumps(asic_fdb, indent=4))
    WRITE_LOG_DEBUG("ASIC route table: %s", json.dumps(asic_route_table, indent=4))
    WRITE_LOG_DEBUG("ASIC neigh table: %s", json.dumps(asic_neigh_table, indent=4))
    return neighbors, mux_states, hw_mux_states, asic_fdb, asic_route_table, asic_neigh_table


def get_if_br_oid_to_port_name_map():
    """Return port bridge oid to port name map."""
    db = swsscommon.SonicV2Connector(host="127.0.0.1")
    port_name_map = port_util.get_interface_oid_map(db)[1]
    if_br_oid_map = port_util.get_bridge_port_map(db)
    if_br_oid_to_port_name_map = {}
    for if_br_oid, if_oid in if_br_oid_map.items():
        if if_oid in port_name_map:
            if_br_oid_to_port_name_map[if_br_oid] = port_name_map[if_oid]
    return if_br_oid_to_port_name_map


def get_mux_cable_config():
    """Return mux cable config from CONFIG_DB."""
    mux_cables = {}
    db = swsscommon.ConfigDBConnector(use_unix_socket_path=False)
    db.connect()
    mux_cables = db.get_table("MUX_CABLE")
    return mux_cables


def get_mux_server_to_port_map(mux_cables):
    """Return mux server ip to port name map."""
    mux_server_to_port_map = {}
    for port, mux_details in mux_cables.items():
        if "server_ipv4" in mux_details:
            server_ipv4 = str(ipaddress.ip_interface(mux_details["server_ipv4"]).ip)
            mux_server_to_port_map[server_ipv4] = port
        if "server_ipv6" in mux_details:
            server_ipv6 = str(ipaddress.ip_interface(mux_details["server_ipv6"]).ip)
            mux_server_to_port_map[server_ipv6] = port
    return mux_server_to_port_map


def get_mac_to_port_name_map(asic_fdb, if_oid_to_port_name_map):
    """Return mac to port name map."""
    mac_to_port_name_map = {}
    for mac, port_br_oid in asic_fdb.items():
        mac_to_port_name_map[mac] = if_oid_to_port_name_map[port_br_oid]
    return mac_to_port_name_map


def check_neighbor_consistency(neighbors, mux_states, hw_mux_states, mac_to_port_name_map,
                               asic_route_table, asic_neigh_table, mux_server_to_port_map):
    """Checks if neighbors are consistent with mux states."""

    asic_route_destinations = set(json.loads(_)["dest"].split("/")[0] for _ in asic_route_table)
    asic_neighs = set(json.loads(_)["ip"] for _ in asic_neigh_table)

    check_results = []
    show_items = ["NEIGHBOR", "MAC", "PORT", "MUX_STATE", "IN_MUX_TOGGLE", "NEIGHBOR_IN_ASIC", "TUNNRL_IN_ASIC", "HWSTATUS"]
    for neighbor_ip in natsorted(list(neighbors.keys())):
        mac = neighbors[neighbor_ip]
        check_result = [None] * len(show_items)
        check_result[0] = neighbor_ip
        check_result[1] = mac

        if mac not in mac_to_port_name_map:
            check_results.append(check_result)
            continue

        port_name = mac_to_port_name_map[mac]
        # NOTE: mux server ips are always fixed to the mux port
        if neighbor_ip in mux_server_to_port_map:
            port_name = mux_server_to_port_map[neighbor_ip]
        check_result[2] = port_name

        mux_state = mux_states[port_name]
        hw_mux_state = hw_mux_states[port_name]
        check_result[3] = mux_state
        check_result[4] = "yes" if mux_state != hw_mux_state else "no"
        check_result[5] = "yes" if neighbor_ip in asic_neighs else "no"
        check_result[6] = "yes" if neighbor_ip in asic_route_destinations else "no"

        if mux_state == "active":
            if check_result[5] == "yes" and check_result[6] != "yes":
                check_result[7] = "consistent"
            else:
                check_result[7] = "inconsistent"
        elif mux_state == "standby":
            if check_result[5] != "yes" and check_result[6] == "yes":
                check_result[7] = "consistent"
            else:
                check_result[7] = "inconsistent"
        check_results.append(check_result)

    output_lines = tabulate.tabulate(
        check_results,
        headers=show_items,
        tablefmt="simple"
    )
    for output_line in output_lines.split("\n"):
        WRITE_LOG_WARN(output_line)


if __name__ == "__main__":
    args = parse_args()
    config_logging(args)

    mux_cables = get_mux_cable_config()
    mux_server_to_port_map = get_mux_server_to_port_map(mux_cables)
    if_oid_to_port_name_map = get_if_br_oid_to_port_name_map()
    neighbors, mux_states, hw_mux_states, asic_fdb, asic_route_table, asic_neigh_table = read_tables_from_db()
    mac_to_port_name_map = get_mac_to_port_name_map(asic_fdb, if_oid_to_port_name_map)

    check_neighbor_consistency(
        neighbors,
        mux_states,
        hw_mux_states,
        mac_to_port_name_map,
        asic_route_table,
        asic_neigh_table,
        mux_server_to_port_map
    )
