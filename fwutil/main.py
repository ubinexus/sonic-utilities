#!/usr/bin/env python
#
# main.py
#
# Command-line utility for firmware management in SONiC
#

try:
    import sys
    import os
    import time
    import subprocess
    import click
    import imp
    import syslog
    import types
    import traceback
    from tabulate import tabulate
    import urllib
    import signal
except ImportError as e:
    raise ImportError("%s - required module not found" % str(e))

VERSION = '1.0'

SYSLOG_IDENTIFIER = "fwutil"
PLATFORM_SPECIFIC_MODULE_NAME = "fwutil"
PLATFORM_SPECIFIC_CLASS_NAME = "FwUtil"

PLATFORM_ROOT_PATH = '/usr/share/sonic/device'
PLATFORM_ROOT_PATH_DOCKER = '/usr/share/sonic/platform'
SONIC_CFGGEN_PATH = '/usr/local/bin/sonic-cfggen'
HWSKU_KEY = 'DEVICE_METADATA.localhost.hwsku'
PLATFORM_KEY = 'DEVICE_METADATA.localhost.platform'
DEFAULT_FW_IMAGE_PATH = '/tmp/fw_image'

# Global platform-specific fwutil class instance
platform_fwutil = None

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


# Loads platform specific fwutil module from source
def load_platform_fwutil():
    global platform_fwutil

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
        module_file = "/".join([platform_path, "plugins",
                                PLATFORM_SPECIFIC_MODULE_NAME + ".py"])
        module = imp.load_source(PLATFORM_SPECIFIC_MODULE_NAME, module_file)
    except IOError, e:
        log_error("Failed to load platform module '%s': %s" % (
            PLATFORM_SPECIFIC_MODULE_NAME, str(e)), True)
        return -1

    try:
        platform_fwutil_class = getattr(module, PLATFORM_SPECIFIC_CLASS_NAME)
        platform_fwutil = platform_fwutil_class()
    except AttributeError, e:
        log_error("Failed to instantiate '%s' class: %s" %
                  (PLATFORM_SPECIFIC_CLASS_NAME, str(e)), True)
        return -2

    return 0

# ==================== Helper functions ====================

# Needed to prevent "broken pipe" error messages when piping
# output of multiple commands using subprocess.Popen()


def default_sigpipe():
    signal.signal(signal.SIGPIPE, signal.SIG_DFL)


def reporthook(count, block_size, total_size):
    global start_time, last_time
    cur_time = int(time.time())
    if count == 0:
        start_time = cur_time
        last_time = cur_time
        return

    if cur_time == last_time:
        return

    last_time = cur_time

    duration = cur_time - start_time
    progress_size = int(count * block_size)
    speed = int(progress_size / (1024 * duration))
    percent = int(count * block_size * 100 / total_size)
    time_left = (total_size - progress_size) / speed / 1024
    sys.stdout.write("\r...%d%%, %d MB, %d KB/s, %d seconds left...   " %
                     (percent, progress_size / (1024 * 1024), speed, time_left))
    sys.stdout.flush()


# Function which validates whether a given URL specifies an existent file
# on a reachable remote machine. Will abort the current operation if not
def validate_url_or_abort(url):
    # Attempt to retrieve HTTP response code
    try:
        urlfile = urllib.urlopen(url)
        response_code = urlfile.getcode()
        urlfile.close()
    except IOError, err:
        response_code = None

    if not response_code:
        click.echo("Did not receive a response from remote machine. Aborting...")
        raise click.Abort()
    else:
        # Check for a 4xx response code which indicates a nonexistent URL
        if response_code / 100 == 4:
            click.echo("Image file not found on remote machine. Aborting...")
            raise click.Abort()


def get_module_list():
    # Get list of supported module
    err = load_platform_fwutil() if platform_fwutil is None else 0
    if err:
        exit("Failed to load get list of supported modules")
    return platform_fwutil.get_module_list()


# ==================== CLI commands and groups ====================


# This is our main entrypoint - the main 'fwutil' command
@click.group()
def cli():
    """fwutil - Command line utility for managing module's firmware"""

    if os.geteuid() != 0:
        click.echo("Root privileges are required for this operation")
        sys.exit(1)

    # Load platform-specific fwutil class
    err = load_platform_fwutil()
    if err != 0:
        sys.exit(2)

# 'version' subcommand
@cli.command()
def version():
    """Display version info"""
    click.echo("fwutil version {0}".format(VERSION))

# 'show' subgroup
@cli.group()
def show():
    """Display version of module's firmware"""
    pass

# 'version' subcommand
@show.command()
def version():
    """Display version of module's firmware"""
    header = ['Module', 'Submodule', 'Version']
    version_table = []

    try:
        supported_modules = platform_fwutil.get_module_list()
    except NotImplementedError:
        click.echo(
            "This functionality is currently not implemented for this platform")
        sys.exit(5)

    for module in supported_modules:
        try:
            module_fw_dict = platform_fwutil.get_fw_version(module)
        except NotImplementedError:
            click.echo(
                "This functionality is currently not implemented for this platform")
            sys.exit(5)

        if module_fw_dict.get('has_submodule'):
            sub_module_fw_dict = module_fw_dict.get("fw_version")
            for submodule in sub_module_fw_dict:
                version_table.append(
                    [module, submodule, sub_module_fw_dict[submodule]])
        else:
            version_table.append(
                [module, "", module_fw_dict.get("fw_version")])

    if version_table:
        click.echo(tabulate(version_table, header, tablefmt="simple"))

# 'install' subgroup
@cli.group()
def install():
    """ Firmware installation manager """
    if os.geteuid() != 0:
        exit("Root privileges required for this operation")

# Install firmware
@cli.command()
@click.option('-m', '--module', required=True, type=click.Choice(get_module_list()))
@click.argument('url')
def install(module, url):
    """ Install firmware image from local binary or URL"""
    if url.startswith('http://') or url.startswith('https://'):
        click.echo('Downloading image...')
        validate_url_or_abort(url)
        try:
            urllib.urlretrieve(url, DEFAULT_FW_IMAGE_PATH, reporthook)
        except Exception, e:
            click.echo("Download error")
            raise click.Abort()
        image_path = DEFAULT_FW_IMAGE_PATH
    else:
        image_path = url

    # Verify that the local file exists and is a regular file
    if not os.path.isfile(image_path):
        click.echo(
            "Image file '{}' does not exist or is not a regular file. Aborting...".format(image_path))
        raise click.Abort()

    try:
        result = platform_fwutil.install(module, image_path)
    except NotImplementedError:
        click.echo(
            "This functionality is currently not implemented for this platform")
        sys.exit(5)

    if result:
        click.echo("Done")
    else:
        click.echo("Failed")


if __name__ == '__main__':
    cli()
