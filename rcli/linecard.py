import time
import paramiko
from rich.console import Console

from getpass import getpass
from .utils import get_linecard_ip
from . import interactive

EMPTY_OUTPUTS = ['', '\x1b[?2004l\r']

class Linecard:

    # def __init__(self, hostname, username, console):
    #     """Initialize Linecard object and store credentials, connection, and channel."""
    #     # Store credentials
    #     self.hostname = hostname
    #     self.username = username
    #     self.console = console

    def __init__(self, hostname, username, console, print_login=True):
        """Initialize Linecard object and store credentials, connection, and channel."""
        self.hostname = hostname
        self.username = username
        self.console = console

        if not os.path.exists(os.path.expanduser(f"~/.ssh/id_rsa")):
            os.system(f'ssh-keygen -f {os.path.expanduser(f"~/.ssh/id_rsa")} -N ""')

        try:
            self.connect(print_login=print_login)
        except paramiko.ssh_exception.AuthenticationException:
            # host does not trust this client, perform a ssh-copy-id
            password = getpass(f"Password for '{hostname}': ")
            pub_key = open(os.path.expanduser(f"~/.ssh/id_rsa.pub"), "rt")
            pub_key_contents = pub_key.read()
            pub_key.close()
            self.connect(password, print_login=print_login)
            self.channel.send(f'mkdir ~/.ssh \n')
            self.get_channel_output()
            self.channel.send(f'echo \'{pub_key_contents}\' >> ~/.ssh/authorized_keys \n')
            self.get_channel_output()

    def connect(self, password=None, print_login=True):
        # Create connection to server and initialize shell channel
        self.connection = paramiko.SSHClient()
        self.connection.load_system_host_keys()
        pkey = paramiko.RSAKey.from_private_key_file(os.path.expanduser("~/.ssh/id_rsa"))
        self.connection.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        self.connection.connect(self.ip, username=self.username, password=password)
        self.channel = "hi"

        # Create channel for shell input/output
        # self.channel = self.connection.get_transport().open_session()
        # self.channel.get_pty()
        # self.channel.invoke_shell()
        # self.channel.send("stty -echo\n")

        # if print_login:
        #     # Print initial SONiC login message
        #     print(self.get_channel_output())
        # else:
        #     # Flush output
        #     self.get_channel_output()

    def start_shell(self):
        """Continuously wait for a command to be inputted, execute that command on remote shell, and print output."""
        self.channel = self.connection.get_transport().open_session()
        self.channel.get_pty()
        self.channel.invoke_shell()
        interactive.interactive_shell(self.channel)
        # command = ""
        # while command not in EXIT_KEYWORDS:
        #     self.channel.send(command + "\n")
        #     output = self.get_channel_output(with_prompt=True)
        #     prompt_index = max(0, output.rfind("\n"))
        #     prompt = output[prompt_index:]
        #     print("{}".format(output[:prompt_index]))
        #     command = input(prompt.replace("\n",""))

        self.connection.close()


    def execute_cmd(self, command):
        """Execute a single command on remote shell and return the output."""
        stdin, stdout, stderr = self.connection.exec_command(command + "\n")
        output = stdout.read().decode('utf-8')
        self.connection.close()
        return output
        self.connection.exec_command(command + "\n")
        output = self.get_channel_output()
        self.connection.close()
        return output


    def get_channel_output(self):
        """Helper method to print output from remote shell session."""
        output = ''
        while self.channel.recv_ready() or output in EMPTY_OUTPUTS:
            if self.channel.recv_ready():
                # Add additional bytes of STDOUT to existing output
                output += self.channel.recv(6144).decode('utf-8')
            else:
                # Channel has no output yet, wait for command to finish running
                time.sleep(0.1)

        # Return output without default prompt (i.e. `admin@vlab-t2-sup:~$`)
        end_index = output.rfind("\n")
        return output[:max(end_index, 0)]

    
    # @staticmethod
    # def get_linecard(linecard_name: str, username, console, print_login=True):
    #     """Get a linecard and try to ssh without password. If auth fails, ask for password and ssh-copy-id."""

    #     if not os.path.exists(os.path.expanduser(f"~/.ssh/id_rsa")):
    #         os.system(f'ssh-keygen -f {os.path.expanduser(f"~/.ssh/id_rsa")} -N ""')

    #     new_linecard = Linecard(linecard_name, username, console)
    #     try:
    #         new_linecard.connect(print_login=print_login)
    #     except paramiko.ssh_exception.AuthenticationException:
    #         # host does not trust this client, perform a ssh-copy-id
    #         password = getpass(f"Password for '{linecard_name}': ")
    #         pub_key = open(os.path.expanduser(f"~/.ssh/id_rsa.pub"), "rt")
    #         pub_key_contents = pub_key.read()
    #         pub_key.close()
    #         new_linecard = Linecard(linecard_name, username, console)
    #         new_linecard.connect(password, print_login=print_login)
    #         new_linecard.channel.send(f'mkdir ~/.ssh \n')
    #         new_linecard.get_channel_output()
    #         new_linecard.channel.send(f'echo \'{pub_key_contents}\' >> ~/.ssh/authorized_keys \n')
    #         new_linecard.get_channel_output()

        return new_linecard

# Example usage
if __name__=="__main__":
    hostname = '10.250.0.121'
    username = 'admin'
    password = 'password'
    client = Linecard(hostname, username, Console())
    client.start_shell()
