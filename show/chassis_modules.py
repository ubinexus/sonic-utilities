import click
from natsort import natsorted
from tabulate import tabulate
from swsssdk import SonicV2Connector

import utilities_common.cli as clicommon

CHASSIS_MODULE_INFO_TABLE = 'CHASSIS_MODULE_TABLE'
CHASSIS_MODULE_INFO_KEY_TEMPLATE = 'CHASSIS_MODULE {}'
CHASSIS_MODULE_INFO_DESC_FIELD = 'desc'
CHASSIS_MODULE_INFO_SLOT_FIELD = 'slot'
CHASSIS_MODULE_INFO_OPERSTATUS_FIELD = 'oper_status'
CHASSIS_MODULE_INFO_ADMINSTATUS_FIELD = 'admin_status'

@click.group(cls=clicommon.AliasedGroup)
def chassis_modules():
    """Show chassis-modules information"""
    pass

@chassis_modules.command()
@clicommon.pass_db
@click.argument('chassis_module_name', metavar='<module_name>', required=False)
def status(db, chassis_module_name):
    """Show chassis-modules status"""

    header = ['Name', 'Description', 'Slot', 'Oper-Status', 'Admin-Status']
    chassis_cfg_table = db.cfgdb.get_table('CHASSIS_MODULE')

    state_db = SonicV2Connector(host="127.0.0.1")
    state_db.connect(state_db.STATE_DB)

    keys = state_db.keys(state_db.STATE_DB, CHASSIS_MODULE_INFO_TABLE + '*')
    if not keys:
        print('Chassis-Module Not detected\n')
        return

    table = []
    for key in natsorted(keys):
        key_list = key.split('|')
        if len(key_list) != 2: # error data in DB, log it and ignore
            print('Warn: Invalid key in table CHASSIS_MODULE_TABLE: {}'.format(key))
            continue

        if chassis_module_name and (key_list[1] != chassis_module_name):
            continue

        data_dict = state_db.get_all(state_db.STATE_DB, key)
        desc = data_dict[CHASSIS_MODULE_INFO_DESC_FIELD]
        slot = data_dict[CHASSIS_MODULE_INFO_SLOT_FIELD]
        oper_status = data_dict[CHASSIS_MODULE_INFO_OPERSTATUS_FIELD]

        admin_status = 'up'
        config_data = chassis_cfg_table.get(key_list[1])
        if config_data is not None:
            admin_status = config_data.get(CHASSIS_MODULE_INFO_ADMINSTATUS_FIELD)

        table.append((key_list[1], desc, slot, oper_status, admin_status))

    if table:
        click.echo(tabulate(table, header, tablefmt='simple', stralign='right'))
    else:
        click.echo('No chassis_module status data available\n')
