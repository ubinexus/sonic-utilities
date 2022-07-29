import click

from swsscommon.swsscommon import SonicV2Connector

CHASSIS_MODULE_INFO_TABLE = 'CHASSIS_MODULE_TABLE'
CHASSIS_MODULE_INFO_KEY_TEMPLATE = 'CHASSIS_MODULE {}'
CHASSIS_MODULE_INFO_DESC_FIELD = 'desc'
CHASSIS_MODULE_INFO_SLOT_FIELD = 'slot'
CHASSIS_MODULE_INFO_OPERSTATUS_FIELD = 'oper_status'
CHASSIS_MODULE_INFO_ADMINSTATUS_FIELD = 'admin_status'

CHASSIS_MIDPLANE_INFO_TABLE = 'CHASSIS_MIDPLANE_TABLE'
CHASSIS_MIDPLANE_INFO_IP_FIELD = 'ip_address'
CHASSIS_MIDPLANE_INFO_ACCESS_FIELD = 'access'

def get_linecard_ip(linecard_name: str):
    """Show chassis-modules midplane-status"""

    state_db = SonicV2Connector(host="127.0.0.1")
    state_db.connect(state_db.STATE_DB)

    key_pattern = '*'

    keys = state_db.keys(state_db.STATE_DB, CHASSIS_MIDPLANE_INFO_TABLE + key_pattern)
    if not keys:
        click.echo('{} table is empty'.format(key_pattern, CHASSIS_MIDPLANE_INFO_TABLE))
        return

    for key in keys:
        key_list = key.split('|')
        if len(key_list) != 2:  # error data in DB, log it and ignore
            click.echo('Warn: Invalid Key {} in {} table'.format(key, CHASSIS_MIDPLANE_INFO_TABLE))
            continue

        data_dict = state_db.get_all(state_db.STATE_DB, key)
        ip = data_dict[CHASSIS_MIDPLANE_INFO_IP_FIELD]

        if key_list[1].lower().replace("-","") == linecard_name.lower().replace("-",""):
            return ip
    
    # Not able to find linecard in table
    return

def get_all_linecards(ctx, args, incomplete):
    """Return a list of all accessible linecard names."""

    state_db = SonicV2Connector(host="127.0.0.1")
    state_db.connect(state_db.STATE_DB)

    key_pattern = '*'

    keys = state_db.keys(state_db.STATE_DB, CHASSIS_MIDPLANE_INFO_TABLE + key_pattern)
    if not keys:
        click.echo('{} table is empty'.format(key_pattern, CHASSIS_MIDPLANE_INFO_TABLE))
        return []

    linecards = []

    for key in keys:
        key_list = key.split('|')
        if len(key_list) != 2:  # error data in DB, log it and ignore
            click.echo('Warn: Invalid Key {} in {} table'.format(key, CHASSIS_MIDPLANE_INFO_TABLE))
            continue

        data_dict = state_db.get_all(state_db.STATE_DB, key)
        linecard_name = key_list[1].lower().replace("-","")
        linecard_ip = data_dict[CHASSIS_MIDPLANE_INFO_IP_FIELD]
        
        linecards.append(
            (linecard_name, linecard_ip)
        )
    
    return [lc for lc in linecards if incomplete in lc[0]]
