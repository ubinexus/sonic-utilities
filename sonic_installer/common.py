"""
Module holding common functions and constants used by sonic_installer and its
subpackages.
"""

import subprocess
import sys
import os

import click

HOST_PATH = '/host'
IMAGE_PREFIX = 'SONiC-OS-'
IMAGE_DIR_PREFIX = 'image-'
TMP_PREFIX = '/var/tmp'

# Run bash command and print output to stdout
def run_command(command, img_to_delete=None):
    click.echo(click.style("Command: ", fg='cyan') + click.style(command, fg='green'))

    proc = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)
    (out, _) = proc.communicate()

    click.echo(out)

    if proc.returncode != 0:
        if img_to_delete:
            if os.path.exists(img_to_delete):
                os.remove(img_to_delete)
        sys.exit(proc.returncode)
