#!/usr/bin/env python3
#
# main.py
#
# Command-line utility for interacting with SFP transceivers within SONiC
#

import os
import sys
import natsort
import ast
import time
import datetime

import subprocess
import click
import sonic_platform
import sonic_platform_base.sonic_sfp.sfputilhelper
from sonic_platform_base.sfp_base import SfpBase
from swsscommon.swsscommon import SonicV2Connector
from natsort import natsorted
from sonic_py_common import device_info, logger, multi_asic
from utilities_common.sfp_helper import covert_application_advertisement_to_output_string
from utilities_common.sfp_helper import QSFP_DATA_MAP
from tabulate import tabulate

VERSION = '3.0'

SYSLOG_IDENTIFIER = "sfputil"

PLATFORM_JSON = 'platform.json'
PORT_CONFIG_INI = 'port_config.ini'

EXIT_FAIL = -1
EXIT_SUCCESS = 0
ERROR_PERMISSIONS = 1
ERROR_CHASSIS_LOAD = 2
ERROR_SFPUTILHELPER_LOAD = 3
ERROR_PORT_CONFIG_LOAD = 4
ERROR_NOT_IMPLEMENTED = 5
ERROR_INVALID_PORT = 6
SMBUS_BLOCK_WRITE_SIZE = 32
# Default host password as per CMIS spec:
# http://www.qsfp-dd.com/wp-content/uploads/2021/05/CMIS5p0.pdf
CDB_DEFAULT_HOST_PASSWORD = 0x00001011

MAX_LPL_FIRMWARE_BLOCK_SIZE = 116 #Bytes

PAGE_SIZE = 128
PAGE_OFFSET = 128

SFF8472_A0_SIZE = 256

# TODO: We should share these maps and the formatting functions between sfputil and sfpshow
QSFP_DD_DATA_MAP = {
    'model': 'Vendor PN',
    'vendor_oui': 'Vendor OUI',
    'vendor_date': 'Vendor Date Code(YYYY-MM-DD Lot)',
    'manufacturer': 'Vendor Name',
    'vendor_rev': 'Vendor Rev',
    'serial': 'Vendor SN',
    'type': 'Identifier',
    'ext_identifier': 'Extended Identifier',
    'ext_rateselect_compliance': 'Extended RateSelect Compliance',
    'cable_length': 'cable_length',
    'cable_type': 'Length',
    'nominal_bit_rate': 'Nominal Bit Rate(100Mbs)',
    'specification_compliance': 'Specification compliance',
    'encoding': 'Encoding',
    'connector': 'Connector',
    'application_advertisement': 'Application Advertisement',
    'active_firmware': 'Active Firmware Version',
    'inactive_firmware': 'Inactive Firmware Version',
    'hardware_rev': 'Hardware Revision',
    'media_interface_code': 'Media Interface Code',
    'host_electrical_interface': 'Host Electrical Interface',
    'host_lane_count': 'Host Lane Count',
    'media_lane_count': 'Media Lane Count',
    'host_lane_assignment_option': 'Host Lane Assignment Options',
    'media_lane_assignment_option': 'Media Lane Assignment Options',
    'active_apsel_hostlane1': 'Active App Selection Host Lane 1',
    'active_apsel_hostlane2': 'Active App Selection Host Lane 2',
    'active_apsel_hostlane3': 'Active App Selection Host Lane 3',
    'active_apsel_hostlane4': 'Active App Selection Host Lane 4',
    'active_apsel_hostlane5': 'Active App Selection Host Lane 5',
    'active_apsel_hostlane6': 'Active App Selection Host Lane 6',
    'active_apsel_hostlane7': 'Active App Selection Host Lane 7',
    'active_apsel_hostlane8': 'Active App Selection Host Lane 8',
    'media_interface_technology': 'Media Interface Technology',
    'cmis_rev': 'CMIS Revision',
    'supported_max_tx_power': 'Supported Max TX Power',
    'supported_min_tx_power': 'Supported Min TX Power',
    'supported_max_laser_freq': 'Supported Max Laser Frequency',
    'supported_min_laser_freq': 'Supported Min Laser Frequency'
}

SFP_DOM_CHANNEL_MONITOR_MAP = {
    'rx1power': 'RXPower',
    'tx1bias': 'TXBias',
    'tx1power': 'TXPower'
}

SFP_DOM_CHANNEL_THRESHOLD_MAP = {
    'txpowerhighalarm':   'TxPowerHighAlarm',
    'txpowerlowalarm':    'TxPowerLowAlarm',
    'txpowerhighwarning': 'TxPowerHighWarning',
    'txpowerlowwarning':  'TxPowerLowWarning',
    'rxpowerhighalarm':   'RxPowerHighAlarm',
    'rxpowerlowalarm':    'RxPowerLowAlarm',
    'rxpowerhighwarning': 'RxPowerHighWarning',
    'rxpowerlowwarning':  'RxPowerLowWarning',
    'txbiashighalarm':    'TxBiasHighAlarm',
    'txbiaslowalarm':     'TxBiasLowAlarm',
    'txbiashighwarning':  'TxBiasHighWarning',
    'txbiaslowwarning':   'TxBiasLowWarning'
}

QSFP_DOM_CHANNEL_THRESHOLD_MAP = {
    'rxpowerhighalarm':   'RxPowerHighAlarm',
    'rxpowerlowalarm':    'RxPowerLowAlarm',
    'rxpowerhighwarning': 'RxPowerHighWarning',
    'rxpowerlowwarning':  'RxPowerLowWarning',
    'txbiashighalarm':    'TxBiasHighAlarm',
    'txbiaslowalarm':     'TxBiasLowAlarm',
    'txbiashighwarning':  'TxBiasHighWarning',
    'txbiaslowwarning':   'TxBiasLowWarning'
}

DOM_MODULE_THRESHOLD_MAP = {
    'temphighalarm':  'TempHighAlarm',
    'templowalarm':   'TempLowAlarm',
    'temphighwarning': 'TempHighWarning',
    'templowwarning': 'TempLowWarning',
    'vcchighalarm':   'VccHighAlarm',
    'vcclowalarm':    'VccLowAlarm',
    'vcchighwarning': 'VccHighWarning',
    'vcclowwarning':  'VccLowWarning'
}

QSFP_DOM_CHANNEL_MONITOR_MAP = {
    'rx1power': 'RX1Power',
    'rx2power': 'RX2Power',
    'rx3power': 'RX3Power',
    'rx4power': 'RX4Power',
    'tx1bias':  'TX1Bias',
    'tx2bias':  'TX2Bias',
    'tx3bias':  'TX3Bias',
    'tx4bias':  'TX4Bias',
    'tx1power': 'TX1Power',
    'tx2power': 'TX2Power',
    'tx3power': 'TX3Power',
    'tx4power': 'TX4Power'
}

QSFP_DD_DOM_CHANNEL_MONITOR_MAP = {
    'rx1power': 'RX1Power',
    'rx2power': 'RX2Power',
    'rx3power': 'RX3Power',
    'rx4power': 'RX4Power',
    'rx5power': 'RX5Power',
    'rx6power': 'RX6Power',
    'rx7power': 'RX7Power',
    'rx8power': 'RX8Power',
    'tx1bias':  'TX1Bias',
    'tx2bias':  'TX2Bias',
    'tx3bias':  'TX3Bias',
    'tx4bias':  'TX4Bias',
    'tx5bias':  'TX5Bias',
    'tx6bias':  'TX6Bias',
    'tx7bias':  'TX7Bias',
    'tx8bias':  'TX8Bias',
    'tx1power': 'TX1Power',
    'tx2power': 'TX2Power',
    'tx3power': 'TX3Power',
    'tx4power': 'TX4Power',
    'tx5power': 'TX5Power',
    'tx6power': 'TX6Power',
    'tx7power': 'TX7Power',
    'tx8power': 'TX8Power'
}

DOM_MODULE_MONITOR_MAP = {
    'temperature': 'Temperature',
    'voltage': 'Vcc'
}

DOM_CHANNEL_THRESHOLD_UNIT_MAP = {
    'txpowerhighalarm':   'dBm',
    'txpowerlowalarm':    'dBm',
    'txpowerhighwarning': 'dBm',
    'txpowerlowwarning':  'dBm',
    'rxpowerhighalarm':   'dBm',
    'rxpowerlowalarm':    'dBm',
    'rxpowerhighwarning': 'dBm',
    'rxpowerlowwarning':  'dBm',
    'txbiashighalarm':    'mA',
    'txbiaslowalarm':     'mA',
    'txbiashighwarning':  'mA',
    'txbiaslowwarning':   'mA'
}

DOM_MODULE_THRESHOLD_UNIT_MAP = {
    'temphighalarm':   'C',
    'templowalarm':    'C',
    'temphighwarning': 'C',
    'templowwarning':  'C',
    'vcchighalarm':    'Volts',
    'vcclowalarm':     'Volts',
    'vcchighwarning':  'Volts',
    'vcclowwarning':   'Volts'
}

DOM_VALUE_UNIT_MAP = {
    'rx1power': 'dBm',
    'rx2power': 'dBm',
    'rx3power': 'dBm',
    'rx4power': 'dBm',
    'tx1bias': 'mA',
    'tx2bias': 'mA',
    'tx3bias': 'mA',
    'tx4bias': 'mA',
    'tx1power': 'dBm',
    'tx2power': 'dBm',
    'tx3power': 'dBm',
    'tx4power': 'dBm',
    'temperature': 'C',
    'voltage': 'Volts'
}

QSFP_DD_DOM_VALUE_UNIT_MAP = {
    'rx1power': 'dBm',
    'rx2power': 'dBm',
    'rx3power': 'dBm',
    'rx4power': 'dBm',
    'rx5power': 'dBm',
    'rx6power': 'dBm',
    'rx7power': 'dBm',
    'rx8power': 'dBm',
    'tx1bias': 'mA',
    'tx2bias': 'mA',
    'tx3bias': 'mA',
    'tx4bias': 'mA',
    'tx5bias': 'mA',
    'tx6bias': 'mA',
    'tx7bias': 'mA',
    'tx8bias': 'mA',
    'tx1power': 'dBm',
    'tx2power': 'dBm',
    'tx3power': 'dBm',
    'tx4power': 'dBm',
    'tx5power': 'dBm',
    'tx6power': 'dBm',
    'tx7power': 'dBm',
    'tx8power': 'dBm',
    'temperature': 'C',
    'voltage': 'Volts'
}

RJ45_PORT_TYPE = 'RJ45'

# Global platform-specific Chassis class instance
platform_chassis = None

# Global platform-specific sfputil class instance
platform_sfputil = None

# Global logger instance
log = logger.Logger(SYSLOG_IDENTIFIER)

def is_sfp_present(port_name):
    physical_port = logical_port_to_physical_port_index(port_name)
    sfp = platform_chassis.get_sfp(physical_port)

    try:
        presence = sfp.get_presence()
    except NotImplementedError:
        click.echo("sfp get_presence() NOT implemented!", err=True)
        sys.exit(ERROR_NOT_IMPLEMENTED)

    return bool(presence)


def is_port_type_rj45(port_name):
    physical_port = logical_port_to_physical_port_index(port_name)

    try:
        port_types = platform_chassis.get_port_or_cage_type(physical_port)
        return SfpBase.SFP_PORT_TYPE_BIT_RJ45 == port_types
    except NotImplementedError:
        pass

    return False
# ========================== Methods for formatting output ==========================

# Convert dict values to cli output string
def format_dict_value_to_string(sorted_key_table,
                                dom_info_dict, dom_value_map,
                                dom_unit_map, alignment=0):
    output = ''
    indent = ' ' * 8
    separator = ": "
    for key in sorted_key_table:
        if dom_info_dict is not None and key in dom_info_dict and dom_info_dict[key] != 'N/A':
            value = dom_info_dict[key]
            units = ''
            if type(value) != str or (value != 'Unknown' and not value.endswith(dom_unit_map[key])):
                units = dom_unit_map[key]
            output += '{}{}{}{}{}\n'.format((indent * 2),
                                            dom_value_map[key],
                                            separator.rjust(len(separator) + alignment - len(dom_value_map[key])),
                                            value,
                                            units)
    return output


def convert_sfp_info_to_output_string(sfp_info_dict):
    indent = ' ' * 8
    output = ''
    sfp_type = sfp_info_dict['type']
    # CMIS supported module types include QSFP-DD and OSFP
    if sfp_type.startswith('QSFP-DD') or sfp_type.startswith('OSFP'):
        sorted_qsfp_data_map_keys = sorted(QSFP_DD_DATA_MAP, key=QSFP_DD_DATA_MAP.get)
        for key in sorted_qsfp_data_map_keys:
            if key == 'cable_type':
                output += '{}{}: {}\n'.format(indent, sfp_info_dict['cable_type'], sfp_info_dict['cable_length'])
            elif key == 'cable_length':
                pass
            elif key == 'specification_compliance':
                output += '{}{}: {}\n'.format(indent, QSFP_DD_DATA_MAP[key], sfp_info_dict[key])
            elif key == 'supported_max_tx_power' or key == 'supported_min_tx_power':
                if key in sfp_info_dict:  # C-CMIS compliant / coherent modules
                    output += '{}{}: {}dBm\n'.format(indent, QSFP_DD_DATA_MAP[key], sfp_info_dict[key])
            elif key == 'supported_max_laser_freq' or key == 'supported_min_laser_freq':
                if key in sfp_info_dict:  # C-CMIS compliant / coherent modules
                    output += '{}{}: {}GHz\n'.format(indent, QSFP_DD_DATA_MAP[key], sfp_info_dict[key])
            elif key == 'application_advertisement':
                output += covert_application_advertisement_to_output_string(indent, sfp_info_dict)
            else:
                try:
                    output += '{}{}: {}\n'.format(indent, QSFP_DD_DATA_MAP[key], sfp_info_dict[key])
                except (KeyError, ValueError) as e:
                    output += '{}{}: N/A\n'.format(indent, QSFP_DD_DATA_MAP[key])

    else:
        sorted_qsfp_data_map_keys = sorted(QSFP_DATA_MAP, key=QSFP_DATA_MAP.get)
        for key in sorted_qsfp_data_map_keys:
            if key == 'cable_type':
                output += '{}{}: {}\n'.format(indent, sfp_info_dict['cable_type'], sfp_info_dict['cable_length'])
            elif key == 'cable_length':
                pass
            elif key == 'specification_compliance':
                output += '{}{}:\n'.format(indent, QSFP_DATA_MAP['specification_compliance'])

                spec_compliance_dict = {}
                try:
                    spec_compliance_dict = ast.literal_eval(sfp_info_dict['specification_compliance'])
                    sorted_compliance_key_table = natsorted(spec_compliance_dict)
                    for compliance_key in sorted_compliance_key_table:
                        output += '{}{}: {}\n'.format((indent * 2), compliance_key, spec_compliance_dict[compliance_key])
                except ValueError as e:
                    output += '{}N/A\n'.format((indent * 2))
            else:
                output += '{}{}: {}\n'.format(indent, QSFP_DATA_MAP[key], sfp_info_dict[key])

    return output


# Convert DOM sensor info in DB to CLI output string
def convert_dom_to_output_string(sfp_type, dom_info_dict):
    indent = ' ' * 8
    output_dom = ''
    channel_threshold_align = 18
    module_threshold_align = 15

    if sfp_type.startswith('QSFP') or sfp_type.startswith('OSFP'):
        # Channel Monitor
        if sfp_type.startswith('QSFP-DD') or sfp_type.startswith('OSFP'):
            output_dom += (indent + 'ChannelMonitorValues:\n')
            sorted_key_table = natsorted(QSFP_DD_DOM_CHANNEL_MONITOR_MAP)
            output_channel = format_dict_value_to_string(
                sorted_key_table, dom_info_dict,
                QSFP_DD_DOM_CHANNEL_MONITOR_MAP,
                QSFP_DD_DOM_VALUE_UNIT_MAP)
            output_dom += output_channel
        else:
            output_dom += (indent + 'ChannelMonitorValues:\n')
            sorted_key_table = natsorted(QSFP_DOM_CHANNEL_MONITOR_MAP)
            output_channel = format_dict_value_to_string(
                sorted_key_table, dom_info_dict,
                QSFP_DOM_CHANNEL_MONITOR_MAP,
                DOM_VALUE_UNIT_MAP)
            output_dom += output_channel

        # Channel Threshold
        if sfp_type.startswith('QSFP-DD') or sfp_type.startswith('OSFP'):
            dom_map = SFP_DOM_CHANNEL_THRESHOLD_MAP
        else:
            dom_map = QSFP_DOM_CHANNEL_THRESHOLD_MAP

        output_dom += (indent + 'ChannelThresholdValues:\n')
        sorted_key_table = natsorted(dom_map)
        output_channel_threshold = format_dict_value_to_string(
            sorted_key_table, dom_info_dict,
            dom_map,
            DOM_CHANNEL_THRESHOLD_UNIT_MAP,
            channel_threshold_align)
        output_dom += output_channel_threshold

        # Module Monitor
        output_dom += (indent + 'ModuleMonitorValues:\n')
        sorted_key_table = natsorted(DOM_MODULE_MONITOR_MAP)
        output_module = format_dict_value_to_string(
            sorted_key_table, dom_info_dict,
            DOM_MODULE_MONITOR_MAP,
            DOM_VALUE_UNIT_MAP)
        output_dom += output_module

        # Module Threshold
        output_dom += (indent + 'ModuleThresholdValues:\n')
        sorted_key_table = natsorted(DOM_MODULE_THRESHOLD_MAP)
        output_module_threshold = format_dict_value_to_string(
            sorted_key_table, dom_info_dict,
            DOM_MODULE_THRESHOLD_MAP,
            DOM_MODULE_THRESHOLD_UNIT_MAP,
            module_threshold_align)
        output_dom += output_module_threshold

    else:
        output_dom += (indent + 'MonitorData:\n')
        sorted_key_table = natsorted(SFP_DOM_CHANNEL_MONITOR_MAP)
        output_channel = format_dict_value_to_string(
            sorted_key_table, dom_info_dict,
            SFP_DOM_CHANNEL_MONITOR_MAP,
            DOM_VALUE_UNIT_MAP)
        output_dom += output_channel

        sorted_key_table = natsorted(DOM_MODULE_MONITOR_MAP)
        output_module = format_dict_value_to_string(
            sorted_key_table, dom_info_dict,
            DOM_MODULE_MONITOR_MAP,
            DOM_VALUE_UNIT_MAP)
        output_dom += output_module

        output_dom += (indent + 'ThresholdData:\n')

        # Module Threshold
        sorted_key_table = natsorted(DOM_MODULE_THRESHOLD_MAP)
        output_module_threshold = format_dict_value_to_string(
            sorted_key_table, dom_info_dict,
            DOM_MODULE_THRESHOLD_MAP,
            DOM_MODULE_THRESHOLD_UNIT_MAP,
            module_threshold_align)
        output_dom += output_module_threshold

        # Channel Threshold
        sorted_key_table = natsorted(SFP_DOM_CHANNEL_THRESHOLD_MAP)
        output_channel_threshold = format_dict_value_to_string(
            sorted_key_table, dom_info_dict,
            SFP_DOM_CHANNEL_THRESHOLD_MAP,
            DOM_CHANNEL_THRESHOLD_UNIT_MAP,
            channel_threshold_align)
        output_dom += output_channel_threshold

    return output_dom


# =============== Getting and printing SFP data ===============


#
def get_physical_port_name(logical_port, physical_port, ganged):
    """
        Returns:
          port_num if physical
          logical_port:port_num if logical port and is a ganged port
          logical_port if logical and not ganged
    """
    if logical_port == physical_port:
        return str(logical_port)
    elif ganged:
        return "{}:{} (ganged)".format(logical_port, physical_port)
    else:
        return logical_port


def logical_port_name_to_physical_port_list(port_name):
    if port_name.startswith("Ethernet"):
        if platform_sfputil.is_logical_port(port_name):
            return platform_sfputil.get_logical_to_physical(port_name)
        else:
            click.echo("Error: Invalid port '{}'".format(port_name))
            return None
    else:
        return [int(port_name)]

def logical_port_to_physical_port_index(port_name):
    if not platform_sfputil.is_logical_port(port_name):
        click.echo("Error: invalid port '{}'\n".format(port_name))
        print_all_valid_port_values()
        sys.exit(ERROR_INVALID_PORT)

    physical_port = logical_port_name_to_physical_port_list(port_name)[0]
    if physical_port is None:
        click.echo("Error: No physical port found for logical port '{}'".format(port_name))
        sys.exit(EXIT_FAIL)

    return physical_port


def print_all_valid_port_values():
    click.echo("Valid values for port: {}\n".format(str(platform_sfputil.logical)))


# ==================== Methods for initialization ====================


# Instantiate platform-specific Chassis class
def load_platform_chassis():
    global platform_chassis

    # Load new platform api class
    try:
        platform_chassis = sonic_platform.platform.Platform().get_chassis()
    except Exception as e:
        log.log_error("Failed to instantiate Chassis due to {}".format(repr(e)))

    if not platform_chassis:
        return False

    return True


# Instantiate SfpUtilHelper class
def load_sfputilhelper():
    global platform_sfputil

    # we have to make use of sfputil for some features
    # even though when new platform api is used for all vendors.
    # in this sense, we treat it as a part of new platform api.
    # we have already moved sfputil to sonic_platform_base
    # which is the root of new platform api.
    platform_sfputil = sonic_platform_base.sonic_sfp.sfputilhelper.SfpUtilHelper()

    if not platform_sfputil:
        return False

    return True


def load_port_config():
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
        log.log_error("Error reading port info ({})".format(str(e)), True)
        return False

    return True

# ==================== CLI commands and groups ====================


# This is our main entrypoint - the main 'sfputil' command
@click.group()
def cli():
    """sfputil - Command line utility for managing SFP transceivers"""

    if os.geteuid() != 0:
        click.echo("Root privileges are required for this operation")
        sys.exit(ERROR_PERMISSIONS)

    # Load platform-specific Chassis class
    if not load_platform_chassis():
        sys.exit(ERROR_CHASSIS_LOAD)

    # Load SfpUtilHelper class
    if not load_sfputilhelper():
        sys.exit(ERROR_SFPUTILHELPER_LOAD)

    # Load port info
    if not load_port_config():
        sys.exit(ERROR_PORT_CONFIG_LOAD)


# 'show' subgroup
@cli.group()
def show():
    """Display status of SFP transceivers"""
    pass


# 'eeprom' subcommand
@show.command()
@click.option('-p', '--port', metavar='<port_name>', help="Display SFP EEPROM data for port <port_name> only")
@click.option('-d', '--dom', 'dump_dom', is_flag=True, help="Also display Digital Optical Monitoring (DOM) data")
@click.option('-n', '--namespace', default=None, help="Display interfaces for specific namespace")
def eeprom(port, dump_dom, namespace):
    """Display EEPROM data of SFP transceiver(s)"""
    logical_port_list = []
    output = ""

    # Create a list containing the logical port names of all ports we're interested in
    if port is None:
        logical_port_list = platform_sfputil.logical
    else:
        if platform_sfputil.is_logical_port(port) == 0:
            click.echo("Error: invalid port '{}'\n".format(port))
            print_all_valid_port_values()
            sys.exit(ERROR_INVALID_PORT)

        logical_port_list = [port]

    for logical_port_name in logical_port_list:
        ganged = False
        i = 1

        physical_port_list = logical_port_name_to_physical_port_list(logical_port_name)
        if physical_port_list is None:
            click.echo("Error: No physical ports found for logical port '{}'".format(logical_port_name))
            return

        if len(physical_port_list) > 1:
            ganged = True

        for physical_port in physical_port_list:
            port_name = get_physical_port_name(logical_port_name, i, ganged)

            if is_port_type_rj45(port_name):
                output += "{}: SFP EEPROM is not applicable for RJ45 port\n".format(port_name)
                output += '\n'
                continue

            try:
                presence = platform_chassis.get_sfp(physical_port).get_presence()
            except NotImplementedError:
                click.echo("Sfp.get_presence() is currently not implemented for this platform")
                sys.exit(ERROR_NOT_IMPLEMENTED)

            if not presence:
                output += "{}: SFP EEPROM not detected\n".format(port_name)
            else:
                output += "{}: SFP EEPROM detected\n".format(port_name)

                try:
                    xcvr_info = platform_chassis.get_sfp(physical_port).get_transceiver_info()
                except NotImplementedError:
                    click.echo("Sfp.get_transceiver_info() is currently not implemented for this platform")
                    sys.exit(ERROR_NOT_IMPLEMENTED)

                output += convert_sfp_info_to_output_string(xcvr_info)

                if dump_dom:
                    try:
                        xcvr_dom_info = platform_chassis.get_sfp(physical_port).get_transceiver_bulk_status()
                    except NotImplementedError:
                        click.echo("Sfp.get_transceiver_bulk_status() is currently not implemented for this platform")
                        sys.exit(ERROR_NOT_IMPLEMENTED)

                    try:
                        xcvr_dom_threshold_info = platform_chassis.get_sfp(physical_port).get_transceiver_threshold_info()
                        if xcvr_dom_threshold_info:
                            xcvr_dom_info.update(xcvr_dom_threshold_info)
                    except NotImplementedError:
                        click.echo("Sfp.get_transceiver_threshold_info() is currently not implemented for this platform")
                        sys.exit(ERROR_NOT_IMPLEMENTED)

                    output += convert_dom_to_output_string(xcvr_info['type'], xcvr_dom_info)

            output += '\n'

    click.echo(output)

# 'eeprom-hexdump' subcommand
@show.command()
@click.option('-p', '--port', metavar='<port_name>', required=True, help="Display SFP EEPROM hexdump for port <port_name>")
@click.option('-n', '--page', metavar='<page_number>', help="Display SFP EEEPROM hexdump for <page_number_in_hex>")
def eeprom_hexdump(port, page):
    """Display EEPROM hexdump of SFP transceiver(s) for a given port name and page number"""
    output = ""

    if platform_sfputil.is_logical_port(port) == 0:
        click.echo("Error: invalid port {}".format(port))
        print_all_valid_port_values()
        sys.exit(ERROR_INVALID_PORT)

    if page is None:
        page = '0'

    logical_port_name = port
    physical_port = logical_port_to_physical_port_index(logical_port_name)

    if is_port_type_rj45(logical_port_name):
        click.echo("{}: SFP EEPROM Hexdump is not applicable for RJ45 port".format(port))
        sys.exit(ERROR_INVALID_PORT)

    try:
        presence = platform_chassis.get_sfp(physical_port).get_presence()
    except NotImplementedError:
        click.echo("Sfp.get_presence() is currently not implemented for this platform")
        sys.exit(ERROR_NOT_IMPLEMENTED)

    if not presence:
        click.echo("SFP EEPROM not detected")
        sys.exit(ERROR_NOT_IMPLEMENTED)
    else:
        try:
            id = platform_chassis.get_sfp(physical_port).read_eeprom(0, 1)
            if id is None:
                click.echo("Error: Failed to read EEPROM for offset 0!")
                sys.exit(ERROR_NOT_IMPLEMENTED)
        except NotImplementedError:
            click.echo("Sfp.read_eeprom() is currently not implemented for this platform")
            sys.exit(ERROR_NOT_IMPLEMENTED)

        if id[0] == 0x3:
            output = eeprom_hexdump_sff8472(port, physical_port, page)
        else:
            output = eeprom_hexdump_sff8636(port, physical_port, page)

    output += '\n'

    click.echo(output)

def eeprom_hexdump_sff8472(port, physical_port, page):
    try:
        output = ""
        indent = ' ' * 8
        output += 'EEPROM hexdump for port {} page {}h'.format(port, page)
        output += '\n{}A0h dump'.format(indent)
        page_dump = platform_chassis.get_sfp(physical_port).read_eeprom(0, SFF8472_A0_SIZE)
        if page_dump is None:
            click.echo("Error: Failed to read EEPROM for A0h!")
            sys.exit(ERROR_NOT_IMPLEMENTED)

        output += hexdump(indent, page_dump, 0)
        page_dump = platform_chassis.get_sfp(physical_port).read_eeprom(SFF8472_A0_SIZE, PAGE_SIZE)
        if page_dump is None:
            click.echo("Error: Failed to read EEPROM for A2h!")
            sys.exit(ERROR_NOT_IMPLEMENTED)
        else:
            output += '\n\n{}A2h dump (lower 128 bytes)'.format(indent)
            output += hexdump(indent, page_dump, 0)

        page_dump = platform_chassis.get_sfp(physical_port).read_eeprom(SFF8472_A0_SIZE + PAGE_OFFSET + (int(page, base=16) * PAGE_SIZE), PAGE_SIZE)
        if page_dump is None:
            click.echo("Error: Failed to read EEPROM for A2h upper page!")
            sys.exit(ERROR_NOT_IMPLEMENTED)
        else:
            output += '\n\n{}A2h dump (upper 128 bytes) page {}h'.format(indent, page)
            output += hexdump(indent, page_dump, PAGE_OFFSET)
    except NotImplementedError:
        click.echo("Sfp.read_eeprom() is currently not implemented for this platform")
        sys.exit(ERROR_NOT_IMPLEMENTED)
    except ValueError:
        click.echo("Please enter a numeric page number")
        sys.exit(ERROR_NOT_IMPLEMENTED)

    return output

def eeprom_hexdump_sff8636(port, physical_port, page):
    try:
        output = ""
        indent = ' ' * 8
        output += 'EEPROM hexdump for port {} page {}h'.format(port, page)
        output += '\n{}Lower page 0h'.format(indent)
        page_dump = platform_chassis.get_sfp(physical_port).read_eeprom(0, PAGE_SIZE)
        if page_dump is None:
            click.echo("Error: Failed to read EEPROM for page 0!")
            sys.exit(ERROR_NOT_IMPLEMENTED)

        output += hexdump(indent, page_dump, 0)
        page_dump = platform_chassis.get_sfp(physical_port).read_eeprom(int(page, base=16) * PAGE_SIZE + PAGE_OFFSET, PAGE_SIZE)
        if page_dump is None:
            click.echo("Error: Failed to read EEPROM!")
            sys.exit(ERROR_NOT_IMPLEMENTED)
        else:
            output += '\n\n{}Upper page {}h'.format(indent, page)
            output += hexdump(indent, page_dump, PAGE_OFFSET)
    except NotImplementedError:
        click.echo("Sfp.read_eeprom() is currently not implemented for this platform")
        sys.exit(ERROR_NOT_IMPLEMENTED)
    except ValueError:
        click.echo("Please enter a numeric page number")
        sys.exit(ERROR_NOT_IMPLEMENTED)

    return output

def convert_byte_to_valid_ascii_char(byte):
    if byte < 32 or 126 < byte:
        return '.'
    else:
        return chr(byte)

def hexdump(indent, data, mem_address):
    ascii_string = ''
    result = ''
    for byte in data:
        ascii_string = ascii_string + convert_byte_to_valid_ascii_char(byte)
        byte_string = "{:02x}".format(byte)
        if mem_address % 16 == 0:
            mem_address_string = "{:08x}".format(mem_address)
            result += '\n{}{} '.format(indent, mem_address_string)
            result += '{} '.format(byte_string)
        elif mem_address % 16 == 15:
            result += '{} '.format(byte_string)
            result += '|{}|'.format(ascii_string)
            ascii_string = ""
        elif mem_address % 16 == 8:
            result += ' {} '.format(byte_string)
        else:
            result += '{} '.format(byte_string)
        mem_address += 1

    return result

# 'presence' subcommand
@show.command()
@click.option('-p', '--port', metavar='<port_name>', help="Display SFP presence for port <port_name> only")
def presence(port):
    """Display presence of SFP transceiver(s)"""
    logical_port_list = []
    output_table = []
    table_header = ["Port", "Presence"]

    # Create a list containing the logical port names of all ports we're interested in
    if port is None:
        logical_port_list = platform_sfputil.logical
    else:
        if platform_sfputil.is_logical_port(port) == 0:
            click.echo("Error: invalid port '{}'\n".format(port))
            print_all_valid_port_values()
            sys.exit(ERROR_INVALID_PORT)

        logical_port_list = [port]

    logical_port_list = natsort.natsorted(logical_port_list)
    for logical_port_name in logical_port_list:
        ganged = False
        i = 1

        physical_port_list = logical_port_name_to_physical_port_list(logical_port_name)
        if physical_port_list is None:
            click.echo("Error: No physical ports found for logical port '{}'".format(logical_port_name))
            return

        if len(physical_port_list) > 1:
            ganged = True

        for physical_port in physical_port_list:
            port_name = get_physical_port_name(logical_port_name, i, ganged)

            try:
                presence = platform_chassis.get_sfp(physical_port).get_presence()
            except NotImplementedError:
                click.echo("This functionality is currently not implemented for this platform")
                sys.exit(ERROR_NOT_IMPLEMENTED)

            status_string = "Present" if presence else "Not present"
            output_table.append([port_name, status_string])

            i += 1

    click.echo(tabulate(output_table, table_header, tablefmt="simple"))


# 'error-status' subcommand
def fetch_error_status_from_platform_api(port):
    """Fetch the error status from platform API and return the output as a string
    Args:
        port: the port whose error status will be fetched.
              None represents for all ports.
    Returns:
        A string consisting of the error status of each port.
    """
    if port is None:
        logical_port_list = natsort.natsorted(platform_sfputil.logical)
    else:
        logical_port_list = [port]

    output = []
    for logical_port_name in logical_port_list:
        physical_port = logical_port_to_physical_port_index(logical_port_name)

        if is_port_type_rj45(logical_port_name):
            output.append([logical_port_name, "N/A"])
        else:
            try:
                error_description = platform_chassis.get_sfp(physical_port).get_error_description()
                output.append([logical_port_name, error_description])
            except NotImplementedError:
                click.echo("get_error_description NOT implemented for port {}".format(logical_port_name))
                sys.exit(ERROR_NOT_IMPLEMENTED)

    return output

def fetch_error_status_from_state_db(port, state_db):
    """Fetch the error status from STATE_DB and return them in a list.
    Args:
        port: the port whose error status will be fetched.
              None represents for all ports.
    Returns:
        A list consisting of tuples (port, description) and sorted by port.
    """
    status = {}
    if port:
        status[port] = state_db.get_all(state_db.STATE_DB, 'TRANSCEIVER_STATUS|{}'.format(port))
    else:
        ports = state_db.keys(state_db.STATE_DB, 'TRANSCEIVER_STATUS|*')
        for key in ports:
            status[key.split('|')[1]] = state_db.get_all(state_db.STATE_DB, key)

    sorted_ports = natsort.natsorted(status)
    output = []
    for port in sorted_ports:
        if is_port_type_rj45(port):
            description = "N/A"
        else:
            statestring = status[port].get('status')
            description = status[port].get('error')
            if statestring == '1':
                description = 'OK'
            elif statestring == '0':
                description = 'Unplugged'
            elif description == 'N/A':
                log.log_error("Inconsistent state found for port {}: state is {} but error description is N/A".format(port, statestring))
                description = 'Unknown state: {}'.format(statestring)

        output.append([port, description])

    return output

@show.command()
@click.option('-p', '--port', metavar='<port_name>', help="Display SFP error status for port <port_name> only")
@click.option('-hw', '--fetch-from-hardware', 'fetch_from_hardware', is_flag=True, default=False, help="Fetch the error status from hardware directly")
def error_status(port, fetch_from_hardware):
    """Display error status of SFP transceiver(s)"""
    output_table = []
    table_header = ["Port", "Error Status"]

    # Create a list containing the logical port names of all ports we're interested in
    if port and platform_sfputil.is_logical_port(port) == 0:
        click.echo("Error: invalid port '{}'\n".format(port))
        click.echo("Valid values for port: {}\n".format(str(platform_sfputil.logical)))
        sys.exit(ERROR_INVALID_PORT)

    if fetch_from_hardware:
        output_table = fetch_error_status_from_platform_api(port)
    else:
        namespaces = multi_asic.get_front_end_namespaces()
        for namespace in namespaces:
            state_db = SonicV2Connector(use_unix_socket_path=False, namespace=namespace)
            if state_db is not None:
                state_db.connect(state_db.STATE_DB)
                output_table.extend(fetch_error_status_from_state_db(port, state_db))
            else:
                click.echo("Failed to connect to STATE_DB")
                return

    click.echo(tabulate(output_table, table_header, tablefmt='simple'))


# 'lpmode' subcommand
@show.command()
@click.option('-p', '--port', metavar='<port_name>', help="Display SFP low-power mode status for port <port_name> only")
def lpmode(port):
    """Display low-power mode status of SFP transceiver(s)"""
    logical_port_list = []
    output_table = []
    table_header = ["Port", "Low-power Mode"]

    # Create a list containing the logical port names of all ports we're interested in
    if port is None:
        logical_port_list = platform_sfputil.logical
    else:
        if platform_sfputil.is_logical_port(port) == 0:
            click.echo("Error: invalid port '{}'\n".format(port))
            print_all_valid_port_values()
            sys.exit(ERROR_INVALID_PORT)

        logical_port_list = [port]

    for logical_port_name in logical_port_list:
        ganged = False
        i = 1

        physical_port_list = logical_port_name_to_physical_port_list(logical_port_name)
        if physical_port_list is None:
            click.echo("Error: No physical ports found for logical port '{}'".format(logical_port_name))
            return

        if is_port_type_rj45(logical_port_name):
            output_table.append([logical_port_name, "N/A"])
        else:
            if len(physical_port_list) > 1:
                ganged = True

            for physical_port in physical_port_list:
                port_name = get_physical_port_name(logical_port_name, i, ganged)

                try:
                    lpmode = platform_chassis.get_sfp(physical_port).get_lpmode()
                except NotImplementedError:
                    click.echo("This functionality is currently not implemented for this platform")
                    sys.exit(ERROR_NOT_IMPLEMENTED)

                if lpmode:
                    output_table.append([port_name, "On"])
                else:
                    output_table.append([port_name, "Off"])

                i += 1

    click.echo(tabulate(output_table, table_header, tablefmt='simple'))

def show_firmware_version(physical_port):
    try:
        sfp = platform_chassis.get_sfp(physical_port)
        api = sfp.get_xcvr_api()
        out = api.get_module_fw_info()
        click.echo(out['info'])
    except NotImplementedError:
        click.echo("This functionality is currently not implemented for this platform")
        sys.exit(ERROR_NOT_IMPLEMENTED)

# 'fwversion' subcommand
@show.command()
@click.argument('port_name', metavar='<port_name>', required=True)
def fwversion(port_name):
    """Show firmware version of the transceiver"""

    physical_port = logical_port_to_physical_port_index(port_name)
    sfp = platform_chassis.get_sfp(physical_port)

    if is_port_type_rj45(port_name):
        click.echo("Show firmware version is not applicable for RJ45 port {}.".format(port_name))
        sys.exit(EXIT_FAIL)

    try:
        presence = sfp.get_presence()
    except NotImplementedError:
        click.echo("sfp get_presence() NOT implemented!")
        sys.exit(EXIT_FAIL)

    if not presence:
        click.echo("{}: SFP EEPROM not detected\n".format(port_name))
        sys.exit(EXIT_FAIL)

    show_firmware_version(physical_port)
    sys.exit(EXIT_SUCCESS)

# 'lpmode' subgroup
@cli.group()
def lpmode():
    """Enable or disable low-power mode for SFP transceiver"""
    pass


# Helper method for setting low-power mode
def set_lpmode(logical_port, enable):
    ganged = False
    i = 1

    if platform_sfputil.is_logical_port(logical_port) == 0:
        click.echo("Error: invalid port '{}'\n".format(logical_port))
        print_all_valid_port_values()
        sys.exit(ERROR_INVALID_PORT)

    physical_port_list = logical_port_name_to_physical_port_list(logical_port)
    if physical_port_list is None:
        click.echo("Error: No physical ports found for logical port '{}'".format(logical_port))
        return

    if is_port_type_rj45(logical_port):
        click.echo("{} low-power mode is not applicable for RJ45 port {}.".format("Enabling" if enable else "Disabling", logical_port))
        sys.exit(EXIT_FAIL)

    if len(physical_port_list) > 1:
        ganged = True

    for physical_port in physical_port_list:
        click.echo("{} low-power mode for port {} ... ".format(
            "Enabling" if enable else "Disabling",
            get_physical_port_name(logical_port, i, ganged)), nl=False)

        try:
            result = platform_chassis.get_sfp(physical_port).set_lpmode(enable)
        except NotImplementedError:
            click.echo("This functionality is currently not implemented for this platform")
            sys.exit(ERROR_NOT_IMPLEMENTED)

        if result:
            click.echo("OK")
        else:
            click.echo("Failed")

        i += 1


# 'off' subcommand
@lpmode.command()
@click.argument('port_name', metavar='<port_name>')
def off(port_name):
    """Disable low-power mode for SFP transceiver"""
    set_lpmode(port_name, False)


# 'on' subcommand
@lpmode.command()
@click.argument('port_name', metavar='<port_name>')
def on(port_name):
    """Enable low-power mode for SFP transceiver"""
    set_lpmode(port_name, True)


# 'reset' subcommand
@cli.command()
@click.argument('port_name', metavar='<port_name>')
def reset(port_name):
    """Reset SFP transceiver"""
    ganged = False
    i = 1

    if platform_sfputil.is_logical_port(port_name) == 0:
        click.echo("Error: invalid port '{}'\n".format(port_name))
        print_all_valid_port_values()
        sys.exit(ERROR_INVALID_PORT)

    physical_port_list = logical_port_name_to_physical_port_list(port_name)
    if physical_port_list is None:
        click.echo("Error: No physical ports found for logical port '{}'".format(port_name))
        return

    if is_port_type_rj45(port_name):
        click.echo("Reset is not applicable for RJ45 port {}.".format(port_name))
        sys.exit(EXIT_FAIL)

    if len(physical_port_list) > 1:
        ganged = True

    for physical_port in physical_port_list:
        click.echo("Resetting port {} ... ".format(get_physical_port_name(port_name, i, ganged)), nl=False)

        try:
            result = platform_chassis.get_sfp(physical_port).reset()
        except NotImplementedError:
            click.echo("This functionality is currently not implemented for this platform")
            sys.exit(ERROR_NOT_IMPLEMENTED)

        if result:
            click.echo("OK")
        else:
            click.echo("Failed")

        i += 1

def update_firmware_info_to_state_db(port_name):
    physical_port = logical_port_to_physical_port_index(port_name)

    namespaces = multi_asic.get_front_end_namespaces()
    for namespace in namespaces:
        state_db = SonicV2Connector(use_unix_socket_path=False, namespace=namespace)
        if state_db is not None:
            state_db.connect(state_db.STATE_DB)
            active_firmware, inactive_firmware = platform_chassis.get_sfp(physical_port).get_transceiver_info_firmware_versions()
            state_db.set(state_db.STATE_DB, 'TRANSCEIVER_INFO|{}'.format(port_name), "active_firmware", active_firmware)
            state_db.set(state_db.STATE_DB, 'TRANSCEIVER_INFO|{}'.format(port_name), "inactive_firmware", inactive_firmware)

# 'firmware' subgroup
@cli.group()
def firmware():
    """Download/Upgrade firmware on the transceiver"""
    pass

def run_firmware(port_name, mode):
    """
        Make the inactive firmware as the current running firmware
        @port_name:
        @mode: 0, 1, 2, 3 different modes to run the firmware
        Returns 1 on success, and exit_code = -1 on failure
    """
    status = 0
    physical_port = logical_port_to_physical_port_index(port_name)
    sfp = platform_chassis.get_sfp(physical_port)

    try:
        api = sfp.get_xcvr_api()
    except NotImplementedError:
        click.echo("This functionality is currently not implemented for this platform")
        sys.exit(ERROR_NOT_IMPLEMENTED)

    if mode == 0:
        click.echo("Running firmware: Non-hitless Reset to Inactive Image")
    elif mode == 1:
        click.echo("Running firmware: Hitless Reset to Inactive Image")
    elif mode == 2:
        click.echo("Running firmware: Attempt non-hitless Reset to Running Image")
    elif mode == 3:
        click.echo("Running firmware: Attempt Hitless Reset to Running Image")
    else:
        click.echo("Running firmware: Unknown mode {}".format(mode))
        sys.exit(EXIT_FAIL)

    try:
        status = api.cdb_run_firmware(mode)
    except NotImplementedError:
        click.echo("This functionality is not applicable for this transceiver")
        sys.exit(EXIT_FAIL)

    return status

def is_fw_switch_done(port_name):
    """
        Make sure the run_firmware cmd is done
        @port_name:
        Returns 1 on success, and exit_code = -1 on failure
    """
    status = 0
    physical_port = logical_port_to_physical_port_index(port_name)
    sfp = platform_chassis.get_sfp(physical_port)

    try:
        api = sfp.get_xcvr_api()
    except NotImplementedError:
        click.echo("This functionality is currently not implemented for this platform")
        sys.exit(ERROR_NOT_IMPLEMENTED)

    try:
        MAX_WAIT = 60 # 60s timeout.
        is_busy = 1 # Initial to 1 for entering while loop at least one time.
        timeout_time = time.time() + MAX_WAIT
        while is_busy and (time.time() < timeout_time):
            fw_info = api.get_module_fw_info()
            is_busy = 1 if (fw_info['status'] == False) and (fw_info['result'] is not None) else 0
            time.sleep(2)

        if fw_info['status'] == True:
            (ImageA, ImageARunning, ImageACommitted, ImageAInvalid,
             ImageB, ImageBRunning, ImageBCommitted, ImageBInvalid, _, _) = fw_info['result']

            if (ImageARunning == 1) and (ImageAInvalid == 1):       # ImageA is running, but also invalid.
                click.echo("FW info error : ImageA shows running, but also shows invalid!")
                status = -1 # Abnormal status.
            elif (ImageBRunning == 1) and (ImageBInvalid == 1):     # ImageB is running, but also invalid.
                click.echo("FW info error : ImageB shows running, but also shows invalid!")
                status = -1 # Abnormal status.
            elif (ImageARunning == 1) and (ImageACommitted == 0):   # ImageA is running, but not committed.
                click.echo("FW images switch successful : ImageA is running")
                status = 1  # run_firmware is done. 
            elif (ImageBRunning == 1) and (ImageBCommitted == 0):   # ImageB is running, but not committed.
                click.echo("FW images switch successful : ImageB is running")
                status = 1  # run_firmware is done. 
            else:                                                   # No image is running, or running and committed image is same.
                click.echo("FW info error : Failed to switch into uncommitted image!")
                status = -1 # Failure for Switching images.
        else:
            click.echo("FW switch : Timeout!")
            status = -1     # Timeout or check code error or CDB not supported.

    except NotImplementedError:
        click.echo("This functionality is not applicable for this transceiver")

    return status

def commit_firmware(port_name):
    status = 0
    physical_port = logical_port_to_physical_port_index(port_name)
    sfp = platform_chassis.get_sfp(physical_port)

    try:
        api = sfp.get_xcvr_api()
    except NotImplementedError:
        click.echo("This functionality is currently not implemented for this platform")
        sys.exit(ERROR_NOT_IMPLEMENTED)

    try:
        status = api.cdb_commit_firmware()
    except NotImplementedError:
        click.echo("This functionality is not applicable for this transceiver")

    return status

def download_firmware(port_name, filepath):
    """Download firmware on the transceiver"""
    try:
        fd = open(filepath, 'rb')
        fd.seek(0, 2)
        file_size = fd.tell()
        fd.seek(0, 0)
    except FileNotFoundError:
        click.echo("Firmware file {} NOT found".format(filepath))
        sys.exit(EXIT_FAIL)

    physical_port = logical_port_to_physical_port_index(port_name)
    sfp = platform_chassis.get_sfp(physical_port)
    try:
        api = sfp.get_xcvr_api()
    except NotImplementedError:
        click.echo("This functionality is NOT applicable to this platform")
        sys.exit(ERROR_NOT_IMPLEMENTED)

    try:
        fwinfo = api.get_module_fw_mgmt_feature()
        if fwinfo['status'] == True:
            startLPLsize, maxblocksize, lplonly_flag, autopaging_flag, writelength = fwinfo['feature']
        else:
            click.echo("Failed to fetch CDB Firmware management features")
            sys.exit(EXIT_FAIL)
    except NotImplementedError:
        click.echo("This functionality is NOT applicable for this transceiver")
        sys.exit(ERROR_NOT_IMPLEMENTED)

    click.echo('CDB: Starting firmware download')
    startdata = fd.read(startLPLsize)
    status = api.cdb_start_firmware_download(startLPLsize, startdata, file_size)
    if status != 1:
        click.echo('CDB: Start firmware download failed - status {}'.format(status))
        sys.exit(EXIT_FAIL)

    # Increase the optoe driver's write max to speed up firmware download
    try:
        sfp.set_optoe_write_max(SMBUS_BLOCK_WRITE_SIZE)
    except NotImplementedError:
        click.echo("Platform doesn't implement optoe write max change. Skipping value increase.")

    with click.progressbar(length=file_size, label="Downloading ...") as bar:
        address = 0
        if lplonly_flag:
            BLOCK_SIZE = min(MAX_LPL_FIRMWARE_BLOCK_SIZE, maxblocksize)
        else:
            BLOCK_SIZE = maxblocksize
        remaining = file_size - startLPLsize
        while remaining > 0:
            count = BLOCK_SIZE if remaining >= BLOCK_SIZE else remaining
            data = fd.read(count)
            if len(data) != count:
                click.echo("Firmware file read failed!")
                sys.exit(EXIT_FAIL)

            if lplonly_flag:
                status = api.cdb_lpl_block_write(address, data)
            else:
                status = api.cdb_epl_block_write(address, data, autopaging_flag, writelength)
            if (status != 1):
                click.echo("CDB: firmware download failed! - status {}".format(status))
                sys.exit(EXIT_FAIL)

            bar.update(count)
            address += count
            remaining -= count

    # Restore the optoe driver's write max to '1' (default value)
    try:
        sfp.set_optoe_write_max(1)
    except NotImplementedError:
        click.echo("Platform doesn't implement optoe write max change. Skipping value restore!")

    status = api.cdb_firmware_download_complete()
    update_firmware_info_to_state_db(port_name)
    click.echo('CDB: firmware download complete')
    return status

# 'run' subcommand
@firmware.command()
@click.argument('port_name', required=True, default=None)
@click.option('--mode', default="0", type=click.Choice(["0", "1", "2", "3"]), show_default=True,
                                                         help="0 = Non-hitless Reset to Inactive Image\n \
                                                               1 = Hitless Reset to Inactive Image (Default)\n \
                                                               2 = Attempt non-hitless Reset to Running Image\n \
                                                               3 = Attempt Hitless Reset to Running Image\n")
def run(port_name, mode):
    """Run the firmware with default mode=0"""

    if is_port_type_rj45(port_name):
        click.echo("This functionality is not applicable for RJ45 port {}.".format(port_name))
        sys.exit(EXIT_FAIL)

    if not is_sfp_present(port_name):
        click.echo("{}: SFP EEPROM not detected\n".format(port_name))
        sys.exit(EXIT_FAIL)

    status = run_firmware(port_name, int(mode))
    if status != 1:
        click.echo('Failed to run firmware in mode={}! CDB status: {}'.format(mode, status))
        sys.exit(EXIT_FAIL)

    update_firmware_info_to_state_db(port_name)
    click.echo("Firmware run in mode={} success".format(mode))

# 'commit' subcommand
@firmware.command()
@click.argument('port_name', required=True, default=None)
def commit(port_name):
    """Commit the running firmware"""

    if is_port_type_rj45(port_name):
        click.echo("This functionality is not applicable for RJ45 port {}.".format(port_name))
        sys.exit(EXIT_FAIL)

    if not is_sfp_present(port_name):
        click.echo("{}: SFP EEPROM not detected\n".format(port_name))
        sys.exit(EXIT_FAIL)

    status = commit_firmware(port_name)
    if status != 1:
        click.echo('Failed to commit firmware! CDB status: {}'.format(status))
        sys.exit(EXIT_FAIL)

    update_firmware_info_to_state_db(port_name)
    click.echo("Firmware commit successful")

# 'upgrade' subcommand
@firmware.command()
@click.argument('port_name', required=True, default=None)
@click.argument('filepath', required=True, default=None)
def upgrade(port_name, filepath):
    """Upgrade firmware on the transceiver"""

    physical_port = logical_port_to_physical_port_index(port_name)

    if is_port_type_rj45(port_name):
        click.echo("This functionality is not applicable for RJ45 port {}.".format(port_name))
        sys.exit(EXIT_FAIL)

    if not is_sfp_present(port_name):
        click.echo("{}: SFP EEPROM not detected\n".format(port_name))
        sys.exit(EXIT_FAIL)

    show_firmware_version(physical_port)

    status = download_firmware(port_name, filepath)
    if status == 1:
        click.echo("Firmware download complete success")
    else:
        click.echo("Firmware download complete failed! CDB status = {}".format(status))
        sys.exit(EXIT_FAIL)

    default_mode = 0
    status = run_firmware(port_name, default_mode)
    if status != 1:
        click.echo('Failed to run firmware in mode={} ! CDB status: {}'.format(default_mode, status))
        sys.exit(EXIT_FAIL)

    click.echo("Firmware run in mode {} successful".format(default_mode))

    if is_fw_switch_done(port_name) != 1:
        click.echo('Failed to switch firmware images!')
        sys.exit(EXIT_FAIL)

    status = commit_firmware(port_name)
    if status != 1:
        click.echo('Failed to commit firmware! CDB status: {}'.format(status))
        sys.exit(EXIT_FAIL)

    click.echo("Firmware commit successful")

# 'download' subcommand
@firmware.command()
@click.argument('port_name', required=True, default=None)
@click.argument('filepath', required=True, default=None)
def download(port_name, filepath):
    """Download firmware on the transceiver"""

    if is_port_type_rj45(port_name):
        click.echo("This functionality is not applicable for RJ45 port {}.".format(port_name))
        sys.exit(EXIT_FAIL)

    if not is_sfp_present(port_name):
       click.echo("{}: SFP EEPROM not detected\n".format(port_name))
       sys.exit(EXIT_FAIL)

    start = time.time()
    status = download_firmware(port_name, filepath)
    if status == 1:
        click.echo("Firmware download complete success")
    else:
        click.echo("Firmware download complete failed! status = {}".format(status))
        sys.exit(EXIT_FAIL)
    end = time.time()
    click.echo("Total download Time: {}".format(str(datetime.timedelta(seconds=end-start))))


# 'unlock' subcommand
@firmware.command()
@click.argument('port_name', required=True, default=None)
@click.option('--password', type=click.INT, help="Password in integer\n")
def unlock(port_name, password):
    """Unlock the firmware download feature via CDB host password"""
    physical_port = logical_port_to_physical_port_index(port_name)
    sfp = platform_chassis.get_sfp(physical_port)

    if is_port_type_rj45(port_name):
        click.echo("This functionality is not applicable for RJ45 port {}.".format(port_name))
        sys.exit(EXIT_FAIL)

    if not is_sfp_present(port_name):
       click.echo("{}: SFP EEPROM not detected\n".format(port_name))
       sys.exit(EXIT_FAIL)

    try:
        api = sfp.get_xcvr_api()
    except NotImplementedError:
        click.echo("This functionality is currently not implemented for this platform")
        sys.exit(ERROR_NOT_IMPLEMENTED)

    if password is None:
        password = CDB_DEFAULT_HOST_PASSWORD
    try:
        status = api.cdb_enter_host_password(int(password))
    except NotImplementedError:
        click.echo("This functionality is not applicable for this transceiver")
        sys.exit(EXIT_FAIL)

    if status == 1:
        click.echo("CDB: Host password accepted")
    else:
        click.echo("CDB: Host password NOT accepted! status = {}".format(status))

# 'version' subcommand
@cli.command()
def version():
    """Display version info"""
    click.echo("sfputil version {0}".format(VERSION))


if __name__ == '__main__':
    cli()
