#!/usr/bin/env python3

import os, sys
import json, jsonschema
import argparse
import syslog
import traceback


CONFIG_DB_SCHEMA = {
    "$schema": "http://json-schema.org/draft-06/schema",
    "type": "object",
    "title": "Schema for config_db.json critical structure needed before reboot",
    "required": [
        "ACL_TABLE",
        "BGP_NEIGHBOR",
        "BGP_PEER_RANGE",
        "BUFFER_PG",
        "BUFFER_POOL",
        "BUFFER_PROFILE",
        "BUFFER_QUEUE",
        "CABLE_LENGTH",
        "CRM",
        "DEVICE_METADATA",
        "DEVICE_NEIGHBOR",
        "DEVICE_NEIGHBOR_METADATA",
        "DHCP_SERVER",
        "DSCP_TO_TC_MAP",
        "FEATURE",
        "FLEX_COUNTER_TABLE",
        "KDUMP",
        "LOOPBACK_INTERFACE",
        "MAP_PFC_PRIORITY_TO_QUEUE",
        "MGMT_INTERFACE",
        "MGMT_PORT",
        "NTP_SERVER",
        "PFC_WD",
        "PORT",
        "PORTCHANNEL",
        "PORTCHANNEL_INTERFACE",
        "PORTCHANNEL_MEMBER",
        "PORT_QOS_MAP",
        "QUEUE",
        "SCHEDULER",
        "SNMP",
        "SNMP_COMMUNITY",
        "SYSLOG_SERVER",
        "TACPLUS_SERVER",
        "TC_TO_PRIORITY_GROUP_MAP",
        "TC_TO_QUEUE_MAP",
        "VERSIONS",
        "VLAN",
        "VLAN_INTERFACE",
        "VLAN_MEMBER",
        "WRED_PROFILE"
    ],
    "properties": {
        "ACL_TABLE": {
            "$id": "#/properties/ACL_TABLE",
            "type": "object"
        },
        "BGP_NEIGHBOR": {
            "$id": "#/properties/BGP_NEIGHBOR",
            "type": "object"
        },
        "BGP_PEER_RANGE": {
            "$id": "#/properties/BGP_PEER_RANGE",
            "type": "object"
        },
        "BUFFER_PG": {
            "$id": "#/properties/BUFFER_PG",
            "type": "object"
        },
        "BUFFER_POOL": {
            "$id": "#/properties/BUFFER_POOL",
            "type": "object"
        },
        "BUFFER_PROFILE": {
            "$id": "#/properties/BUFFER_PROFILE",
            "type": "object"
        },
        "BUFFER_QUEUE": {
            "$id": "#/properties/BUFFER_QUEUE",
            "type": "object"
        },
        "CABLE_LENGTH": {
            "$id": "#/properties/CABLE_LENGTH",
            "type": "object"
        },
        "CRM": {
            "$id": "#/properties/CRM",
            "type": "object"
        },
        "DEVICE_METADATA": {
            "$id": "#/properties/DEVICE_METADATA",
            "type": "object"
        },
        "DEVICE_NEIGHBOR": {
            "$id": "#/properties/DEVICE_NEIGHBOR",
            "type": "object"
        },
        "DEVICE_NEIGHBOR_METADATA": {
            "$id": "#/properties/DEVICE_NEIGHBOR_METADATA",
            "type": "object"
        },
        "DHCP_SERVER": {
            "$id": "#/properties/DHCP_SERVER",
            "type": "object"
        },
        "DSCP_TO_TC_MAP": {
            "$id": "#/properties/DSCP_TO_TC_MAP",
            "type": "object"
        },
        "FEATURE": {
            "$id": "#/properties/FEATURE",
            "type": "object",
            "required": [
                "acms",
                "bgp",
                "database",
                "dhcp_relay",
                "lldp",
                "mux",
                "pmon",
                "radv",
                "snmp",
                "swss",
                "syncd",
                "teamd",
                "telemetry"
            ],
            "properties": {
                "acms": {
                    "$id": "#/properties/FEATURE/properties/acms",
                    "type": "object"
                },
                "bgp": {
                    "$id": "#/properties/FEATURE/properties/bgp",
                    "type": "object"
                },
                "database": {
                    "$id": "#/properties/FEATURE/properties/database",
                    "type": "object"
                },
                "dhcp_relay": {
                    "$id": "#/properties/FEATURE/properties/dhcp_relay",
                    "type": "object"
                },
                "lldp": {
                    "$id": "#/properties/FEATURE/properties/lldp",
                    "type": "object"
                },
                "mux": {
                    "$id": "#/properties/FEATURE/properties/mux",
                    "type": "object"
                },
                "pmon": {
                    "$id": "#/properties/FEATURE/properties/pmon",
                    "type": "object"
                },
                "radv": {
                    "$id": "#/properties/FEATURE/properties/radv",
                    "type": "object"
                },
                "snmp": {
                    "$id": "#/properties/FEATURE/properties/snmp",
                    "type": "object"
                },
                "swss": {
                    "$id": "#/properties/FEATURE/properties/swss",
                    "type": "object"
                },
                "syncd": {
                    "$id": "#/properties/FEATURE/properties/syncd",
                    "type": "object"
                },
                "teamd": {
                    "$id": "#/properties/FEATURE/properties/teamd",
                    "type": "object"
                },
                "telemetry": {
                    "$id": "#/properties/FEATURE/properties/telemetry",
                    "type": "object"
                }
            }
        },
        "FLEX_COUNTER_TABLE": {
            "$id": "#/properties/FLEX_COUNTER_TABLE",
            "type": "object"
        },
        "KDUMP": {
            "$id": "#/properties/KDUMP",
            "type": "object"
        },
        "LOOPBACK_INTERFACE": {
            "$id": "#/properties/LOOPBACK_INTERFACE",
            "type": "object"
        },
        "MAP_PFC_PRIORITY_TO_QUEUE": {
            "$id": "#/properties/MAP_PFC_PRIORITY_TO_QUEUE",
            "type": "object"
        },
        "MGMT_INTERFACE": {
            "$id": "#/properties/MGMT_INTERFACE",
            "type": "object"
        },
        "MGMT_PORT": {
            "$id": "#/properties/MGMT_PORT",
            "type": "object"
        },
        "NTP_SERVER": {
            "$id": "#/properties/NTP_SERVER",
            "type": "object"
        },
        "PFC_WD": {
            "$id": "#/properties/PFC_WD",
            "type": "object"
        },
        "PORT": {
            "$id": "#/properties/PORT",
            "type": "object"
        },
        "PORTCHANNEL": {
            "$id": "#/properties/PORTCHANNEL",
            "type": "object"
        },
        "PORTCHANNEL_INTERFACE": {
            "$id": "#/properties/PORTCHANNEL_INTERFACE",
            "type": "object"
        },
        "PORTCHANNEL_MEMBER": {
            "$id": "#/properties/PORTCHANNEL_MEMBER",
            "type": "object"
        },
        "PORT_QOS_MAP": {
            "$id": "#/properties/PORT_QOS_MAP",
            "type": "object"
        },
        "QUEUE": {
            "$id": "#/properties/QUEUE",
            "type": "object"
        },
        "SCHEDULER": {
            "$id": "#/properties/SCHEDULER",
            "type": "object"
        },
        "SNMP": {
            "$id": "#/properties/SNMP",
            "type": "object"
        },
        "SNMP_COMMUNITY": {
            "$id": "#/properties/SNMP_COMMUNITY",
            "type": "object"
        },
        "SYSLOG_SERVER": {
            "$id": "#/properties/SYSLOG_SERVER",
            "type": "object"
        },
        "TACPLUS_SERVER": {
            "$id": "#/properties/TACPLUS_SERVER",
            "type": "object"
        },
        "TC_TO_PRIORITY_GROUP_MAP": {
            "$id": "#/properties/TC_TO_PRIORITY_GROUP_MAP",
            "type": "object"
        },
        "TC_TO_QUEUE_MAP": {
            "$id": "#/properties/TC_TO_QUEUE_MAP",
            "type": "object"
        },
        "VERSIONS": {
            "$id": "#/properties/VERSIONS",
            "type": "object",
            "required": [
                "DATABASE"
            ],
            "properties": {
                "DATABASE": {
                    "$id": "#/properties/VERSIONS/properties/DATABASE",
                    "type": "object",
                    "required": [
                        "VERSION"
                    ],
                    "properties": {
                        "VERSION": {
                            "$id": "#/properties/VERSIONS/properties/DATABASE/properties/VERSION",
                            "type": "string"
                        }
                    }
                }
            }
        },
        "VLAN": {
            "$id": "#/properties/VLAN",
            "type": "object"
        },
        "VLAN_INTERFACE": {
            "$id": "#/properties/VLAN_INTERFACE",
            "type": "object"
        },
        "VLAN_MEMBER": {
            "$id": "#/properties/VLAN_MEMBER",
            "type": "object"
        },
        "WRED_PROFILE": {
            "$id": "#/properties/WRED_PROFILE",
            "type": "object"
        }
    }
}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config_db_file', type=str,
        default='/etc/sonic/config_db.json',
        help='Absolute location of config_db.json file')

    args = parser.parse_args()
    config_db_file = args.config_db_file
    config_db_data = dict()

    # Read config_db.json and check if it is a valid JSON file
    try:
        with open(config_db_file) as fp:
            config_db_data = json.load(fp)
    except ValueError as err:
        syslog.syslog(syslog.LOG_DEBUG, "Config DB json file is not a valid json file. " +\
            "Error: {}".format(str(err)))
        return 1

    # What: Validate if critical tables and entries are present in config_db.json
    # Why: This is needed to avoid rebooting with a bad config_db.json; which can
    #   potentially trigger failures in the reboot recovery path.
    # How: Check config_db.json against a schema (CONFIG_DB_SCHEMA) which defines
    #   REQUIRED tables and their types.
    try:
        jsonschema.validate(instance=config_db_data, schema=CONFIG_DB_SCHEMA)
    except jsonschema.exceptions.ValidationError as err:
        syslog.syslog(syslog.LOG_ERR, "Database is missing tables/entries needed for reboot procedure. " +\
            "Config db integrity check failed with:\n{}".format(str(err)))
        return 1
    syslog.syslog(syslog.LOG_DEBUG, "Database integrity checks passed.")
    return 0


if __name__ == '__main__':
    res = 0
    try:
        res = main()
    except KeyboardInterrupt:
        syslog.syslog(syslog.LOG_NOTICE, "SIGINT received. Quitting")
        res = 1
    except Exception as e:
        syslog.syslog(syslog.LOG_ERR, "Got an exception %s: Traceback: %s" % (str(e), traceback.format_exc()))
        res = 2
    finally:
        syslog.closelog()
    try:
        sys.exit(res)
    except SystemExit:
        os._exit(res)
