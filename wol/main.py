#!/usr/bin/env python3

"""
use wol to generate and send Wake-On-LAN (WOL) "Magic Packet" to specific interface

Usage: wol_click [OPTIONS] INTERFACE TARGET_MAC

  Generate and send Wake-On-LAN (WOL) "Magic Packet" to specific interface

Options:
  -b           Use broadcast MAC address instead of target device's MAC
               address as Destination MAC Address in Ethernet Frame Header.
               [default: False]
  -p password  An optional 4 or 6 byte password, in ethernet hex format or
               quad-dotted decimal  [default: ]
  -c count     For each target MAC address, the count of magic packets to
               send. count must between 1 and 5. This param must use with -i.
               [default: 1]
  -i interval  Wait interval milliseconds between sending each magic packet.
               interval must between 0 and 2000. This param must use with -c.
               [default: 0]
  -v           Verbose output  [default: False]
  -h, --help   Show this message and exit.

Examples:
  wol Ethernet10 00:11:22:33:44:55
  wol Ethernet10 00:11:22:33:44:55 -b
  wol Vlan1000 00:11:22:33:44:55,11:33:55:77:99:bb -p 00:22:44:66:88:aa
  wol Vlan1000 00:11:22:33:44:55,11:33:55:77:99:bb -p 192.168.1.1 -c 3 -i 2000
"""

import binascii
import click
import copy
import netifaces
import os
import socket
import time

CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])
EPILOG = """\b
Examples:
  wol Ethernet10 00:11:22:33:44:55
  wol Ethernet10 00:11:22:33:44:55 -b
  wol Vlan1000 00:11:22:33:44:55,11:33:55:77:99:bb -p 00:22:44:66:88:aa
  wol Vlan1000 00:11:22:33:44:55,11:33:55:77:99:bb -p 192.168.1.1 -c 3 -i 2000
"""
ORDINAL_NUMBER = ["0", "1st", "2nd", "3rd", "4th", "5th"]
ETHER_TYPE_WOL = b'\x08\x42'


class MacAddress(object):
    def __init__(self, mac):
        self.mac = mac

    def __str__(self):
        return "%x:%x:%x:%x:%x:%x" % (self.mac[0], self.mac[1], self.mac[2], self.mac[3], self.mac[4], self.mac[5])

    def __eq__(self, other):
        return self.mac == other.mac

    def to_bytes(self):
        return copy.copy(self.mac)


BROADCAST_MAC = MacAddress(b'\xff\xff\xff\xff\xff\xff')


def is_root():
    return os.geteuid() == 0


def get_interface_operstate(interface):
    with open('/sys/class/net/{}/operstate'.format(interface), 'r') as f:
        return f.read().strip().lower()


def get_interface_mac(interface):
    mac = netifaces.ifaddresses(interface)[netifaces.AF_LINK][0].get('addr')
    return MacAddress(binascii.unhexlify(mac.replace(':', '').replace('-', '')))


def build_magic_packet(interface, target_mac, broadcast, password):
    dst_mac = BROADCAST_MAC if broadcast else target_mac
    src_mac = get_interface_mac(interface)
    return dst_mac.to_bytes() + src_mac.to_bytes() + ETHER_TYPE_WOL \
        + b'\xff' * 6 + target_mac.to_bytes() * 16 + password


def send_magic_packet(interface, pkt, count, interval, verbose):
    target_mac = MacAddress(pkt[20:26])
    if verbose:
        print("Sending {} magic packet to {} via interface {}".format(count, target_mac, interface))
    sock = socket.socket(socket.AF_PACKET, socket.SOCK_RAW)
    sock.bind((interface, 0))
    for i in range(count):
        sock.send(pkt)
        if verbose:
            print("{} magic packet sent to {}".format(ORDINAL_NUMBER[i + 1], target_mac))
        if i + 1 != count:
            time.sleep(interval / 1000)
    sock.close()


def validate_interface(ctx, param, value):
    if value not in netifaces.interfaces():
        raise click.BadParameter("invalid SONiC interface name {}".format(value))
    if get_interface_operstate(value) != 'up':
        raise click.BadParameter("interface {} is not up".format(value))
    return value


def validate_target_mac(ctx, param, value):
    mac_list = []
    for mac_s in value.split(','):
        try:
            mac_b = binascii.unhexlify(mac_s.replace(':', '').replace('-', ''))
        except binascii.Error:
            raise click.BadParameter("invalid MAC address {}".format(mac_s))
        if len(mac_b) != 6:
            raise click.BadParameter("invalid MAC address {}".format(mac_s))
        mac_list.append(MacAddress(mac_b))
    return mac_list


def validate_password(ctx, param, value):
    if len(value) == 0:
        return b''  # Empty password is valid.
    elif len(value) <= 15:  # The length of a valid IPv4 address is less or equal to 15.
        try:
            password = socket.inet_aton(value)
        except OSError:
            raise click.BadParameter("invalid password format")
    else:  # The length of a valid MAC address is 17.
        try:
            password = binascii.unhexlify(value.replace(':', '').replace('-', ''))
        except binascii.Error:
            raise click.BadParameter("invalid password format")
    if len(password) not in [4, 6]:
        raise click.BadParameter("password must be 4 or 6 bytes")
    return password


def validate_count_interval(count, interval):
    if count is None and interval is None:
        return 1, 0  # By default, count=1 and interval=0.
    if count is None or interval is None:
        raise click.BadParameter("count and interval must be used together")
    # The values are confirmed in valid range by click.IntRange().
    return count, interval


@click.command(context_settings=CONTEXT_SETTINGS, epilog=EPILOG)
@click.argument('interface', type=click.STRING, callback=validate_interface)
@click.argument('target_mac', type=click.STRING, callback=validate_target_mac)
@click.option('-b', 'broadcast', is_flag=True, show_default=True, default=False,
              help="Use broadcast MAC address instead of target device's MAC address as Destination MAC Address in Ethernet Frame Header.")
@click.option('-p', 'password', type=click.STRING, show_default=True, default='', callback=validate_password, metavar='password',
              help='An optional 4 or 6 byte password, in ethernet hex format or quad-dotted decimal')
@click.option('-c', 'count', type=click.IntRange(1, 5), metavar='count', show_default=True,  # default=1,
              help='For each target MAC address, the count of magic packets to send. count must between 1 and 5. This param must use with -i.')
@click.option('-i', 'interval', type=click.IntRange(0, 2000), metavar='interval',  # show_default=True, default=0,
              help="Wait interval milliseconds between sending each magic packet. interval must between 0 and 2000. This param must use with -c.")
@click.option('-v', 'verbose', is_flag=True, show_default=True, default=False,
              help='Verbose output')
def wol(interface, target_mac, broadcast, password, count, interval, verbose):
    """
    Generate and send Wake-On-LAN (WOL) "Magic Packet" to specific interface
    """
    count, interval = validate_count_interval(count, interval)

    if not is_root():
        raise click.ClickException("root priviledge is required to run this script")

    for mac in target_mac:
        pkt = build_magic_packet(interface, mac, broadcast, password)
        try:
            send_magic_packet(interface, pkt, count, interval, verbose)
        except Exception as e:
            raise click.ClickException(f'Exception: {e}')


if __name__ == '__main__':
    wol()
