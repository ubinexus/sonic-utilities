import click
import os
import paramiko

from getpass import getpass
from .utils import get_linecard_ip, get_password
from . import interactive

EMPTY_OUTPUTS = ['', '\x1b[?2004l\r']

class Linecard:

    def __init__(self, linecard_name, username, password=None, use_ssh_keys=False):
        """
        Initialize Linecard object and store credentials, connection, and channel
        
        :param linecard_name: The name of the linecard you want to connect to
        :param username: The username to use to connect to the linecard
        :param password: The linecard password. If password not provided, it 
            will prompt the user for it
        :param use_ssh_keys: Whether or not to use SSH keys to authenticate.
        """
        self.ip = get_linecard_ip(linecard_name)

        if not self.ip:
            click.echo("Linecard '{}' not found.\n".format(linecard_name))
            self.connection = None
            return None

        self.linecard_name = linecard_name
        self.username = username

        if use_ssh_keys and os.environ.get("SSH_AUTH_SOCK"):
            # The user wants to use SSH keys and the ssh agent is running
            self.connection = paramiko.SSHClient()
            # if ip address not in known_hosts, ignore known_hosts error
            self.connection.load_system_host_keys()
            self.connection.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            ssh_agent = paramiko.Agent()
            available_keys = ssh_agent.get_keys()
            if available_keys:
                # Try to connect using all keys
                connected = False
                for key in available_keys:
                    try:
                        self.connection.connect(self.ip, username=username, pkey=key)
                        # If we connected successfully without error, break out of loop
                        connected = True
                        break
                    except paramiko.ssh_exception.AuthenticationException:
                        # key didn't work
                        continue
                if not connected:
                    # None of the available keys worked, copy new keys over
                    password = password if password is not None else get_password(username)
                    self.ssh_copy_id(password)
            else:
                # host does not trust this client, perform ssh-copy-id
                password = password if password is not None else get_password(username)
                self.ssh_copy_id(password)

        else:
            password = password if password is not None else getpass(
                "Password for username '{}': ".format(username),
                # Pass in click stdout stream - this is similar to using click.echo
                stream=click.get_text_stream('stdout')
            )
            self.connection = paramiko.SSHClient()
            # if ip address not in known_hosts, ignore known_hosts error
            self.connection.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            try:
                self.connection.connect(self.ip, username=self.username, password=password)
            except paramiko.ssh_exception.NoValidConnectionsError as e:
                self.connection = None
                click.echo(e)

    def ssh_copy_id(self, password:str) -> None:
        """
        This function generates a new ssh key, copies it to the remote server, 
        and adds it to the ssh-agent for 15 minutes
        
        :param password: The password for the user
        :type password: str
        """
        default_key_path = os.path.expanduser(os.path.join("~/",".ssh","id_rsa"))
        # If ssh keys don't exist, create them
        if not os.path.exists(default_key_path):
            os.system(
                'ssh-keygen -f {} -N "" > /dev/null'.format(default_key_path)
            )

        # Get contents of public keys
        pub_key = open(default_key_path + ".pub", "rt")
        pub_key_contents = pub_key.read()
        pub_key.close()

        # Connect to linecard using password
        self.connection.connect(self.ip, username=self.username, password=password)

        # Create ssh directory (if it doesn't exist) and add supervisor public 
        # key to authorized_keys
        self.connection.exec_command('mkdir ~/.ssh -p \n')
        self.connection.exec_command(
            'echo \'{}\' >> ~/.ssh/authorized_keys \n'
            .format(pub_key_contents)
        )

        # Add key to supervisor SSH Agent with 15 minute timeout
        os.system('ssh-add -t 15m  {}'.format(default_key_path))

        # Now that keys are stored in SSH Agent, remove keys from disk
        os.remove(default_key_path)
        os.remove('{}.pub'.format(default_key_path))

    def start_shell(self) -> None:
        """
        Opens a session, gets a pseudo-terminal, invokes a shell, and then 
        attaches the host shell to the remote shell.
        """
        # Create shell session
        self.channel = self.connection.get_transport().open_session()
        self.channel.get_pty()
        self.channel.invoke_shell()
        # Use Paramiko Interactive script to connect to the shell
        interactive.interactive_shell(self.channel)
        # After user exits interactive shell, close the connection
        self.connection.close()


    def execute_cmd(self, command) -> str:
        """
        Takes a command as an argument, executes it on the remote shell, and returns the output
        
        :param command: The command to execute on the remote shell
        :return: The output of the command.
        """
        # Execute the command and gather errors and output
        _, stdout, stderr = self.connection.exec_command(command + "\n")
        output = stdout.read().decode('utf-8')
        
        if stderr:
            # Error was present, add message to output
            output += stderr.read().decode('utf-8')
        
        # Close connection and return output
        self.connection.close()
        return output
