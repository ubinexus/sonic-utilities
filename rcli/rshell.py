import os
import click
import paramiko

from .linecard import Linecard
from .utils import get_all_linecards

@click.command()
@click.argument('linecard_name', type=str, autocompletion=get_all_linecards)
@click.option('-p','--password', type=str)
def rshell(linecard_name, password=None):
    """
    Open interactive shell for one linecard
    
    :param linecard_name: The name of the linecard to connect to
    :param password: The password for the linecard, if not provided inline 
        user will be prompted for password
    """
    username = os.getlogin()
    try:
        lc = Linecard(linecard_name, username, password)
        if lc.connection:
            # If connection was created, connection exists. Otherwise, user will see an error message.
            lc.start_shell()
    except paramiko.ssh_exception.AuthenticationException:
        click.echo("Login failed on '{}' with username '{}'".format(linecard_name, username))    


if __name__=="__main__":
    rshell(prog_name='rshell')
