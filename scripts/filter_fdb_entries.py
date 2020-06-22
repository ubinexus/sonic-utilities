#!/usr/bin/env python

import json
import sys
import os
import argparse
import syslog
import traceback
import time

from collections import defaultdict

def get_vlan_entries_map(filename):
    """
        Retreives Vlan information from Config DB file

        fdb entries could be contaminated with foreigh Vlan entries as seen in the cose of 
        FTOS fast conversion. SONiC Vlan configuration will be used to filter those invalid
        Vlan entries out.

        Args:
            filename(str): Config DB data file

        Returns:
            vlan_map(dict) map of Vlan configuration for SONiC device
    """
    with open(filename, 'r') as fp:
        config_db_entries = json.load(fp)

    return config_db_entries["VLAN"] if "VLAN" in config_db_entries.keys() else defaultdict()

def get_arp_entries_map(arp_filename, config_db_filename):
    """
        Generate map for ARP entries

        ARP entry map is using the MAC as a key for the arp entry. The map key is reformated in order
        to match FDB table formatting

        Args:
            arp_filename(str): ARP entry file name
            config_db_filename(str): Config DB file name

        Returns:
            arp_map(dict) map of ARP entries using MAC as key.
    """
    vlan_map = get_vlan_entries_map(config_db_filename)

    with open(arp_filename, 'r') as fp:
        arp_entries = json.load(fp)

    arp_map = defaultdict()
    for arp in arp_entries:
        for key, config in arp.items():
            entry_partial_keys = key.split(':')
            if 'NEIGH_TABLE' in entry_partial_keys[0] and entry_partial_keys[1] in vlan_map.keys() \
                and "neigh" in config.keys():
                arp_map[config["neigh"].replace(':', '-')] = ""

    return arp_map

def filter_fdb_entries(fdb_filename, arp_filename, config_db_filename, backup_file):
    """
        Filter FDB entries based on MAC presence into ARP entries

        FDB entries that do not have MAC entry in the ARP table are filtered out. New FDB entries
        file will be created if it has fewer entries than original one.

        Args:
            fdb_filename(str): FDB entries file name
            arp_filename(str): ARP entry file name
            config_db_filename(str): Config DB file name
            backup_file(bool): Create backup copy of FDB file before creating new one

        Returns:
            None
    """
    arp_map = get_arp_entries_map(arp_filename, config_db_filename)

    with open(fdb_filename, 'r') as fp:
        fdb_entries = json.load(fp)

    def filter_fdb_entry(fdb_entry):
        for key, _ in fdb_entry.items():
            if 'FDB_TABLE' in key:
                return key.split(':')[-1] in arp_map

        # malformed entry, default to False so it will be deleted
        return False

    new_fdb_entries = list(filter(filter_fdb_entry, fdb_entries))

    if len(new_fdb_entries) < len(fdb_entries):
        if backup_file:
            os.rename(fdb_filename, fdb_filename + '-' + time.strftime("%Y%m%d-%H%M%S"))

        with open(fdb_filename, 'w') as fp:
            json.dump(new_fdb_entries, fp, indent=2, separators=(',', ': '))

def file_exists_or_raise(filename):
    """
        Check if file exists on the file system

        Args:
            filename(str): File name

        Returns:
            None

        Raises:
            Exception file does not exist
    """
    if not os.path.exists(filename):
        raise Exception("file '{0}' does not exist".format(filename))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--fdb', type=str, default='/tmp/fdb.json', help='fdb file name')
    parser.add_argument('-a', '--arp', type=str, default='/tmp/arp.json', help='arp file name')
    parser.add_argument('-c', '--config_db', type=str, default='/tmp/config_db.json', help='config db file name')
    parser.add_argument('-b', '--backup_file', type=bool, default=True, help='Back up old fdb entries file')
    args = parser.parse_args()

    fdb_filename = args.fdb
    arp_filename = args.arp
    config_db_filename = args.config_db
    backup_file = args.backup_file

    try:
        file_exists_or_raise(fdb_filename)
        file_exists_or_raise(arp_filename)
        file_exists_or_raise(config_db_filename)
    except Exception as e:
        syslog.syslog(syslog.LOG_ERR, "Got an exception %s: Traceback: %s" % (str(e), traceback.format_exc()))
    else:
        filter_fdb_entries(fdb_filename, arp_filename, config_db_filename, backup_file)

    return 0

if __name__ == '__main__':
    res = 0
    try:
        syslog.openlog('filter_fdb_entries')
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
