import click
from swsssdk import ConfigDBConnector
import utilities_common.cli as clicommon

CFG_TACACS_SERVER_MAX_NUM = 8

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
@click.argument('auth_protocol', nargs=-1, type=click.Choice(["tacacs+", "local", "default"]))
def login(auth_protocol):
    """Switch login authentication [ {tacacs+, local} | default ]"""
    if len(auth_protocol) is 0:
        click.echo('Argument "auth_protocol" is required')
        return

    if 'default' in auth_protocol:
        del_table_key('AAA', 'authentication', 'login')
    else:
        val = auth_protocol[0]
        if len(auth_protocol) == 2:
            val += ',' + auth_protocol[1]
        add_table_kv('AAA', 'authentication', 'login', val)
authentication.add_command(login)

# cmd: aaa authorization
@click.command()
@click.argument('protocol', nargs=-1, type=click.Choice([ "tacacs+", "local", "tacacs+ local"]))
def authorization(protocol):
    """Switch AAA authorization [tacacs+ | local | '\"tacacs+ local\"']"""
    if len(protocol) == 0:
        click.echo('Argument "protocol" is required')
        return

    if len(protocol) == 1 and (protocol[0] == 'tacacs+' or protocol[0] == 'local'):
        add_table_kv('AAA', 'authorization', 'login', protocol[0])
    elif len(protocol) == 1 and protocol[0] == 'tacacs+ local':
        add_table_kv('AAA', 'authorization', 'login', 'tacacs+,local')
    else:
        click.echo('Not a valid command')
aaa.add_command(authorization)

# cmd: aaa accounting
@click.command()
@click.argument('protocol', nargs=-1, type=click.Choice(["disable", "tacacs+", "local", "tacacs+ local"]))
def accounting(protocol):
    """Switch AAA accounting [disable | tacacs+ | local | '\"tacacs+ local\"']"""
    if len(protocol) == 0:
        click.echo('Argument "protocol" is required')
        return

    if len(protocol) == 1:
        if protocol[0] == 'tacacs+' or protocol[0] == 'local':
            add_table_kv('AAA', 'accounting', 'login', protocol[0])
        elif protocol[0] == 'tacacs+ local':
            add_table_kv('AAA', 'accounting', 'login', 'tacacs+,local')
        elif protocol[0] == 'disable':
            del_table_key('AAA', 'accounting', 'login')
        else:
            click.echo('Not a valid command')
    else:
        click.echo('Not a valid command')
aaa.add_command(accounting)

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
        click.echo('Argument "second" is required')
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
        click.echo('Argument "type" is required')
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
        add_table_kv('TACPLUS', 'global', 'passkey', secret)
    else:
        click.echo('Argument "secret" is required')
tacacs.add_command(passkey)
default.add_command(passkey)


def tacacs_server_config_num_get(config_db, ctx):
    tacacs_server_table = config_db.get_table('TACPLUS_SERVER')
    num = len(list(tacacs_server_table))
    if num >= CFG_TACACS_SERVER_MAX_NUM:
        ctx.fail("tacacs server reached max size({})".format(CFG_TACACS_SERVER_MAX_NUM))
        return False
    return True


# cmd: tacacs add <ip_address> --timeout SECOND --key SECRET --type TYPE --port PORT --pri PRIORITY
@click.command()
@click.argument('address', metavar='<ip_address>')
@click.option('-t', '--timeout', help='Transmission timeout interval, default 5', type=int)
@click.option('-k', '--key', help='Shared secret')
@click.option('-a', '--auth_type', help='Authentication type, default pap', type=click.Choice(["chap", "pap", "mschap", "login"]))
@click.option('-o', '--port', help='TCP port range is 1 to 65535, default 49', type=click.IntRange(1, 65535), default=49)
@click.option('-p', '--pri', help="Priority, default 1", type=click.IntRange(1, 64), default=1)
@click.option('-m', '--use-mgmt-vrf', help="Management vrf, default is no vrf", is_flag=True)
@click.pass_context
def add(ctx, address, timeout, key, auth_type, port, pri, use_mgmt_vrf):
    """Specify a TACACS+ server"""
    if not clicommon.is_ipaddress(address):
        ctx.fail('Invalid ip address')
        return

    config_db = ConfigDBConnector()
    config_db.connect()
    
    if (False == tacacs_server_config_num_get(config_db, ctx)):
        return
            
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
    if not clicommon.is_ipaddress(address):
        click.echo('Invalid ip address')
        return

    config_db = ConfigDBConnector()
    config_db.connect()
    config_db.set_entry('TACPLUS_SERVER', address, None)
tacacs.add_command(delete)
