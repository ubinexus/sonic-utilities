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
    entry_data_set = set()

    for ns, cfgdb in db.cfgdb_clients.items():
        entry_data = cfgdb.get_entry('FEATURE', name)
        if not entry_data:
            click.echo("Feature '{}' doesn't exist".format(name))
            sys.exit(1)
        entry_data_set.add(entry_data['state'])

    if len(entry_data_set) > 1:
        click.echo("Feature '{}' state is not consistent across namespaces".format(name))
        sys.exit(1)

    if entry_data['state'] == "always_enabled":
        click.echo("Feature '{}' state is always enabled and can not be modified".format(name))
        return

    for ns, cfgdb in db.cfgdb_clients.items():
        cfgdb.mod_entry('FEATURE', name, {'state': state})

#
# 'autorestart' command ('config feature autorestart ...')
#
@feature.command(name='autorestart', short_help="Enable/disable autosrestart of a feature")
@click.argument('name', metavar='<feature-name>', required=True)
@click.argument('autorestart', metavar='<autorestart>', required=True, type=click.Choice(["enabled", "disabled"]))
@pass_db
def feature_autorestart(db, name, autorestart):
    """Enable/disable autorestart of a feature"""
    entry_data_set = set()

    for ns, cfgdb in db.cfgdb_clients.items():
        entry_data = cfgdb.get_entry('FEATURE', name)
        if not entry_data:
            click.echo("Feature '{}' doesn't exist".format(name))
            sys.exit(1)
        entry_data_set.add(entry_data['auto_restart'])

    if len(entry_data_set) > 1:
        click.echo("Feature '{}' auto-restart is not consistent across namespaces".format(name))
        sys.exit(1)

    if entry_data['auto_restart'] == "always_enabled":
        click.echo("Feature '{}' auto-restart is always enabled and can not be modified".format(name))
        return

    for ns, cfgdb in db.cfgdb_clients.items():
        cfgdb.mod_entry('FEATURE', name, {'auto_restart': autorestart})


#
# 'hign_mem_restart' command ('config feature high_mem_restart ...')
#
@feature.command(name='high_mem_restart', short_help="Enable/disable high memory restart of a feature")
@click.argument('feature_name', metavar='<feature_name>', required=True)
@click.argument('high_mem_restart_status', metavar='<high_mem_restart_status>', required=True, type=click.Choice(["enabled", "disabled"]))
@pass_db
def feature_high_mem_restart(db, feature_name, high_mem_restart_status):
    """Enable/disable the high memory restart of a feature"""
    feature_high_mem_restart_status = set()

    for namespace, config_db in db.cfgdb_clients.items():
        feature_table = config_db.get_table('FEATURE')
        if not feature_table:
            click.echo("Unable to retrieve 'FEATURE' table from Config DB.")
            sys.exit(2)

        feature_config = config_db.get_entry('FEATURE', feature_name)
        if not feature_config:
            click.echo("Unable to retrieve configuration of feature '{}' from 'FEATURE' table.".format(feature_name))
            sys.exit(3)

        feature_high_mem_restart_status.add(feature_config['high_mem_restart'])

    if len(feature_high_mem_restart_status) > 1:
        click.echo("High memory restart status of feature '{}' is not consistent across namespaces.".format(feature_name))
        sys.exit(4)

    if feature_config['high_mem_restart'] == "always_enabled":
        click.echo("High memory restart of feature '{}' is always enabled and can not be modified".format(feature_name))
        return

    for namespace, config_db in db.cfgdb_clients.items():
        config_db.mod_entry('FEATURE', feature_name, {'high_mem_restart': high_mem_restart_status})


#
# 'mem_threshold' command ('config feature mem_threshold ...')
#
@feature.command(name='mem_threshold', short_help="Configure the memory threshold (in Bytes) of a feature")
@click.argument('feature_name', metavar='<feature_name>', required=True)
@click.argument('mem_threshold', metavar='<mem_threshold_in_bytes>', required=True)
@pass_db
def feature_mem_threshold(db, feature_name, mem_threshold):
    """Configure the memory threshold of a feature"""
    feature_mem_thresholds = set()

    for namespace, config_db in db.cfgdb_clients.items():
        feature_table = config_db.get_table('FEATURE')
        if not feature_table:
            click.echo("Unable to retrieve 'FEATURE' table from Config DB.")
            sys.exit(5)

        feature_config = config_db.get_entry('FEATURE', feature_name)
        if not feature_config:
            click.echo("Unable to retrieve configuration of feature '{}' from 'FEATURE' table.".format(feature_name))
            sys.exit(6)

        feature_mem_thresholds.add(feature_config['mem_threshold'])

    if len(feature_mem_thresholds) > 1:
        click.echo("Memory threshold of feature '{}' is not consistent across namespaces.".format(feature_name))
        sys.exit(7)

    for namespace, config_db in db.cfgdb_clients.items():
        config_db.mod_entry('FEATURE', feature_name, {'mem_threshold': mem_threshold})
