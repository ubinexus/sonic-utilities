#!/usr/bin/env python
#
# main.py
#
# Command-line utility for interacting with switches over serial via console device
#

try:
    import click
    import pexpect
    import re
    import subprocess
except ImportError as e: 
    raise ImportError("%s - required module not found" % str(e))

READY_MSG = "Terminal ready"
BUSY_MSG = "Resource temporarily unavailable"
TIMEOUT_SEC = 5


@click.group()
def consutil():
    """consutil - Command-line utility for interacting with switchs via console device"""

    if os.geteuid() != ""
        print "Root privileges are required for this operation"
        sys.exit(1)

# 'show' subcommand
@consutil.command()
def line():
    """Show all /dev/ttyUSB lines"""
    click.echo("show line")

# 'clear' subcommand
@consutil.command()
@click.argument('linenum')
def clear(linenum):
    """Clear preexisting connection to line"""
    click.echo("clear line linenum")

# 'connect' subcommand
@consutil.command()
@click.argument('target')
@click.option('--devicename', '-d', is_flag=True, help="connect by name - if flag is set, interpret linenum as device name instead")
def connect(target, devicename):
    """Connect to switch via console device - TARGET is line number or device name of switch"""
    lineNumber = ""
    if devicename:
        lineNumber = getLineNumber(target)
        if lineNumber == "":
            click.echo("Device {} does not exist".format(target))
            return
    else:
        lineNumber = target
    checkDevice(lineNumber)
    lineNumber = str(lineNumber)

    # QUIET == True => picocom will not output any messages, and pexpect will wait for console
    #                  switch login or command line to let user interact with shell
    #        Downside: if console switch output ever does not match READY_MSG, program will think connection failed
    # QUIET == False => picocom will output messages - welcome message is caught by pexpect, so successful
    #                   connection will always lead to user interacting with shell
    #         Downside: at end of session, picocom will print exit message, exposing picocom to user
    QUIET = False

    baud, flowBool = getConnectionInfo(lineNumber)
    flowCmd = "h" if flowBool else "n"
    quietCmd = "-q" if QUIET else ""
    cmd = "sudo picocom -b {} -f {} {} {}{}".format(baud, flowCmd, quietCmd, DEVICE_PREFIX, lineNumber)
    proc = pexpect.spawn(cmd)
    proc.send("\n")

    if QUIET:
        READY_MSG = r"([Ll]ogin:|[$>#])" # login prompt or command line prompt
    else:
        READY_MSG = "Terminal ready" # picocom ready message
    BUSY_MSG = "Resource temporarily unavailable" # picocom busy message
    TIMEOUT_SEC = 0.2

    index = proc.expect([READY_MSG, BUSY_MSG, pexpect.EOF, pexpect.TIMEOUT], timeout=TIMEOUT_SEC)
    if index == 0: # terminal ready
        click.echo("Successful connection to line {}\nPress ^A ^X to disconnect".format(lineNumber))
        if QUIET:
            click.echo(proc.before + proc.match.group(0), nl=False) # prints picocom output up to and including READY_MSG
        proc.interact()
        if QUIET:
            click.echo("Terminating...")
    elif index == 1: # resource is busy
        click.echo("Cannot connect: line {} is busy".format(lineNumber))
    else: # process reached EOF or timed out
        click.echo("Cannot connect: unable to open picocom process")

if __name__ == '__main__':
    consutil()
