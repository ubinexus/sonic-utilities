#!/usr/bin/env python
#
# main.py
#
# Command-line utility for interacting with PCIE in SONiC
#

try:
    import sys
    import os
    import subprocess
    import click
    import imp
    import syslog
    import types
    import traceback
    from tabulate import tabulate
except ImportError as e:
    raise ImportError("%s - required module not found" % str(e))

VERSION = '1.0'

SYSLOG_IDENTIFIER = "pcietil"
PLATFORM_SPECIFIC_MODULE_NAME = "pcieutil"
PLATFORM_SPECIFIC_CLASS_NAME = "PcieUtil"

PLATFORM_ROOT_PATH = '/usr/share/sonic/device'
PLATFORM_ROOT_PATH_DOCKER = '/usr/share/sonic/platform'
SONIC_CFGGEN_PATH = '/usr/local/bin/sonic-cfggen'
HWSKU_KEY = 'DEVICE_METADATA.localhost.hwsku'
PLATFORM_KEY = 'DEVICE_METADATA.localhost.platform'

# Global platform-specific psuutil class instance
platform_pcieutil = None
hwsku_path = None

# ========================== Syslog wrappers ==========================


def log_info(msg, also_print_to_console=False):
    syslog.openlog(SYSLOG_IDENTIFIER)
    syslog.syslog(syslog.LOG_INFO, msg)
    syslog.closelog()

    if also_print_to_console:
        click.echo(msg)


def log_warning(msg, also_print_to_console=False):
    syslog.openlog(SYSLOG_IDENTIFIER)
    syslog.syslog(syslog.LOG_WARNING, msg)
    syslog.closelog()

    if also_print_to_console:
        click.echo(msg)


def log_error(msg, also_print_to_console=False):
    syslog.openlog(SYSLOG_IDENTIFIER)
    syslog.syslog(syslog.LOG_ERR, msg)
    syslog.closelog()

    if also_print_to_console:
        click.echo(msg)


# ==================== Methods for initialization ====================

# Returns platform and HW SKU
def get_platform_and_hwsku():
    try:
        proc = subprocess.Popen([SONIC_CFGGEN_PATH, '-H', '-v', PLATFORM_KEY],
                                stdout=subprocess.PIPE,
                                shell=False,
                                stderr=subprocess.STDOUT)
        stdout = proc.communicate()[0]
        proc.wait()
        platform = stdout.rstrip('\n')

        proc = subprocess.Popen([SONIC_CFGGEN_PATH, '-d', '-v', HWSKU_KEY],
                                stdout=subprocess.PIPE,
                                shell=False,
                                stderr=subprocess.STDOUT)
        stdout = proc.communicate()[0]
        proc.wait()
        hwsku = stdout.rstrip('\n')
    except OSError, e:
        raise OSError("Cannot detect platform")

    return (platform, hwsku)


# Loads platform specific psuutil module from source
def load_platform_pcieutil():
    global platform_pcieutil
    global hwsku_path
    # Get platform and hwsku
    (platform, hwsku) = get_platform_and_hwsku()

    # Load platform module from source
    platform_path = ''
    if len(platform) != 0:
        platform_path = "/".join([PLATFORM_ROOT_PATH, platform])
    else:
        platform_path = PLATFORM_ROOT_PATH_DOCKER
    hwsku_path = "/".join([platform_path, hwsku])
#    print(hwsku_path)

    try:
        module_file = "/".join([platform_path, "plugins", PLATFORM_SPECIFIC_MODULE_NAME + ".py"])
        module = imp.load_source(PLATFORM_SPECIFIC_MODULE_NAME, module_file)
    except IOError, e:
        log_error("Failed to load platform module '%s': %s" % (PLATFORM_SPECIFIC_MODULE_NAME, str(e)), True)
        return -1

    try:
        platform_pcieutil_class = getattr(module, PLATFORM_SPECIFIC_CLASS_NAME)
        platform_pcieutil = platform_pcieutil_class()
    except AttributeError, e:
        log_error("Failed to instantiate '%s' class: %s" % (PLATFORM_SPECIFIC_CLASS_NAME, str(e)), True)
        return -2

    return 0


# ==================== CLI commands and groups ====================


# This is our main entrypoint - the main 'psuutil' command
@click.group()
def cli():
    """pcieutil - Command line utility for providing PSU status"""
    if os.geteuid() != 0:
        click.echo("Root privileges are required for this operation")
        sys.exit(1)

    # Load platform-specific psuutil class
    err = load_platform_pcieutil()
    if err != 0:
        sys.exit(2)

# 'version' subcommand
@cli.command()
def version():
    """Display version info"""
    click.echo("pcieutil version {0}".format(VERSION))

#show the platform PCIE info


def print_test_title(testname):
    click.echo("{0:-^80s}".format("-"))
    click.echo("{name: ^80s}".format(name=testname))
    click.echo("{0:-^80s}".format("-"))

#  Show PCIE lnkSpeed
@cli.command()
def pciespeed():
    '''Display PCIE Speed '''
    testname = "Show Switch PCIE lnkSpeed"
    print_test_title(testname)
    speedDict = platform_pcieutil.get_pcie_speed(hwsku_path)
    for key,value in speedDict.items():
        click.echo('{0}\n     {1}\n'.format(key,value))



#  Show PCIE Vender ID and Device ID
@cli.command()
def pcieid():
    '''Display PCIE ID Info '''
    testname = "Show PCIE Vender ID and Device ID"
    print_test_title(testname)
    idDict= platform_pcieutil.get_pcie_id(hwsku_path)
    for key,value in idDict.items(): 
        venderId = value['venderId']
        deviceId = value['deviceId']
        click.echo('Device:    {0}\n      VenderId:   {1}\n      DeviceId:   {2}\n'.format(key,venderId,deviceId))

        
               
if __name__ == '__main__':
    cli()
