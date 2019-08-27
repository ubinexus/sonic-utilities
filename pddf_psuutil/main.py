#!/usr/bin/env python
#
# main.py
#
# Command-line utility for interacting with PSU Controller in PDDF mode in SONiC
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

SYSLOG_IDENTIFIER = "psuutil"
PLATFORM_SPECIFIC_MODULE_NAME = "psuutil"
PLATFORM_SPECIFIC_CLASS_NAME = "PsuUtil"

PLATFORM_ROOT_PATH = '/usr/share/sonic/device'
PLATFORM_ROOT_PATH_DOCKER = '/usr/share/sonic/platform'
SONIC_CFGGEN_PATH = '/usr/local/bin/sonic-cfggen'
HWSKU_KEY = 'DEVICE_METADATA.localhost.hwsku'
PLATFORM_KEY = 'DEVICE_METADATA.localhost.platform'
PDDF_FILE_PATH = '/usr/share/sonic/platform/pddf_support'
# Global platform-specific psuutil class instance
platform_psuutil = None
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


# Loads platform specific psuutil module from source
def load_platform_psuutil():
    global platform_psuutil

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
        platform_psuutil_class = getattr(module, PLATFORM_SPECIFIC_CLASS_NAME)
        platform_psuutil = platform_psuutil_class()
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


# This is our main entrypoint - the main 'psuutil' command
@click.group()
def cli():
    """psuutil - Command line utility for providing PSU status"""

    if os.geteuid() != 0:
        click.echo("Root privileges are required for this operation")
        sys.exit(1)

    if not check_pddf_mode():
        click.echo("PDDF mode should be supported and enabled for this platform for this operation")
        sys.exit(1)

    # Load platform-specific psuutil class
    err = load_platform_psuutil()
    if err != 0:
        sys.exit(2)

# 'version' subcommand
@cli.command()
def version():
    """Display version info"""
    click.echo("psuutil version {0}".format(VERSION))

# 'numpsus' subcommand
@cli.command()
def numpsus():
    """Display number of supported PSUs on device"""
    click.echo(str(platform_psuutil.get_num_psus()))

# 'status' subcommand
@cli.command()
@click.option('-i', '--index', default=-1, type=int, help="the index of PSU")
def status(index):
    """Display PSU status"""
    supported_psu = range(1, platform_psuutil.get_num_psus() + 1)
    psu_ids = []
    if (index < 0):
        psu_ids = supported_psu
    else:
        psu_ids = [index]

    header = ['PSU', 'Status']
    status_table = []

    for psu in psu_ids:
        msg = ""
        psu_name = "PSU {}".format(psu)
        if psu not in supported_psu:
            click.echo("Error! The {} is not available on the platform.\n" \
            "Number of supported PSU - {}.".format(psu_name, platform_psuutil.get_num_psus()))
            continue
        presence = platform_psuutil.get_psu_presence(psu)
        if presence:
            oper_status = platform_psuutil.get_psu_status(psu)
            msg = 'OK' if oper_status else "NOT OK"
        else:
            msg = 'NOT PRESENT'
        status_table.append([psu_name, msg])

    if status_table:
        click.echo(tabulate(status_table, header, tablefmt="simple"))

# 'mfrinfo' subcommand
@cli.command()
@click.option('-i', '--index', default=-1, type=int, help="the index of PSU")
def mfrinfo(index):
    """Display PSU manufacturer info"""
    supported_psu = range(1, platform_psuutil.get_num_psus() + 1)
    psu_ids = []
    info = ""
    if (index < 0):
        psu_ids = supported_psu
    else:
        psu_ids = [index]

    for psu in psu_ids:
        msg = ""
        psu_name = "PSU {}".format(psu)
        if psu not in supported_psu:
            click.echo("Error! The {} is not available on the platform.\n" \
            "Number of supported PSU - {}.".format(psu_name, platform_psuutil.get_num_psus()))
            continue
        status = platform_psuutil.get_psu_status(psu)
        if not status:
            click.echo("{} is Not OK\n".format(psu_name))
            continue

        model_name = platform_psuutil.get_model(psu)
        mfr_id = platform_psuutil.get_mfr_id(psu)
        serial_num = platform_psuutil.get_serial(psu)
        airflow_dir = platform_psuutil.get_direction(psu)
        
        click.echo("{} is OK\nManufacture Id: {}\n" \
                "Model: {}\nSerial Number: {}\n" \
                "Fan Direction: {}\n".format(psu_name, mfr_id, model_name, serial_num, airflow_dir))


# 'seninfo' subcommand
@cli.command()
@click.option('-i', '--index', default=-1, type=int, help="the index of PSU")
def seninfo(index):
    """Display PSU sensor info"""
    supported_psu = range(1, platform_psuutil.get_num_psus() + 1)
    psu_ids = []
    if (index < 0):
        psu_ids = supported_psu
    else:
        psu_ids = [index]

    for psu in psu_ids:
        msg = ""
        psu_name = "PSU {}".format(psu)
        if psu not in supported_psu:
            click.echo("Error! The {} is not available on the platform.\n" \
            "Number of supported PSU - {}.".format(psu_name, platform_psuutil.get_num_psus()))
            continue
        oper_status = platform_psuutil.get_psu_status(psu)
        
        if not oper_status:
            click.echo("{} is Not OK\n".format(psu_name))
            continue

        v_out = platform_psuutil.get_output_voltage(psu)
        i_out = platform_psuutil.get_output_current(psu)
        p_out = platform_psuutil.get_output_power(psu)
        # p_out would be in micro watts, convert it into milli watts
        p_out = p_out/1000

        fan1_rpm = platform_psuutil.get_fan_rpm(psu, 1)
        click.echo("{} is OK\nOutput Voltage: {} mv\n" \
                "Output Current: {} ma\nOutput Power: {} mw\n" \
                "Fan1 Speed: {} rpm\n".format(psu_name, v_out, i_out, p_out, fan1_rpm))

@cli.group()
def debug():
    """pddf_psuutil debug commands"""
    pass

@debug.command()
def dump_sysfs():
    """Dump all PSU related SysFS paths"""
    status = platform_psuutil.dump_sysfs()

    if status:
        for i in status:
            click.echo(i)


if __name__ == '__main__':
    cli()
