import click
import os
import paramiko

from .utils import get_linecard_ip, get_password
from . import interactive

EMPTY_OUTPUTS = ['', '\x1b[?2004l\r']

class Linecard:

    def __init__(self, linecard_name, username, password=None, password_filename=None, use_ssh_keys=False):
        """
        Initialize Linecard object and store credentials, connection, and channel
        
        :param linecard_name: The name of the linecard you want to connect to
        :param username: The username to use to connect to the linecard
        :param password: The linecard password.
        :param password_filename: The file containing the password. If password 
            and password_filename not provided, it will prompt the user for it
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
                    except paramiko.SSHException:
                        pass
                if not connected:
                    self.ssh_copy_id(password_filename)
            else:
                # host does not trust this client, perform ssh-copy-id
                self.ssh_copy_id(password_filename)

        else:
            password = password if password is not None else get_password(
                username, password_filename
            )
            self.connection = paramiko.SSHClient()
            # if ip address not in known_hosts, ignore known_hosts error
            self.connection.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            try:
                self.connection.connect(self.ip, username=self.username, password=password)
            except paramiko.ssh_exception.NoValidConnectionsError as e:
                self.connection = None
                click.echo(e)

    def ssh_copy_id(self, password_filename:str) -> None:
        """
        This function generates a new ssh key, copies it to the remote server, 
        and adds it to the ssh-agent for 15 minutes
        
        :param password_filename: The name of the file that contains the 
            password for the user
        :type password_filename: str
        """
        default_key_path = os.path.expanduser(os.path.join("~/",".ssh","id_rsa"))
        os.system(
            'ssh-keygen -f {} -N "" > /dev/null'.format(default_key_path)
        )
        pub_key = open(default_key_path + ".pub", "rt")
        pub_key_contents = pub_key.read()
        pub_key.close()
        password = get_password(self.username, password_filename)
        self.connection.connect(self.ip, username=self.username, password=password)
        self.connection.exec_command('mkdir ~/.ssh -p \n')
        self.connection.exec_command(
            'echo \'{}\' >> ~/.ssh/authorized_keys \n'
            .format(pub_key_contents)
        )
        # Add key for 15 min
        os.system('ssh-add -t 15m  {}'.format(default_key_path))

        # Remove keys from disk
        os.remove(default_key_path)
        os.remove('{}.pub'.format(default_key_path))

    def start_shell(self):
        """
        Opens a session, gets a pseudo-terminal, invokes a shell, and then 
        attaches the host shell to the remote shell.
        """
        self.channel = self.connection.get_transport().open_session()
        self.channel.get_pty()
        self.channel.invoke_shell()
        interactive.interactive_shell(self.channel)
        self.connection.close()


    def execute_cmd(self, command):
        """
        Takes a command as an argument, executes it on the remote shell, and returns the output
        
        :param command: The command to execute on the remote shell
        :return: The output of the command.
        """
        _, stdout, stderr = self.connection.exec_command(command + "\n")
        output = stdout.read().decode('utf-8')
        
        if stderr:
            output += stderr.read().decode('utf-8')

        self.connection.close()
        return output
