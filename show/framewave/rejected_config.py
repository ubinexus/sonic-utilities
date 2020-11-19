import click
from swsssdk import SonicDBConfig
from swsscommon.swsscommon import SonicV2Connector
import utilities_common.cli as clicommon
import tabulate as tabulate_module
from tabulate import tabulate

tabulate_module.PRESERVE_WHITESPACE = True

#
# 'rejected-config' command ("show rejected-config")
#
@click.group(name='rejected-config', cls=clicommon.AliasedGroup)
def rejected_config():
    """Show configuration rejected by YMM"""
    return


@rejected_config.command()
def summary():
    """Show rejected-config summary information"""

    key_field_value_dictionary = get_rejected_rows()

    click.echo("Rejected operations:")
    for rejected_key, field_value_map in key_field_value_dictionary.items():
        operation = field_value_map.get("operation")
        click.echo("  " + operation + "  " + rejected_key)


@rejected_config.command()
@click.option('--json', is_flag=True, help="JSON output")
def detail(json):
    """Show rejected-config detail information"""
    if json:
        show_in_json_format()
    else:
        show_in_redis_format()


def show_in_redis_format():
    """Show rejected-config detail information in redis format"""

    key_field_value_dictionary = get_rejected_rows()

    # Looping through all rejected keys and displaying their fields from DB.
    for rejected_key, field_value_map in key_field_value_dictionary.items():
        click.echo(field_value_map.get("operation") + "  " + rejected_key)
        field_value_map.erase("operation")
        field_value_table = []
        # Print (field, values) tuples for current key
        for field in field_value_map:
            value = field_value_map.get(field)
            field_value_table.append(["        ", field, value])
        click.echo(tabulate(field_value_table, tablefmt="plain"))


def show_in_json_format():
    """Show rejected-config detail information in json format"""

    key_field_value_dictionary = get_rejected_rows()

    # Looping through all rejected keys and displaying their fields from DB.
    for rejected_key, field_value_map in key_field_value_dictionary.items():
        config_db_table, config_db_subkeys = \
            rejected_key.split(SonicDBConfig.get_separator("CONFIG_DB"), 1)
        field_value_dictionary = {}
        subkeys_dictionary = {}
        table_dictionary = {}

        operation = field_value_map.get("operation")
        field_value_map.erase("operation")
        click.echo(operation + ":")
        # Build the dictionary to be displayed as Json packets
        for field in field_value_map:
            value = field_value_map.get(field)
            field_value_dictionary[field] = value

        subkeys_dictionary[config_db_subkeys] = field_value_dictionary
        table_dictionary[config_db_table] = subkeys_dictionary
        click.echo(clicommon.json_dump(table_dictionary))


def get_rejected_rows():
    """Read the rejected config stored in APPL_DB"""
    db_connector = SonicV2Connector()
    db_connector.connect(db_connector.APPL_DB)
    key_field_value_dictionary = {}

    # Fetching data from appl db for _REJECTED_CONFIG
    rejected_config_keys = db_connector.keys(db_connector.APPL_DB,
                                             "_REJECTED_CONFIG:*")

    # Loop through all keys from _REJECTED_CONFIG table and store them and   
    # their maps of fields and values in a dictionary.
    # A key from _REJECTED_CONFIG table consists of the name of the table 
    # and the rejected key from CONFIG_DB, delimited by ':'. 
    # For example: _REJECTED_CONFIG:ISIS_SR_PREFIX_MAP|2|ipv4|10.28.0.2/32.
    for rejected_config_key in rejected_config_keys:
        table, config_db_key = \
            rejected_config_key.split(SonicDBConfig.get_separator("APPL_DB"),
                                      1)
        # Get the row from redis APPL_DB
        field_value_map = db_connector.get_all(db_connector.APPL_DB,
                                               rejected_config_key)
        key_field_value_dictionary[config_db_key] = field_value_map

    return key_field_value_dictionary
