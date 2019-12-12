#!/usr/bin/env python -u
# -*- coding: utf-8 -*-

import click
import netaddr
import ipaddress
import re
from swsssdk import ConfigDBConnector

TAC_PLUS_MAXSERVERS = 8
TAC_PLUS_PASSKEY_MAX_LEN = 32

RADIUS_MAXSERVERS = 8
RADIUS_PASSKEY_MAX_LEN = 32

def is_ipaddress(val):
    if not val:
        return False
    try:
        netaddr.IPAddress(str(val))
    except:
        return False
    return True

def is_secret(secret):
    return bool(re.match('^' + '[0-9A-Za-z]*' + '$', secret))

def add_table_kv(table, entry, key, val):
    config_db = ConfigDBConnector()
    config_db.connect()
    config_db.mod_entry(table, entry, {key:val})


def del_table_key(table, entry, key):
    config_db = ConfigDBConnector()
    config_db.connect()
    data = config_db.get_entry(table, entry)
    if data:
        if key in data:
            del data[key]
        config_db.set_entry(table, entry, data)


@click.group()
def aaa():
    """AAA command line"""
    pass


# cmd: aaa authentication
@click.group()
def authentication():
    """User authentication"""
    pass
aaa.add_command(authentication)


# cmd: aaa authentication failthrough
@click.command()
@click.argument('option', type=click.Choice(["enable", "disable", "default"]))
def failthrough(option):
    """Allow AAA fail-through [enable | disable | default]"""
    if option == 'default':
        del_table_key('AAA', 'authentication', 'failthrough')
    else:
        if option == 'enable':
            add_table_kv('AAA', 'authentication', 'failthrough', True)
        elif option == 'disable':
            add_table_kv('AAA', 'authentication', 'failthrough', False)
authentication.add_command(failthrough)


# cmd: aaa authentication fallback
@click.command()
@click.argument('option', type=click.Choice(["enable", "disable", "default"]))
def fallback(option):
    """Allow AAA fallback [enable | disable | default]"""
    if option == 'default':
        del_table_key('AAA', 'authentication', 'fallback')
    else:
        if option == 'enable':
            add_table_kv('AAA', 'authentication', 'fallback', True)
        elif option == 'disable':
            add_table_kv('AAA', 'authentication', 'fallback', False)
authentication.add_command(fallback)


@click.command()
@click.argument('auth_protocol', nargs=-1, type=click.Choice(["radius", "tacacs+", "local", "default"]))
def login(auth_protocol):
    """Switch login authentication [ {radius, tacacs+, local} | default ]"""
    if len(auth_protocol) is 0:
        print 'Not support empty argument'
        return
    elif len(auth_protocol) > 2:
        print 'Not a valid command.'
        return

    if 'default' in auth_protocol:
        if len(auth_protocol) !=1:
            click.echo('Not a valid command')
            return
        del_table_key('AAA', 'authentication', 'login')
    else:
        val = auth_protocol[0]
        if len(auth_protocol) == 2:
            val2 = auth_protocol[1]
            good_ap = False
            if val == 'local':
                if val2 == 'radius' or val2 == 'tacacs+':
                    good_ap = True
            elif val == 'radius' or val == 'tacacs+':
                if val2 == 'local':
                    good_ap = True
            if good_ap == True:
                val += ',' + val2
            else:
                click.echo('Not a valid command')
                return

        add_table_kv('AAA', 'authentication', 'login', val)
authentication.add_command(login)


@click.group()
def tacacs():
    """TACACS+ server configuration"""
    pass


@click.group()
@click.pass_context
def default(ctx):
    """set its default configuration"""
    ctx.obj = 'default'
tacacs.add_command(default)


@click.command()
@click.argument('second', metavar='<time_second>', type=click.IntRange(1, 60), required=False)
@click.pass_context
def timeout(ctx, second):
    """Specify TACACS+ server global timeout <1 - 60>"""
    if ctx.obj == 'default':
        del_table_key('TACPLUS', 'global', 'timeout')
    elif second:
        add_table_kv('TACPLUS', 'global', 'timeout', second)
    else:
        click.echo('Not support empty argument')
tacacs.add_command(timeout)
default.add_command(timeout)


@click.command()
@click.argument('type', metavar='<type>', type=click.Choice(["chap", "pap", "mschap", "login"]), required=False)
@click.pass_context
def authtype(ctx, type):
    """Specify TACACS+ server global auth_type [chap | pap | mschap | login]"""
    if ctx.obj == 'default':
        del_table_key('TACPLUS', 'global', 'auth_type')
    elif type:
        add_table_kv('TACPLUS', 'global', 'auth_type', type)
    else:
        click.echo('Not support empty argument')
tacacs.add_command(authtype)
default.add_command(authtype)


@click.command()
@click.argument('secret', metavar='<secret_string>', required=False)
@click.pass_context
def passkey(ctx, secret):
    """Specify TACACS+ server global passkey <STRING>"""
    if ctx.obj == 'default':
        del_table_key('TACPLUS', 'global', 'passkey')
    elif secret:
        if len(secret) > TAC_PLUS_PASSKEY_MAX_LEN:
            click.echo('Maximum of %d chars can be configured' % TAC_PLUS_PASSKEY_MAX_LEN)
            return
        elif not is_secret(secret):
            click.echo('Valid chars are [0-9A-Za-z]')
            return
        add_table_kv('TACPLUS', 'global', 'passkey', secret)
    else:
        click.echo('Not support empty argument')
tacacs.add_command(passkey)
default.add_command(passkey)


# cmd: tacacs add <ip_address> --timeout SECOND --key SECRET --type TYPE --port PORT --pri PRIORITY
@click.command()
@click.argument('address', metavar='<ip_address>')
@click.option('-t', '--timeout', help='Transmission timeout interval, default 5', type=click.IntRange(1, 60))
@click.option('-k', '--key', help='Shared secret')
@click.option('-a', '--auth_type', help='Authentication type, default pap', type=click.Choice(["chap", "pap", "mschap", "login"]))
@click.option('-o', '--port', help='TCP port range is 1 to 65535, default 49', type=click.IntRange(1, 65535), default=49)
@click.option('-p', '--pri', help="Priority, default 1", type=click.IntRange(1, 64), default=1)
@click.option('-m', '--use-mgmt-vrf', help="Management vrf, default is no vrf", is_flag=True)
def add(address, timeout, key, auth_type, port, pri, use_mgmt_vrf):
    """Specify a TACACS+ server"""
    if not is_ipaddress(address):
        click.echo('Invalid ip address')
        return
    if address == "0.0.0.0":
        click.echo('enter non-zero ip address')
        return
    ip = ipaddress.IPv4Address(address)
    if ip.is_reserved:
        click.echo('Reserved ip is not valid')
        return
    if ip.is_multicast:
        click.echo('Multicast ip is not valid')
        return

    if key:
        if len(key) > TAC_PLUS_PASSKEY_MAX_LEN:
            click.echo('--key: Maximum of %d chars can be configured' % TAC_PLUS_PASSKEY_MAX_LEN)
            return
        elif not is_secret(key):
            click.echo('--key: Valid chars are [0-9A-Za-z]')
            return

    config_db = ConfigDBConnector()
    config_db.connect()
    old_data = config_db.get_table('TACPLUS_SERVER')
    if address in old_data :
        click.echo('server %s already exists' % address)
        return
    if len(old_data) == TAC_PLUS_MAXSERVERS:
        click.echo('Maximum of %d can be configured' % TAC_PLUS_MAXSERVERS)
    else:
        data = {
            'tcp_port': str(port),
            'priority': pri
        }
        if auth_type is not None:
            data['auth_type'] = auth_type
        if timeout is not None:
            data['timeout'] = str(timeout)
        if key is not None:
            data['passkey'] = key
        if use_mgmt_vrf :
            data['vrf'] = "mgmt"
        config_db.set_entry('TACPLUS_SERVER', address, data)
tacacs.add_command(add)


# cmd: tacacs delete <ip_address>
# 'del' is keyword, replace with 'delete'
@click.command()
@click.argument('address', metavar='<ip_address>')
def delete(address):
    """Delete a TACACS+ server"""
    if not is_ipaddress(address):
        click.echo('Invalid ip address')
        return

    config_db = ConfigDBConnector()
    config_db.connect()
    config_db.set_entry('TACPLUS_SERVER', address, None)
tacacs.add_command(delete)


@click.group()
def radius():
    """RADIUS server configuration"""
    pass


@click.group()
@click.pass_context
def default(ctx):
    """set its default configuration"""
    ctx.obj = 'default'
radius.add_command(default)


@click.command()
@click.argument('second', metavar='<time_second>', type=click.IntRange(1, 60), required=False)
@click.pass_context
def timeout(ctx, second):
    """Specify RADIUS server global timeout <1 - 60>"""
    if ctx.obj == 'default':
        del_table_key('RADIUS', 'global', 'timeout')
    elif second:
        add_table_kv('RADIUS', 'global', 'timeout', second)
    else:
        click.echo('Not support empty argument')
radius.add_command(timeout)
default.add_command(timeout)


@click.command()
@click.argument('retries', metavar='<retry_attempts>', type=click.IntRange(1, 10), required=False)
@click.pass_context
def retransmit(ctx, retries):
    """Specify RADIUS server global retry attempts <1 - 10>"""
    if ctx.obj == 'default':
        del_table_key('RADIUS', 'global', 'retransmit')
    elif retries:
        add_table_kv('RADIUS', 'global', 'retransmit', retries)
    else:
        click.echo('Not support empty argument')
radius.add_command(retransmit)
default.add_command(retransmit)


@click.command()
@click.argument('type', metavar='<type>', type=click.Choice(["chap", "pap", "mschapv2"]), required=False)
@click.pass_context
def authtype(ctx, type):
    """Specify RADIUS server global auth_type [chap | pap | mschapv2]"""
    if ctx.obj == 'default':
        del_table_key('RADIUS', 'global', 'auth_type')
    elif type:
        add_table_kv('RADIUS', 'global', 'auth_type', type)
    else:
        click.echo('Not support empty argument')
radius.add_command(authtype)
default.add_command(authtype)


@click.command()
@click.argument('secret', metavar='<secret_string>', required=False)
@click.pass_context
def passkey(ctx, secret):
    """Specify RADIUS server global passkey <STRING>"""
    if ctx.obj == 'default':
        del_table_key('RADIUS', 'global', 'passkey')
    elif secret:
        if len(secret) > RADIUS_PASSKEY_MAX_LEN:
            click.echo('Maximum of %d chars can be configured' % RADIUS_PASSKEY_MAX_LEN)
            return
        elif not is_secret(secret):
            click.echo('Valid chars are [0-9A-Za-z]')
            return
        add_table_kv('RADIUS', 'global', 'passkey', secret)
    else:
        click.echo('Not support empty argument')
radius.add_command(passkey)
default.add_command(passkey)

@click.command()
@click.argument('src_ip', metavar='<source_ip>', required=False)
@click.pass_context
def sourceip(ctx, src_ip):
    """Specify RADIUS server global source ip <IPAddress>"""
    if ctx.obj == 'default':
        del_table_key('RADIUS', 'global', 'src_ip')
        return
    elif not src_ip:
        click.echo('Not support empty argument')
        return

    if not is_ipaddress(src_ip):
        click.echo('Invalid ip address')
        return

    v6_invalid_list = [ipaddress.IPv6Address(unicode('0::0')), ipaddress.IPv6Address(unicode('0::1'))]
    net = ipaddress.ip_network(unicode(src_ip), strict=False)
    if (net.version == 4):
        if src_ip == "0.0.0.0":
            click.echo('enter non-zero ip address')
            return
        ip = ipaddress.IPv4Address(src_ip)
        if ip.is_reserved:
            click.echo('Reserved ip is not valid')
            return
        if ip.is_multicast:
            click.echo('Multicast ip is not valid')
            return
    elif (net.version == 6):
        ip = ipaddress.IPv6Address(src_ip)
        if (ip.is_multicast):
            click.echo('Multicast ip is not valid')
            return
        if (ip in v6_invalid_list):
            click.echo('Invalid ip address')
            return
    add_table_kv('RADIUS', 'global', 'src_ip', src_ip)

radius.add_command(sourceip)
default.add_command(sourceip)


# cmd: radius add <ip_address> --retransmit COUNT --timeout SECOND --key SECRET --type TYPE --auth-port PORT --pri PRIORITY
@click.command()
@click.argument('address', metavar='<ip_address>')
@click.option('-r', '--retransmit', help='Retransmit attempts, default 3', type=click.IntRange(1, 10))
@click.option('-t', '--timeout', help='Transmission timeout interval, default 5', type=click.IntRange(1, 60))
@click.option('-k', '--key', help='Shared secret')
@click.option('-a', '--auth_type', help='Authentication type, default pap', type=click.Choice(["chap", "pap", "mschapv2"]))
@click.option('-o', '--auth-port', help='UDP port range is 1 to 65535, default 1812', type=click.IntRange(1, 65535), default=1812)
@click.option('-p', '--pri', help="Priority, default 1", type=click.IntRange(1, 64), default=1)
@click.option('-m', '--use-mgmt-vrf', help="Management vrf, default is no vrf", is_flag=True)
def add(address, retransmit, timeout, key, auth_type, auth_port, pri, use_mgmt_vrf):
    """Specify a RADIUS server"""
    if not is_ipaddress(address):
        click.echo('Invalid ip address')
        return

    v6_invalid_list = [ipaddress.IPv6Address(unicode('0::0')), ipaddress.IPv6Address(unicode('0::1'))]
    net = ipaddress.ip_network(unicode(address), strict=False)
    if (net.version == 4):
        if address == "0.0.0.0":
            click.echo('enter non-zero ip address')
            return
        ip = ipaddress.IPv4Address(address)
        if ip.is_reserved:
            click.echo('Reserved ip is not valid')
            return
        if ip.is_multicast:
            click.echo('Multicast ip is not valid')
            return
    elif (net.version == 6):
        ip = ipaddress.IPv6Address(address)
        if (ip.is_multicast):
            click.echo('Multicast ip is not valid')
            return
        if (ip in v6_invalid_list):
            click.echo('Invalid ip address')
            return

    if key:
        if len(key) > RADIUS_PASSKEY_MAX_LEN:
            click.echo('--key: Maximum of %d chars can be configured' % RADIUS_PASSKEY_MAX_LEN)
            return
        elif not is_secret(key):
            click.echo('--key: Valid chars are [0-9A-Za-z]')
            return

    config_db = ConfigDBConnector()
    config_db.connect()
    old_data = config_db.get_table('RADIUS_SERVER')
    if address in old_data :
        click.echo('server %s already exists' % address)
        return
    if len(old_data) == RADIUS_MAXSERVERS:
        click.echo('Maximum of %d can be configured' % RADIUS_MAXSERVERS)
    else:
        data = {
            'auth_port': str(auth_port),
            'priority': pri
        }
        if auth_type is not None:
            data['auth_type'] = auth_type
        if retransmit is not None:
            data['retransmit'] = str(retransmit)
        if timeout is not None:
            data['timeout'] = str(timeout)
        if key is not None:
            data['passkey'] = key
        if use_mgmt_vrf :
            data['vrf'] = "mgmt"
        config_db.set_entry('RADIUS_SERVER', address, data)
radius.add_command(add)


# cmd: radius delete <ip_address>
# 'del' is keyword, replace with 'delete'
@click.command()
@click.argument('address', metavar='<ip_address>')
def delete(address):
    """Delete a RADIUS server"""
    if not is_ipaddress(address):
        click.echo('Invalid ip address')
        return

    config_db = ConfigDBConnector()
    config_db.connect()
    config_db.set_entry('RADIUS_SERVER', address, None)
radius.add_command(delete)


if __name__ == "__main__":
    aaa()

