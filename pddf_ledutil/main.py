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

SYSLOG_IDENTIFIER = "ledutil"
PLATFORM_SPECIFIC_MODULE_NAME = "ledutil"
PLATFORM_SPECIFIC_CLASS_NAME = "LedUtil"

PLATFORM_ROOT_PATH = '/usr/share/sonic/device'
PLATFORM_ROOT_PATH_DOCKER = '/usr/share/sonic/platform'
SONIC_CFGGEN_PATH = '/usr/local/bin/sonic-cfggen'
HWSKU_KEY = 'DEVICE_METADATA.localhost.hwsku'
PLATFORM_KEY = 'DEVICE_METADATA.localhost.platform'
PDDF_FILE_PATH = '/usr/share/sonic/platform/pddf_support'
# Global platform-specific ledutil class instance
platform_ledutil = None
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


# Loads platform specific ledutil module from source
def load_platform_ledutil():
    global platform_ledutil

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
        platform_ledutil_class = getattr(module, PLATFORM_SPECIFIC_CLASS_NAME)
        platform_ledutil = platform_ledutil_class()
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


# This is our main entrypoint - the main 'ledutil' command
@click.group()
def cli():
    """pddf_ledutil - Command line utility for providing FAN information"""

    if os.geteuid() != 0:
        click.echo("Root privileges are required for this operation")
        sys.exit(1)

    if not check_pddf_mode():
        click.echo("PDDF mode should be supported and enabled for this platform for this operation")
        sys.exit(1)

    # Load platform-specific ledutil class
    err = load_platform_ledutil()
    if err != 0:
        sys.exit(2)

# 'version' subcommand
@cli.command()
def version():
    """Display version info"""
    click.echo("PDDF ledutil version {0}".format(VERSION))

# 'getstatusled' subcommand
@cli.command()
@click.argument('device_name', type=click.STRING)
@click.argument('index', type=click.STRING)
def getstatusled(device_name, index):
    if device_name is None:
        click.echo("device_name is required")
        raise click.Abort()

    outputs = platform_ledutil.get_status_led(device_name, index)
    click.echo(outputs)


# 'setstatusled' subcommand
@cli.command()
@click.argument('device_name', type=click.STRING)
@click.argument('index', type=click.STRING)
@click.argument('color', type=click.STRING)
@click.argument('color_state', type=click.STRING)
def setstatusled(device_name, index, color, color_state):
    if device_name is None:
        click.echo("device_name is required")
        raise click.Abort()

    outputs = platform_ledutil.set_status_led(device_name, index, color, color_state)
    click.echo(outputs)

if __name__ == '__main__':
    cli()
