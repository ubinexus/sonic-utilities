import sys
import click
from natsort import natsorted
from tabulate import tabulate

from utilities_common.cli import AbbreviationGroup, pass_db
from swsssdk import ConfigDBConnector

#
# 'feature' group (show feature ...)
#
@click.group(cls=AbbreviationGroup, name='feature', invoke_without_command=False)
def feature():
    """Show feature status"""
    pass


def make_body(name, fields, defaults, data):
    body = [ name ]
    i = 0
    for fld in fields:
        body.append(data[fld] if fld in data else defaults[i])
        i += 1

    return body


#
# 'status' subcommand (show feature status)
#
@feature.command('status', short_help="Show feature state")
@click.argument('feature_name', required=False)
@pass_db
def feature_status(db, feature_name):
    fields = [
            ('State', 'state', ""),
            ('AutoRestart', 'auto_restart', ""),
            ('SystemState', 'system_state', ""),
            ('UpdateTime', 'update_time', ""),
            ('ContainerId', 'container_id', ""),
            ('ContainerVersion', 'container_version', ""),
            ('CurrentOwner', 'current_owner', ""),
            ('RemoteState', "remote_state", "none")
            ]
    header = ["Feature"]
    field_names = []
    field_defaults = []
    for k in fields:
        header.append(k[0])
        field_names.append(k[1])
        field_defaults.append(k[2])

    state_db = ConfigDBConnector()
    state_db.db_connect("STATE_DB", wait_for_init=False, retry_on=True)
    state_table = state_db.get_table('FEATURE')

    feature_table = db.cfgdb.get_table('FEATURE')
    body = []
    if feature_name:
        if feature_table.has_key(feature_name):
            data = feature_table[feature_name]
            if feature_name in state_table:
                data.update(state_table[feature_name])
            body.append(make_body(feature_name, field_names, field_defaults, data))
        else:
            click.echo("Can not find feature {}".format(feature_name))
            sys.exit(1)
    else:
        for key in natsorted(feature_table.keys()):
            data = feature_table[key]
            if key in state_table:
                data.update(state_table[key])
            body.append(make_body(key, field_names, field_defaults, data))
    click.echo(tabulate(body, header))

#
# 'config' subcommand (show feature config)
#
@feature.command('config', short_help="Show feature config")
@click.argument('feature_name', required=False)
@pass_db
def feature_config(db, feature_name):
    fields = [
            ('State', 'state', ""),
            ('AutoRestart', 'auto_restart', ""),
            ('Owner', 'set_owner', "local"),
            ('no-fallback', 'no_fallback_to_local', "false")
            ]
    header = ["Feature"]
    field_names = []
    field_defaults = []
    for k in fields:
        header.append(k[0])
        field_names.append(k[1])
        field_defaults.append(k[2])

    feature_table = db.cfgdb.get_table('FEATURE')
    body = []
    if feature_name:
        if feature_table.has_key(feature_name):
            data = feature_table[feature_name]
            body.append(make_body(feature_name, field_names, field_defaults, data))
        else:
            click.echo("Can not find feature {}".format(feature_name))
            sys.exit(1)
    else:
        for key in natsorted(feature_table.keys()):
            data = feature_table[key]
            body.append(make_body(key, field_names, field_defaults, data))
    click.echo(tabulate(body, header))


#
# 'autorestart' subcommand (show feature autorestart)
#
@feature.command('autorestart', short_help="Show auto-restart state for a feature")
@click.argument('feature_name', required=False)
@pass_db
def feature_autorestart(db, feature_name):
    header = ['Feature', 'AutoRestart']
    body = []
    feature_table = db.cfgdb.get_table('FEATURE')
    if feature_name:
        if feature_table and feature_table.has_key(feature_name):
            body.append([feature_name, feature_table[feature_name]['auto_restart']])
        else:
            click.echo("Can not find feature {}".format(feature_name))
            sys.exit(1)
    else:
        for name in natsorted(feature_table.keys()):
            body.append([name, feature_table[name]['auto_restart']])
    click.echo(tabulate(body, header))
