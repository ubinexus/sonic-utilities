#!/usr/bin/env python
#########################################################
# Copyright 2021 Cisco Systems, Inc.
# All rights reserved.
#
# CLI Extensions for show command
#########################################################

try:
    import click
    import subprocess
    import yaml
    from show import platform
    import utilities_common.cli as clicommon
except ImportError as e:
    raise ImportError("%s - required module not found" % str(e))

PLATFORM_PY = '/opt/cisco/bin/platform.py'

# Platform specific version invoked by generic show.version
def version(verbose):
    filespec = '/opt/cisco/etc/build_info.yaml'
    with open(filespec) as f:
        build_info = yaml.safe_load(f)
    for d in build_info.get('sdk_versions', []):
        for k,v in d.items():
            click.echo('{}: {}'.format(k,v))

@click.command()
def inventory():
    """ Show platform inventory information """
    cmd = 'inventory.py show'
    clicommon.run_command(cmd)

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
            inventory,
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
    install_extensions(cli)
