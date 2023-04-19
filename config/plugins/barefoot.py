#!/usr/bin/env python

import click
import json
import subprocess
from sonic_py_common import device_info
from swsscommon.swsscommon import ConfigDBConnector
from show.plugins.barefoot import check_profile, get_chip_family

def abort_if_false(ctx, param, value):
    if not value:
        ctx.abort()

@click.group()
def barefoot():
    pass

def check_supported_profile(profile, chip_family):
    """Check if profile is supported"""
    if chip_family == 'tofino' and profile[0] != 'x' or \
        chip_family == 'tofino2' and profile[0] != 'y':
        return False
    return True

def check_profile_exist(profile, chip_family):
    """Check if profile exists"""
    completed_process = subprocess.run(['docker', 'exec', '-it', 'syncd',
        'test', '-d', '/opt/bfn/install_' + profile + '_' + chip_family])

    if completed_process.returncode != 0:
        click.echo('No profile with the provided name found for {}'.format(chip_family))
        raise click.Abort()
    return True

@barefoot.command()
@click.option('-y', '--yes', is_flag=True, callback=abort_if_false,
    expose_value=False, prompt='Swss service will be restarted, continue?')
@click.argument('profile')
def profile(profile):
    # Check if profile can be changed
    if check_profile():
        click.echo('Cannot change profile: default one is in use')
        raise click.Abort()

    # Get chip family
    chip_family = get_chip_family()

    # Check if profile is supported
    if check_supported_profile(profile, chip_family) == False:
        click.echo('Specified profile is unsupported on the system')
        raise click.Abort()

    # Check if profile exists
    check_profile_exist(profile, chip_family)

    # Update configuration
    config_db = ConfigDBConnector()
    config_db.connect()
    profile += '_' + chip_family
    config_db.mod_entry('DEVICE_METADATA', 'localhost', {'p4_profile': profile})
    subprocess.run(['systemctl', 'restart', 'swss'], check=True)

def register(cli):
    version_info = device_info.get_sonic_version_info()
    if version_info and version_info.get('asic_type') == 'barefoot':
        cli.commands['platform'].add_command(barefoot)
