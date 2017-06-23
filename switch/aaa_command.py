#!/usr/bin/env python -u
# -*- coding: utf-8 -*-

import click
import aaa_config

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
        aaa_config.set_debug(True)
debug.add_command(on)


@click.command()
@click.pass_context
def off(ctx):
    """Close command"""
    if ctx.obj == 'debug':
        aaa_config.set_debug(False)
debug.add_command(off)


@click.command()
def show():
    """AAA show configuration"""
    aaa_config.show_conf()
aaa.add_command(show)


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
        aaa_config.set_fail_through(True)
failthrough.add_command(enable)


@click.command()
@click.pass_context
def disable(ctx):
    """Disable Command"""
    if ctx.obj == 'failthrough':
        aaa_config.set_fail_through(False)
failthrough.add_command(disable)


@click.command()
@click.argument('pam_priority', nargs=-1, type=click.Choice(["tacacs", "local"]))
def login(pam_priority):
    """Switch login"""
    aaa_config.set_auth_login(pam_priority)
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
    aaa_config.set_src_ip(ip)
tacacs.add_command(src_ip)


# cmd: tacacs add HOST --timeout SECOND --key SECRET --type TYPE --port PORT --pri PRIORITY
@click.command()
@click.argument('host')
@click.option('--timeout', help='Transmission timeout interval', type=int, default=5)
@click.option('--key', help='Shared secret', default='test123')
@click.option('--type', help='Authentication type', type=click.Choice(["chap", "pap"]), default='pap')
@click.option('--port', help='TCP port range is 1 to 65535', type=click.IntRange(1, 65535), default=49)
@click.option('--pri', help="Priority", type=click.IntRange(1, 512), default=1)
def add(host, timeout, key, type, port, pri):
    """Specify a TACACS+ server"""
    aaa_config.add_server(host, str(port), key, str(timeout), type, pri)
tacacs.add_command(add)


# cmd: tacacs delete HOST
# 'del' is keyword, replace with 'delete'
@click.command()
@click.argument('host')
def delete(host):
    """Delete a TACACS+ server"""
    aaa_config.del_server(host)
tacacs.add_command(delete)


if __name__ == "__main__":
    aaa()

