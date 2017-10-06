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


# cmd: aaa authentication fallback
@click.group()
@click.pass_context
def fallback(ctx):
    """Allow AAA fallback"""
    ctx.obj = "fallback"
authentication.add_command(fallback)


@click.command()
@click.pass_context
def enable(ctx):
    """Enable Command"""
    if ctx.obj == 'failthrough':
        set_entry('AAA', 'authentication', {
            'failthrough': True
        })
    elif ctx.obj == 'fallback':
        set_entry('AAA', 'authentication', {
            'fallback': True
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
    elif ctx.obj == 'fallback':
        set_entry('AAA', 'authentication', {
            'fallback': False
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


@click.group()
@click.pass_context
def no(ctx):
    """Negate a command or set its defaults"""
    ctx.obj = 'no'
tacacs.add_command(no)


@click.command()
@click.argument('second', metavar='<time_second>', type=int, required=False)
@click.pass_context
def timeout(ctx, second):
    """Specify TACACS+ server global timeout"""
    if ctx.obj == 'no':
        set_entry('TACPLUS', 'global', {
            'timeout': None
        })
    elif second:
        set_entry('TACPLUS', 'global', {
            'timeout': second
        })
    else:
        click.echo('Not support empty argument')
tacacs.add_command(timeout)
no.add_command(timeout)


@click.command()
@click.argument('type', metavar='<type>', type=click.Choice(["chap", "pap", "mschap"]), required=False)
@click.pass_context
def authtype(ctx, type):
    """Specify TACACS+ server global auth_type"""
    if ctx.obj == 'no':
        set_entry('TACPLUS', 'global', {
            'auth_type': None
        })
    elif type:
        set_entry('TACPLUS', 'global', {
            'auth_type': type
        })
    else:
        click.echo('Not support empty argument')
tacacs.add_command(authtype)
no.add_command(authtype)


@click.command()
@click.argument('secret', metavar='<secret_string>', required=False)
@click.pass_context
def passkey(ctx, secret):
    """Specify TACACS+ server global passkey"""
    if ctx.obj == 'no':
        set_entry('TACPLUS', 'global', {
            'passkey': None
        })
    elif secret:
        set_entry('TACPLUS', 'global', {
            'passkey': secret
        })
    else:
        click.echo('Not support empty argument')
tacacs.add_command(passkey)
no.add_command(passkey)


# cmd: tacacs add <ip_address> --timeout SECOND --key SECRET --type TYPE --port PORT --pri PRIORITY
@click.command()
@click.argument('address', metavar='<ip_address>')
@click.option('-t', '--timeout', help='Transmission timeout interval, default 5', type=int)
@click.option('-k', '--key', help='Shared secret')
@click.option('-a', '--auth_type', help='Authentication type, default pap', type=click.Choice(["chap", "pap", "mschap"]))
@click.option('-o', '--port', help='TCP port range is 1 to 65535, default 49', type=click.IntRange(1, 65535), default=49)
@click.option('-p', '--pri', help="Priority, default 1", type=click.IntRange(1, 64), default=1)
def add(address, timeout, key, auth_type, port, pri):
    """Specify a TACACS+ server"""
    if not is_ipaddress(address):
        click.echo('Invalid ip address')
        return

    config_db = ConfigDBConnector()
    config_db.connect()
    old_data = config_db.get_entry('TACPLUS_SERVER', address)
    if old_data != {}:
        click.echo('server %s already exists' % address)
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

    set_entry('TACPLUS_SERVER', address, None)
tacacs.add_command(delete)


if __name__ == "__main__":
    aaa()

