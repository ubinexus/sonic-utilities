import click
import utilities_common.cli as clicommon
import os
from swsscommon.swsscommon import  ConfigDBConnector
import subprocess

#
# 'system' group ("config system ...")
#

@click.group(cls=clicommon.AliasedGroup)
def system():
    """configure system custom parameters"""
    pass



@system.command()
@click.pass_context
def key(ctx):
    """ command to add encryption master key"""
    current_key = subprocess.call('sudo cat /etc/sonic/enc_master_key > /dev/null 2>&1', shell=True)
    if current_key == 0:
        click.echo("ERROR: There is already an encryption key configured.",err=True)
        return
    click.echo("Enter the new encryption master key:")
    new_key = click.prompt("",prompt_suffix="")
    if not is_valid_key(new_key):
            ctx.fail("ERROR: The key contains unsupported characters. Remove spaces, #, and , from the key.")

    subprocess.call('echo "{}" | sudo tee /etc/sonic/enc_master_key > /dev/null'.format(new_key), shell=True)
    subprocess.call('sudo chmod 644 /etc/sonic/enc_master_key', shell=True)
    click.echo("New encryption key stored.")



def is_valid_key(key):
    # Define a list of unsupported characters
    unsupported_characters = [' ', '#', ',']
    
    # Check if the key contains any unsupported characters
    for char in unsupported_characters:
        if char in key:
            return False
    return True
