#!/usr/sbin/env python

import click
import time
import re
from swsscommon.swsscommon import SonicV2Connector
import utilities_common.cli as clicommon

#
# 'chassis_modules' group ('config chassis_modules ...')
#
@click.group(cls=clicommon.AliasedGroup)
def chassis():
    """Configure chassis commands group"""
    pass

@chassis.group()
def modules():
    """Configure chassis modules"""
    pass

def get_config_module_state(db, chassis_module_name):
    config_db = db.cfgdb
    fvs = config_db.get_entry('CHASSIS_MODULE', chassis_module_name)
    if not fvs:
        return 'up'
    else:
        return fvs['admin_status']

TIMEOUT_SECS = 10

#
# Name: get_config_module_state_timeout
# return: True: timeout, False: not timeout
#
def get_config_module_state_timeout(ctx, db, chassis_module_name, state):
    counter = 0
    while  get_config_module_state(db, chassis_module_name) != state:
        time.sleep(1)
        counter += 1
        if counter >= TIMEOUT_SECS:
            ctx.fail("get_config_module_state {} timeout".format(chassis_module_name))
            return True
    return False

def get_asic_list_from_db(chassisdb, chassis_module_name):
    asic_list = []
    asics_keys_list = chassisdb.keys("CHASSIS_STATE_DB", "CHASSIS_FABRIC_ASIC_TABLE*")
    for asic_key in asics_keys_list:
        name = chassisdb.get("CHASSIS_STATE_DB", asic_key, "name")
        if name == chassis_module_name:
            asic_id = int(re.search(r"(\d+)$", asic_key).group())
            asic_list.append(asic_id)
    return asic_list

#
# Syntax: fabric_module_set_admin_status <chassis_module_name> <'up'/'down'>
#
def fabric_module_set_admin_status(chassis_module_name, state):
    chassisdb = SonicV2Connector(host="127.0.0.1")
    chassisdb.connect("CHASSIS_STATE_DB")
    asic_list = get_asic_list_from_db(chassisdb, chassis_module_name)

    if len(asic_list) == 0:
        return

    if state == "down":
        for asic in asic_list:
            click.echo("Stop swss@{} and syncd@{} ...".format(asic, asic))
            clicommon.run_command('sudo systemctl stop swss@{}.service'.format(asic))
            # wait for service is down
            time.sleep(2)
            chassisdb.delete("CHASSIS_STATE_DB","CHASSIS_FABRIC_ASIC_TABLE|asic" + str(asic))
            click.echo("Start swss@{} and syncd@{} ...".format(asic, asic))
            clicommon.run_command('sudo systemctl start swss@{}.service'.format(asic))
    else:
        for asic in asic_list:
            click.echo("Start swss@{} and syncd@{} ...".format(asic, asic))
            clicommon.run_command('sudo systemctl start swss@{}.service'.format(asic))

#
# 'shutdown' subcommand ('config chassis_modules shutdown ...')
#
@modules.command('shutdown')
@clicommon.pass_db
@click.argument('chassis_module_name', metavar='<module_name>', required=True)
def shutdown_chassis_module(db, chassis_module_name):
    """Chassis-module shutdown of module"""
    config_db = db.cfgdb
    ctx = click.get_current_context()

    if not chassis_module_name.startswith("SUPERVISOR") and \
       not chassis_module_name.startswith("LINE-CARD") and \
       not chassis_module_name.startswith("FABRIC-CARD"):
        ctx.fail("'module_name' has to begin with 'SUPERVISOR', 'LINE-CARD' or 'FABRIC-CARD'")

    #To avoid duplicate operation
    if get_config_module_state(db, chassis_module_name) == 'down':
        click.echo("Module {} is already in down state".format(chassis_module_name))
        return

    if chassis_module_name.startswith("FABRIC-CARD"):
        click.echo("Shutting down chassis module {}".format(chassis_module_name))        
        fvs = {'admin_status': 'down'}
        config_db.set_entry('CHASSIS_MODULE', chassis_module_name, fvs)
        if not get_config_module_state_timeout(ctx, db, chassis_module_name, 'down'):
            fabric_module_set_admin_status(chassis_module_name, 'down')

#
# 'startup' subcommand ('config chassis_modules startup ...')
#
@modules.command('startup')
@clicommon.pass_db
@click.argument('chassis_module_name', metavar='<module_name>', required=True)
def startup_chassis_module(db, chassis_module_name):
    """Chassis-module startup of module"""
    config_db = db.cfgdb
    ctx = click.get_current_context()

    #To avoid duplicate operation
    if get_config_module_state(db, chassis_module_name) == 'up':
        click.echo("Module {} is already set to up state".format(chassis_module_name))
        return

    if chassis_module_name.startswith("FABRIC-CARD"):
        click.echo("Starting up chassis module {}".format(chassis_module_name))
        config_db.set_entry('CHASSIS_MODULE', chassis_module_name, None)
        if not get_config_module_state_timeout(ctx, db, chassis_module_name, 'up'):
            fabric_module_set_admin_status(chassis_module_name, 'up')
