#!/usr/bin/env python
#
# main.py
#
# Command-line utility for interacting with switches over serial via console device
#

try:
    import click
    import os
    import pexpect
    import re
    import subprocess
    import sys
    from tabulate import tabulate
    from lib import *
except ImportError as e:
    raise ImportError("%s - required module not found" % str(e))

    
Baudlist = ['9600','19200','115200']
flowlist = [ 'x','h','n']
    
    
@click.group()
def consutil():
    """consutil - Command-line utility for interacting with switches via console device"""

    if os.geteuid() != 0:
        click.echo("Root privileges are required for this operation")
        sys.exit(1)

# 'show' subcommand
@consutil.command()
def show():
    """Show all /dev/ttyUSB lines and their info"""
    devices = getAllDevices()
    busyDevices = getBusyDevices()
    LengthPre = getPrefixLen()
 
    header = ["Line", "Actual/Configured Baud", "PID", "Start Time"]
    body = []
    for device in devices:
        lineNum = device[LengthPre:]
        busy = " "
        pid = ""
        date = ""
        if lineNum in busyDevices:
            pid, date = busyDevices[lineNum]
            busy = "*"
        actBaud, confBaud, _ = getConnectionInfo(lineNum)
        # repeated "~" will be replaced by spaces - hacky way to align the "/"s
        baud = "{}/{}{}".format(actBaud, confBaud, "~"*(15-len(confBaud)))
        body.append([busy+lineNum, baud, pid, date])
        
    # replace repeated "~" with spaces - hacky way to align the "/"s
    click.echo(tabulate(body, header, stralign="right").replace('~', ' ')) 

# 'clear' subcommand
@consutil.command()
@click.argument('linenum')
def clear(linenum):
    """Clear preexisting connection to line"""
    checkDevice(linenum)
    linenum = str(linenum)

    busyDevices = getBusyDevices()
    if linenum in busyDevices:
        pid, _ = busyDevices[linenum]
        cmd = "sudo kill -SIGTERM " + pid
        click.echo("Sending SIGTERM to process " + pid)
        run_command(cmd)
    else:
        click.echo("No process is connected to line " + linenum)

# 'connect' subcommand
@consutil.command()
@click.argument('target')
@click.option('--devicename', '-d', is_flag=True, help="connect by name - if flag is set, interpret linenum as device name instead")
@click.option('--baudrate','-b',default=9600,show_default=True,type=str,help="connect with assigned baudrate support 9600,19200,115200")
@click.option('--databits','-i',default=8,show_default=True,help="set data bits range 5~8")
@click.option('--stopbits','-j',default=1,show_default=True,help="set stop bits 1 or 2")
@click.option('--parity','-p',help="set parity none/odd/even/")
@click.option('--flowcontrol','-f',help="set flow control")
def connect(target, devicename,baudrate,databits,stopbits,parity,flowcontrol):
    """Connect to switch via console device - TARGET is line number or device name of switch"""
    lineNumber = getLineNumber(target, devicename)
    checkDevice(lineNumber)
    lineNumber = str(lineNumber)
    devicename1 = DEVICE_PREFIX+lineNumber
    
    if baudrate is None:
        actBaud = "9600"
    elif baudrate not in Baudlist:
        print 'Invalid baud rate only support 9600/19200/115200. Default is 9600.'
        actBaud = "9600"
    else:
        print 'baudrate=',baudrate
        actBaud = baudrate
        
    if flowcontrol is None:
       flowCmd = "n"
    elif flowcontrol not in flowlist:
       print 'Invalid flowcontrol only support n,x,h. Default is n.'
       flowCmd = "n"
    else:
       print 'flowcontrol=',flowcontrol
       flowCmd= flowcontrol

    # build and start picocom command
    actBaud, _, flowBool = getConnectionInfo(lineNumber)
    flowCmd = "h" if flowBool else "n"
    quietCmd = "-q" if QUIET else ""
    cmd = "sudo picocom -b {} -f {} {} {}".format(actBaud, flowCmd, quietCmd,devicename1)
    proc = pexpect.spawn(cmd)
    proc.send("\n")

    if QUIET:
        readyMsg = DEV_READY_MSG
    else:
        readyMsg = "Terminal ready" # picocom ready message
    busyMsg = "Resource temporarily unavailable" # picocom busy message

    # interact with picocom or print error message, depending on pexpect output
    index = proc.expect([readyMsg, busyMsg, pexpect.EOF, pexpect.TIMEOUT], timeout=TIMEOUT_SEC)
    if index == 0: # terminal ready
        click.echo("Successful connection to line {}\nPress ^A ^X to disconnect".format(lineNumber))
        if QUIET:
            # prints picocom output up to and including readyMsg
            click.echo(proc.before + proc.match.group(0), nl=False) 
        proc.interact()
        if QUIET:
            click.echo("\nTerminating...")
    elif index == 1: # resource is busy
        click.echo("Cannot connect: line {} is busy".format(lineNumber))
    else: # process reached EOF or timed out
        click.echo("Cannot connect: unable to open picocom process")

if __name__ == '__main__':
    consutil()
