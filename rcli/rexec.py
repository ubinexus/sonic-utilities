import os
import click
import paramiko

from .linecard import Linecard
from .utils import get_all_linecards, get_password, get_password_from_file

@click.command()
@click.argument('linecard_names', nargs=-1, type=str, required=True, autocompletion=get_all_linecards)
@click.option('-c', '--command', type=str, required=True)
@click.option('-k','--use-ssh-keys/--no-keys', default=False)
@click.option('-p','--password-filename', type=str)
def cli(linecard_names, command, use_ssh_keys=False, password_filename=None):
    """
    Executes a command on one or many linecards
    
    :param linecard_names: A list of linecard names to execute the command on, 
        use `all` to execute on all linecards.
    :param command: The command to execute on the linecard(s)
    :param use_ssh_keys: If True, will attempt to use ssh keys to login to the 
        linecard. If False, will prompt for password, defaults to False (optional)
    :param password_filename: A file containing the password for the linecard. If 
        not provided inline, user will be prompted for password. File should be 
        relative to current path.
    """
    username = os.getlogin()
    
    if list(linecard_names) == ["all"]:
        # Get all linecard names using autocompletion helper
        linecard_names = get_all_linecards(None, None, "")

    if use_ssh_keys:
        # If we want to use ssh keys, check if the user provided a password
        password = None if not password_filename else get_password_from_file(password_filename)
    elif password_filename:
        # Don't use ssh keys and read password from file
        password = get_password_from_file(password_filename)
    else:
        # Password filename was not provided, read password from user input
        password = get_password(username)

    # Iterate through each linecard, execute command, and gather output
    for linecard_name in linecard_names:
        try:
            lc = Linecard(linecard_name, username, password, use_ssh_keys)
            if lc.connection:
                # If connection was created, connection exists. Otherwise, user will see an error message.
                click.echo("======== {} output: ========".format(lc.linecard_name))
                click.echo(lc.execute_cmd(command))
        except paramiko.ssh_exception.AuthenticationException:
            click.echo("Login failed on '{}' with username '{}'".format(linecard_name, username))

if __name__=="__main__":
    cli(prog_name='rexec')
