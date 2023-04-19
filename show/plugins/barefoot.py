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
           r's/install_\\\(.\*\\\)_tofino.\*/\\1/'
            r' | sed "s/$/\r/"', check=True, shell=True).stdout

def get_available_profiles(opts):
    """Get available profiles"""
    return subprocess.run('docker exec -it syncd find /opt/bfn -mindepth 1 '
        r'-maxdepth 1 -type d,l ' + opts + 
        r' | sed s%/opt/bfn/install_\\\(.\*\\\)_tofino.\*%\\1%'
        r' | sed "s/$/\r/"', shell=True).stdout

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
    click.echo(get_current_profile(), nl=False)

    # Check supported profiles 
    opts = ''
    if chip_family == 'tofino':
        opts = r' -name install_x\*_' + chip_family
    elif chip_family == 'tofino2':
        opts = r' -name install_y\*_' + chip_family
    else:
        opts = r' -name \*_' + chip_family

    # Print profile list
    click.echo('Available profile(s):')
    click.echo(get_available_profiles(opts), nl=False)

def register(cli):
    version_info = device_info.get_sonic_version_info()
    if version_info and version_info.get('asic_type') == 'barefoot':
        cli.commands['platform'].add_command(barefoot)
