#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
from swsssdk import ConfigDBConnector
from swsssdk import SonicV2Connector


def get_vnet_intfs():
    config_db = ConfigDBConnector()
    config_db.connect('CONFIG_DB')

    intfs_data = config_db.get_table("INTERFACE")
    vlan_intfs_data = config_db.get_table("VLAN_INTERFACE")

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


def get_rifs_oid():
    db = SonicV2Connector(host='127.0.0.1')
    db.connect(db.COUNTERS_DB)

    keys = db.get_all(db.COUNTERS_DB, 'COUNTERS_RIF_NAME_MAP');

    return keys


def get_vnet_rifs_oid():
    intfs = get_vnet_intfs()
    intfs_oids = get_rifs_oid()

    list = [intfs[k] for k in intfs]
    flattened = [val for sublist in list for val in sublist]

    oids = {}

    for i in intfs_oids:
        if i in flattened:
            oids[i] = intfs_oids[i]

    return oids


def get_vrf_entries():
    db = ConfigDBConnector()
    db.db_connect('ASIC_DB')

    oids = get_vnet_rifs_oid()

    vrid = {}

    for k in oids:
        keys = db.get_all(db.ASIC_DB, 'ASIC_STATE:SAI_OBJECT_TYPE_ROUTER_INTERFACE:{}'.format(oids[k]))
        vrid[k] = keys['SAI_ROUTER_INTERFACE_ATTR_VIRTUAL_ROUTER_ID']

    return vrid


def get_routes_from_app_db():
    db = ConfigDBConnector()
    db.db_connect('APPL_DB')

    intfs = get_vnet_intfs()
    vrfs = get_vrf_entries()

    keys = db.get_keys('VNET_ROUTE_TABLE') + db.get_keys('VNET_ROUTE_TUNNEL_TABLE')

    routes = {}

    for k in keys:
        kv = k.split(':')

        if kv[0] not in routes:
            routes[kv[0]] = {}
            routes[kv[0]]['routes'] = []

            intf = intfs[kv[0]][0]
            routes[kv[0]]['vrf_oid'] = vrfs.get(intf, 'None')

        routes[kv[0]]['routes'].append(kv[1])

    return routes


def get_routes_from_asic_db():
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
        vr = k.lower().split("\"", -1)[11]
        ip = k.lower().split("\"", -1)[3]
        if vr in list:
            if vr_to_vnet[vr] not in routes:
                routes[vr_to_vnet[vr]] = {}
                routes[vr_to_vnet[vr]]['routes'] = []
                routes[vr_to_vnet[vr]]['vrf_oid'] = vr

            routes[vr_to_vnet[vr]]['routes'].append(ip)

    return routes


def get_routes_diff(routes_1, routes_2):
    routes = {}

    for k, v in routes_2.items():
        if k not in routes_1:
            routes[k] = v
        else:
            for rt in v["routes"]:
                if rt not in routes_1[k]["routes"]:
                    if k not in routes:
                        routes[k] = {}
                        routes[k]["routes"] = []
                    routes[k]["routes"].append(rt)
                    routes[k]["vrf_oid"] = routes_1[k]["vrf_oid"]

    return routes


def get_sdk_routes_diff(routes):
    routes_diff = {}
    for k, v in routes.items():
        res = os.system('docker exec syncd "/usr/bin/vnet_route_check.py {} {}"'.format(routes[k], routes[k]["vrf_oid"]))
        if res:
            routes[k] = {}
            routes[k]["routes"] = res

    return routes_diff


def main():

    app_routes = get_routes_from_asic_db()
    asic_routes = get_routes_from_app_db()

    missed_in_asic_db_routes = get_routes_diff(asic_routes, app_routes)
    missed_in_app_db_routes = get_routes_diff(app_routes, asic_routes)
    missed_in_sdk_routes = get_sdk_routes_diff(asic_routes)

    res = {}
    res["results"] = {}
    rc = 0

    if missed_in_asic_db_routes:
        res["results"]["missed_in_asic_db_routes"] = missed_in_asic_db_routes

    if missed_in_app_db_routes:
        res["results"]["missed_in_app_db_routes"] = missed_in_app_db_routes

    if missed_in_sdk_routes:
        res["results"]["missed_in_sdk_routes"] = missed_in_sdk_routes

    if res["results"]:
        rc = -1
        print(json.dumps(res, indent=4))

    sys.exit(rc)


if __name__ == "__main__":
    main()

