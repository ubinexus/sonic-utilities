#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

import syslog


from swsssdk import  SonicV2Connector, SonicDBConfig
from sonic_py_common import multi_asic

class InternalLinkErrMontoring():
    '''Class to monitor the internal link errors for a given namespace'''

    def __init__(self, namespace, port_name_map, filter_for_backend_ports=None):
        '''Initialize the class with the namespace and port_name_map in counters db'''
        self.namespace = namespace
        self.port_name_map = port_name_map
        self.filter_for_backend_ports = filter_for_backend_ports
        self.port_map = self.get_port_map()

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
        Additonally the port map can be filtered for backend ports
        '''
        ports = self.counter_db.get_all('COUNTERS_DB', self.port_name_map)
        if self.filter_for_backend_ports:
            port_to_mon = self.filter_for_backend_ports(self.namespace, ports)
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
                if int(port_counter_value) > int(threshold):
                    err_ports.append(port_name)
            except KeyError:
                print('Bad counter_name')
        return err_ports
    
    def monitor(self, namespace, error_counter_names, threshold ):
        err_ports = []
        for counter_name in error_counter_names:
            err_ports_per_counter = self.get_ports_error_above_threshold(
                    counter_name,threshold)
            if err_ports_per_counter:
                syslog.syslog(syslog.LOG_CRIT,
                                  ' {} error above threshold on internal port {} in {} '.format(counter_name,err_ports_per_counter, namespace))
                err_ports.extend(err_ports_per_counter)
        return err_ports


class PacketChassisInternalLinkMontoring():
    '''A class for monitoring internal links in a Packet Chassis.

    Attributes:
        link_monitor (dict): A dictionary of LinkMonitor objects, keyed by namespace.
        error_counter_names (list): A list of error counter names to monitor.
        threshold (int): The threshold for error counters.
    '''

    def __init__(self):
        '''Initializes a PacketChassisInternalLinkMontoring object.

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
        for namespace in self.namespaces:
            self.appdb[namespace] = self.appl_db(namespace)
            self.configdb[namespace] = self.config_db(namespace)
            self.link_monitor[namespace] = InternalLinkErrMontoring(
                namespace=namespace, port_name_map='COUNTERS_PORT_NAME_MAP',
                filter_for_backend_ports=self.filter_for_backend_ports)
        self.error_counter_names = ['SAI_PORT_STAT_IF_IN_ERRORS',
                                    'SAI_PORT_STAT_IF_OUT_ERRORS']
        # Using fixed values for 201911
        self.threshold = 0
        self.mitigationActionEnabled = True

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

    def get_port_status(self, namespace, port_name):
        ''' Returns operational status of give port 
            When port is admin shut in CONFIG_DB, it might take some time for port to be oper down in APPL_DB.
            As such, status of ports which are admin shut in config DB is reported as down
        '''
        port_cfg = self.configdb[namespace].get_all('CONFIG_DB', 'PORT|{}'.format(port_name))
        port_info = self.appdb[namespace].get_all('APPL_DB', 'PORT_TABLE:{}'.format(port_name))
        if port_cfg:
            if port_cfg['admin_status'] == 'up':
                if port_info:
                    return port_info['oper_status']
        return 'down'

    def filter_for_backend_ports(self, namespace, port_map):
        ''' Returns only internal (backend) ports which are operationally up for monitoring '''
        filtered_port_map = {}
        for k,v in port_map.items():
            if k.startswith('Ethernet-BP'):                
                if self.get_port_status(namespace, k) == 'up':
                    filtered_port_map[k] = v
        return filtered_port_map

    def get_lag_name_for_port(self, namespace, port_name):
        ''' Returns name of the portchannel in which the given port is a member '''
        lag_member = self.appdb[namespace].keys('APPL_DB', 'LAG_MEMBER_TABLE:*:{}'.format(port_name))
        if len(lag_member):
            table = lag_member[0].find(":") + 1
            port = lag_member[0].find(":", table)
            return lag_member[0][table:port]
        return ''

    def get_min_links_for_lag(self, namespace, lag_name):
        ''' Returns min_links configuration of the given portchannel '''
        lag_info = self.configdb[namespace].get_all('CONFIG_DB', 'PORTCHANNEL|{}'.format(lag_name))        
        return int(lag_info['min_links'])        

    def get_active_lag_member_count(self, namespace, lag_name):
        ''' Returns number of member ports that are operationally up in the given portchannel '''
        lag_members = self.appdb[namespace].keys('APPL_DB', 'LAG_MEMBER_TABLE:{}:*'.format(lag_name))
        active_count = 0
        for member in lag_members:
            port = member.rsplit(':', 1)[1]            
            if self.get_port_status(namespace, port) == 'up':
                active_count += 1
        return active_count

    def isolate_lag_member(self, namespace, port_name):
        ''' Set admin_status of given port to down in the CONFIG_DB '''
        ret = self.configdb[namespace].set('CONFIG_DB', 'PORT|{}'.format(port_name), 'admin_status', 'down')
        if ret == 0:
            syslog.syslog(syslog.LOG_CRIT,
                                        'Internal port {} has been shutdown to mitigate errors'.format(port_name))
        else:
            syslog.syslog(syslog.LOG_CRIT,
                                        'Unable to shutdown internal port {}, return code {}'.format(port_name, ret))
    def attempt_to_mitigate_ports(self, namespace, err_port_per_ns):
        ''' Attempt to isolate given list of ports 
            1. Check if number of active links in the portchannel where the port is a member is greater
                than min_links. 
                a. If active links is greater, shutdown the port
                b. If not, return after generating syslog
        '''

        for port_name in err_port_per_ns:            
            syslog.syslog(syslog.LOG_INFO, "Attempting mitigation of port {}".format(port_name))
            lag_name = self.get_lag_name_for_port(namespace, port_name)
            active_count = self.get_active_lag_member_count(namespace, lag_name)
            min_links = self.get_min_links_for_lag(namespace, lag_name)

            if active_count > min_links:
                syslog.syslog(syslog.LOG_INFO, 
                            "Active port count {} in {} sufficient to take mitigate {} (min_links {})".format(
                                active_count, lag_name, port_name, min_links))
                self.isolate_lag_member(namespace, port_name)
            else:
                syslog.syslog(syslog.LOG_CRIT, 
                            "Active port count {} in {} insufficient to take mitigate {} (min_links {})".format(
                                active_count, lag_name, port_name, min_links))

    def monitor(self):
        '''
        Monitors the error counters for each internal port in each namespace.
        If any error counters are above the specified threshold, a syslog message is generated.
        '''
        all_error_ports = []
        for namespace, link_mon in self.link_monitor.items():
            err_port_per_ns = link_mon.monitor(namespace, self.error_counter_names, self.threshold)
            if err_port_per_ns:
                all_error_ports.extend(err_port_per_ns)
                syslog.syslog(syslog.LOG_CRIT,
                              '{} internal ports in {} have errors above threshold'.format(len(err_port_per_ns), namespace))
                if self.mitigationActionEnabled:
                    self.attempt_to_mitigate_ports(namespace, err_port_per_ns)
        return len(all_error_ports)

def main():
    if multi_asic.is_multi_asic():
        link_monitor = PacketChassisInternalLinkMontoring()
        num_of_err_ports =  link_monitor.monitor()
        if num_of_err_ports:
            syslog.syslog(syslog.LOG_CRIT, '{} internal ports have errors above threshold'.format(num_of_err_ports))
            return -1
    return 0



if __name__ == '__main__':
    main()
