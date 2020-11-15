import sys

import click
from utilities_common.cli import AbbreviationGroup, pass_db

#
# 'feature' group ('config feature ...')
#
@click.group(cls=AbbreviationGroup, name='feature', invoke_without_command=False)
def feature():
    """Configure features"""
    pass

def _update_field(db, name, fld, val):
    tbl = db.cfgdb.get_table('FEATURE')
    if name not in tbl:
        click.echo("Unable to retrieve {} from FEATURE table".format(name))
        sys.exit(1)
    db.cfgdb.mod_entry('FEATURE', name, { fld: val })
    

#
# 'owner' command ('config feature owner ...')
#
@feature.command('owner', short_help="set owner for a feature")
@click.argument('name', metavar='<feature-name>', required=True)
@click.argument('owner', metavar='<owner>', required=True, type=click.Choice(["local", "kube"]))
@pass_db
def feature_owner(db, name, owner):
    """Set owner for the feature"""
    _update_field(db, name, "set_owner", owner)


#
# 'fallback' command ('config feature fallback ...')
#
@feature.command('fallback', short_help="set fallback for a feature")
@click.argument('name', metavar='<feature-name>', required=True)
@click.argument('fallback', metavar='<fallback>', required=True, type=click.Choice(["on", "off"]))
@pass_db
def feature_fallback(db, name, fallback):
    """Set fallback for the feature"""
    _update_field(db, name, "no_fallback_to_local", "false" if fallback == "on" else "true")


#
# 'state' command ('config feature state ...')
#
@feature.command('state', short_help="Enable/disable a feature")
@click.argument('name', metavar='<feature-name>', required=True)
@click.argument('state', metavar='<state>', required=True, type=click.Choice(["enabled", "disabled"]))
@pass_db
def feature_state(db, name, state):
    """Enable/disable a feature"""
    state_data = db.cfgdb.get_entry('FEATURE', name)

    if not state_data:
        click.echo("Feature '{}' doesn't exist".format(name))
        sys.exit(1)

    db.cfgdb.mod_entry('FEATURE', name, {'state': state})

#
# 'autorestart' command ('config feature autorestart ...')
#
@feature.command(name='autorestart', short_help="Enable/disable autosrestart of a feature")
@click.argument('name', metavar='<feature-name>', required=True)
@click.argument('autorestart', metavar='<autorestart>', required=True, type=click.Choice(["enabled", "disabled"]))
@pass_db
def feature_autorestart(db, name, autorestart):
    """Enable/disable autorestart of a feature"""
    feature_table = db.cfgdb.get_table('FEATURE')
    if not feature_table:
        click.echo("Unable to retrieve feature table from Config DB.")
        sys.exit(1)

    if name not in feature_table:
        click.echo("Unable to retrieve feature '{}'".format(name))
        sys.exit(1)

    db.cfgdb.mod_entry('FEATURE', name, {'auto_restart': autorestart})
