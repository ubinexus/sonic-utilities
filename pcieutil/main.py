#!/usr/bin/env python3
#
# main.py
#
# Command-line utility for interacting with PCIE in SONiC
#

try:
    import os
    import sys
    from collections import OrderedDict

    import click
    from sonic_py_common import device_info, logger
    from swsssdk import SonicV2Connector
    from tabulate import tabulate
    import utilities_common.cli as clicommon
except ImportError as e:
    raise ImportError("%s - required module not found" % str(e))

VERSION = '1.0'

SYSLOG_IDENTIFIER = "pcieutil"
PLATFORM_SPECIFIC_MODULE_NAME = "pcieutil"

# Global platform-specific psuutil class instance
platform_pcieutil = None
platform_plugins_path = None

log = logger.Logger(SYSLOG_IDENTIFIER)


def print_result(name, result):
    string = "PCI Device:  {} ".format(name)
    length = 105-len(string)
    sys.stdout.write(string)
    for i in range(int(length)):
        sys.stdout.write("-")
    click.echo(' [%s]' % result)

# ==================== Methods for initialization ====================

# Loads platform specific psuutil module from source


def load_platform_pcieutil():
    global platform_pcieutil
    global platform_plugins_path

    # Load platform module from source
    try:
        platform_path, _ = device_info.get_paths_to_platform_and_hwsku_dirs()
        platform_plugins_path = os.path.join(platform_path, "plugins")
        sys.path.append(os.path.abspath(platform_plugins_path))
        from pcieutil import PcieUtil
    except ImportError as e:
        log.log_warning("Failed to load platform-specific PcieUtil module. Falling back to the common implementation")
        try:
            from sonic_platform_base.sonic_pcie.pcie_common import PcieUtil
            platform_pcieutil = PcieUtil(platform_plugins_path)
        except ImportError as e:
            log.log_error("Failed to load default PcieUtil module. Error : {}".format(str(e)), True)
            raise e


# ==================== CLI commands and groups ====================


# This is our main entrypoint - the main 'psuutil' command
@click.group()
def cli():
    """pcieutil - Command line utility for checking pci device"""
    if os.geteuid() != 0:
        click.echo("Root privileges are required for this operation")
        sys.exit(1)

    # Load platform-specific psuutil class
    load_platform_pcieutil()

# 'version' subcommand


@cli.command()
def version():
    """Display version info"""
    click.echo("pcieutil version {0}".format(VERSION))

# show the platform PCIE info


def print_test_title(testname):
    click.echo("{name:=^80s}".format(name=testname))

#  Show PCIE lnkSpeed


@cli.command()
def pcie_show():
    '''Display PCIe Device '''
    testname = "Display PCIe Device"
    print_test_title(testname)
    resultInfo = platform_pcieutil.get_pcie_device()
    for item in resultInfo:
        Bus = item["bus"]
        Dev = item["dev"]
        Fn = item["fn"]
        Name = item["name"]
        Id = item["id"]
        click.echo("bus:dev.fn %s:%s.%s - dev_id=0x%s, %s" % (Bus, Dev, Fn, Id, Name))

# Show PCIe AER status


@cli.group(cls=clicommon.AliasedGroup)
def pcie_aer():
    '''Display PCIe AER status'''
    pass


@pcie_aer.command()
@click.option('-nz', '--no-zero', is_flag=True)
def correctable(no_zero):
    '''Show PCIe AER correctable attributes'''

    statedb = SonicV2Connector()
    statedb.connect(statedb.STATE_DB)
    header = ['AER - CORRECTABLE']

    # AER - Correctable fields (9)
    fields = ['RxErr', 'BadTLP', 'BadDLLP', 'Rollover', 'Timeout', 'NonFatalErr', 'CorrIntErr', 'HeaderOF', 'TOTAL_ERR_COR']
    table = OrderedDict()
    for field in fields:
        table[field] = [field]

    resultInfo = platform_pcieutil.get_pcie_check()
    for item in resultInfo:
        if item["result"] == "Failed":
            continue

        Bus = item["bus"]
        Dev = item["dev"]
        Fn = item["fn"]
        Id = item["id"]

        pcie_dev_key = "PCIE_DEVICE|0x%s|%s:%s.%s" % (Id, Bus, Dev, Fn)
        aer_attribute = statedb.get_all(statedb.STATE_DB, pcie_dev_key)
        if not aer_attribute:
            continue

        if no_zero and all(val=='0' for key, val in aer_attribute.items() if key.startswith('correctable')):
            continue

        # Tabulate Header
        device_name = "%s:%s.%s\n0x%s" % (Bus, Dev, Fn, Id)
        header.append(device_name)

        # Tabulate Row
        for field in fields:
            key = "correctable|" + field
            table[field].append(aer_attribute.get(key, 'NA'))

    click.echo(tabulate(list(table.values()), header, tablefmt="grid"))


@pcie_aer.command()
@click.option('-nz', '--no-zero', is_flag=True)
def fatal(no_zero):
    '''Show PCIe AER fatal attributes'''
    statedb = SonicV2Connector()
    statedb.connect(statedb.STATE_DB)
    header = ['AER - FATAL']

    # AER - Fatal fields (18)
    fields = ['Undefined', 'DLP', 'SDES', 'TLP', 'FCP', 'CmpltTO', 'CmpltAbrt', 'UnxCmplt', 'RxOF', 'MalfTLP', 'ECRC', 'UnsupReq', 'ACSViol', 'UncorrIntErr', 'BlockedTLP', 'AtomicOpBlocked', 'TLPBlockedErr', 'TOTAL_ERR_FATAL']
    table = OrderedDict()
    for field in fields:
        table[field] = [field]

    resultInfo = platform_pcieutil.get_pcie_check()
    for item in resultInfo:
        if item["result"] == "Failed":
            continue

        Bus = item["bus"]
        Dev = item["dev"]
        Fn = item["fn"]
        Id = item["id"]

        pcie_dev_key = "PCIE_DEVICE|0x%s|%s:%s.%s" % (Id, Bus, Dev, Fn)
        aer_attribute = statedb.get_all(statedb.STATE_DB, pcie_dev_key)
        if not aer_attribute:
            continue

        if no_zero and all(val=='0' for key, val in aer_attribute.items() if key.startswith('fatal')):
            continue

        # Tabulate Header
        device_name = "%s:%s.%s\n0x%s" % (Bus, Dev, Fn, Id)
        header.append(device_name)

        # Tabulate Row
        for field in fields:
            key = "fatal|" + field
            table[field].append(aer_attribute.get(key, 'NA'))

    click.echo(tabulate(list(table.values()), header, tablefmt="grid"))


@pcie_aer.command()
@click.option('-nz', '--no-zero', is_flag=True)
def non_fatal(no_zero):
    '''Show PCIe AER non-fatal attributes '''
    statedb = SonicV2Connector()
    statedb.connect(statedb.STATE_DB)
    aer_attribute = {}
    header = ['AER - NONFATAL']

    # AER - Non-Fatal fields (18)
    fields = ['Undefined', 'DLP', 'SDES', 'TLP', 'FCP', 'CmpltTO', 'CmpltAbrt', 'UnxCmplt', 'RxOF', 'MalfTLP', 'ECRC', 'UnsupReq', 'ACSViol', 'UncorrIntErr', 'BlockedTLP', 'AtomicOpBlocked', 'TLPBlockedErr', 'TOTAL_ERR_NONFATAL']
    table = OrderedDict()
    for field in fields:
        table[field] = [field]

    resultInfo = platform_pcieutil.get_pcie_check()
    for item in resultInfo:
        if item["result"] == "Failed":
            continue

        Bus = item["bus"]
        Dev = item["dev"]
        Fn = item["fn"]
        Id = item["id"]

        pcie_dev_key = "PCIE_DEVICE|0x%s|%s:%s.%s" % (Id, Bus, Dev, Fn)
        aer_attribute = statedb.get_all(statedb.STATE_DB, pcie_dev_key)
        if not aer_attribute:
            continue

        if no_zero and all(val=='0' for key, val in aer_attribute.items() if key.startswith('non_fatal')):
            continue

        # Tabulate Header
        device_name = "%s:%s.%s\n0x%s" % (Bus, Dev, Fn, Id)
        header.append(device_name)

        # Tabulate Row
        for field in fields:
            key = "non_fatal|" + field
            table[field].append(aer_attribute.get(key, 'NA'))

    click.echo(tabulate(list(table.values()), header, tablefmt="grid"))


@pcie_aer.command(name='all')
@click.option('-nz', '--no-zero', is_flag=True)
@click.pass_context
def all_errors(ctx, no_zero):
    '''Show all PCIe AER attributes '''
    ctx.forward(correctable)
    click.echo("")

    ctx.forward(fatal)
    click.echo("")

    ctx.forward(non_fatal)
    click.echo("")


#  Show PCIE Vender ID and Device ID
@cli.command()
def pcie_check():
    '''Check PCIe Device '''
    testname = "PCIe Device Check"
    err = 0
    print_test_title(testname)
    resultInfo = platform_pcieutil.get_pcie_check()
    for item in resultInfo:
        if item["result"] == "Passed":
            print_result(item["name"], "Passed")
        else:
            print_result(item["name"], "Failed")
            log.log_warning("PCIe Device: " + item["name"] + " Not Found")
            err += 1
    if err:
        click.echo("PCIe Device Checking All Test ----------->>> FAILED")
    else:
        click.echo("PCIe Device Checking All Test ----------->>> PASSED")


@cli.command()
@click.confirmation_option(prompt="Are you sure to overwrite config file pcie.yaml with current pcie device info?")
def pcie_generate():
    '''Generate config file with current pci device'''
    platform_pcieutil.dump_conf_yaml()
    click.echo("Generate config file pcie.yaml under path %s" % platform_plugins_path)


if __name__ == '__main__':
    cli()
