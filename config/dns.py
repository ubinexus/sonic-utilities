
import click
from swsscommon.swsscommon import ConfigDBConnector
import ipaddress


NAMESERVERS_MAX_NUM = 3


def is_valid_ip_address(address):
    """Check if the given IP address is valid"""
    try:
        ip = ipaddress.ip_address(address)
        if ip.is_reserved or ip.is_multicast or ip.is_loopback:
            return

        invalid_ips = [
            ipaddress.IPv4Address('0.0.0.0'),
            ipaddress.IPv4Address('255.255.255.255'),
            ipaddress.IPv6Address("0::0"),
            ipaddress.IPv6Address("0::1")
            ]
        if ip in invalid_ips:
            return

        return ip
    except Exception:
        return


def get_nameservers(db):
    nameservers = db.get_table('DNS_NAMESERVER')
    return [ipaddress.ip_address(ip) for ip in nameservers]


# 'dns' group ('config dns ...')
@click.group()
@click.pass_context
def dns(ctx):
    """Static DNS configuration"""
    config_db = ConfigDBConnector()
    config_db.connect()
    ctx.obj = {'db': config_db}


# dns nameserver config
@dns.group('nameserver')
@click.pass_context
def nameserver(ctx):
    """Static DNS namesevers configuration"""
    pass


# dns nameserver add
@nameserver.command('add')
@click.argument('ip_address_str', metavar='<ip_address>', required=True)
@click.pass_context
def add_dns_nameserver(ctx, ip_address_str):
    """Add static DNS namesever entry"""
    ip_address = is_valid_ip_address(ip_address_str)
    if not ip_address:
        ctx.fail(f"{ip_address_str} invalid nameserver ip address")

    db = ctx.obj['db']

    nameservers = get_nameservers(db)
    if ip_address in nameservers:
        ctx.fail(f"{ip_address} nameserver is already configured")

    if len(nameservers) >= NAMESERVERS_MAX_NUM:
        ctx.fail(f"The maximum number ({NAMESERVERS_MAX_NUM}) of nameservers exceeded.")

    db.set_entry('DNS_NAMESERVER', ip_address, {})

# dns nameserver delete
@nameserver.command('del')
@click.argument('ip_address_str', metavar='<ip_address>', required=True)
@click.pass_context
def del_dns_nameserver(ctx, ip_address_str):
    """Delete static DNS nameserver entry"""

    ip_address = is_valid_ip_address(ip_address_str)
    if not ip_address:
        ctx.fail(f"{ip_address_str} invalid nameserver ip address")

    db = ctx.obj['db']

    nameservers = get_nameservers(db)
    if ip_address not in nameservers:
        ctx.fail(f"DNS nameserver {ip_address} is not configured")

    db.set_entry('DNS_NAMESERVER', ip_address, None)
