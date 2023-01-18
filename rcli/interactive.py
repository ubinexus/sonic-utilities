# From https://github.com/paramiko/paramiko/blob/main/demos/interactive.py
#
#######################################################################
# 
# Copyright (C) 2003-2007  Robey Pointer <robeypointer@gmail.com>
#
# This file is part of paramiko.
#
# Paramiko is free software; you can redistribute it and/or modify it under the
# terms of the GNU Lesser General Public License as published by the Free
# Software Foundation; either version 2.1 of the License, or (at your option)
# any later version.
#
# Paramiko is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for more
# details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with Paramiko; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301 USA.

import select
import socket
import sys
import termios
import tty

from paramiko.py3compat import u
from paramiko import Channel


def interactive_shell(channel: Channel):
    """
    Continuously wait for commands and execute them
    
    The function is a loop that waits for input from either the channel or the terminal. If input is
    received from the channel, it is printed to the terminal. If input is received from the terminal, it
    is sent to the channel.
    
    :param channel: The channel object we use to communicate with the linecard
    :type channel: paramiko.Channel
    """
    # Save the current tty so we can return to it later
    oldtty = termios.tcgetattr(sys.stdin)
    try:
        tty.setraw(sys.stdin.fileno())
        tty.setcbreak(sys.stdin.fileno())
        channel.settimeout(0.0)

        while True:
            # Continuously wait for commands and execute them
            r, w, e = select.select([channel, sys.stdin], [], [])
            if channel in r:
                try:
                    # Get output from channel
                    x = u(channel.recv(1024))
                    if len(x) == 0:
                        # logout message will be displayed
                        break
                    # Write channel output to terminal
                    sys.stdout.write(x)
                    sys.stdout.flush()
                except socket.timeout:
                    pass
            if sys.stdin in r:
                # If we are able to send input, get the input from stdin
                x = sys.stdin.read(1)
                if len(x) == 0:
                    break
                # Send the input to the channel
                channel.send(x)

    finally:
        # Now that the channel has been exited, return to the previously-saved old tty
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, oldtty)