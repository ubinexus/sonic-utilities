#!/usr/bin/env python -u
# -*- coding: utf-8 -*-

import click
import netaddr
from swsssdk import ConfigDBConnector


def is_ipaddress(val):
    if not val:
        return False
    try:
        netaddr.IPAddress(str(val))
    except:
        return False
    return True


def set_entry(table, entry, data):
    config_db = ConfigDBConnector()
    config_db.connect()
    config_db.set_entry(table, entry, data)


@click.group()
def aaa():
    """AAA command line"""
    pass


@click.group()
@click.pass_context
def debug(ctx):
    """AAA debug"""
    ctx.obj = "debug"
aaa.add_command(debug)


@click.command()
@click.pass_context
def on(ctx):
    """Open command"""
    if ctx.obj == 'debug':
        set_entry('AAA', 'debug', {
            'debug': True
        })
debug.add_command(on)


@click.command()
@click.pass_context
def off(ctx):
    """Close command"""
    if ctx.obj == 'debug':
        set_entry('AAA', 'debug', {
            'debug': False
        })
debug.add_command(off)


# cmd: aaa authentication
@click.group()
def authentication():
    """User authentication"""
    pass
aaa.add_command(authentication)


# cmd: aaa authentication failthrough
@click.group()
@click.pass_context
def failthrough(ctx):
    """Allow AAA fail-through"""
    ctx.obj = "failthrough"
authentication.add_command(failthrough)


@click.command()
@click.pass_context
def enable(ctx):
    """Enable Command"""
    if ctx.obj == 'failthrough':
        set_entry('AAA', 'authentication', {
            'failthrough': True
        })
failthrough.add_command(enable)


@click.command()
@click.pass_context
def disable(ctx):
    """Disable Command"""
    if ctx.obj == 'failthrough':
        set_entry('AAA', 'authentication', {
            'failthrough': False
        })
failthrough.add_command(disable)


@click.command()
@click.argument('auth_protocol', nargs=-1, type=click.Choice(["tacacs+", "local"]))
def login(auth_protocol):
    """Switch login"""
    if len(auth_protocol) is 0:
        print 'Not support empty argument'
        return

    val = auth_protocol[0]
    if len(auth_protocol) == 2:
        val += ',' + auth_protocol[1]

    set_entry('AAA', 'authentication', {
        'login': val
    })
authentication.add_command(login)


@click.group()
def tacacs():
    """TACACS+ server configuration"""
    pass


# cmd: tacacs src_ip IP
@click.command()
@click.argument('ip')
def src_ip(ip):
    """Specify TACACS+ source ip address"""
    if not is_ipaddress(ip):
        print 'Invalid ip address'
        return

    set_entry('TACPLUS_SERVER', 'tacplus_global', {
        'src_ip': ip
    })
tacacs.add_command(src_ip)


# cmd: tacacs timeout SECOND
@click.command()
@click.argument('second', type=int)
def timeout(second):
    """Specify TACACS+ server global timeout"""
    # TODO: Need no command
    set_entry('TACPLUS_SERVER', 'tacplus_global', {
        'timeout': second
    })
tacacs.add_command(timeout)


# cmd: tacacs authtype TYPE
@click.command()
@click.argument('type', type=click.Choice(["chap", "pap", "mschap"]))
def authtype(type):
    """Specify TACACS+ server global auth_type"""
    # TODO: Need no command
    set_entry('TACPLUS_SERVER', 'tacplus_global', {
        'auth_type': type
    })
tacacs.add_command(authtype)


# cmd: tacacs passkey SECRET
@click.command()
@click.argument('secret')
def passkey(secret):
    """Specify TACACS+ server global passkey"""
    # TODO: Need no command
    set_entry('TACPLUS_SERVER', 'tacplus_global', {
        'passkey': secret
    })
tacacs.add_command(passkey)


# cmd: tacacs add ADDRESS --timeout SECOND --key SECRET --type TYPE --port PORT --pri PRIORITY
@click.command()
@click.argument('address')
@click.option('-t', '--timeout', help='Transmission timeout interval, default 5', type=int)
@click.option('-k', '--key', help='Shared secret')
@click.option('-a', '--auth_type', help='Authentication type, default pap', type=click.Choice(["chap", "pap", "mschap"]))
@click.option('-o', '--port', help='TCP port range is 1 to 65535, default 49', type=click.IntRange(1, 65535), default=49)
@click.option('-p', '--pri', help="Priority, default 1", type=click.IntRange(1, 64), default=1)
def add(address, timeout, key, auth_type, port, pri):
    """Specify a TACACS+ server"""
    if not is_ipaddress(address):
        print 'Invalid ip address'
        return

    data = {
        'address': address,
        'tcp_port': str(port),
        'priority': pri
    }
    if auth_type is not None:
        data['auth_type'] = auth_type
    if timeout is not None:
        data['timeout'] = str(timeout)
    if key is not None:
        data['passkey'] = key

    set_entry('TACPLUS_SERVER', address, data)
tacacs.add_command(add)


# cmd: tacacs delete ADDRESS
# 'del' is keyword, replace with 'delete'
@click.command()
@click.argument('address')
def delete(address):
    """Delete a TACACS+ server"""
    if not is_ipaddress(address):
        print 'Invalid ip address'
        return

    # config_db = ConfigDBConnector()
    # config_db.connect()
    # TODO: Need del_entry()
tacacs.add_command(delete)


if __name__ == "__main__":
    aaa()

