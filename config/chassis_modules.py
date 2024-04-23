#!/usr/sbin/env python

import click
import time
import utilities_common.cli as clicommon
from .fabric_module_set_admin_status import fabric_module_set_admin_status

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
    return fvs['admin_status']

TIMEOUT_SECS = 10

# Name: get_config_module_state_timeout
# return: True: timeout, False: not timeout
def get_config_module_state_timeout(ctx, db, chassis_module_name, state):
    counter = 0
    while  get_config_module_state(db, chassis_module_name) != state:
        time.sleep(1)
        counter += 1
        if counter >= TIMEOUT_SECS:
            ctx.fail("get_config_module_state {} timeout".format(chassis_module_name))
            return True
            break
    return False

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
    
    config_db.set_entry('CHASSIS_MODULE', chassis_module_name, None)

    if not get_config_module_state_timeout(ctx, db, chassis_module_name, 'up'):
        fabric_module_set_admin_status(chassis_module_name, 'up')
