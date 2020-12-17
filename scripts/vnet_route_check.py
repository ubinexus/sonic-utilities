#!/usr/bin/env python

import os
import sys
import json
from swsssdk import ConfigDBConnector
from swsssdk import SonicV2Connector
from collections import defaultdict


''' vnet_route_check.py: tool that verifies VNET routes consistancy between SONiC and vendor SDK DBs.

Logically VNET route verification logic consists of 3 parts:
1. Get VNET routes entries that are missed in ASIC_DB but present in APP_DB.
2. Get VNET routes entries that are missed in APP_DB but present in ASIC_DB.
3. Get VNET routes entries that are missed in SDK but present in ASIC_DB.

Returns 0 if there is no inconsistancy found and all VNET routes are aligned in all DBs.
Returns -1 and prints differences between DBs in JSON format to standart output.

Format of differences output:
{
    "results": {
        "missed_in_asic_db_routes": {
            "<vnet_name>": {
                "routes": [
                    "<pfx>/<pfx_len>"
                ]
            }
        },
        "missed_in_app_db_routes": {
            "<vnet_name>": {
                "routes": [
                    "<pfx>/<pfx_len>"
                ]
            }
        },
        "missed_in_sdk_routes": {
            "<vnet_name>": {
                "routes": [
                    "<pfx>/<pfx_len>"
                ]
            }
        }
    }
}

'''


def get_vnet_intfs():
    ''' Returns dictionary VNETs and related VNET interfaces.
    Format: { <vnet_name>: [ <vnet_rif_name> ] }
    '''
    config_db = ConfigDBConnector()
    config_db.connect('CONFIG_DB')

    intfs_data = config_db.get_table('INTERFACE')
    vlan_intfs_data = config_db.get_table('VLAN_INTERFACE')

    vnet_intfs = {}
    for k, v in intfs_data.items():
        if 'vnet_name' in v:
            vnet_name = v['vnet_name']
            if vnet_name in vnet_intfs:
                vnet_intfs[vnet_name].append(k)
            else:
                vnet_intfs[vnet_name] = [k]

    for k, v in vlan_intfs_data.items():
        if 'vnet_name' in v:
            vnet_name = v['vnet_name']
            if vnet_name in vnet_intfs:
                vnet_intfs[vnet_name].append(k)
            else:
                vnet_intfs[vnet_name] = [k]

    return vnet_intfs


def get_all_rifs_oids():
    ''' Returns dictionary of all router interfaces and their OIDs.
    Format: { <rif_name>: <rif_oid> }
    '''
    db = SonicV2Connector(host='127.0.0.1')
    db.connect(db.COUNTERS_DB)

    rif_name_oid_map = db.get_all(db.COUNTERS_DB, 'COUNTERS_RIF_NAME_MAP');

    return rif_name_oid_map


def get_vnet_rifs_oids():
    ''' Returns dictionary of VNET interfaces and their OIDs.
    Format: { <vnet_rif_name>: <vnet_rif_oid> }
    '''
    vnet_intfs = get_vnet_intfs()
    intfs_oids = get_all_rifs_oids()

    vnet_intfs = [vnet_intfs[k] for k in vnet_intfs]
    vnet_intfs = [val for sublist in vnet_intfs for val in sublist]

    vnet_rifs_oids_map = {}

    for intf_name in intfs_oids:
        if intf_name in vnet_intfs:
            vnet_rifs_oids_map[intf_name] = intfs_oids[intf_name]

    return vnet_rifs_oids_map


def get_vrf_entries():
    ''' Returns dictionary of VNET interfaces and corresponding VRF OIDs.
    Format: { <vnet_rif_name>: <vrf_oid> }
    '''
    db = ConfigDBConnector()
    db.db_connect('ASIC_DB')

    vnet_rifs_oids = get_vnet_rifs_oids()

    rif_vrf_map = {}
    for k in vnet_rifs_oids:
        keys = db.get_all(db.ASIC_DB, 'ASIC_STATE:SAI_OBJECT_TYPE_ROUTER_INTERFACE:{}'.format(vnet_rifs_oids[k]))
        rif_vrf_map[k] = keys['SAI_ROUTER_INTERFACE_ATTR_VIRTUAL_ROUTER_ID']

    return rif_vrf_map


def get_vnet_routes_from_app_db():
    ''' Returns dictionary of VNET routes configured per each VNET in APP_DB.
    Format: { <vnet_name>: { 'routes': [ <pfx/pfx_len> ], 'vrf_oid': <oid> } }
    '''
    db = ConfigDBConnector()
    db.db_connect('APPL_DB')

    intfs = get_vnet_intfs()
    vrfs = get_vrf_entries()

    vnet_routes_db_keys = db.get_keys('VNET_ROUTE_TABLE') + db.get_keys('VNET_ROUTE_TUNNEL_TABLE')

    routes = {}

    for vnet_route_db_key in vnet_routes_db_keys:
        kv = vnet_route_db_key.split(':')

        if kv[0] not in routes:
            routes[kv[0]] = {}
            routes[kv[0]]['routes'] = []

            intf = intfs[kv[0]][0]
            routes[kv[0]]['vrf_oid'] = vrfs.get(intf, 'None')

        routes[kv[0]]['routes'].append(kv[1])

    return routes


def get_vnet_routes_from_asic_db():
    ''' Returns dictionary of VNET routes configured per each VNET in ASIC_DB.
    Format: { <vnet_name>: { 'routes': [ <pfx/pfx_len> ], 'vrf_oid': <oid> } }
    '''
    db = ConfigDBConnector()
    db.db_connect('ASIC_DB')

    vrfs = get_vrf_entries()
    list = [vrfs[k] for k in vrfs]
    intfs = get_vnet_intfs()

    vr_to_vnet = {}

    for k, v in intfs.items():
        for k1, v1 in vrfs.items():
            if k1 == v[0]:
                vr_to_vnet[v1] = k

    keys = db.get_keys('ASIC_STATE:SAI_OBJECT_TYPE_ROUTE_ENTRY', False)   

    routes = {}

    for k in keys:
        vr = k.lower().split('\"', -1)[11]
        ip = k.lower().split('\"', -1)[3]
        if vr in list:
            if vr_to_vnet[vr] not in routes:
                routes[vr_to_vnet[vr]] = {}
                routes[vr_to_vnet[vr]]['routes'] = []
                routes[vr_to_vnet[vr]]['vrf_oid'] = vr

            routes[vr_to_vnet[vr]]['routes'].append(ip)

    return routes


def get_vnet_routes_diff(routes_1, routes_2):
    ''' Returns all routes present in routes_2 dictionary but missed in routes_1
    Format: { <vnet_name>: { 'routes': [ <pfx/pfx_len> ], 'vrf_oid': <oid> } }
    '''

    routes = {}

    for k, v in routes_2.items():
        if k not in routes_1:
            routes[k] = v
        else:
            for rt in v['routes']:
                if rt not in routes_1[k]['routes']:
                    if k not in routes:
                        routes[k] = {}
                        routes[k]['routes'] = []
                    routes[k]['routes'].append(rt)
                    routes[k]['vrf_oid'] = routes_1[k]['vrf_oid']

    return routes


def get_sdk_vnet_routes_diff(routes):
    ''' Returns all routes present in routes dictionary but missed in SAI/SDK
    Format: { <vnet_name>: { 'routes': [ <pfx/pfx_len> ], 'vrf_oid': <oid> } }
    '''
    routes_diff = {}

    res = os.system('docker exec syncd test -f /usr/bin/vnet_route_check.py')
    if res != 0:
        return routes_diff

    for k, v in routes.items():
        res = os.system('docker exec syncd "/usr/bin/vnet_route_check.py {} {}"'.format(routes[k]["routes"], routes[k]["vrf_oid"]))
        if res:
            routes[k] = {}
            routes[k]['routes'] = res

    return routes_diff


def main():

    app_db_vnet_routes = get_vnet_routes_from_asic_db()
    asic_db_vnet_routes = get_vnet_routes_from_app_db()

    missed_in_asic_db_routes = get_vnet_routes_diff(asic_db_vnet_routes, app_db_vnet_routes)
    missed_in_app_db_routes = get_vnet_routes_diff(app_db_vnet_routes, asic_db_vnet_routes)
    missed_in_sdk_routes = get_sdk_vnet_routes_diff(asic_db_vnet_routes)

    res = {}
    res['results'] = {}
    rc = 0

    if missed_in_asic_db_routes:
        res['results']['missed_in_asic_db_routes'] = missed_in_asic_db_routes

    if missed_in_app_db_routes:
        res['results']['missed_in_app_db_routes'] = missed_in_app_db_routes

    if missed_in_sdk_routes:
        res['results']['missed_in_sdk_routes'] = missed_in_sdk_routes

    if res['results']:
        rc = -1
        print(json.dumps(res, indent=4))

    sys.exit(rc)


if __name__ == "__main__":
    main()

