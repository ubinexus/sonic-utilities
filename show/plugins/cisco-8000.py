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

@click.command()
@click.option('--raw/--no-raw', default=False, help='Hexdump raw IDPROMs')
@click.option('--all/--no-all', default=False, help='Dump all known IDPROMs')
@click.option('--list/--no-list', default=False, help='List known IDPROMs')
@click.argument('name', nargs=-1)
def idprom(name, raw, all, list):
    """ Show platform IDPROM information """
    args = [ PLATFORM_PY, 'idprom' ]

    if all:
        if len(name) > 0:
            click.echo('?Option --all ignored when given a list of IDPROM names\n')
        elif list:
            click.echo('?Option --all ignored when combined with --list\n')
        else:
            args.append('--all')
    if list:
        if len(name) > 0:
            click.echo('?Option --list ignored when given a list of IDPROM names\n')
        else:
            args.append('--list')
    if raw:
        if list:
            click.echo('?Option --raw ignored when combined with --list\n')
        else:
            args.append('--raw')
    for alias in name:
        args.append(alias)
    clicommon.run_command(args)


def install_extensions(cli):
    extensions = {
        'platform': [
            idprom,
        ],
    }

    groups = {
        'cli': cli,
        'platform': platform.platform,
    }

    for key,root in groups.items():
        for cmd in extensions.get(key, []):
            root.add_command(cmd)

def register(cli):
    version_info = device_info.get_sonic_version_info() 
    if (version_info and version_info.get('asic_type') == 'cisco'):
        install_extensions(cli)
