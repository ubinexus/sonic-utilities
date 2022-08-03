import click
import paramiko

from getpass import getpass
from .utils import get_linecard_ip
from . import interactive

EMPTY_OUTPUTS = ['', '\x1b[?2004l\r']

class Linecard:

    def __init__(self, linecard_name, username, password=None):
        """
        Initialize Linecard object and store credentials, connection, and channel
        
        :param linecard_name: The name of the linecard you want to connect to
        :param username: The username to use to connect to the linecard
        :param password: The password for the username. If not provided, it will prompt the user for it
        """
        self.ip = get_linecard_ip(linecard_name)

        if not self.ip:
            click.echo("Linecard '{}' not found.\n".format(linecard_name))
            self.connection = None
            return None

        self.linecard_name = linecard_name
        self.username = username

        password = password if password is not None else getpass(
            "Password for username '{}': ".format(username),
            # Pass in click stdout stream - this is similar to using click.echo
            stream=click.get_text_stream('stdout')
        )
        
        self.connect(password)

        # come back later for ssh-agent
        #
        # if not os.path.exists(os.path.expanduser(f"~/.ssh/id_rsa")):
        #     os.system(f'ssh-keygen -f {os.path.expanduser(f"~/.ssh/id_rsa")} -N ""')

        # try:
        #     self.connect(print_login=print_login)
        # except paramiko.ssh_exception.AuthenticationException:
        #     # host does not trust this client, perform a ssh-copy-id
        #     password = getpass(f"Password for '{hostname}': ")
        #     pub_key = open(os.path.expanduser(f"~/.ssh/id_rsa.pub"), "rt")
        #     pub_key_contents = pub_key.read()
        #     pub_key.close()
        #     self.connect(password, print_login=print_login)
        #     self.channel.send(f'mkdir ~/.ssh \n')
        #     self.get_channel_output()
        #     self.channel.send(f'echo \'{pub_key_contents}\' >> ~/.ssh/authorized_keys \n')
        #     self.get_channel_output()

    def connect(self, password):
        """
        The function connects to a linecard using the IP address, username, and password provided
        
        :param password: the password for the user
        """
        # Create connection to server and initialize shell channel
        self.connection = paramiko.SSHClient()
        # self.connection.load_system_host_keys()
        # pkey = paramiko.RSAKey.from_private_key_file(os.path.expanduser("~/.ssh/id_rsa"))
        # if ip address not in known_hosts, ignore known_hosts error
        self.connection.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        self.connection.connect(self.ip, username=self.username, password=password)

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
        stdin, stdout, stderr = self.connection.exec_command(command + "\n")
        output = stdout.read().decode('utf-8')
        self.connection.close()
        return output
