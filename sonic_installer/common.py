"""
Module holding common functions and constants used by sonic-installer and its
subpackages.
"""

import subprocess
import sys
import os

import click

from .exception import SonicRuntimeException

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

# Run bash command and return output, raise if it fails
def run_command_or_raise(argv):
    click.echo(click.style("Command: ", fg='cyan') + click.style(' '.join(argv), fg='green'))

    proc = subprocess.Popen(argv, stdout=subprocess.PIPE)
    out, _ = proc.communicate()

    if proc.returncode != 0:
        raise SonicRuntimeException("Failed to run command '{0}'".format(argv))

    return out.rstrip("\n")
