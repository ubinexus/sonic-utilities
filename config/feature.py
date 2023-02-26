import sys

import click
from swsscommon import swsscommon
from utilities_common.cli import AbbreviationGroup, pass_db
from .validated_config_db_connector import ValidatedConfigDBConnector

SELECT_TIMEOUT = 1000  # ms


def set_feature_state(cfgdb_clients, name, state, block):
    """Enable/disable a feature"""
    entry_data_set = set()

    for ns, cfgdb in cfgdb_clients.items():
        entry_data = cfgdb.get_entry('FEATURE', name)
        if not entry_data:
            raise Exception("Feature '{}' doesn't exist".format(name))
        entry_data_set.add(entry_data['state'])

    if len(entry_data_set) > 1:
        raise Exception("Feature '{}' state is not consistent across namespaces".format(name))

    if entry_data['state'] == "always_enabled":
        raise Exception("Feature '{}' state is always enabled and can not be modified".format(name))

    for ns, cfgdb in cfgdb_clients.items():
        try:
            config_db = ValidatedConfigDBConnector(cfgdb)
            config_db.mod_entry('FEATURE', name, {'state': state})
        except ValueError as e:
            ctx = click.get_current_context()
            ctx.fail("Invalid ConfigDB. Error: {}".format(e))

    if block:
        db = swsscommon.DBConnector('STATE_DB', 0)
        tbl = swsscommon.SubscriberStateTable(db, 'FEATURE')
        sel = swsscommon.Select()

        sel.addSelectable(tbl);

        while True:
            rc, _ = sel.select(SELECT_TIMEOUT)

            if rc == swsscommon.Select.TIMEOUT:
                continue
            elif rc == swsscommon.Select.ERROR:
                raise Exception('Failed to wait till feature reaches desired state: select() failed')
            else:
                feature, _, fvs = tbl.pop()
                if feature != name:
                    continue

                actual_state = dict(fvs).get('state')

                if actual_state == 'failed':
                    raise Exception('Feature failed to be {}'.format(state))
                elif actual_state == state:
                    break


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
    try:
        config_db = ValidatedConfigDBConnector(db.cfgdb)
        config_db.mod_entry('FEATURE', name, { fld: val })
    except ValueError as e:
        ctx = click.get_current_context()
        ctx.fail("Invalid ConfigDB. Error: {}".format(e))


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
@click.option('--block', is_flag=True, help='Wait till operation is finished')
@pass_db
def feature_state(db, name, state, block):
    """Enable/disable a feature"""

    try:
        set_feature_state(db.cfgdb_clients, name, state, block)
    except Exception as exception:
        click.echo("{}".format(exception))
        sys.exit(1)

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
        try:
            config_db = ValidatedConfigDBConnector(cfgdb)
            config_db.mod_entry('FEATURE', name, {'auto_restart': autorestart})
        except ValueError as e:
            ctx = click.get_current_context()
            ctx.fail("Invalid ConfigDB. Error: {}".format(e))


#
# 'hign_memory_alert' command ('config feature high_memory_alert ...')
#
@feature.command(name='high_memory_alert', short_help="Enable/disable high memory alerting of a feature")
@click.argument('feature_name', metavar='<feature_name>', required=True)
@click.argument('high_memory_alert_status', metavar='<high_memory_alert_status>', required=True, type=click.Choice(["enabled", "disabled"]))
@pass_db
def feature_high_memory_alert(db, feature_name, high_memory_alert_status):
    """Enable/disable the high memory alert of a feature"""
    feature_high_memory_alert_status = set()

    for namespace, config_db in db.cfgdb_clients.items():
        feature_table = config_db.get_table('FEATURE')
        if not feature_table:
            click.echo("Failed to retrieve 'FEATURE' table from 'Config_DB'!")
            sys.exit(2)

        feature_config = config_db.get_entry('FEATURE', feature_name)
        if not feature_config:
            click.echo("Failed to retrieve configuration of feature '{}' from 'FEATURE' table!"
                       .format(feature_name))
            sys.exit(3)

        if "high_mem_alert" in feature_config:
            feature_high_memory_alert_status.add(feature_config['high_mem_alert'])
        else:
            click.echo("Failed to retrieve 'high_mem_alert' field of feature '{}' from 'FEATURE' table!"
                       .format(feature_name))
            sys.exit(4)

    if len(feature_high_memory_alert_status) > 1:
        click.echo("High memory alert status of feature '{}' is not consistent across different namespaces!"
                   .format(feature_name))
        sys.exit(5)

    if feature_config['high_mem_alert'] == "always_enabled":
        click.echo("High memory alert of feature '{}' is always enabled and can not be modified!"
                   .format(feature_name))
        return

    for namespace, config_db in db.cfgdb_clients.items():
        config_db.mod_entry('FEATURE', feature_name, {'high_mem_alert': high_memory_alert_status})


#
# 'memory_threshold' command ('config feature mem_threshold ...')
#
@feature.command(name='memory_threshold', short_help="Configure the memory threshold (in Bytes) of a feature")
@click.argument('feature_name', metavar='<feature_name>', required=True)
@click.argument('mem_threshold', metavar='<mem_threshold_in_bytes>', required=True)
@pass_db
def feature_memory_threshold(db, feature_name, mem_threshold):
    """Configure the memory threshold of a feature"""
    feature_memory_threshold = set()

    for namespace, config_db in db.cfgdb_clients.items():
        feature_table = config_db.get_table('FEATURE')
        if not feature_table:
            click.echo("Failed to retrieve 'FEATURE' table from 'Config_ DB'!")
            sys.exit(6)

        feature_config = config_db.get_entry('FEATURE', feature_name)
        if not feature_config:
            click.echo("Failed to retrieve configuration of feature '{}' from 'FEATURE' table!"
                       .format(feature_name))
            sys.exit(7)

        if "mem_threshold" in feature_config:
            feature_memory_threshold.add(feature_config['mem_threshold'])
        else:
            click.echo("Failed to retrieve 'mem_threshold' field of feature '[]' from 'FEATURE' table!"
                       .format(feature_name))
            sys.exit(8)

    if len(feature_memory_threshold) > 1:
        click.echo("Memory threshold of feature '{}' is not consistent across different namespaces!"
                   .format(feature_name))
        sys.exit(9)

    for namespace, config_db in db.cfgdb_clients.items():
        config_db.mod_entry('FEATURE', feature_name, {'mem_threshold': mem_threshold})
