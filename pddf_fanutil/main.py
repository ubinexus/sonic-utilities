#!/usr/bin/env python
#
# main.py
#
# Command-line utility for interacting with FAN Controller in PDDF mode in SONiC
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

SYSLOG_IDENTIFIER = "fanutil"
PLATFORM_SPECIFIC_MODULE_NAME = "fanutil"
PLATFORM_SPECIFIC_CLASS_NAME = "FanUtil"

PLATFORM_ROOT_PATH = '/usr/share/sonic/device'
PLATFORM_ROOT_PATH_DOCKER = '/usr/share/sonic/platform'
SONIC_CFGGEN_PATH = '/usr/local/bin/sonic-cfggen'
HWSKU_KEY = 'DEVICE_METADATA.localhost.hwsku'
PLATFORM_KEY = 'DEVICE_METADATA.localhost.platform'
PDDF_FILE_PATH = '/usr/share/sonic/platform/pddf_support'
# Global platform-specific fanutil class instance
platform_fanutil = None
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


# Loads platform specific fanutil module from source
def load_platform_fanutil():
    global platform_fanutil

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
        platform_fanutil_class = getattr(module, PLATFORM_SPECIFIC_CLASS_NAME)
        platform_fanutil = platform_fanutil_class()
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


# This is our main entrypoint - the main 'fanutil' command
@click.group()
def cli():
    """pddf_fanutil - Command line utility for providing FAN information"""

    if os.geteuid() != 0:
        click.echo("Root privileges are required for this operation")
        sys.exit(1)

    if not check_pddf_mode():
        click.echo("PDDF mode should be supported and enabled for this platform for this operation")
        sys.exit(1)

    # Load platform-specific fanutil class
    err = load_platform_fanutil()
    if err != 0:
        sys.exit(2)

# 'version' subcommand
@cli.command()
def version():
    """Display version info"""
    click.echo("PDDF fanutil version {0}".format(VERSION))

# 'numfans' subcommand
@cli.command()
def numfans():
    """Display number of FANs installed on device"""
    click.echo(str(platform_fanutil.get_num_fans()))

# 'status' subcommand
@cli.command()
@click.option('-i', '--index', default=-1, type=int, help="the index of FAN")
def status(index):
    """Display FAN status"""
    supported_fan = range(1, platform_fanutil.get_num_fans() + 1)
    fan_ids = []
    if (index < 0):
        fan_ids = supported_fan
    else:
        fan_ids = [index]

    header = ['FAN', 'Status']
    status_table = []

    for fan in fan_ids:
        msg = ""
        fan_name = "FAN {}".format(fan)
        if fan not in supported_fan:
            click.echo("Error! The {} is not available on the platform.\n" \
            "Number of supported FAN - {}.".format(fan_name, platform_fanutil.get_num_fans()))
            continue
        presence = platform_fanutil.get_presence(fan)
        if presence:
            oper_status = platform_fanutil.get_status(fan)
            msg = 'OK' if oper_status else "NOT OK"
        else:
            msg = 'NOT PRESENT'
        status_table.append([fan_name, msg])

    if status_table:
        click.echo(tabulate(status_table, header, tablefmt="simple"))

# 'direction' subcommand
@cli.command()
@click.option('-i', '--index', default=-1, type=int, help="the index of FAN")
def direction(index):
    """Display FAN airflow direction"""
    supported_fan = range(1, platform_fanutil.get_num_fans() + 1)
    fan_ids = []
    if (index < 0):
        fan_ids = supported_fan
    else:
        fan_ids = [index]

    header = ['FAN', 'Direction']
    status_table = []

    for fan in fan_ids:
        msg = ""
        fan_name = "FAN {}".format(fan)
        if fan not in supported_fan:
            click.echo("Error! The {} is not available on the platform.\n" \
            "Number of supported FAN - {}.".format(fan_name, platform_fanutil.get_num_fans()))
            continue
        direction = platform_fanutil.get_direction(fan)
        status_table.append([fan_name, direction])

    if status_table:
        click.echo(tabulate(status_table, header, tablefmt="simple"))

# 'speed' subcommand
@cli.command()
@click.option('-i', '--index', default=-1, type=int, help="the index of FAN")
def getspeed(index):
    """Display FAN speed in RPM"""
    supported_fan = range(1, platform_fanutil.get_num_fans() + 1)
    fan_ids = []
    if (index < 0):
        fan_ids = supported_fan
    else:
        fan_ids = [index]

    header = ['FAN', 'Front Fan RPM', 'Rear Fan RPM']
    status_table = []

    for fan in fan_ids:
        msg = ""
        fan_name = "FAN {}".format(fan)
        if fan not in supported_fan:
            click.echo("Error! The {} is not available on the platform.\n" \
            "Number of supported FAN - {}.".format(fan_name, platform_fanutil.get_num_fans()))
            continue
        front = platform_fanutil.get_speed(fan)
        rear = platform_fanutil.get_speed_rear(fan)
        status_table.append([fan_name, front, rear])

    if status_table:
        click.echo(tabulate(status_table, header, tablefmt="simple"))

# 'setspeed' subcommand
@cli.command()
@click.argument('speed', type=int)
def setspeed(speed):
    """Set FAN speed in percentage"""
    if speed is None:
        click.echo("speed value is required")
        raise click.Abort()

    status = platform_fanutil.set_speed(speed)
    if status:
        click.echo("Successful")
    else:
        click.echo("Failed")

@cli.group()
def debug():
    """pddf_fanutil debug commands"""
    pass

@debug.command()
def dump_sysfs():
    """Dump all Fan related SysFS paths"""
    status = platform_fanutil.dump_sysfs()

    if status:
        for i in status:
            click.echo(i)



if __name__ == '__main__':
    cli()
