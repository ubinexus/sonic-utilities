import configparser
import os
import re
import subprocess
import sys

import click
import json

from natsort import natsorted
from sonic_py_common import multi_asic
from utilities_common.db import Db

VLAN_SUB_INTERFACE_SEPARATOR = '.'

pass_db = click.make_pass_decorator(Db, ensure=True)

class AbbreviationGroup(click.Group):
    """This subclass of click.Group supports abbreviated subgroup/subcommand names
    """

    def get_command(self, ctx, cmd_name):
        # Try to get builtin commands as normal
        rv = click.Group.get_command(self, ctx, cmd_name)
        if rv is not None:
            return rv

        # Allow automatic abbreviation of the command.  "status" for
        # instance will match "st".  We only allow that however if
        # there is only one command.
        # If there are multiple matches and the shortest one is the common prefix of all the matches, return
        # the shortest one
        matches = []
        shortest = None
        for x in self.list_commands(ctx):
            if x.lower().startswith(cmd_name.lower()):
                matches.append(x)
                if not shortest:
                    shortest = x
                elif len(shortest) > len(x):
                    shortest = x

        if not matches:
            return None
        elif len(matches) == 1:
            return click.Group.get_command(self, ctx, matches[0])
        else:
            for x in matches:
                if not x.startswith(shortest):
                    break
            else:
                return click.Group.get_command(self, ctx, shortest)

            ctx.fail('Too many matches: %s' % ', '.join(sorted(matches)))


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

# Global Config object
_config = None

class AliasedGroup(click.Group):
    """This subclass of click.Group supports abbreviations and
       looking up aliases in a config file with a bit of magic.
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
            return None
        elif len(matches) == 1:
            return click.Group.get_command(self, ctx, matches[0])
        ctx.fail('Too many matches: %s' % ', '.join(sorted(matches)))

class InterfaceAliasConverter(object):
    """Class which handles conversion between interface name and alias"""

    def __init__(self, db=None):

        if db is None:
            self.port_dict = multi_asic.get_port_table()
        else:
            self.config_db = db.cfgdb
            self.port_dict = self.config_db.get_table('PORT')
        self.alias_max_length = 0


        if not self.port_dict:
            click.echo(message="Warning: failed to retrieve PORT table from ConfigDB!", err=True)
            self.port_dict = {}

        for port_name in self.port_dict:
            try:
                if self.alias_max_length < len(
                        self.port_dict[port_name]['alias']):
                   self.alias_max_length = len(
                        self.port_dict[port_name]['alias'])
            except KeyError:
                break

    def name_to_alias(self, interface_name):
        """Return vendor interface alias if SONiC
           interface name is given as argument
        """
        vlan_id = ''
        sub_intf_sep_idx = -1
        if interface_name is not None:
            sub_intf_sep_idx = interface_name.find(VLAN_SUB_INTERFACE_SEPARATOR)
            if sub_intf_sep_idx != -1:
                vlan_id = interface_name[sub_intf_sep_idx + 1:]
                # interface_name holds the parent port name
                interface_name = interface_name[:sub_intf_sep_idx]

            for port_name in self.port_dict:
                if interface_name == port_name:
                    return self.port_dict[port_name]['alias'] if sub_intf_sep_idx == -1 \
                            else self.port_dict[port_name]['alias'] + VLAN_SUB_INTERFACE_SEPARATOR + vlan_id

        # interface_name not in port_dict. Just return interface_name
        return interface_name if sub_intf_sep_idx == -1 else interface_name + VLAN_SUB_INTERFACE_SEPARATOR + vlan_id

    def alias_to_name(self, interface_alias):
        """Return SONiC interface name if vendor
           port alias is given as argument
        """
        vlan_id = ''
        sub_intf_sep_idx = -1
        if interface_alias is not None:
            sub_intf_sep_idx = interface_alias.find(VLAN_SUB_INTERFACE_SEPARATOR)
            if sub_intf_sep_idx != -1:
                vlan_id = interface_alias[sub_intf_sep_idx + 1:]
                # interface_alias holds the parent port alias
                interface_alias = interface_alias[:sub_intf_sep_idx]

            for port_name in self.port_dict:
                if interface_alias == self.port_dict[port_name]['alias']:
                    return port_name if sub_intf_sep_idx == -1 else port_name + VLAN_SUB_INTERFACE_SEPARATOR + vlan_id

        # interface_alias not in port_dict. Just return interface_alias
        return interface_alias if sub_intf_sep_idx == -1 else interface_alias + VLAN_SUB_INTERFACE_SEPARATOR + vlan_id

# Global class instance for SONiC interface name to alias conversion
iface_alias_converter = InterfaceAliasConverter()

def get_interface_naming_mode():
    mode = os.getenv('SONIC_CLI_IFACE_MODE')
    if mode is None:
        mode = "default"
    return mode

def is_ipaddress(val):
    """ Validate if an entry is a valid IP """
    import netaddr
    if not val:
        return False
    try:
        netaddr.IPAddress(str(val))
    except netaddr.core.AddrFormatError:
        return False
    return True


def is_ip_prefix_in_key(key):
    '''
    Function to check if IP address is present in the key. If it
    is present, then the key would be a tuple or else, it shall be
    be string
    '''
    return (isinstance(key, tuple))

def is_valid_port(config_db, port):
    """Check if port is in PORT table"""

    port_table = config_db.get_table('PORT')
    if port in port_table:
        return True

    return False

def is_valid_portchannel(config_db, port):
    """Check if port is in PORT_CHANNEL table"""

    pc_table = config_db.get_table('PORTCHANNEL')
    if port in pc_table:
        return True

    return False

def is_vlanid_in_range(vid):
    """Check if vlan id is valid or not"""

    if vid >= 1 and vid <= 4094:
        return True

    return False

def check_if_vlanid_exist(config_db, vlan):
    """Check if vlan id exits in the config db or ot"""

    if len(config_db.get_entry('VLAN', vlan)) != 0:
        return True

    return False

def is_port_vlan_member(config_db, port, vlan):
    """Check if port is a member of vlan"""

    vlan_ports_data = config_db.get_table('VLAN_MEMBER')
    for key in vlan_ports_data:
        if key[0] == vlan and key[1] == port:
            return True

    return False

def interface_is_in_vlan(vlan_member_table, interface_name):
    """ Check if an interface  is in a vlan """
    for _,intf in vlan_member_table:
        if intf == interface_name:
            return True

    return False

def is_valid_vlan_interface(config_db, interface):
    """ Check an interface is a valid VLAN interface """
    return interface in config_db.get_table("VLAN_INTERFACE")

def interface_is_in_portchannel(portchannel_member_table, interface_name):
    """ Check if an interface is part of portchannel """
    for _,intf in portchannel_member_table:
        if intf == interface_name:
            return True

    return False

def is_port_router_interface(config_db, port):
    """Check if port is a router interface"""

    interface_table = config_db.get_table('INTERFACE')
    for intf in interface_table:
        if port == intf[0]:
            return True

    return False

def is_pc_router_interface(config_db, pc):
    """Check if portchannel is a router interface"""

    pc_interface_table = config_db.get_table('PORTCHANNEL_INTERFACE')
    for intf in pc_interface_table:
        if pc == intf[0]:
            return True

    return False

def is_port_mirror_dst_port(config_db, port):
    """Check if port is already configured as mirror destination port """
    mirror_table = config_db.get_table('MIRROR_SESSION')
    for _,v in mirror_table.items():
        if 'dst_port' in v and v['dst_port'] == port:
            return True

    return False

#
# Use this method to validate unicast IPv4 address
#
def is_ip4_addr_valid(addr, display):
    v4_invalid_list = [ipaddress.IPv4Address(unicode('0.0.0.0')), ipaddress.IPv4Address(unicode('255.255.255.255'))]
    try:
        ip = ipaddress.ip_address(unicode(addr))
        if (ip.version == 4):
            if (ip.is_reserved):
                if display:
                    click.echo ("{} Not Valid, Reason: IPv4 reserved address range.".format(addr))
                return False
            elif (ip.is_multicast):
                if display:
                    click.echo ("{} Not Valid, Reason: IPv4 Multicast address range.".format(addr))
                return False
            elif (ip in v4_invalid_list):
                if display:
                    click.echo ("{} Not Valid.".format(addr))
                return False
            else:
                return True

        else:
            if display:
                click.echo ("{} Not Valid, Reason: Not an IPv4 address".format(addr))
            return False

    except ValueError:
        return False

def vni_id_is_valid(vni):
    """Check if the vni id is in acceptable range (between 1 and 2^24)
    """

    if (vni < 1) or (vni > 16777215):
        return False

    return True

def is_vni_vrf_mapped(ctx, vni):
    """Check if the vni is mapped to vrf
    """

    found = 0
    db = ctx.obj['db']
    vrf_table = db.get_table('VRF')
    vrf_keys = vrf_table.keys()
    if vrf_keys is not None:
      for vrf_key in vrf_keys:
        if ('vni' in vrf_table[vrf_key] and vrf_table[vrf_key]['vni'] == vni):
           found = 1
           break

    if (found == 1):
        print "VNI {} mapped to Vrf {}, Please remove VRF VNI mapping".format(vni, vrf_key)
        return False

    return True

def interface_has_mirror_config(mirror_table, interface_name):
    """Check if port is already configured with mirror config """
    for _,v in mirror_table.items():
        if 'src_port' in v and v['src_port'] == interface_name:
            return True
        if 'dst_port' in v and v['dst_port'] == interface_name:
            return True

    return False

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
    for port_name in natsorted(list(iface_alias_converter.port_dict.keys())):
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

    process = subprocess.Popen(command, shell=True, text=True, stdout=subprocess.PIPE)

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

            elif command.startswith("intfstat"):
                """Show RIF counters"""
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
                """
                Default command conversion
                Search for port names either at the start of a line or preceded immediately by
                whitespace and followed immediately by either the end of a line or whitespace
                or a comma followed by whitespace
                """
                converted_output = raw_output
                for port_name in iface_alias_converter.port_dict:
                    converted_output = re.sub(r"(^|\s){}($|,{{0,1}}\s)".format(port_name),
                            r"\1{}\2".format(iface_alias_converter.name_to_alias(port_name)),
                            converted_output)
                click.echo(converted_output.rstrip('\n'))

    rc = process.poll()
    if rc != 0:
        sys.exit(rc)


def run_command(command, display_cmd=False, ignore_error=False, return_cmd=False, interactive_mode=False):
    """
    Run bash command. Default behavior is to print output to stdout. If the command returns a non-zero
    return code, the function will exit with that return code.

    Args:
        display_cmd: Boolean; If True, will print the command being run to stdout before executing the command
        ignore_error: Boolean; If true, do not exit if command returns a non-zero return code
        return_cmd: Boolean; If true, the function will return the output, ignoring any non-zero return code
        interactive_mode: Boolean; If true, it will treat the process as a long-running process which may generate
                          multiple lines of output over time
    """

    if display_cmd == True:
        click.echo(click.style("Running command: ", fg='cyan') + click.style(command, fg='green'))

    # No conversion needed for intfutil commands as it already displays
    # both SONiC interface name and alias name for all interfaces.
    if get_interface_naming_mode() == "alias" and not command.startswith("intfutil"):
        run_command_in_alias_mode(command)
        sys.exit(0)

    proc = subprocess.Popen(command, shell=True, text=True, stdout=subprocess.PIPE)

    if return_cmd:
        output = proc.communicate()[0]
        return output

    if not interactive_mode:
        (out, err) = proc.communicate()

        if len(out) > 0:
            click.echo(out.rstrip('\n'))

        if proc.returncode != 0 and not ignore_error:
            sys.exit(proc.returncode)

        return

    # interactive mode
    while True:
        output = proc.stdout.readline()
        if output == "" and proc.poll() is not None:
            break
        if output:
            click.echo(output.rstrip('\n'))

    rc = proc.poll()
    if rc != 0:
        sys.exit(rc)


def do_exit(msg):
    m = "FATAL failure: {}. Exiting...".format(msg)
    _log_msg(syslog.LOG_ERR, True, inspect.stack()[1][1], inspect.stack()[1][2], m)
    raise SystemExit(m)


def json_dump(data):
    """
    Dump data in JSON format
    """
    return json.dumps(
        data, sort_keys=True, indent=2, ensure_ascii=False
    )
