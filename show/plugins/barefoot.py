#!/usr/bin/env python

import click
import json
import subprocess
from sonic_py_common import device_info

@click.group()
def barefoot():
    pass

def check_profile():
    """Check if profile can be changed"""
    ret = subprocess.run(['docker', 'exec', '-it', 'syncd',
        'test', '-h', '/opt/bfn/install'])
    if ret.returncode != 0:
        return True
    return False

def get_chip_family():
    """Get chip family"""
    hwsku_dir = device_info.get_path_to_hwsku_dir()
    with open(hwsku_dir + '/switch-tna-sai.conf') as file:
        chip_family = json.load(file)['chip_list'][0]['chip_family'].lower()
    return chip_family

def get_current_profile():
    """Get current profile"""
    return subprocess.run('docker exec -it syncd readlink /opt/bfn/install | sed '
            r's/install_\\\(.\*\\\)_profile/\\1/'
            r' | sed s/install_\\\(.\*\\\)_tofino.\*/\\1/', check=True, shell=True)

def get_profile_format(chip_family):
    """Get profile naming format. Check if contains tofino family information"""
    output = subprocess.check_output(['docker', 'exec', '-it', 'syncd', 'ls', '/opt/bfn']).strip().decode()
    return '_' + chip_family if '_tofino' in output else '_profile'

def get_available_profiles(opts):
    """Get available profiles"""
    return subprocess.run('docker exec -it syncd find /opt/bfn -mindepth 1 '
        r'-maxdepth 1 -type d,l ' + opts + '| sed '
        r's%/opt/bfn/install_\\\(.\*\\\)_profile%\\1%'
        r' | sed s%/opt/bfn/install_\\\(.\*\\\)_tofino.\*%\\1%', shell=True)

@barefoot.command()
def profile():
    # Check if profile can be changed
    if check_profile():
        click.echo('Current profile: default')
        return

    # Get chip family
    chip_family = get_chip_family()

    # Print current profile
    click.echo('Current profile: ', nl=False)
    current_profile = get_current_profile()
    click.echo(current_profile.stdout, nl=False)

    # Check if profile naming format contains tofino family information 
    suffix = get_profile_format(chip_family)

    # Check supported profiles 
    opts = ''
    if chip_family == 'tofino':
        opts = r' -name install_x\*' + suffix
    elif chip_family == 'tofino2':
        opts = r' -name install_y\*' + suffix
    else:
        opts = r' -name \*' + suffix

    # Print profile list
    click.echo('Available profile(s):')
    available_profiles = get_available_profiles(opts)
    click.echo(available_profiles.stdout, nl=False)

def register(cli):
    version_info = device_info.get_sonic_version_info()
    if version_info and version_info.get('asic_type') == 'barefoot':
        cli.commands['platform'].add_command(barefoot)
