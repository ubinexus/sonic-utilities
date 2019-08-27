#!/usr/bin/env python
#
# main.py
#
# Command-line utility for interacting with Thermal sensors in PDDF mode in SONiC
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

SYSLOG_IDENTIFIER = "thermalutil"
PLATFORM_SPECIFIC_MODULE_NAME = "thermalutil"
PLATFORM_SPECIFIC_CLASS_NAME = "ThermalUtil"

PLATFORM_ROOT_PATH = '/usr/share/sonic/device'
PLATFORM_ROOT_PATH_DOCKER = '/usr/share/sonic/platform'
SONIC_CFGGEN_PATH = '/usr/local/bin/sonic-cfggen'
HWSKU_KEY = 'DEVICE_METADATA.localhost.hwsku'
PLATFORM_KEY = 'DEVICE_METADATA.localhost.platform'
PDDF_FILE_PATH = '/usr/share/sonic/platform/pddf_support'
# Global platform-specific thermalutil class instance
platform_thermalutil = None
pddf_support = 0


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


# Loads platform specific thermalutil module from source
def load_platform_thermalutil():
    global platform_thermalutil

    # Get platform and hwsku
    (platform, hwsku) = get_platform_and_hwsku()

    # Load platform module from source
    platform_path = ''
    if len(platform) != 0:
        platform_path = "/".join([PLATFORM_ROOT_PATH, platform])
    else:
        platform_path = PLATFORM_ROOT_PATH_DOCKER
    hwsku_path = "/".join([platform_path, hwsku])

    try:
        module_file = "/".join([platform_path, "plugins", PLATFORM_SPECIFIC_MODULE_NAME + ".py"])
        module = imp.load_source(PLATFORM_SPECIFIC_MODULE_NAME, module_file)
    except IOError, e:
        log_error("Failed to load platform module '%s': %s" % (PLATFORM_SPECIFIC_MODULE_NAME, str(e)), True)
        return -1

    try:
        platform_thermalutil_class = getattr(module, PLATFORM_SPECIFIC_CLASS_NAME)
        # the operation below should be permitted only in PDDF mode
        platform_thermalutil = platform_thermalutil_class()
    except AttributeError, e:
        log_error("Failed to instantiate '%s' class: %s" % (PLATFORM_SPECIFIC_CLASS_NAME, str(e)), True)
        return -2

    return 0

def check_pddf_mode():
    if os.path.exists(PDDF_FILE_PATH):
        pddf_support = 1
        return True
    else:
        pddf_support = 0
        return False

# ==================== CLI commands and groups ====================


# This is our main entrypoint - the main 'thermalutil' command
@click.group()
def cli():
    """pddf_thermalutil - Command line utility for providing Temp Sensors information"""

    if os.geteuid() != 0:
        click.echo("Root privileges are required for this operation")
        sys.exit(1)

    if not check_pddf_mode():
        click.echo("PDDF mode should be supported and enabled for this platform for this operation")
        sys.exit(1)

    # Load platform-specific thermalutil class
    err = load_platform_thermalutil()
    if err != 0:
        sys.exit(2)

# 'version' subcommand
@cli.command()
def version():
    """Display version info"""
    click.echo("PDDF thermalutil version {0}".format(VERSION))

# 'numthermals' subcommand
@cli.command()
def numthermals():
    """Display number of Thermal Sensors installed """
    click.echo(str(platform_thermalutil.get_num_thermals()))

# 'gettemp' subcommand
@cli.command()
@click.option('-i', '--index', default=-1, type=int, help="the index of Temp Sensor")
def gettemp(index):
    """Display Temperature values of thermal sensors"""
    supported_thermal = range(1, platform_thermalutil.get_num_thermals() + 1)
    thermal_ids = []
    if (index < 0):
        thermal_ids = supported_thermal
    else:
        thermal_ids = [index]

    header = ['Temp Sensor', 'Label', 'Value']
    status_table = []

    for thermal in thermal_ids:
        msg = ""
        thermal_name = "TEMP{}".format(thermal)
        if thermal not in supported_thermal:
            click.echo("Error! The {} is not available on the platform.\n" \
            "Number of supported Temp - {}.".format(thermal_name, platform_thermalutil.get_num_thermals()))
            ##continue
        label, value = platform_thermalutil.show_thermal_temp_values(thermal)
        status_table.append([thermal_name, label, value])

    if status_table:
        click.echo(tabulate(status_table, header, tablefmt="simple"))

@cli.group()
def debug():
    """pddf_thermalutil debug commands"""
    pass

@debug.command()
def dump_sysfs():
    """Dump all Temp Sensor related SysFS paths"""
    status = platform_thermalutil.dump_sysfs()

    if status:
        for i in status:
            click.echo(i)


if __name__ == '__main__':
    cli()
