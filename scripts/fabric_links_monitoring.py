#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

import os
import sys
import time
import json
import syslog
import subprocess

from swsssdk import  SonicV2Connector, SonicDBConfig
from sonic_py_common import multi_asic

class FabricLinkErrMontoring():
    '''Class to monitor the fabric link errors for a given namespace'''

    def __init__(self, namespace, port_name_map, filter_for_up_ports=None):
        '''Initialize the class with the namespace and port_name_map in counters db'''
        self.namespace = namespace
        self.port_name_map = port_name_map
        self.filter_for_up_ports = filter_for_up_ports
        self.port_map = self.get_port_map()
        print('Fabric device id :', namespace)
        subprocess.run(["sonic-clear", "fabriccountersport"])
        self.prev_port_counters = self.port_counters

    @property
    def counter_db(self):
        '''Return the counter db object'''
        db = SonicV2Connector(namespace=self.namespace)
        db.connect('COUNTERS_DB')
        return db

    def get_port_map(self):
        '''
        Return the port map from the counter db
        for the port_names in the port_name_map
        Additonally the port map can be filtered for UP ports
        '''
        ports = self.counter_db.get_all('COUNTERS_DB', self.port_name_map)
        if self.filter_for_up_ports:
            port_to_mon = self.filter_for_up_ports(self.namespace, ports)
        return port_to_mon

    @property
    def port_counters(self):
        '''Return the port counters for all the port in the port_map'''
        port_counters = {}
        for port_name, port_oid in self.port_map.items():
            port_counter = self.counter_db.get_all(
                    "COUNTERS_DB", 'COUNTERS:{}'.format(port_oid))
            port_counters[port_name] = port_counter
        return port_counters

    def get_ports_error_above_threshold(self, counter_name, threshold):
        ''' 
        Return the list of ports which have the counter value above the threshold
        '''
        err_ports = []
        for port_name, port_counter in self.port_counters.items():
            try:
                port_counter_value = port_counter[counter_name]
                prev_port_counter_value = self.prev_port_counters[port_name][counter_name]
                if (int(port_counter_value) - int(prev_port_counter_value)) > threshold:
                    err_ports.append(port_name)
            except KeyError:
                print('Bad counter_name')

        self.prev_port_counters = self.port_counters.copy()     
        return err_ports
    
    def monitor(self, namespace, error_counter_names, threshold ):
        err_ports = []
        
        for counter_name in error_counter_names:
            err_ports_per_counter = self.get_ports_error_above_threshold(
                    counter_name,threshold)
            if err_ports_per_counter:
                syslog.syslog(syslog.LOG_CRIT,
                                  ' {} error above threshold on fabric port {} in {} '.format(counter_name,err_ports_per_counter, namespace))
                err_ports.extend(err_ports_per_counter)
        return err_ports


class PacketChassisFabricLinkMontoring():
    '''A class for monitoring internal links in a Packet Chassis.

    Attributes:
        link_monitor (dict): A dictionary of LinkMonitor objects, keyed by namespace.
        error_counter_names (list): A list of error counter names to monitor.
        threshold (int): The threshold for error counters.
    '''

    def __init__(self):
        '''Initializes a PacketChassisFabricLinkMontoring object.

        Args:
            link_monitor (dict): A dictionary of LinkMonitor objects, keyed by namespace.
            error_counter_names (list): A list of error counter names to monitor.
            threshold (int): The threshold for error counters.

        Returns:
            None
        '''

        self.link_monitor = {}
        self.appdb = {}
        self.configdb = {}
        self.statedb = {}
        for namespace in self.namespaces:
            self.appdb[namespace] = self.appl_db(namespace)
            self.configdb[namespace] = self.config_db(namespace)
            self.statedb[namespace] = self.state_db(namespace)
            self.link_monitor[namespace] = FabricLinkErrMontoring(
                namespace=namespace, port_name_map='COUNTERS_FABRIC_PORT_NAME_MAP',
                filter_for_up_ports=self.filter_for_up_ports)
        self.error_counter_names = ['SAI_PORT_STAT_IF_IN_ERRORS']
        self.threshold = 60

    @property
    def namespaces(self):
        namespaces = []
        SonicDBConfig.load_sonic_global_db_config()
        namespaces = multi_asic.get_namespace_list()
        return namespaces
        
    def config_db(self,namespace):
        '''Returns the config db object for the namespace'''
        db = SonicV2Connector(namespace=namespace)
        db.connect('CONFIG_DB')
        return db
    
    def appl_db(self, namespace):
        '''Returns the application db object for the namespace'''
        db = SonicV2Connector(namespace=namespace)
        db.connect('APPL_DB')
        return db

    def state_db(self, namespace):
        '''Returns the state db object for the namespace'''
        db = SonicV2Connector(namespace=namespace)
        db.connect('STATE_DB')
        return db

    def get_port_status(self, namespace, port_name):
        ''' Returns operational status of give port 
            When port is admin shut in CONFIG_DB, it might take some time for port to be oper down in APPL_DB.
            As such, status of ports which are admin shut in config DB is reported as down
        '''
        port_info = self.statedb[namespace].get_all('STATE_DB', 'FABRIC_PORT_TABLE|{}'.format(port_name))
        return port_info['STATUS']

    def filter_for_up_ports(self, namespace, port_map):
        ''' Returns only internal (backend) ports which are operationally up for monitoring '''
        filtered_port_map = {}
        if port_map:
            for k,v in port_map.items():
                if self.get_port_status(namespace, k) == 'up':
                    filtered_port_map[k] = v
        return filtered_port_map

    def monitor(self):
        '''
        Monitors the error counters for each fabric port in each namespace.
        If any error counters are above the specified threshold, a syslog message is generated.
        '''
        all_error_ports = []
        while True:
            for namespace, link_mon in self.link_monitor.items():
                err_port_per_ns = link_mon.monitor(namespace, self.error_counter_names, self.threshold)
                if err_port_per_ns:
                    syslog.syslog(syslog.LOG_CRIT,
                                '{} fabric ports in {} have errors above threshold'.format(len(err_port_per_ns), namespace))
            time.sleep(60)

def main():
    if multi_asic.is_multi_asic():
        link_monitor = PacketChassisFabricLinkMontoring()
        link_monitor.monitor()
    return 0

if __name__ == '__main__':
    main()
