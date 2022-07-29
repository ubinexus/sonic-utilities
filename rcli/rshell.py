import os
import click
import paramiko

from .linecard import Linecard
from .utils import get_all_linecards

@click.command()
@click.argument('linecard_name', type=click.STRING, autocompletion=get_all_linecards)
@click.option('-u','--username')
def rshell(linecard_name, username):
    """Open interactive shell for one linecard."""
    if username is None:
        username = os.getlogin()
    try:
        lc = Linecard(linecard_name, username)
        if lc.channel:
            # If channel was created, connection exists. Otherwise, user will see an error message.
            lc.start_shell()
    except paramiko.ssh_exception.AuthenticationException:
        click.echo("Login failed on '{}' with username '{}'".format(linecard_name, username))    


if __name__=="__main__":
    rshell(prog_name='rshell')
