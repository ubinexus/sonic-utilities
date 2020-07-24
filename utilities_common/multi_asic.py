import argparse
import functools
import json
import subprocess

import click

from sonic_device_util import get_all_namespaces
from sonic_device_util import get_namespaces
from sonic_device_util import get_num_npus
from sonic_device_util import is_multi_npu
from sonic_device_util import is_bgp_session_internal
from sonic_device_util import is_port_channel_internal
from sonic_device_util import is_port_internal
from swsssdk import ConfigDBConnector
from swsssdk import SonicDBConfig
from swsssdk import SonicV2Connector
from utilities_common.constants import *

class MultiAsic(object):

    def __init__(self, display_option=DISPLAY_ALL, namespace_option=None):
        self.namespace_option = namespace_option
        self.display_option = display_option
        SonicDBConfig.load_sonic_global_db_config()
        self.current_namespace = None
        self.is_multi_asic = is_multi_npu()

    def connect_dbs_for_ns(self,namespace=DEFAULT_NAMESPACE):
        '''
        The function connects to the DBs for a given namespace and
        returns the handle
        If no namespace is provided, it will connect to the db in the
        default namespace.
        In case of multi ASIC, the default namespace is the database instance running the on the host
        In case of single ASIC, the namespace has to be DEFAULT_NAMESPACE
        '''

        db = SonicV2Connector(use_unix_socket_path=True, namespace=namespace)
        db.connect(db.APPL_DB)
        db.connect(db.CONFIG_DB)
        db.connect(db.STATE_DB)
        db.connect(db.COUNTERS_DB)
        db.connect(db.ASIC_DB)
        return db

    def connect_config_db_for_ns(self, namespace=DEFAULT_NAMESPACE):
        '''
        The function connects to the config DB for a given namespace and
        returns the handle
        If no namespace is provided, it will connect to the db in the
        default namespace.
        In case of multi ASIC, the default namespace is the database instance running the on the host
        In case of single ASIC, the namespace has to be DEFAULT_NAMESPACE
        '''
        config_db = ConfigDBConnector(use_unix_socket_path=True, namespace=namespace)
        config_db.connect()
        return config_db

    def is_object_internal(self, object_type, cli_object):
        '''
        The function checks if a CLI object is internal and returns true or false.
        Internal objects are port or portchannel which are connected to other 
        ports or portchannels within a multi ASIC device.

        For single asic, this function is not applicable
        '''
        if object_type == PORT_OBJ:
            return is_port_internal(cli_object)
        elif object_type == PORT_CHANNEL_OBJ:
            return is_port_channel_internal(cli_object)
        elif object_type == BGP_NEIGH_OBJ:
            return is_bgp_session_internal(cli_object)

    def skip_display(self, object_type, cli_object):
        '''
        The function determines if the passed cli_object has to be displayed or not.
        returns true if the display_option is external and  the cli object is internal.
        returns false, if the cli option is all or if it the platform is single ASIC.

        '''
        if not self.is_multi_asic:
            return False
        if self.display_option == DISPLAY_ALL:
            return False
        return self.is_object_internal(object_type, cli_object)

    def get_ns_list_based_on_options(self):
        ns_list = []
        if not self.is_multi_asic:
            return [DEFAULT_NAMESPACE]
        else:
            namespaces = get_all_namespaces()
            if self.namespace_option is None:
                if self.display_option ==  DISPLAY_ALL:
                    ns_list = namespaces['front_ns'] + namespaces['back_ns']
                else:
                    ns_list = namespaces['front_ns']
            else:
                if self.namespace_option not in get_namespaces():
                    raise ValueError('Unknown Namespace {}'.format(self.namespace_option))
                ns_list = [self.namespace_option]
        return ns_list
    
def multi_asic_ns_choices():
    if not is_multi_npu() :
        return [DEFAULT_NAMESPACE]
    choices =  get_namespaces()
    return choices

def multi_asic_display_choices():
    if not is_multi_npu():
        return [DISPLAY_ALL]
    else:
        return [DISPLAY_ALL, DISPLAY_EXTERNAL]

def multi_asic_display_default_option():
    if not is_multi_npu():
        return DISPLAY_ALL
    else:
        return  DISPLAY_EXTERNAL

_multi_asic_click_options = [
    click.option('--display', '-d', 'display', default=multi_asic_display_default_option(), show_default=True, type=click.Choice(multi_asic_display_choices()), help='Show internal interfaces'),
    click.option('--namespace', '-n', 'namespace', default=None, type=click.Choice(multi_asic_ns_choices()), show_default=True, help='Namespace name or all'),
    #click.option('--namespace', '-n', 'namespace',  callback=multi_asic_ns_callback, show_default=True, help='Namespace name or all'),
    ]

def multi_asic_click_options(func):
    for option in reversed(_multi_asic_click_options):
        func = option(func)
    return func

def run_on_all_asics(func):
    '''
    This decorator is used on the CLI functions which needs to be
    run on all the namespaces in the multi ASIC platform
    The decorator loops through all the required namespaces,
    for every iteration, it connects to all the DBs and provides an handle
    to the wrapped function.

    '''
    @functools.wraps(func)
    def wrapped_run_on_all_asics(self, *args, **kwargs):
        ns_list =  self.multi_asic.get_ns_list_based_on_options()
        for ns in ns_list:
            self.multi_asic.current_namespace = ns
            self.db = self.multi_asic.connect_dbs_for_ns(ns)
            self.config_db = self.multi_asic.connect_config_db_for_ns(ns)
            func(self,  *args, **kwargs)
    return wrapped_run_on_all_asics

def multi_asic_args(parser=None):
    if parser is None:
        parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)

    parser.add_argument('-d','--display',   default=DISPLAY_EXTERNAL, help='Display all interfaces or only external interfaces')
    parser.add_argument('-n','--namespace',   default=None, help='Display interfaces for specific namespace')
    return parser
