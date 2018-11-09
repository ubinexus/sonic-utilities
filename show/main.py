#! /usr/bin/python -u

import errno
import json
import getpass
import os
import re
import subprocess
import sys
import textfsm
import types


import click
from click_default_group import DefaultGroup
from collections import defaultdict
from natsort import natsorted
from tabulate import tabulate
from netaddr import IPAddress
from pprint import pprint

import sonic_platform
from swsssdk import ConfigDBConnector
from swsssdk import SonicV2Connector

#import mlnx

try:
    # noinspection PyPep8Naming
    import ConfigParser as configparser
except ImportError:
    # noinspection PyUnresolvedReferences
    import configparser


# This is from the aliases example:
# https://github.com/pallets/click/blob/57c6f09611fc47ca80db0bd010f05998b3c0aa95/examples/aliases/aliases.py
class Config(object):
    """Object to hold CLI config"""

    def __init__(self):
        self.path = os.getcwd()
        self.aliases = {}

    def read_config(self, filename):
        parser = configparser.RawConfigParser()
        parser.read([filename])
        try:
            self.aliases.update(parser.items('aliases'))
        except configparser.NoSectionError:
            pass


class InterfaceAliasConverter(object):
    """Class which handles conversion between interface name and alias"""

    def __init__(self):
        self.alias_max_length = 0
        cmd = 'sonic-cfggen -d --var-json "PORT"'
        p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
        self.port_dict = json.loads(p.stdout.read())

        for port_name in self.port_dict.keys():
            if self.alias_max_length < len(
                    self.port_dict[port_name]['alias']):
               self.alias_max_length = len(
                    self.port_dict[port_name]['alias'])

    def name_to_alias(self, interface_name):
        """Return vendor interface alias if SONiC
           interface name is given as argument
        """
        if interface_name is not None:
            for port_name in self.port_dict.keys():
                if interface_name == port_name:
                    return self.port_dict[port_name]['alias']

        click.echo("Invalid interface {}".format(interface_name))
        raise click.Abort()

    def alias_to_name(self, interface_alias):
        """Return SONiC interface name if vendor
           port alias is given as argument
        """
        if interface_alias is not None:
            for port_name in self.port_dict.keys():
                if interface_alias == self.port_dict[port_name]['alias']:
                    return port_name

        click.echo("Invalid interface {}".format(interface_alias))
        raise click.Abort()


# Global Config object
_config = None


# This aliased group has been modified from click examples to inherit from DefaultGroup instead of click.Group.
# DefaultGroup is a superclass of click.Group which calls a default subcommand instead of showing
# a help message if no subcommand is passed
class AliasedGroup(DefaultGroup):
    """This subclass of a DefaultGroup supports looking up aliases in a config
    file and with a bit of magic.
    """

    def get_command(self, ctx, cmd_name):
        global _config

        # If we haven't instantiated our global config, do it now and load current config
        if _config is None:
            _config = Config()

            # Load our config file
            cfg_file = os.path.join(os.path.dirname(__file__), 'aliases.ini')
            _config.read_config(cfg_file)

        # Try to get builtin commands as normal
        rv = click.Group.get_command(self, ctx, cmd_name)
        if rv is not None:
            return rv

        # No builtin found. Look up an explicit command alias in the config
        if cmd_name in _config.aliases:
            actual_cmd = _config.aliases[cmd_name]
            return click.Group.get_command(self, ctx, actual_cmd)

        # Alternative option: if we did not find an explicit alias we
        # allow automatic abbreviation of the command.  "status" for
        # instance will match "st".  We only allow that however if
        # there is only one command.
        matches = [x for x in self.list_commands(ctx)
                   if x.lower().startswith(cmd_name.lower())]
        if not matches:
            # No command name matched. Issue Default command.
            ctx.arg0 = cmd_name
            cmd_name = self.default_cmd_name
            return DefaultGroup.get_command(self, ctx, cmd_name)
        elif len(matches) == 1:
            return DefaultGroup.get_command(self, ctx, matches[0])
        ctx.fail('Too many matches: %s' % ', '.join(sorted(matches)))


# To be enhanced. Routing-stack information should be collected from a global
# location (configdb?), so that we prevent the continous execution of this
# bash oneliner. To be revisited once routing-stack info is tracked somewhere.
def get_routing_stack():
    command = "sudo docker ps | grep bgp | awk '{print$2}' | cut -d'-' -f3 | cut -d':' -f1"

    try:
        proc = subprocess.Popen(command,
                                stdout=subprocess.PIPE,
                                shell=True,
                                stderr=subprocess.STDOUT)
        stdout = proc.communicate()[0]
        proc.wait()
        result = stdout.rstrip('\n')

    except OSError, e:
        raise OSError("Cannot detect routing-stack")

    return (result)


# Global Routing-Stack variable
routing_stack = get_routing_stack()


def run_command(command, display_cmd=False):
    if display_cmd:
        click.echo(click.style("Command: ", fg='cyan') + click.style(command, fg='green'))

    # No conversion needed for intfutil commands as it already displays
    # both SONiC interface name and alias name for all interfaces.
    if get_interface_mode() == "alias" and not command.startswith("intfutil"):
        run_command_in_alias_mode(command)
        raise sys.exit(0)

    proc = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)

    while True:
        output = proc.stdout.readline()
        if output == "" and proc.poll() is not None:
            break
        if output:
            click.echo(output.rstrip('\n'))

    rc = proc.poll()
    if rc != 0:
        sys.exit(rc)


def get_interface_mode():
    mode = os.getenv('SONIC_CLI_IFACE_MODE')
    if mode is None:
        mode = "default"
    return mode


# Global class instance for SONiC interface name to alias conversion
iface_alias_converter = InterfaceAliasConverter()


def print_output_in_alias_mode(output, index):
    """Convert and print all instances of SONiC interface
       name to vendor-sepecific interface aliases.
    """

    alias_name = ""
    interface_name = ""

    # Adjust tabulation width to length of alias name
    if output.startswith("---"):
        word = output.split()
        dword = word[index]
        underline = dword.rjust(iface_alias_converter.alias_max_length,
                                '-')
        word[index] = underline
        output = '  ' .join(word)

    # Replace SONiC interface name with vendor alias
    word = output.split()
    if word:
        interface_name = word[index]
        interface_name = interface_name.replace(':', '')
    for port_name in natsorted(iface_alias_converter.port_dict.keys()):
            if interface_name == port_name:
                alias_name = iface_alias_converter.port_dict[port_name]['alias']
    if alias_name:
        if len(alias_name) < iface_alias_converter.alias_max_length:
            alias_name = alias_name.rjust(
                                iface_alias_converter.alias_max_length)
        output = output.replace(interface_name, alias_name, 1)

    click.echo(output.rstrip('\n'))


def run_command_in_alias_mode(command):
    """Run command and replace all instances of SONiC interface names
       in output with vendor-sepecific interface aliases.
    """

    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)

    while True:
        output = process.stdout.readline()
        if output == '' and process.poll() is not None:
            break

        if output:
            index = 1
            raw_output = output
            output = output.lstrip()

            if command.startswith("portstat"):
                """Show interface counters"""
                index = 0
                if output.startswith("IFACE"):
                    output = output.replace("IFACE", "IFACE".rjust(
                               iface_alias_converter.alias_max_length))
                print_output_in_alias_mode(output, index)

            elif command == "pfcstat":
                """Show pfc counters"""
                index = 0
                if output.startswith("Port Tx"):
                    output = output.replace("Port Tx", "Port Tx".rjust(
                                iface_alias_converter.alias_max_length))

                elif output.startswith("Port Rx"):
                    output = output.replace("Port Rx", "Port Rx".rjust(
                                iface_alias_converter.alias_max_length))
                print_output_in_alias_mode(output, index)

            elif (command.startswith("sudo sfputil show eeprom")):
                """show interface transceiver eeprom"""
                index = 0
                print_output_in_alias_mode(raw_output, index)

            elif (command.startswith("sudo sfputil show")):
                """show interface transceiver lpmode,
                   presence
                """
                index = 0
                if output.startswith("Port"):
                    output = output.replace("Port", "Port".rjust(
                               iface_alias_converter.alias_max_length))
                print_output_in_alias_mode(output, index)

            elif command == "sudo lldpshow":
                """show lldp table"""
                index = 0
                if output.startswith("LocalPort"):
                    output = output.replace("LocalPort", "LocalPort".rjust(
                               iface_alias_converter.alias_max_length))
                print_output_in_alias_mode(output, index)

            elif command.startswith("queuestat"):
                """show queue counters"""
                index = 0
                if output.startswith("Port"):
                    output = output.replace("Port", "Port".rjust(
                               iface_alias_converter.alias_max_length))
                print_output_in_alias_mode(output, index)

            elif command == "fdbshow":
                """show mac"""
                index = 3
                if output.startswith("No."):
                    output = "  " + output
                    output = re.sub(
                                'Type', '      Type', output)
                elif output[0].isdigit():
                    output = "    " + output
                print_output_in_alias_mode(output, index)
            elif command.startswith("nbrshow"):
                """show arp"""
                index = 2
                if "Vlan" in output:
                    output = output.replace('Vlan', '  Vlan')
                print_output_in_alias_mode(output, index)

            else:
                if index:
                    for port_name in iface_alias_converter.port_dict.keys():
                        regex = re.compile(r"\b{}\b".format(port_name))
                        result = re.findall(regex, raw_output)
                        if result:
                            interface_name = ''.join(result)
                            if not raw_output.startswith("    PortID:"):
                                raw_output = raw_output.replace(
                                    interface_name,
                                    iface_alias_converter.name_to_alias(
                                            interface_name))
                    click.echo(raw_output.rstrip('\n'))

    rc = process.poll()
    if rc != 0:
        sys.exit(rc)


CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help', '-?'])

#
# 'cli' group (root group)
#

# This is our entrypoint - the main "show" command
# TODO: Consider changing function name to 'show' for better understandability
@click.group(cls=AliasedGroup, context_settings=CONTEXT_SETTINGS)
def cli():
    """SONiC command line - 'show' command"""
    pass


#
# 'arp' command ("show arp")
#

@cli.command()
@click.argument('ipaddress', required=False)
@click.option('-if', '--iface')
@click.option('--verbose', is_flag=True, help="Enable verbose output")
def arp(ipaddress, iface, verbose):
    """Show IP ARP table"""
    cmd = "nbrshow -4"

    if ipaddress is not None:
        cmd += " -ip {}".format(ipaddress)

    if iface is not None:
        if get_interface_mode() == "alias":
            if not ((iface.startswith("PortChannel")) or
                    (iface.startswith("eth"))):
                iface = iface_alias_converter.alias_to_name(iface)

        cmd += " -if {}".format(iface)

    run_command(cmd, display_cmd=verbose)

#
# 'ndp' command ("show ndp")
#

@cli.command()
@click.argument('ip6address', required=False)
@click.option('-if', '--iface')
@click.option('--verbose', is_flag=True, help="Enable verbose output")
def ndp(ip6address, iface, verbose):
    """Show IPv6 Neighbour table"""
    cmd = "nbrshow -6"

    if ip6address is not None:
        cmd += " -ip {}".format(ip6address)

    if iface is not None:
        cmd += " -if {}".format(iface)

    run_command(cmd, display_cmd=verbose)

#
# 'interfaces' group ("show interfaces ...")
#

@cli.group(cls=AliasedGroup, default_if_no_args=False)
def interfaces():
    """Show details of the network interfaces"""
    pass

# 'alias' subcommand ("show interfaces alias")
@interfaces.command()
@click.argument('interfacename', required=False)
def alias(interfacename):
    """Show Interface Name/Alias Mapping"""

    cmd = 'sonic-cfggen -d --var-json "PORT"'
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)

    port_dict = json.loads(p.stdout.read())

    header = ['Name', 'Alias']
    body = []

    if interfacename is not None:
        if get_interface_mode() == "alias":
            interfacename = iface_alias_converter.alias_to_name(interfacename)

        # If we're given an interface name, output name and alias for that interface only
        if interfacename in port_dict:
            if 'alias' in port_dict[interfacename]:
                body.append([interfacename, port_dict[interfacename]['alias']])
            else:
                body.append([interfacename, interfacename])
        else:
            click.echo("Invalid interface name, '{0}'".format(interfacename))
            return
    else:
        # Output name and alias for all interfaces
        for port_name in natsorted(port_dict.keys()):
            if 'alias' in port_dict[port_name]:
                body.append([port_name, port_dict[port_name]['alias']])
            else:
                body.append([port_name, port_name])

    click.echo(tabulate(body, header))

#
# 'neighbor' group ###
#
@interfaces.group(cls=AliasedGroup, default_if_no_args=False)
def neighbor():
    """Show neighbor related information"""
    pass

# 'expected' subcommand ("show interface neighbor expected")
@neighbor.command()
@click.argument('interfacename', required=False)
def expected(interfacename):
    """Show expected neighbor information by interfaces"""
    neighbor_cmd = 'sonic-cfggen -d --var-json "DEVICE_NEIGHBOR"'
    p1 = subprocess.Popen(neighbor_cmd, shell=True, stdout=subprocess.PIPE)
    neighbor_dict = json.loads(p1.stdout.read())

    neighbor_metadata_cmd = 'sonic-cfggen -d --var-json "DEVICE_NEIGHBOR_METADATA"'
    p2 = subprocess.Popen(neighbor_metadata_cmd, shell=True, stdout=subprocess.PIPE)
    neighbor_metadata_dict = json.loads(p2.stdout.read())

    #Swap Key and Value from interface: name to name: interface
    device2interface_dict = {}
    for port in natsorted(neighbor_dict.keys()):
        device2interface_dict[neighbor_dict[port]['name']] = {'localPort': port, 'neighborPort': neighbor_dict[port]['port']}

    header = ['LocalPort', 'Neighbor', 'NeighborPort', 'NeighborLoopback', 'NeighborMgmt', 'NeighborType']
    body = []
    if interfacename:
        for device in natsorted(neighbor_metadata_dict.keys()):
            if device2interface_dict[device]['localPort'] == interfacename:
                body.append([device2interface_dict[device]['localPort'],
                             device,
                             device2interface_dict[device]['neighborPort'],
                             neighbor_metadata_dict[device]['lo_addr'],
                             neighbor_metadata_dict[device]['mgmt_addr'],
                             neighbor_metadata_dict[device]['type']])
    else:
        for device in natsorted(neighbor_metadata_dict.keys()):
            body.append([device2interface_dict[device]['localPort'],
                         device,
                         device2interface_dict[device]['neighborPort'],
                         neighbor_metadata_dict[device]['lo_addr'],
                         neighbor_metadata_dict[device]['mgmt_addr'],
                         neighbor_metadata_dict[device]['type']])

    click.echo(tabulate(body, header))

# 'summary' subcommand ("show interfaces summary")
@interfaces.command()
@click.argument('interfacename', required=False)
@click.option('--verbose', is_flag=True, help="Enable verbose output")
def summary(interfacename, verbose):
    """Show interface status and information"""

    cmd = "/sbin/ifconfig"

    if interfacename is not None:
        if get_interface_mode() == "alias":
            interfacename = iface_alias_converter.alias_to_name(interfacename)

        cmd += " {}".format(interfacename)

    run_command(cmd, display_cmd=verbose)


@interfaces.group(cls=AliasedGroup, default_if_no_args=False)
def transceiver():
    """Show SFP Transceiver information"""
    pass


@transceiver.command()
@click.argument('interfacename', required=False)
@click.option('-d', '--dom', 'dump_dom', is_flag=True, help="Also display Digital Optical Monitoring (DOM) data")
@click.option('--verbose', is_flag=True, help="Enable verbose output")
def eeprom(interfacename, dump_dom, verbose):
    """Show interface transceiver EEPROM information"""

    cmd = "sudo sfputil show eeprom"

    if dump_dom:
        cmd += " --dom"

    if interfacename is not None:
        if get_interface_mode() == "alias":
            interfacename = iface_alias_converter.alias_to_name(interfacename)

        cmd += " -p {}".format(interfacename)

    run_command(cmd, display_cmd=verbose)


@transceiver.command()
@click.argument('interfacename', required=False)
@click.option('--verbose', is_flag=True, help="Enable verbose output")
def lpmode(interfacename, verbose):
    """Show interface transceiver low-power mode status"""

    cmd = "sudo sfputil show lpmode"

    if interfacename is not None:
        if get_interface_mode() == "alias":
            interfacename = iface_alias_converter.alias_to_name(interfacename)

        cmd += " -p {}".format(interfacename)

    run_command(cmd, display_cmd=verbose)

@transceiver.command()
@click.argument('interfacename', required=False)
@click.option('--verbose', is_flag=True, help="Enable verbose output")
def presence(interfacename, verbose):
    """Show interface transceiver presence"""

    cmd = "sudo sfputil show presence"

    if interfacename is not None:
        if get_interface_mode() == "alias":
            interfacename = iface_alias_converter.alias_to_name(interfacename)

        cmd += " -p {}".format(interfacename)

    run_command(cmd, display_cmd=verbose)


@interfaces.command()
@click.argument('interfacename', required=False)
@click.option('--verbose', is_flag=True, help="Enable verbose output")
def description(interfacename, verbose):
    """Show interface status, protocol and description"""

    cmd = "intfutil description"

    if interfacename is not None:
        if get_interface_mode() == "alias":
            interfacename = iface_alias_converter.alias_to_name(interfacename)

        cmd += " {}".format(interfacename)

    run_command(cmd, display_cmd=verbose)


@interfaces.command()
@click.argument('interfacename', required=False)
@click.option('--verbose', is_flag=True, help="Enable verbose output")
def status(interfacename, verbose):
    """Show Interface status information"""

    cmd = "intfutil status"

    if interfacename is not None:
        if get_interface_mode() == "alias":
            interfacename = iface_alias_converter.alias_to_name(interfacename)

        cmd += " {}".format(interfacename)

    run_command(cmd, display_cmd=verbose)


# 'counters' subcommand ("show interfaces counters")
@interfaces.command()
@click.option('-a', '--printall', is_flag=True)
@click.option('-c', '--clear', is_flag=True)
@click.option('-p', '--period')
@click.option('--verbose', is_flag=True, help="Enable verbose output")
def counters(period, printall, clear, verbose):
    """Show interface counters"""

    cmd = "portstat"

    if clear:
        cmd += " -c"
    else:
        if printall:
            cmd += " -a"
        if period is not None:
            cmd += " -p {}".format(period)

    run_command(cmd, display_cmd=verbose)

# 'portchannel' subcommand ("show interfaces portchannel")
@interfaces.command()
@click.option('--verbose', is_flag=True, help="Enable verbose output")
def portchannel(verbose):
    """Show PortChannel information"""
    cmd = "teamshow"
    run_command(cmd, display_cmd=verbose)

#
# 'pfc' group ("show pfc ...")
#

@cli.group(cls=AliasedGroup, default_if_no_args=False)
def pfc():
    """Show details of the priority-flow-control (pfc) """
    pass

# 'counters' subcommand ("show interfaces pfccounters")
@pfc.command()
@click.option('-c', '--clear', is_flag=True)
@click.option('--verbose', is_flag=True, help="Enable verbose output")
def counters(clear, verbose):
    """Show pfc counters"""

    cmd = "pfcstat"

    if clear:
        cmd += " -c"

    run_command(cmd, display_cmd=verbose)

# 'naming_mode' subcommand ("show interfaces naming_mode")
@interfaces.command()
@click.option('--verbose', is_flag=True, help="Enable verbose output")
def naming_mode(verbose):
    """Show interface naming_mode status"""

    click.echo(get_interface_mode())


#
# 'watermark' group ("show watermark telemetry interval")
#

@cli.group(cls=AliasedGroup, default_if_no_args=False)
def watermark():
    """Show details of watermark """
    pass

@watermark.group()
def telemetry():
    """Show watermark telemetry info"""
    pass

@telemetry.command('interval')
def show_tm_interval():
    """Show telemetry interval"""
    command = 'watermarkcfg --show-interval'
    run_command(command)


#
# 'queue' group ("show queue ...")
#

@cli.group(cls=AliasedGroup, default_if_no_args=False)
def queue():
    """Show details of the queues """
    pass

# 'queuecounters' subcommand ("show queue counters")
@queue.command()
@click.argument('interfacename', required=False)
@click.option('-c', '--clear', is_flag=True)
@click.option('--verbose', is_flag=True, help="Enable verbose output")
def counters(interfacename, clear, verbose):
    """Show queue counters"""

    cmd = "queuestat"

    if interfacename is not None:
        if get_interface_mode() == "alias":
            interfacename = iface_alias_converter.alias_to_name(interfacename)

    if clear:
        cmd += " -c"
    else:
        if interfacename is not None:
            cmd += " -p {}".format(interfacename)

    run_command(cmd, display_cmd=verbose)

# watermarks subcommands ("show queue watermarks|persistent-watermarks")

@queue.group()
def watermark():
    """Show queue user WM"""
    pass

@watermark.command('unicast')
def wm_q_uni():
    """Show user WM for unicast queues"""
    command = 'watermarkstat -t q_shared_uni'
    run_command(command)

@watermark.command('multicast')
def wm_q_multi():
    """Show user WM for multicast queues"""
    command = 'watermarkstat -t q_shared_multi'
    run_command(command)

@queue.group(name='persistent-watermark')
def persistent_watermark():
    """Show queue persistent WM"""
    pass

@persistent_watermark.command('unicast')
def pwm_q_uni():
    """Show persistent WM for persistent queues"""
    command = 'watermarkstat -p -t q_shared_uni'
    run_command(command)

@persistent_watermark.command('multicast')
def pwm_q_multi():
    """Show persistent WM for multicast queues"""
    command = 'watermarkstat -p -t q_shared_multi'
    run_command(command)


#
# 'priority-group' group ("show priority-group ...")
#

@cli.group(name='priority-group', cls=AliasedGroup, default_if_no_args=False)
def priority_group():
    """Show details of the PGs """


@priority_group.group()
def watermark():
    """Show priority_group user WM"""
    pass

@watermark.command('headroom')
def wm_pg_headroom():
    """Show user headroom WM for pg"""
    command = 'watermarkstat -t pg_headroom'
    run_command(command)

@watermark.command('shared')
def wm_pg_shared():
    """Show user shared WM for pg"""
    command = 'watermarkstat -t pg_shared'
    run_command(command)

@priority_group.group(name='persistent-watermark')
def persistent_watermark():
    """Show queue persistent WM"""
    pass

@persistent_watermark.command('headroom')
def pwm_pg_headroom():
    """Show persistent headroom WM for pg"""
    command = 'watermarkstat -p -t pg_headroom'
    run_command(command)

@persistent_watermark.command('shared')
def pwm_pg_shared():
    """Show persistent shared WM for pg"""
    command = 'watermarkstat -p -t pg_shared'
    run_command(command)

#
# 'pfc' group ###
#

@interfaces.group(cls=AliasedGroup, default_if_no_args=False)
def pfc():
    """Show PFC information"""
    pass


#
# 'pfc status' command ###
#

@pfc.command()
@click.argument('interface', type=click.STRING, required=False)
def status(interface):
    """Show PFC information"""
    if interface is None:
        interface = ""

    run_command("pfc show asymmetric {0}".format(interface))


#
# 'mac' command ("show mac ...")
#

@cli.command()
@click.option('-v', '--vlan')
@click.option('-p', '--port')
@click.option('--verbose', is_flag=True, help="Enable verbose output")
def mac(vlan, port, verbose):
    """Show MAC (FDB) entries"""

    cmd = "fdbshow"

    if vlan is not None:
        cmd += " -v {}".format(vlan)

    if port is not None:
        cmd += " -p {}".format(port)

    run_command(cmd, display_cmd=verbose)

#
# 'ip' group ("show ip ...")
#

# This group houses IP (i.e., IPv4) commands and subgroups
@cli.group()
def ip():
    """Show IP (IPv4) commands"""
    pass


#
# 'route' subcommand ("show ip route")
#

@ip.command()
@click.argument('ipaddress', required=False)
@click.option('--verbose', is_flag=True, help="Enable verbose output")
def route(ipaddress, verbose):
    """Show IP (IPv4) routing table"""
    cmd = 'sudo vtysh -c "show ip route'

    if ipaddress is not None:
        cmd += ' {}'.format(ipaddress)

    cmd += '"'

    run_command(cmd, display_cmd=verbose)

# 'protocol' command
@ip.command()
@click.option('--verbose', is_flag=True, help="Enable verbose output")
def protocol(verbose):
    """Show IPv4 protocol information"""
    cmd = 'sudo vtysh -c "show ip protocol"'
    run_command(cmd, display_cmd=verbose)


#
# 'ipv6' group ("show ipv6 ...")
#

# This group houses IPv6-related commands and subgroups
@cli.group()
def ipv6():
    """Show IPv6 commands"""
    pass


#
# 'route' subcommand ("show ipv6 route")
#

@ipv6.command()
@click.argument('ipaddress', required=False)
@click.option('--verbose', is_flag=True, help="Enable verbose output")
def route(ipaddress, verbose):
    """Show IPv6 routing table"""
    cmd = 'sudo vtysh -c "show ipv6 route'

    if ipaddress is not None:
        cmd += ' {}'.format(ipaddress)

    cmd += '"'

    run_command(cmd, display_cmd=verbose)


# 'protocol' command
@ipv6.command()
@click.option('--verbose', is_flag=True, help="Enable verbose output")
def protocol(verbose):
    """Show IPv6 protocol information"""
    cmd = 'sudo vtysh -c "show ipv6 protocol"'
    run_command(cmd, display_cmd=verbose)


#
# Inserting BGP functionality into cli's show parse-chain.
# BGP commands are determined by the routing-stack being elected.
#
if routing_stack == "quagga":
    from .bgp_quagga_v4 import bgp
    ip.add_command(bgp)
    from .bgp_quagga_v6 import bgp
    ipv6.add_command(bgp)
elif routing_stack == "frr":
    @cli.command()
    @click.argument('bgp_args', nargs = -1, required = False)
    @click.option('--verbose', is_flag=True, help="Enable verbose output")
    def bgp(bgp_args, verbose):
        """BGP information"""
        bgp_cmd = "show bgp"
        for arg in bgp_args:
            bgp_cmd += " " + str(arg)
        cmd = 'sudo vtysh -c "{}"'.format(bgp_cmd)
        run_command(cmd, display_cmd=verbose)


#
# 'lldp' group ("show lldp ...")
#

@cli.group(cls=AliasedGroup, default_if_no_args=False)
def lldp():
    """LLDP (Link Layer Discovery Protocol) information"""
    pass

# Default 'lldp' command (called if no subcommands or their aliases were passed)
@lldp.command()
@click.argument('interfacename', required=False)
@click.option('--verbose', is_flag=True, help="Enable verbose output")
def neighbors(interfacename, verbose):
    """Show LLDP neighbors"""
    cmd = "sudo lldpctl"

    if interfacename is not None:
        if get_interface_mode() == "alias":
            interfacename = iface_alias_converter.alias_to_name(interfacename)

        cmd += " {}".format(interfacename)

    run_command(cmd, display_cmd=verbose)

# 'table' subcommand ("show lldp table")
@lldp.command()
@click.option('--verbose', is_flag=True, help="Enable verbose output")
def table(verbose):
    """Show LLDP neighbors in tabular format"""
    cmd = "sudo lldpshow"
    run_command(cmd, display_cmd=verbose)

#
# 'platform' group ("show platform ...")
#

@cli.group(cls=AliasedGroup, default_if_no_args=False)
def platform():
    """Show platform-specific hardware info"""
    pass

version_info = sonic_platform.get_sonic_version_info()
if (version_info and version_info.get('asic_type') == 'mellanox'):
    platform.add_command(mlnx.mlnx)

# 'summary' subcommand ("show platform summary")
@platform.command()
def summary():
    """Show hardware platform information"""
    machine_info = sonic_platform.get_machine_info()
    platform = sonic_platform.get_platform_info(machine_info)

    config_db = ConfigDBConnector()
    config_db.connect()
    data = config_db.get_table('DEVICE_METADATA')

    try:
        hwsku = data['localhost']['hwsku']
    except KeyError:
        hwsku = "Unknown"

    version_info = sonic_platform.get_sonic_version_info()
    asic_type = version_info['asic_type']

    click.echo("Platform: {}".format(platform))
    click.echo("HwSKU: {}".format(hwsku))
    click.echo("ASIC: {}".format(asic_type))

# 'syseeprom' subcommand ("show platform syseeprom")
@platform.command()
@click.option('--verbose', is_flag=True, help="Enable verbose output")
def syseeprom(verbose):
    """Show system EEPROM information"""
    cmd = "sudo decode-syseeprom"
    run_command(cmd, display_cmd=verbose)

# 'psustatus' subcommand ("show platform psustatus")
@platform.command()
@click.option('-i', '--index', default=-1, type=int, help="the index of PSU")
@click.option('--verbose', is_flag=True, help="Enable verbose output")
def psustatus(index, verbose):
    """Show PSU status information"""
    cmd = "sudo psuutil status"

    if index >= 0:
        cmd += " -i {}".format(index)

    run_command(cmd, display_cmd=verbose)

#
# 'logging' command ("show logging")
#

@cli.command()
@click.argument('process', required=False)
@click.option('-l', '--lines')
@click.option('-f', '--follow', is_flag=True)
@click.option('--verbose', is_flag=True, help="Enable verbose output")
def logging(process, lines, follow, verbose):
    """Show system log"""
    if follow:
        cmd = "sudo tail -F /var/log/syslog"
        run_command(cmd, display_cmd=verbose)
    else:
        if os.path.isfile("/var/log/syslog.1"):
            cmd = "sudo cat /var/log/syslog.1 /var/log/syslog"
        else:
            cmd = "sudo cat /var/log/syslog"

        if process is not None:
            cmd += " | grep '{}'".format(process)

        if lines is not None:
            cmd += " | tail -{}".format(lines)

        run_command(cmd, display_cmd=verbose)


#
# 'version' command ("show version")
#

@cli.command()
def version():
    """Show version information"""
    version_info = sonic_platform.get_sonic_version_info()

    click.echo("SONiC Software Version: SONiC.{}".format(version_info['build_version']))
    click.echo("Distribution: Debian {}".format(version_info['debian_version']))
    click.echo("Kernel: {}".format(version_info['kernel_version']))
    click.echo("Build commit: {}".format(version_info['commit_id']))
    click.echo("Build date: {}".format(version_info['build_date']))
    click.echo("Built by: {}".format(version_info['built_by']))

    click.echo("\nDocker images:")
    cmd = 'sudo docker images --format "table {{.Repository}}\\t{{.Tag}}\\t{{.ID}}\\t{{.Size}}"'
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    click.echo(p.stdout.read())

#
# 'environment' command ("show environment")
#

@cli.command()
@click.option('--verbose', is_flag=True, help="Enable verbose output")
def environment(verbose):
    """Show environmentals (voltages, fans, temps)"""
    cmd = "sudo sensors"
    run_command(cmd, display_cmd=verbose)


#
# 'processes' group ("show processes ...")
#

@cli.group(cls=AliasedGroup, default_if_no_args=False)
def processes():
    """Display process information"""
    pass

@processes.command()
@click.option('--verbose', is_flag=True, help="Enable verbose output")
def summary(verbose):
    """Show processes info"""
    # Run top batch mode to prevent unexpected newline after each newline
    cmd = "ps -eo pid,ppid,cmd,%mem,%cpu "
    run_command(cmd, display_cmd=verbose)


# 'cpu' subcommand ("show processes cpu")
@processes.command()
@click.option('--verbose', is_flag=True, help="Enable verbose output")
def cpu(verbose):
    """Show processes CPU info"""
    # Run top in batch mode to prevent unexpected newline after each newline
    cmd = "top -bn 1 -o %CPU"
    run_command(cmd, display_cmd=verbose)

# 'memory' subcommand
@processes.command()
@click.option('--verbose', is_flag=True, help="Enable verbose output")
def memory(verbose):
    """Show processes memory info"""
    # Run top batch mode to prevent unexpected newline after each newline
    cmd = "top -bn 1 -o %MEM"
    run_command(cmd, display_cmd=verbose)

#
# 'users' command ("show users")
#

@cli.command()
@click.option('--verbose', is_flag=True, help="Enable verbose output")
def users(verbose):
    """Show users"""
    cmd = "who"
    run_command(cmd, display_cmd=verbose)


#
# 'techsupport' command ("show techsupport")
#

@cli.command()
@click.option('--verbose', is_flag=True, help="Enable verbose output")
def techsupport(verbose):
    """Gather information for troubleshooting"""
    cmd = "sudo generate_dump -v"
    run_command(cmd, display_cmd=verbose)


#
# 'runningconfiguration' group ("show runningconfiguration")
#

@cli.group(cls=AliasedGroup, default_if_no_args=False)
def runningconfiguration():
    """Show current running configuration information"""
    pass


# 'all' subcommand ("show runningconfiguration all")
@runningconfiguration.command()
@click.option('--verbose', is_flag=True, help="Enable verbose output")
def all(verbose):
    """Show full running configuration"""
    cmd = "sonic-cfggen -d --print-data"
    run_command(cmd, display_cmd=verbose)


# 'bgp' subcommand ("show runningconfiguration bgp")
@runningconfiguration.command()
@click.option('--verbose', is_flag=True, help="Enable verbose output")
def bgp(verbose):
    """Show BGP running configuration"""
    cmd = 'sudo vtysh -c "show running-config"'
    run_command(cmd, display_cmd=verbose)


# 'interfaces' subcommand ("show runningconfiguration interfaces")
@runningconfiguration.command()
@click.argument('interfacename', required=False)
@click.option('--verbose', is_flag=True, help="Enable verbose output")
def interfaces(interfacename, verbose):
    """Show interfaces running configuration"""
    cmd = "cat /etc/network/interfaces"

    if interfacename is not None:
        cmd += " | grep {} -A 4".format(interfacename)

    run_command(cmd, display_cmd=verbose)


# 'snmp' subcommand ("show runningconfiguration snmp")
@runningconfiguration.command()
@click.argument('server', required=False)
@click.option('--verbose', is_flag=True, help="Enable verbose output")
def snmp(server, verbose):
    """Show SNMP information"""
    cmd = "sudo docker exec snmp cat /etc/snmp/snmpd.conf"

    if server is not None:
        cmd += " | grep -i agentAddress"

    run_command(cmd, display_cmd=verbose)


# 'ntp' subcommand ("show runningconfiguration ntp")
@runningconfiguration.command()
@click.option('--verbose', is_flag=True, help="Enable verbose output")
def ntp(verbose):
    """Show NTP running configuration"""
    cmd = "cat /etc/ntp.conf"
    run_command(cmd, display_cmd=verbose)


#
# 'startupconfiguration' group ("show startupconfiguration ...")
#

@cli.group(cls=AliasedGroup, default_if_no_args=False)
def startupconfiguration():
    """Show startup configuration information"""
    pass


# 'bgp' subcommand  ("show startupconfiguration bgp")
@startupconfiguration.command()
@click.option('--verbose', is_flag=True, help="Enable verbose output")
def bgp(verbose):
    """Show BGP startup configuration"""
    cmd = "sudo docker ps | grep bgp | awk '{print$2}' | cut -d'-' -f3 | cut -d':' -f1"
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
    result = proc.stdout.read().rstrip()
    click.echo("Routing-Stack is: {}".format(result))
    if result == "quagga":
        run_command('sudo docker exec bgp cat /etc/quagga/bgpd.conf', display_cmd=verbose)
    elif result == "frr":
        run_command('sudo docker exec bgp cat /etc/frr/bgpd.conf', display_cmd=verbose)
    elif result == "gobgp":
        run_command('sudo docker exec bgp cat /etc/gpbgp/bgpd.conf', display_cmd=verbose)
    else:
        click.echo("Unidentified routing-stack")

#
# 'ntp' command ("show ntp")
#

@cli.command()
@click.option('--verbose', is_flag=True, help="Enable verbose output")
def ntp(verbose):
    """Show NTP information"""
    cmd = "ntpq -p -n"
    run_command(cmd, display_cmd=verbose)


#
# 'uptime' command ("show uptime")
#

@cli.command()
@click.option('--verbose', is_flag=True, help="Enable verbose output")
def uptime(verbose):
    """Show system uptime"""
    cmd = "uptime -p"
    run_command(cmd, display_cmd=verbose)

@cli.command()
@click.option('--verbose', is_flag=True, help="Enable verbose output")
def clock(verbose):
    """Show date and time"""
    cmd ="date"
    run_command(cmd, display_cmd=verbose)

@cli.command('system-memory')
@click.option('--verbose', is_flag=True, help="Enable verbose output")
def system_memory(verbose):
    """Show memory information"""
    cmd = "free -m"
    run_command(cmd, display_cmd=verbose)

@cli.group(cls=AliasedGroup, default_if_no_args=False)
def vlan():
    """Show VLAN information"""
    pass

@vlan.command()
@click.option('--verbose', is_flag=True, help="Enable verbose output")
def brief(verbose):
    """Show all bridge information"""
    config_db = ConfigDBConnector()
    config_db.connect()
    header = ['VLAN ID', 'IP Address', 'Ports', 'Port Tagging', 'DHCP Helper Address']
    body = []
    vlan_keys = []

    # Fetching data from config_db for VLAN, VLAN_INTERFACE and VLAN_MEMBER
    vlan_dhcp_helper_data = config_db.get_table('VLAN')
    vlan_ip_data = config_db.get_table('VLAN_INTERFACE')
    vlan_ports_data = config_db.get_table('VLAN_MEMBER')

    vlan_keys = natsorted(vlan_dhcp_helper_data.keys())

    # Defining dictionaries for DHCP Helper address, Interface Gateway IP,
    # VLAN ports and port tagging
    vlan_dhcp_helper_dict = {}
    vlan_ip_dict = {}
    vlan_ports_dict = {}
    vlan_tagging_dict = {}

    # Parsing DHCP Helpers info
    for key in natsorted(vlan_dhcp_helper_data.keys()):
        try:
            if vlan_dhcp_helper_data[key]['dhcp_servers']:
                vlan_dhcp_helper_dict[str(key.strip('Vlan'))] = vlan_dhcp_helper_data[key]['dhcp_servers']
        except KeyError:
            vlan_dhcp_helper_dict[str(key.strip('Vlan'))] = " "
            pass

    # Parsing VLAN Gateway info
    for key in natsorted(vlan_ip_data.keys()):
        interface_key = str(key[0].strip("Vlan"))
        interface_value = str(key[1])
        if interface_key in vlan_ip_dict:
            vlan_ip_dict[interface_key].append(interface_value)
        else:
            vlan_ip_dict[interface_key] = [interface_value]

    # Parsing VLAN Ports info
    for key in natsorted(vlan_ports_data.keys()):
        ports_key = str(key[0].strip("Vlan"))
        ports_value = str(key[1])
        ports_tagging = vlan_ports_data[key]['tagging_mode']
        if ports_key in vlan_ports_dict:
            vlan_ports_dict[ports_key].append(ports_value)
        else:
            vlan_ports_dict[ports_key] = [ports_value]
        if ports_key in vlan_tagging_dict:
            vlan_tagging_dict[ports_key].append(ports_tagging)
        else:
            vlan_tagging_dict[ports_key] = [ports_tagging]

    # Printing the following dictionaries in tablular forms:
    # vlan_dhcp_helper_dict={}, vlan_ip_dict = {}, vlan_ports_dict = {}
    # vlan_tagging_dict = {}
    for key in natsorted(vlan_dhcp_helper_dict.keys()):
        if key not in vlan_ip_dict:
            ip_address = ""
        else:
            ip_address = ','.replace(',', '\n').join(vlan_ip_dict[key])
        if key not in vlan_ports_dict:
            vlan_ports = ""
        else:
            vlan_ports = ','.replace(',', '\n').join((vlan_ports_dict[key]))
        if key not in vlan_dhcp_helper_dict:
            dhcp_helpers = ""
        else:
            dhcp_helpers = ','.replace(',', '\n').join(vlan_dhcp_helper_dict[key])
        if key not in vlan_tagging_dict:
            vlan_tagging = ""
        else:
            vlan_tagging = ','.replace(',', '\n').join((vlan_tagging_dict[key]))
        body.append([key, ip_address, vlan_ports, vlan_tagging, dhcp_helpers])
    click.echo(tabulate(body, header, tablefmt="grid"))

@vlan.command()
@click.option('-s', '--redis-unix-socket-path', help='unix socket path for redis connection')
def config(redis_unix_socket_path):
    kwargs = {}
    if redis_unix_socket_path:
        kwargs['unix_socket_path'] = redis_unix_socket_path
    config_db = ConfigDBConnector(**kwargs)
    config_db.connect(wait_for_init=False)
    data = config_db.get_table('VLAN')
    keys = data.keys()

    def tablelize(keys, data):
        table = []

        for k in keys:
            for m in data[k].get('members', []):
                r = []
                r.append(k)
                r.append(data[k]['vlanid'])
                if get_interface_mode() == "alias":
                    alias = iface_alias_converter.name_to_alias(m)
                    r.append(alias)
                else:
                    r.append(m)

                entry = config_db.get_entry('VLAN_MEMBER', (k, m))
                mode = entry.get('tagging_mode')
                if mode == None:
                    r.append('?')
                else:
                    r.append(mode)

                table.append(r)

        return table

    header = ['Name', 'VID', 'Member', 'Mode']
    click.echo(tabulate(tablelize(keys, data), header))

@cli.command('services')
def services():
    """Show all daemon services"""
    cmd = "sudo docker ps --format '{{.Names}}'"
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
    while True:
        line = proc.stdout.readline()
        if line != '':
                print(line.rstrip()+'\t'+"docker")
                print("---------------------------")
                cmd = "sudo docker exec {} ps aux | sed '$d'".format(line.rstrip())
                proc1 = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
                print proc1.stdout.read()
        else:
                break

@cli.command()
def aaa():
    """Show AAA configuration"""
    config_db = ConfigDBConnector()
    config_db.connect()
    data = config_db.get_table('AAA')
    output = ''

    aaa = {
        'authentication': {
            'login': 'local (default)',
            'failthrough': 'True (default)',
            'fallback': 'True (default)'
        }
    }
    if 'authentication' in data:
        aaa['authentication'].update(data['authentication'])
    for row in aaa:
        entry = aaa[row]
        for key in entry:
            output += ('AAA %s %s %s\n' % (row, key, str(entry[key])))
    click.echo(output)


@cli.command()
def tacacs():
    """Show TACACS+ configuration"""
    config_db = ConfigDBConnector()
    config_db.connect()
    output = ''
    data = config_db.get_table('TACPLUS')

    tacplus = {
        'global': {
            'auth_type': 'pap (default)',
            'timeout': '5 (default)',
            'passkey': '<EMPTY_STRING> (default)'
        }
    }
    if 'global' in data:
        tacplus['global'].update(data['global'])
    for key in tacplus['global']:
        output += ('TACPLUS global %s %s\n' % (str(key), str(tacplus['global'][key])))

    data = config_db.get_table('TACPLUS_SERVER')
    if data != {}:
        for row in data:
            entry = data[row]
            output += ('\nTACPLUS_SERVER address %s\n' % row)
            for key in entry:
                output += ('               %s %s\n' % (key, str(entry[key])))
    click.echo(output)


#
# 'mirror' group ###
#

@cli.group(cls=AliasedGroup, default_if_no_args=False)
def mirror():
    """Show mirroring (Everflow) information"""
    pass


# 'session' subcommand  ("show mirror session")
@mirror.command()
@click.argument('session_name', required=False)
@click.option('--verbose', is_flag=True, help="Enable verbose output")
def session(session_name, verbose):
    """Show existing everflow sessions"""
    cmd = "acl-loader show session"

    if session_name is not None:
        cmd += " {}".format(session_name)

    run_command(cmd, display_cmd=verbose)


#
# 'acl' group ###
#

@cli.group(cls=AliasedGroup, default_if_no_args=False)
def acl():
    """Show ACL related information"""
    pass


# 'rule' subcommand  ("show acl rule")
@acl.command()
@click.argument('table_name', required=False)
@click.argument('rule_id', required=False)
@click.option('--verbose', is_flag=True, help="Enable verbose output")
def rule(table_name, rule_id, verbose):
    """Show existing ACL rules"""
    cmd = "acl-loader show rule"

    if table_name is not None:
        cmd += " {}".format(table_name)

    if rule_id is not None:
        cmd += " {}".format(rule_id)

    run_command(cmd, display_cmd=verbose)


# 'table' subcommand  ("show acl table")
@acl.command()
@click.argument('table_name', required=False)
@click.option('--verbose', is_flag=True, help="Enable verbose output")
def table(table_name, verbose):
    """Show existing ACL tables"""
    cmd = "acl-loader show table"

    if table_name is not None:
        cmd += " {}".format(table_name)

    run_command(cmd, display_cmd=verbose)


#
# 'ecn' command ("show ecn")
#
@cli.command('ecn')
def ecn():
    """Show ECN configuration"""
    cmd = "ecnconfig -l"
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
    click.echo(proc.stdout.read())


# 'mmu' command ("show mmu")
#
@cli.command('mmu')
def mmu():
    """Show mmu configuration"""
    cmd = "mmuconfig -l"
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
    click.echo(proc.stdout.read())


#
# 'reboot-cause' command ("show reboot-cause")
#
@cli.command('reboot-cause')
def reboot_cause():
    """Show cause of most recent reboot"""
    PREVIOUS_REBOOT_CAUSE_FILE = "/var/cache/sonic/previous-reboot-cause.txt"

    # At boot time, PREVIOUS_REBOOT_CAUSE_FILE is generated based on
    # the contents of the 'reboot cause' file as it was left when the device
    # went down for reboot. This file should always be created at boot,
    # but check first just in case it's not present.
    if not os.path.isfile(PREVIOUS_REBOOT_CAUSE_FILE):
        click.echo("Unable to determine cause of previous reboot\n")
    else:
        cmd = "cat {}".format(PREVIOUS_REBOOT_CAUSE_FILE)
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
        click.echo(proc.stdout.read())


#
# 'line' command ("show line")
#
@cli.command('line')
def line():
    """Show all /dev/ttyUSB lines and their info"""
    cmd = "consutil show"
    run_command(cmd, display_cmd=verbose)
    return


@cli.group(cls=AliasedGroup, default_if_no_args=False)
def warm_restart():
    """Show warm restart configuration and state"""
    pass

@warm_restart.command()
@click.option('-s', '--redis-unix-socket-path', help='unix socket path for redis connection')
def state(redis_unix_socket_path):
    """Show warm restart state"""
    kwargs = {}
    if redis_unix_socket_path:
        kwargs['unix_socket_path'] = redis_unix_socket_path

    data = {}
    db = SonicV2Connector(host='127.0.0.1')
    db.connect(db.STATE_DB, False)   # Make one attempt only

    TABLE_NAME_SEPARATOR = '|'
    prefix = 'WARM_RESTART_TABLE' + TABLE_NAME_SEPARATOR
    _hash = '{}{}'.format(prefix, '*')
    table_keys = db.keys(db.STATE_DB, _hash)

    def remove_prefix(text, prefix):
        if text.startswith(prefix):
            return text[len(prefix):]
        return text

    table = []
    for tk in table_keys:
        entry = db.get_all(db.STATE_DB, tk)
        r = []
        r.append(remove_prefix(tk, prefix))
        r.append(entry['restore_count'])

        if 'state' not in  entry:
            r.append("")
        else:
            r.append(entry['state'])

        table.append(r)

    header = ['name', 'restore_count', 'state']
    click.echo(tabulate(table, header))

@warm_restart.command()
@click.option('-s', '--redis-unix-socket-path', help='unix socket path for redis connection')
def config(redis_unix_socket_path):
    """Show warm restart config"""
    kwargs = {}
    if redis_unix_socket_path:
        kwargs['unix_socket_path'] = redis_unix_socket_path
    config_db = ConfigDBConnector(**kwargs)
    config_db.connect(wait_for_init=False)
    data = config_db.get_table('WARM_RESTART')
    keys = data.keys()

    def tablelize(keys, data):
        table = []

        for k in keys:
            r = []
            r.append(k)

            if 'enable' not in  data[k]:
                r.append("false")
            else:
                r.append(data[k]['enable'])

            if 'neighsyncd_timer' in  data[k]:
                r.append("neighsyncd_timer")
                r.append(data[k]['neighsyncd_timer'])
            else:
                r.append("NULL")
                r.append("NULL")

            table.append(r)

        return table

    header = ['name', 'enable', 'timer_name', 'timer_duration']
    click.echo(tabulate(tablelize(keys, data), header))



def run_command_save(command, display_cmd=False):
    """run a command and save the output"""
    if display_cmd:
        click.echo(click.style("Command: ", fg='cyan') + click.style(command, fg='green'))
    try:
        proc = subprocess.Popen(command,
                                stdout=subprocess.PIPE,
                                shell=True,
                                stderr=subprocess.STDOUT)
        stdout = proc.communicate()[0]
        proc.wait()
        result = stdout.rstrip('\n')
    except OSError, e:
        raise OSError("Error running command")
    return (result)


# Open ifconfig textfsm template and store as template
def get_template_info(templatename):
    """
    The function is used to open the textfsm templates
    """
    with open('/usr/lib/python2.7/dist-packages/show/' + templatename, 'r') as f:
        template = textfsm.TextFSM(f)
        return template


# Parse ifconfig string with textfsm template and store as data
def parse_template(template, show_command_info):
    """
    This function uses the textFSM template and the string you want to parse.
    It returns the data it parses from the Regex in the TextFSM template.
    """
    data = template.ParseText(show_command_info)
    return data


def remove_headers(template):
    """
    Create list of item headers and remove the 1st header using the template.header
    int_header has Interfaces as first item in list so we will remove it as it is not needed.
    """
    get_template_headers = template.header
    del get_template_headers[0]
    return get_template_headers


def create_temp_dict(if_data):
    """
    Create interface dictionary from if_data with each interface as a key
    Return a dictionary
    """
    temp_dict = {element[0]: element[1:] for element in if_data}
    return temp_dict


def create_interface_dict(temp_dict, get_template_headers):
    """
    Create dictionary within dictionary with outer key being interface
    and many inner dictionaries matching values of FSM.
    Return a dictionary
    """
    for k, v in temp_dict.iteritems():
        temp_dict[k] = dict(zip(get_template_headers, v))
    return temp_dict


def create_if_int_keys(if_dict):
    """
    Get a list of interface keys from if_interface keys
    Return a list
    """
    get_if_int_keys = []
    for if_keys in if_dict:
        get_if_int_keys.append(if_keys)
    return get_if_int_keys


def convert_mask(get_if_int_keys, if_dict):
    """
    Convert subnet mask from dotted decimal to cidr from interface keys list and interface dictionary
    return: show interface summary dictionary
    """
    for item in get_if_int_keys:
        if if_dict[item]['IPv4Mask'].startswith('2'):
            if_dict[item]["IPv4Mask"] = IPAddress(if_dict[item]["IPv4Mask"]).netmask_bits()
            if_dict[item]["IPv4Mask"] = "/" + str(if_dict[item]["IPv4Mask"])
    return if_dict

def remove_unused_lldp_table_headers(lldp_table_dict):
    """
    Remove headers: "-----------" from lldp table dictionary
    """
    if "-----------" in lldp_table_dict.keys():
        del lldp_table_dict["-----------"]
    return lldp_table_dict


def remove_unused_lldp_table_dict_keys(lldp_table_dict):
    """
    Remove unused lldp table keys "LocalPort" and "Capability"
    return: lldp table dictionary
    """
    if "Capability" in lldp_table_dict.keys():
        del lldp_table_dict["Capability"]
    elif "LocalPort" in lldp_table_dict.keys():
        del lldp_table_dict['LocalPort']
    return lldp_table_dict


def merge(x, y):
    # store a copy of x, but overwrite with y's values where applicable
    merged = dict(x, **y)

    xkeys = x.keys()

    # if the value of merged[key] was overwritten with y[key]'s value
    # then we need to put back any missing x[key] values
    for key in xkeys:
        # if this key is a dictionary, recurse
        if type(x[key]) is types.DictType and y.has_key(key):
            merged[key] = merge(x[key], y[key])

    return merged


def return_show_ip_int_brief(final_dict):
    """
    This is to print the final output of the command to the cli
    :param final_dict:
    :return: CLI command output
    """
    default_dict = dict.fromkeys(['RXOverruns',
                                  'RXPackets',
                                  'RXHRTraffic',
                                  'TXPackets',
                                  'TXErrors',
                                  'RXBytes',
                                  'IPv6GlobalAddress',
                                  'Lanes',
                                  'IPv4Mask',
                                  'TXDropped',
                                  'TXQueuelen',
                                  'RXFrame',
                                  'RemotePortDescr',
                                  'TXOverruns',
                                  'Oper',
                                  'RXErrors',
                                  'Admin',
                                  'MTU',
                                  'RemotePortID',
                                  'Alias',
                                  'TXBytes',
                                  'IPv6LinkLocalAddress',
                                  'IPv4Address',
                                  'Capability',
                                  'RXDropped',
                                  'TXHRTraffic',
                                  'Collisions',
                                  'TXCarrier',
                                  'MAC',
                                  'IPv6HostAddress',
                                  'RemoteDevice',
                                  'Speed',
                                  'ComplianceCode',
                                  'Detected',
                                  'Identifier',
                                  'VendorName',
                                  'VendorRev'], '')

    header = ['Interface', 'Alias', 'IPv4Address', 'MTU', 'Speed', 'Oper', 'Admin', 'OpticPresent', 'OpticType', 'OpticModel',
              'Neighbor', 'NeighborPort']
    body = []
    for interface in natsorted(final_dict):
        body.append([interface,
                     final_dict[interface]['Alias'],
                     final_dict[interface]['IPv4Address'] + final_dict[interface]['IPv4Mask'],
                     final_dict[interface]['MTU'],
                     final_dict[interface]['Speed'],
                     final_dict[interface]['Admin'],
                     final_dict[interface]['Oper'],
                     final_dict[interface]['Detected'],
                     final_dict[interface]['Identifier'],
                     final_dict[interface]['ComplianceCode'],
                     final_dict[interface]['RemoteDevice'],
                     final_dict[interface]['RemotePortID'],
                     ])
    print(tabulate(body, header))


def delete_unused_key(dict):
    """
    Remove unused Key/Value pairs in the dictionary
    :param dict:
    :return:
    """
    del dict['LocalPort']
    del dict['Bridge']
    del dict['docker0']
    del dict['Total']
    return dict


def return_show_ifconfig(show_ifconfig, ifconfig_template):
    """
    Get IPAddress info from "show interface summary" and use the textfsm ifconfig_template
    to parse the output and create a dictionary
    :param show_ifconfig: This is the show interface summary output
    :param ifconfig_template: This is the ifconfig textfsm template
    :return: ifconfig_dict dictionary made from parsing the output with the textfsm template.
    """
    get_if_template = get_template_info(ifconfig_template)
    parse_if_template = parse_template(get_if_template, show_ifconfig)
    get_if_headers = remove_headers(get_if_template)
    temp_if_int_dict = create_temp_dict(parse_if_template)
    if_int_dict = create_interface_dict(temp_if_int_dict, get_if_headers)
    get_if_keys = create_if_int_keys(if_int_dict)
    ifconfig_dict = convert_mask(get_if_keys, if_int_dict)
    return ifconfig_dict


def return_show_int_status(show_int_status, interface_status_template):
    """
    Get interface info from show interface status and parse it with the textfsm template
    to create a dictionary
    :param show_ifconfig: This is the show interface status output
    :param ifconfig_template: This is the interface status textfsm template
    :return: show_int_status_dict dictionary made from parsing the output with the textfsm template.
    """
    get_int_status_template = get_template_info(interface_status_template)
    parse_int_status_template = parse_template(get_int_status_template, show_int_status)
    get_int_status_headers = remove_headers(get_int_status_template)
    temp_int_status_dict = create_temp_dict(parse_int_status_template)
    show_int_status_dict = create_interface_dict(temp_int_status_dict, get_int_status_headers)
    return show_int_status_dict


def return_show_lldp_table(show_lldp_table, lldp_table_template):
    """
    Get interface info from show lldp table and parse it with the textfsm template
    to create a dictionary
    :param show_lldp_table: This is the show lldp table output
    :param ifconfig_template: This is the lldp table textfsm template
    :return: show_lldp_table_dict dictionary made from parsing the output with the textfsm template.
    """
    get_lldp_table_template = get_template_info(lldp_table_template)
    parse_lldp_table_template = parse_template(get_lldp_table_template, show_lldp_table)
    get_lldp_table_headers = remove_headers(get_lldp_table_template)
    first_temp_lldp_table_dict = create_temp_dict(parse_lldp_table_template)
    delete_unused_lldp_table_headers = remove_unused_lldp_table_headers(first_temp_lldp_table_dict)
    second_temp_lldp_table_dict = create_interface_dict(first_temp_lldp_table_dict, get_lldp_table_headers)
    show_lldp_table_dict = remove_unused_lldp_table_dict_keys(second_temp_lldp_table_dict)
    return show_lldp_table_dict


def return_show_interface_tranceiver(show_int_transceiver, int_transceiver_template):
    """
    Get interface transceiver info from show interface transceiver eeprom and parse it with the textfsm template
    to create a dictionary
    :param show_int_transceiver: This is the show interface tranceiver eeprom output
    :param int_transceiver_template: This is the interface transceiver  textfsm template
    :return: show_int_transcevier_dict dictionary made from parsing the output with the textfsm template.
    """
    get_int_transceiver_template = get_template_info(int_transceiver_template)
    parse_int_transceiver_template = parse_template(get_int_transceiver_template, show_int_transceiver)
    get_int_transceiver_headers = remove_headers(get_int_transceiver_template)
    temp_int_transceiver_dict = create_temp_dict(parse_int_transceiver_template)
    show_int_transceiver_dict = create_interface_dict(temp_int_transceiver_dict, get_int_transceiver_headers)
    return show_int_transceiver_dict


def return_show_ip_interface_brief(if_dict, int_status_dict, lldp_table_dict, int_transceiver_dict):
    """
    This combines the four dictionaries into one which is used to create the output
    :param if_dict: This is the show int summary output dictionary that has been parsed by the show int summary testfsm template.
    :param int_status_dict: This is the show int status output dictionary that has been parsed by the show int status testfsm template.
    :param lldp_table_dict: This is the show lldp table output dictionary that has been parsed by the lldp table textfsm template.
    :param int_transceiver_dict: This is the show int transceiver eeprom output dictionary that has been parsed by the show int tranceiver eeprom textfsm template.
    :return: This returns the combined dictionary and sets any key with no values to an empty string.
    """
    default_dict = dict.fromkeys(['RXOverruns',
                                  'RXPackets',
                                  'RXHRTraffic',
                                  'TXPackets',
                                  'TXErrors',
                                  'RXBytes',
                                  'IPv6GlobalAddress',
                                  'Lanes',
                                  'IPv4Mask',
                                  'TXDropped',
                                  'TXQueuelen',
                                  'RXFrame',
                                  'RemotePortDescr',
                                  'TXOverruns',
                                  'Oper',
                                  'RXErrors',
                                  'Admin',
                                  'MTU',
                                  'RemotePortID',
                                  'Alias',
                                  'TXBytes',
                                  'IPv6LinkLocalAddress',
                                  'IPv4Address',
                                  'Capability',
                                  'RXDropped',
                                  'TXHRTraffic',
                                  'Collisions',
                                  'TXCarrier',
                                  'MAC',
                                  'IPv6HostAddress',
                                  'RemoteDevice',
                                  'Speed',
                                  'ComplianceCode',
                                  'Detected',
                                  'Identifier',
                                  'VendorName',
                                  'VendorRev'], '')
    combined_if_dict_and_int_status_dict = merge(if_dict, int_status_dict)
    combined_if_dict_and_lldp_table_dict = merge(if_dict, lldp_table_dict)
    temporary_combined_dict = merge(combined_if_dict_and_int_status_dict, combined_if_dict_and_lldp_table_dict)
    temp_combined_dict = merge(temporary_combined_dict, int_transceiver_dict)
    temp_combined_dict = delete_unused_key(temp_combined_dict)
    new_key_list = temp_combined_dict.keys()
    new_key_dict = dict.fromkeys(new_key_list, default_dict)
    temp_show_ip_int_brief_dict = merge(new_key_dict, temp_combined_dict)
    show_ip_int_brief_dict = return_show_ip_int_brief(temp_show_ip_int_brief_dict)
    return show_ip_int_brief_dict


def return_combined_commands(ifconfig, show_int_status, show_lldp_table, show_int_transceiver):
    """
    This returns the combined commands into one output for show ip interfaces.
    :param ifconfig: This is the show int summary dictionary parsed by it's textfsm template
    :param show_int_status: This is the show int status dictionary parsed by it's textfsm template
    :param show_lldp_table: This is the show lldp table dictionary parsed by it's textfsm template
    :param show_int_transceiver: This is the show int tranceiver eeprom dictionary parsed by it's textfsm template.
    :return: The combined output to the CLI.
    """
    if_dict = return_show_ifconfig(ifconfig, "ifconfig_template")
    int_status_dict = return_show_int_status(show_int_status, "interface_status_template")
    lldp_table_dict = return_show_lldp_table(show_lldp_table, "lldp_table_template")
    int_transceiver_dict = return_show_interface_tranceiver(show_int_transceiver, "int_transceiver_template")
    show_ip_int_brief = return_show_ip_interface_brief(if_dict, int_status_dict, lldp_table_dict, int_transceiver_dict)
    return (show_ip_int_brief)


@ip.command()
@click.option('--verbose', is_flag=True, help="Enable verbose output")
def interfaces(verbose):
    """Show ip interfaces command information"""
    ifconfig = run_command_save('show interface summary')
    show_int_status = run_command_save('show interface status')
    show_int_status = run_command_save('show interface status')
    show_lldp_table = run_command_save('show lldp table')
    show_int_transceiver = run_command_save('show interface transceiver eeprom')
    show_ip_int_brief = return_combined_commands(ifconfig, show_int_status, show_lldp_table, show_int_transceiver)
    click.echo(show_ip_int_brief)


if __name__ == '__main__':
    cli() 