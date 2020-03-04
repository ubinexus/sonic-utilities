#!/usr/bin/env python

import traceback
import sys
import argparse
import syslog
from swsssdk import ConfigDBConnector
import sonic_device_util
import os
import subprocess
import json


SYSLOG_IDENTIFIER = 'db_migrator'


def log_info(msg):
    syslog.openlog(SYSLOG_IDENTIFIER)
    syslog.syslog(syslog.LOG_INFO, msg)
    syslog.closelog()


def log_error(msg):
    syslog.openlog(SYSLOG_IDENTIFIER)
    syslog.syslog(syslog.LOG_ERR, msg)
    syslog.closelog()


class DBMigrator():
    def __init__(self, socket=None):
        """
        Version string format:
           version_<major>_<minor>_<build>
              major: starting from 1, sequentially incrementing in master
                     branch.
              minor: in github branches, minor version stays in 0. This minor
                     version creates space for private branches derived from
                     github public branches. These private branches shall use
                     none-zero values.
              build: sequentially increase within a minor version domain.
        """
        self.CURRENT_VERSION = 'version_1_0_3'

        self.TABLE_NAME      = 'VERSIONS'
        self.TABLE_KEY       = 'DATABASE'
        self.TABLE_FIELD     = 'VERSION'

        db_kwargs = {}
        if socket:
            db_kwargs['unix_socket_path'] = socket

        self.configDB        = ConfigDBConnector(**db_kwargs)
        self.configDB.db_connect('CONFIG_DB')


    def migrate_pfc_wd_table(self):
        '''
        Migrate all data entries from table PFC_WD_TABLE to PFC_WD
        '''
        data = self.configDB.get_table('PFC_WD_TABLE')
        for key in data.keys():
            self.configDB.set_entry('PFC_WD', key, data[key])
        self.configDB.delete_table('PFC_WD_TABLE')

    def is_ip_prefix_in_key(self, key):
        '''
        Function to check if IP address is present in the key. If it
        is present, then the key would be a tuple or else, it shall be
        be string
        '''
        return (isinstance(key, tuple))

    def migrate_interface_table(self):
        '''
        Migrate all data from existing INTERFACE table with IP Prefix
        to have an additional ONE entry without IP Prefix. For. e.g, for an entry
        "Vlan1000|192.168.0.1/21": {}", this function shall add an entry without
        IP prefix as ""Vlan1000": {}". This is for VRF compatibility.
        '''
        if_db = []
        if_tables = {
                     'INTERFACE',
                     'PORTCHANNEL_INTERFACE',
                     'VLAN_INTERFACE',
                     'LOOPBACK_INTERFACE'
                    }
        for table in if_tables:
            data = self.configDB.get_table(table)
            for key in data.keys():
                if not self.is_ip_prefix_in_key(key):
                    if_db.append(key)
                    continue

        for table in if_tables:
            data = self.configDB.get_table(table)
            for key in data.keys():
                if not self.is_ip_prefix_in_key(key) or key[0] in if_db:
                    continue
                log_info('Migrating interface table for ' + key[0])
                self.configDB.set_entry(table, key[0], data[key])
                if_db.append(key[0])

    def mlnx_migrate_buffer_pool_size(self):
        """
        On Mellanox platform the buffer pool size changed since 
        version with new SDK 4.3.3052, SONiC to SONiC update 
        from version with old SDK will be broken without migration.
        This migration is specifically for Mellanox platform. 
        """
        # Buffer pools defined in version 1_0_2
        buffer_pools = ['ingress_lossless_pool', 'egress_lossless_pool', 'ingress_lossy_pool', 'egress_lossy_pool']

        # Old default buffer pool values on Mellanox platform 
        spc1_t0_default_value = [{'ingress_lossless_pool': '4194304'}, {'egress_lossless_pool': '16777152'}, {'ingress_lossy_pool': '7340032'}, {'egress_lossy_pool': '7340032'}]
        spc1_t1_default_value = [{'ingress_lossless_pool': '2097152'}, {'egress_lossless_pool': '16777152'}, {'ingress_lossy_pool': '5242880'}, {'egress_lossy_pool': '5242880'}]
        spc2_t0_default_value = [{'ingress_lossless_pool': '8224768'}, {'egress_lossless_pool': '35966016'}, {'ingress_lossy_pool': '8224768'}, {'egress_lossy_pool': '8224768'}]
        spc2_t1_default_value = [{'ingress_lossless_pool': '12042240'}, {'egress_lossless_pool': '35966016'}, {'ingress_lossy_pool': '12042240'}, {'egress_lossy_pool': '12042240'}]
 
        # Get platform info and hwsku from config_db.json
        config_db_file_path = "/etc/sonic/config_db.json"
        if not os.path.exists(config_db_file_path):
            log_info("config_db.json not exist, skip")
            return False
        try:
            with open(config_db_file_path) as config_db_file:
                config_db = json.load(config_db_file)
                device_data = config_db['DEVICE_METADATA']
                hwsku = device_data['localhost']['hwsku']
                platform = device_data['localhost']['platform']
        except IOError:
            log_error("failed to open config_db.json file, skip migration")
            return False
        
        # Get current buffer pool configuration, only migrate configration which 
        # with default values, if it's not default, leave it as is.
        pool_size_in_db_list = []
        data = config_db['BUFFER_POOL']
        pools_in_db = data.keys()

        # Buffer pool numbers is different with default, don't need migrate
        if len(pools_in_db) != len(buffer_pools):
            return True

        # If some buffer pool is not default ones, don't need migrate
        for buffer_pool in buffer_pools:
            if buffer_pool not in pools_in_db:
                return True
            pool_size_in_db_list.append({buffer_pool: data[buffer_pool]['size']})
        
        # To check if the buffer pool size is equal to default values
        if pool_size_in_db_list == spc1_t0_default_value or pool_size_in_db_list == spc1_t1_default_value \
            or pool_size_in_db_list == spc2_t0_default_value or pool_size_in_db_list == spc2_t1_default_value:
            # Generate buffer configuration from latest template
            tmp_json_file = "/tmp/mlnx_buffers_all.json"
            device_buffer_template_path = os.path.join("/usr/share/sonic/device/", platform, hwsku, 'buffers.json.j2')
            command = "sonic-cfggen -d -t {} >{}".format(device_buffer_template_path, tmp_json_file)
            try:
                subprocess.check_call(command, shell=True)
            except:
                log_error("failed to generate new mlnx buffer configuration, skip migration")
                return False

            # Extract the new buffer pool size configuration from above tmp file and update DB
            try:
                with open(tmp_json_file) as tmp_buffer_file:
                    buffer_json = json.load(tmp_buffer_file)
                    for pool in buffer_pools:
                        self.configDB.set_entry('BUFFER_POOL', pool, buffer_json['BUFFER_POOL'][pool])
                    log_info("Successfully migrate mlnx buffer pool size to the latest.")
                    return True
            except IOError:
                log_error("failed to open tmp mlnx buffer json configuration file, skip migration")
                return False
        else:
            # It's not using default buffer pool configuration, no migraton needed.
            return True

    def version_unknown(self):
        """
        version_unknown tracks all SONiC versions that doesn't have a version
        string defined in config_DB.
        Nothing can be assumped when migrating from this version to the next
        version.
        Any migration operation needs to test if the DB is in expected format
        before migrating date to the next version.
        """

        log_info('Handling version_unknown')

        # NOTE: Uncomment next 3 lines of code when the migration code is in
        #       place. Note that returning specific string is intentional,
        #       here we only intended to migrade to DB version 1.0.1.
        #       If new DB version is added in the future, the incremental
        #       upgrade will take care of the subsequent migrations.
        self.migrate_pfc_wd_table()
        self.migrate_interface_table()
        self.set_version('version_1_0_2')
        return 'version_1_0_2'

    def version_1_0_1(self):
        """
        Version 1_0_1.
        """
        log_info('Handling version_1_0_1')

        self.migrate_interface_table()
        self.set_version('version_1_0_2')
        return 'version_1_0_2'

    def version_1_0_2(self):
        """
        Version 1_0_2.
        """
        log_info('Handling version_1_0_2')
        # Check ASIC type, if Mellanox platform then need DB migration
        version_info = sonic_device_util.get_sonic_version_info()
        if version_info['asic_type'] == "mellanox":
            if self.mlnx_migrate_buffer_pool_size():
                self.set_version('version_1_0_3')
        else:
            self.set_version('version_1_0_3')
        return None

    def version_1_0_3(self):
        """
        Current latest version. Nothing to do here.
        """
        log_info('Handling version_1_0_3')

        return None

    def get_version(self):
        version = self.configDB.get_entry(self.TABLE_NAME, self.TABLE_KEY)
        if version and version[self.TABLE_FIELD]:
            return version[self.TABLE_FIELD]

        return 'version_unknown'


    def set_version(self, version=None):
        if not version:
            version = self.CURRENT_VERSION
        log_info('Setting version to ' + version)
        entry = { self.TABLE_FIELD : version }
        self.configDB.set_entry(self.TABLE_NAME, self.TABLE_KEY, entry)


    def migrate(self):
        version = self.get_version()
        log_info('Upgrading from version ' + version)
        while version:
            next_version = getattr(self, version)()
            if next_version == version:
                raise Exception('Version migrate from %s stuck in same version' % version)
            version = next_version


def main():
    try:
        parser = argparse.ArgumentParser()

        parser.add_argument('-o',
                            dest='operation',
                            metavar='operation (migrate, set_version, get_version)',
                            type = str,
                            required = False,
                            choices=['migrate', 'set_version', 'get_version'],
                            help = 'operation to perform [default: get_version]',
                            default='get_version')
        parser.add_argument('-s',
                        dest='socket',
                        metavar='unix socket',
                        type = str,
                        required = False,
                        help = 'the unix socket that the desired database listens on',
                        default = None )
        args = parser.parse_args()
        operation = args.operation
        socket_path = args.socket

        if socket_path:
            dbmgtr = DBMigrator(socket=socket_path)
        else:
            dbmgtr = DBMigrator()

        result = getattr(dbmgtr, operation)()
        if result:
            print(str(result))

    except Exception as e:
        log_error('Caught exception: ' + str(e))
        traceback.print_exc()
        print(str(e))
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
