import os
import click
import paramiko
import time

from .linecard import Linecard
from .utils import get_all_linecards
from getpass import getpass

@click.command()
@click.argument('linecards', nargs=-1, required=True, autocompletion=get_all_linecards)
@click.option('-c', '--command', required=True)
@click.option('-u','--username')
def rexec(linecards, command, username):
    """Execute a command on one (or many) linecards."""
    username = username if username else os.getlogin()
    password = getpass("Password for '{}': ".format(username))
    
    shells = []
    # Collect linecards
    for linecard_name in linecards:
        try:
            lc = Linecard(linecard_name, username, password, print_login=False)
            shells.append(lc)
        except paramiko.ssh_exception.AuthenticationException:
            print("Login failed on '{}' with username '{}'".format(linecard_name, username))
    
    # Delay for linecards to flush output
    time.sleep(0.5)

    # Execute commands
    for linecard in shells:
        if linecard.channel:
            # If channel was created, connection exists. Otherwise, user will see an error message.
            print("======== {} output: ========".format(linecard.linecard_name))
            print(linecard.execute_cmd(command))

if __name__=="__main__":
    rexec(prog_name='rexec')
