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
@click.command()
@click.argument('option', type=click.Choice(["enable", "disable", "default"]))
def failthrough(option):
    """Allow AAA fail-through [enable | disable | default]"""
    val = None
    if option == 'enable':
        val = True
    elif option == 'disable':
        val = False

    set_entry('AAA', 'authentication', {
        'failthrough': val
    })
authentication.add_command(failthrough)


# cmd: aaa authentication fallback
@click.command()
@click.argument('option', type=click.Choice(["enable", "disable", "default"]))
def fallback(option):
    """Allow AAA fallback [enable | disable | default]"""
    val = None
    if option == 'enable':
        val = True
    elif option == 'disable':
        val = False

    set_entry('AAA', 'authentication', {
        'fallback': val
    })
authentication.add_command(fallback)


@click.command()
@click.argument('auth_protocol', nargs=-1, type=click.Choice(["tacacs+", "local", "default"]))
def login(auth_protocol):
    """Switch login authentication [ {tacacs+, local} | default ]"""
    if len(auth_protocol) is 0:
        print 'Not support empty argument'
        return

    if 'default' in auth_protocol:
        val = None
    else:
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
def default(ctx):
    """set its default configuration"""
    ctx.obj = 'default'
tacacs.add_command(default)
authentication.add_command(default)


@click.command()
@click.argument('second', metavar='<time_second>', type=click.IntRange(0, 60), required=False)
@click.pass_context
def timeout(ctx, second):
    """Specify TACACS+ server global timeout <0 - 60>"""
    if ctx.obj == 'default':
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
default.add_command(timeout)


@click.command()
@click.argument('type', metavar='<type>', type=click.Choice(["chap", "pap", "mschap"]), required=False)
@click.pass_context
def authtype(ctx, type):
    """Specify TACACS+ server global auth_type [chap | pap | mschap]"""
    if ctx.obj == 'default':
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
default.add_command(authtype)


@click.command()
@click.argument('secret', metavar='<secret_string>', required=False)
@click.pass_context
def passkey(ctx, secret):
    """Specify TACACS+ server global passkey <STRING>"""
    if ctx.obj == 'default':
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
default.add_command(passkey)


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

