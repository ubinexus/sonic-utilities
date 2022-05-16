#!/usr/bin/env python
#########################################################
# Copyright 2021 Cisco Systems, Inc.
# All rights reserved.
#
# CLI Extensions for show command
#########################################################

try:
    import click
    import yaml
    from show import platform
    from sonic_py_common import device_info
    import utilities_common.cli as clicommon
except ImportError as e:
    raise ImportError("%s - required module not found" % str(e))

PLATFORM_PY = '/opt/cisco/bin/platform.py'
BUILD_INFO = '/opt/cisco/etc/build_info.yaml'

@click.command()
def inventory():
    """Show Platform Inventory"""
    args = [ PLATFORM_PY, 'inventoryshow' ]
    clicommon.run_command(args)

@click.command()
def version():
    """Show Platform SDK Version"""
    try: 
        with open(BUILD_INFO,'r') as f:
            contents = f.read()
        print(contents)
        f.close()
    except Exception as e:
        print(e)

@click.command()
def idprom():
    """Show Platform Idprom Inventory"""
    args = [ PLATFORM_PY, 'idprom' ]
    clicommon.run_command(args)

def register(cli):
    version_info = device_info.get_sonic_version_info() 
    if (version_info and version_info.get('asic_type') == 'cisco-8000'):
        cli.commands['platform'].add_command(inventory)
        cli.commands['platform'].add_command(idprom)
        cli.commands['platform'].add_command(version)
