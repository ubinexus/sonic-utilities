import os
import click
import paramiko
import time

from .linecard import Linecard
from .utils import get_all_linecards
from getpass import getpass

@click.command()
@click.argument('linecard_names', nargs=-1, type=str, required=True, autocompletion=get_all_linecards)
@click.option('-c', '--command', type=str, required=True)
@click.option('-p','--password', type=str)
def rexec(linecard_names, command, password=None):
    """
    Executes a command on one or many linecards
    
    :param linecard_names: A list of linecard names to execute the command on, 
        use `all` to execute on all linecards.
    :param command: The command to execute on the linecard(s)
    :param password: This is the password for the user. If not provided, the 
        user will be prompted
    for it
    """
    username = os.getlogin()
    password = password if password is not None else getpass(
            "Password for username '{}': ".format(username),
            # Pass in click stdout stream - this is similar to using click.echo
            stream=click.get_text_stream('stdout')
        )
    
    if list(linecard_names) == ["all"]:
        # Get all linecard names using autocompletion helper
        linecard_names = get_all_linecards(None, None, "")


    for linecard_name in linecard_names:
        try:
            lc = Linecard(linecard_name, username, password)
            if lc.connection:
                # If connection was created, connection exists. Otherwise, user will see an error message.
                click.echo("======== {} output: ========".format(lc.linecard_name))
                click.echo(lc.execute_cmd(command))
        except paramiko.ssh_exception.AuthenticationException:
            click.echo("Login failed on '{}' with username '{}'".format(linecard_name, username))

if __name__=="__main__":
    rexec(prog_name='rexec')
