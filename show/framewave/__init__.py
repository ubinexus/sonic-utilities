import json
import os
import subprocess
import sys
import re

import click
import netifaces
import utilities_common.cli as clicommon
import utilities_common.multi_asic as multi_asic_util
import utilities_common.constants as constants
from natsort import natsorted
from sonic_py_common import device_info, multi_asic
from swsssdk import ConfigDBConnector
from swsscommon.swsscommon import SonicV2Connector
from tabulate import tabulate
from utilities_common.db import Db

def add_commands(cli):
    @cli.command('route-map')
    @click.argument('route_map_name', required=False)
    @click.option('--verbose', is_flag=True, help="Enable verbose output")
    def route_map(route_map_name, verbose):
        """show route-map"""
        cmd = 'sudo vtysh -c "show route-map'
        if route_map_name is not None:
            cmd += ' {}'.format(route_map_name)
        cmd += '"'
        run_command(cmd, display_cmd=verbose)

    #
    # 'ip' group ("show ip ...")
    #

    # This group houses IP (i.e., IPv4) commands and subgroups
    @cli.group(cls=clicommon.AliasedGroup)
    def ip():
        """Show IP (IPv4) commands"""
        pass


    #
    # get_if_admin_state
    #
    # Given an interface name, return its admin state reported by the kernel.
    #
    def get_if_admin_state(iface):
        admin_file = "/sys/class/net/{0}/flags"

        try:
            state_file = open(admin_file.format(iface), "r")
        except IOError as e:
            print("Error: unable to open file: %s" % str(e))
            return "error"

        content = state_file.readline().rstrip()
        flags = int(content, 16)

        if flags & 0x1:
            return "up"
        else:
            return "down"


    #
    # get_if_oper_state
    #
    # Given an interface name, return its oper state reported by the kernel.
    #
    def get_if_oper_state(iface):
        oper_file = "/sys/class/net/{0}/carrier"

        try:
            state_file = open(oper_file.format(iface), "r")
        except IOError as e:
            print("Error: unable to open file: %s" % str(e))
            return "error"

        oper_state = state_file.readline().rstrip()
        if oper_state == "1":
            return "up"
        else:
            return "down"


    #
    # get_if_master
    #
    # Given an interface name, return its master reported by the kernel.
    #
    def get_if_master(iface):
        oper_file = "/sys/class/net/{0}/master"

        if os.path.exists(oper_file.format(iface)):
            real_path = os.path.realpath(oper_file.format(iface))
            return os.path.basename(real_path)
        else:
            return ""


    #
    # 'show ip interfaces' command on framewave routing stack
    #
    # Display all interfaces with master, an IPv4 address, admin/oper states
    # Addresses from all scopes are included. Interfaces with no addresses are
    # excluded.
    #
    @ip.command()
    def interfaces():
        """Show interfaces IPv4 address"""
        import netaddr
        header = ['Interface', 'Master', 'IPv4 address/mask', 'Admin/Oper']
        data = []

        interfaces = natsorted(netifaces.interfaces())

        for iface in interfaces:
            ipaddresses = netifaces.ifaddresses(iface)

            if netifaces.AF_INET in ipaddresses:
                ifaddresses = []
                for ipaddr in ipaddresses[netifaces.AF_INET]:
                    local_ip = str(ipaddr['addr'])
                    netmask = netaddr.IPAddress(ipaddr['netmask']).netmask_bits()
                    ifaddresses.append(["", local_ip + "/" + str(netmask)])

                if len(ifaddresses) > 0:
                    admin = get_if_admin_state(iface)
                    if admin == "up":
                        oper = get_if_oper_state(iface)
                    else:
                        oper = "down"
                    master = get_if_master(iface)
                    if clicommon.get_interface_naming_mode() == "alias":
                        iface = iface_alias_converter.name_to_alias(iface)

                    data.append([iface, master, ifaddresses[0][1], admin + "/" + oper])

                    for ifaddr in ifaddresses[1:]:
                        data.append(["", "", ifaddr[1], admin + "/" + oper])

        print(tabulate(data, header, tablefmt="simple", stralign='left', missingval=""))

    # Autocomplete function for the framewave ip/ipv6 route types
    def framewave_ac_route_type(ctx, args, incomplete):
        arg_string = ['bgp', 'isis', 'static', 'local', 'connected']
        return [elem for elem in arg_string if incomplete in elem]


    @ip.command()
    @click.argument('args', metavar='[bgp|isis|static|local|connected|<destination-prefix>]',
                    required=False, autocompletion=framewave_ac_route_type)
    @click.option('--vrf', type=str, help="Show routes for VRF VRF-NAME")
    @click.option('--fib', is_flag=True, help="Show routes in the FIB")
    @click.option('--json', is_flag=True, help="JSON output")
    @click.option('--verbose', is_flag=True, help="Enable verbose output")
    def route(args, vrf, fib, verbose, json):
        """
        Show IP (IPv4) routing table.\n
             destination-prefix  Only show routes to the specified destination\n
             connected  Only show connected routes\n
             bgp|isis|static|local  Only show routes of the specified type\n
        """

        cmd = 'sudo docker exec bgp /opt/framewave/bin/show-route --ipv4'
        if args is not None:
            cmd += " " + str(args)
        if vrf is not None:
            cmd += " --vrf " + str(vrf)
        if fib:
            cmd += " --fib"
        if json:
            cmd += " --json"
        run_command(cmd, display_cmd=verbose)


    #
    # 'ipv6' group ("show ipv6 ...")
    #

    # This group houses IPv6-related commands and subgroups
    @cli.group(cls=clicommon.AliasedGroup)
    def ipv6():
        """Show IPv6 commands"""
        pass

    #
    # 'show ipv6 interfaces' command
    #
    # Display all interfaces with master, an IPv6 address, admin/oper states.
    # Addresses from all scopes are included. Interfaces with no addresses are
    # excluded.
    #
    @ipv6.command()
    def interfaces():
        """Show interfaces IPv6 address"""
        header = ['Interface', 'Master', 'IPv6 address/mask', 'Admin/Oper']
        data = []

        interfaces = natsorted(netifaces.interfaces())

        for iface in interfaces:
            ipaddresses = netifaces.ifaddresses(iface)

            if netifaces.AF_INET6 in ipaddresses:
                ifaddresses = []
                for ipaddr in ipaddresses[netifaces.AF_INET6]:
                    local_ip = str(ipaddr['addr'])
                    netmask = ipaddr['netmask'].split('/', 1)[-1]
                    ifaddresses.append(["", local_ip + "/" + str(netmask)])

                if len(ifaddresses) > 0:
                    admin = get_if_admin_state(iface)
                    if admin == "up":
                        oper = get_if_oper_state(iface)
                    else:
                        oper = "down"
                    master = get_if_master(iface)
                    if clicommon.get_interface_naming_mode() == "alias":
                        iface = iface_alias_converter.name_to_alias(iface)
                    data.append([iface, master, ifaddresses[0][1], admin + "/" + oper])
                    for ifaddr in ifaddresses[1:]:
                        data.append(["", "", ifaddr[1], admin + "/" + oper])

        print(tabulate(data, header, tablefmt="simple", stralign='left', missingval=""))


    #
    # 'route' subcommand ("show ipv6 route")
    #
    @ipv6.command()
    @click.argument('args', metavar='[bgp|isis|static|local|connected|<destination-prefix>]',
                    required=False, autocompletion=framewave_ac_route_type)
    @click.option('--vrf', type=str, help="Show routes for VRF VRF-NAME")
    @click.option('--fib', is_flag=True, help="Show routes in the FIB")
    @click.option('--json', is_flag=True, help="JSON output")
    @click.option('--verbose', is_flag=True, help="Enable verbose output")
    def route(args, vrf, fib, verbose, json):
        """
        Show IP (IPv6) routing table.\n
             destination-prefix  Only show routes to the specified destination\n
             connected  Only show connected routes\n
             bgp|isis|static|local  Only show routes of the specified type\n
        """
        cmd = 'sudo docker exec bgp /opt/framewave/bin/show-route --ipv6'
        if args is not None:
            cmd += " " + str(args)
        if vrf is not None:
            cmd += " --vrf " + str(vrf)
        if fib:
            cmd += " --fib"
        if json:
            cmd += " --json"
        run_command(cmd, display_cmd=verbose)

    #
    # 'show route-summary' command ("show route-summary")
    #
    @cli.command('route-summary')
    @click.option('--ipv4', is_flag=True, help="Show ipv4 route summary")
    @click.option('--ipv6', is_flag=True, help="Show ipv6 route summary")
    @click.option('--vrf', type=str, help="Show routes for VRF VRF-NAME")
    @click.option('--json', is_flag=True, help="JSON output")
    @click.option('--verbose', is_flag=True, help="Enable verbose output")
    def route_summary(ipv4, ipv6, vrf, verbose, json):
        """
        Show route summary.\n

        """
        cmd = 'sudo docker exec bgp /opt/framewave/bin/show-route-summary'
        if ipv4:
            cmd+= " --ipv4"
        if ipv6:
            cmd+= " --ipv6"
        if vrf is not None:
            cmd += " --vrf " + str(vrf)
        if json:
            cmd += " --json"
        run_command(cmd, display_cmd=verbose)

    #
    # Inserting BGP functionality into cli's show parse-chain.
    #
    from .bgp import bgp
    cli.add_command(bgp)

    #
    # Inserting IS-IS functionality into cli's show parse-chain.
    #
    from .isis import isis
    cli.add_command(isis)

    #
    # Inserting BFD functionality into cli's show parse-chain.
    #
    from .bfd import bfd
    cli.add_command(bfd)

    #
    # Inserting SR functionality into cli's show parse-chain.
    #
    from .sr import segment_routing
    cli.add_command(segment_routing)

    #
    # Inserting MPLS functionality into cli's show parse-chain.
    #
    from .mpls import mpls
    cli.add_command(mpls)

    #
    # Inserting LACP functionality into cli's show parse-chain.
    #
    from .lacp import lacp
    cli.add_command(lacp)

    #
    # Inserting LDP functionality into cli's show parse-chain.
    #
    from .ldp import ldp
    cli.add_command(ldp)


    from .rejected_config import rejected_config
    cli.add_command(rejected_config)

    # Autocomplete function for the framewave techsupport arguments.
    def framewave_ac_techsupport(ctx, args, incomplete):
        arg_string = ['dataplane', 'routes', 'interfaces', 'bgp', 'isis', 'mpls', 'sr', 'detail']
        return [elem for elem in arg_string if incomplete in elem]


    #
    # 'techsupport' command ("show techsupport")
    #

    @cli.command()
    @click.argument('args', metavar='[dataplane|routes|interfaces|bgp|isis|mpls|sr|detail]',
                        required=False, autocompletion=framewave_ac_techsupport)
    @click.option('--since', required=False, help="Collect logs and core files since given date")
    @click.option('-g', '--global-timeout', default=30, type=int, help="Global timeout in minutes. Default 30 mins")
    @click.option('-c', '--cmd-timeout', default=5, type=int, help="Individual command timeout in minutes. Default 5 mins")
    @click.option('--verbose', is_flag=True, help="Enable verbose output")
    @click.option('--allow-process-stop', is_flag=True, help="Dump additional data which may require system interruption")
    @click.option('--silent', is_flag=True, help="Run techsupport in silent mode")
    def techsupport(args, since, global_timeout, cmd_timeout, verbose, allow_process_stop, silent):
        """Gather information for troubleshooting"""
        # Run the sigtrace command and redirect its status output to /dev/null
        # to not modify the show techsupport output
        cmd = "docker exec -i bgp /opt/framewave/bin/sigtrace /var/log/bgp/ipstrc.log > /dev/null"
        run_command(cmd)

        cmd = "sudo timeout -s SIGTERM --foreground {}m".format(global_timeout)

        if allow_process_stop:
            cmd += " -a"

        if silent:
            cmd += " generate_dump"
            click.echo("Techsupport is running with silent option. This command might take a long time.")
        else:
            cmd += " generate_dump -v"

        if args is not None:
            cmd += " -d " + str(args)

        if since:
            cmd += " -s '{}'".format(since)

        cmd += " -t {}".format(cmd_timeout)
        run_command(cmd, display_cmd=verbose)

def run_command(command, display_cmd=False, return_cmd=False):
    if display_cmd:
        click.echo(click.style("Command: ", fg='cyan') + click.style(command, fg='green'))

    # No conversion needed for intfutil commands as it already displays
    # both SONiC interface name and alias name for all interfaces.
    if clicommon.get_interface_naming_mode() == "alias" and not command.startswith("intfutil"):
        clicommon.run_command_in_alias_mode(command)
        raise sys.exit(0)

    proc = subprocess.Popen(command, shell=True, text=True, stdout=subprocess.PIPE)

    while True:
        if return_cmd:
            output = proc.communicate()[0]
            return output
        output = proc.stdout.readline()
        if output == "" and proc.poll() is not None:
            break
        if output:
            click.echo(output.rstrip('\n'))

    rc = proc.poll()
    if rc != 0:
        sys.exit(rc)


def showifpresent(cmd_name, config_name, verbose):
    """
    Prints config name to terminal and shows config if present
    """
    click.echo(config_name)
    if run_command(cmd_name, return_cmd=True):
        run_command(cmd_name, display_cmd=verbose)
    else:
        click.echo("{\n    EMPTY\n}")


#
# 'runningconfiguration' group ("show runningconfiguration")
#
def add_runningconfiguration(runningconfiguration):
    # 'bgp' subcommand ("show runningconfiguration bgp")
    @runningconfiguration.command()
    @click.option('--verbose', is_flag=True, help="Enable verbose output")
    def bgp(verbose):
        """Show BGP running configuration"""
        cmd_asn = "sonic-cfggen -d --var-json DEVICE_METADATA | jq .localhost.bgp_asn"
        dev_meta = '"DEVICE_METADATA": {\n    "localhost": {\n        "bgp_asn": '
        dev_close = '    }\n}'

        proc = subprocess.Popen(cmd_asn, shell=True, text=True, stdout=subprocess.PIPE)
        output = proc.stdout.readline()
        if output == "" and proc.poll() is not None:
            click.echo("{EMPTY}")
        if output:
            click.echo(dev_meta + output + dev_close)

        cmd_nbor = "sonic-cfggen -d --var-json BGP_NEIGHBOR"
        showifpresent(cmd_nbor, '"BGP_NEIGHBOR":', verbose)

    # 'isis' subcommand ("show runningconfiguration isis")
    @runningconfiguration.command()
    @click.option('--verbose', is_flag=True, help="Enable verbose output")
    def isis(verbose):
        """Show ISIS running configuration"""
        cmd_router = "sonic-cfggen -d --var-json ISIS_ROUTER"
        cmd_level = "sonic-cfggen -d --var-json ISIS_LEVEL"
        cmd_if = "sonic-cfggen -d --var-json ISIS_INTERFACE"
        cmd_if_level = "sonic-cfggen -d --var-json ISIS_INTERFACE_LEVEL"
        cmd_if_afi_safi = "sonic-cfggen -d --var-json ISIS_INTERFACE_AFI_SAFI"

        showifpresent(cmd_router, '"ISIS_ROUTER":', verbose)
        showifpresent(cmd_level, '"ISIS_LEVEL":', verbose)
        showifpresent(cmd_if, '"ISIS_INTERFACE":', verbose)
        showifpresent(cmd_if_level, '"ISIS_INTERFACE_LEVEL":', verbose)
        showifpresent(cmd_if_afi_safi, '"ISIS_INTERFACE_AFI_SAFI":', verbose)


    # 'segment-routing' subcommand ("show runningconfiguration segment-routing")
    @runningconfiguration.command()
    @click.option('--verbose', is_flag=True, help="Enable verbose output")
    def sr(verbose):
        """Show segment routing running configuration"""
        cmd_g_blocks = "sonic-cfggen -d --var-json SR_GLOBAL_BLOCKS"
        cmd_sr_config = "sonic-cfggen -d --var-json ISIS_SR_CONFIG"
        cmd_isis_sr = "sonic-cfggen -d --var-json ISIS_SR_PREFIX_MAP"

        showifpresent(cmd_g_blocks, '"SR_GLOBAL_BLOCKS":', verbose)
        showifpresent(cmd_sr_config, '"ISIS_SR_CONFIG":', verbose)
        showifpresent(cmd_isis_sr, '"ISIS_SR_PREFIX_MAP":', verbose)


    # 'mpls' subcommand ("show runningconfiguration mpls")
    @runningconfiguration.command()
    @click.option('--verbose', is_flag=True, help="Enable verbose output")
    def mpls(verbose):
        """Show MPLS running configuration"""
        cmd_r_param = "sonic-cfggen -d --var-json MPLS_ROUTER_PARAMETERS"
        cmd_res = "sonic-cfggen -d --var-json MPLS_RESERVED_LABEL_BLOCK"

        showifpresent(cmd_r_param, '"MPLS_ROUTER_PARAMETERS":', verbose)
        showifpresent(cmd_res, '"MPLS_RESERVED_LABEL_BLOCK":', verbose)
