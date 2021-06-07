"""
Autogenerated config CLI plugin.


"""

import click
import utilities_common.cli as clicommon
import utilities_common.general as general
from config import config_mgmt


# Load sonic-cfggen from source since /usr/local/bin/sonic-cfggen does not have .py extension.
sonic_cfggen = general.load_module_from_source('sonic_cfggen', '/usr/local/bin/sonic-cfggen')


def exit_with_error(*args, **kwargs):
    """ Print a message and abort CLI. """

    click.secho(*args, **kwargs)
    raise click.Abort()


def validate_config_or_raise(cfg):
    """ Validate config db data using ConfigMgmt """

    try:
        cfg = sonic_cfggen.FormatConverter.to_serialized(cfg)
        config_mgmt.ConfigMgmt().loadData(cfg)
    except Exception as err:
        raise Exception('Failed to validate configuration: {}'.format(err))


def add_entry_validated(db, table, key, data):
    """ Add new entry in table and validate configuration """

    cfg = db.get_config()
    cfg.setdefault(table, {})
    if key in cfg[table]:
        raise Exception(f"{key} already exists")

    cfg[table][key] = data

    validate_config_or_raise(cfg)
    db.set_entry(table, key, data)


def update_entry_validated(db, table, key, data, create_if_not_exists=False):
    """ Update entry in table and validate configuration.
    If attribute value in data is None, the attribute is deleted.
    """

    cfg = db.get_config()
    cfg.setdefault(table, {})

    if create_if_not_exists:
        cfg[table].setdefault(key, {})

    if key not in cfg[table]:
        raise Exception(f"{key} does not exist")

    for attr, value in data.items():
        if value is None and attr in cfg[table][key]:
            cfg[table][key].pop(attr)
        else:
            cfg[table][key][attr] = value

    validate_config_or_raise(cfg)
    db.set_entry(table, key, cfg[table][key])


def del_entry_validated(db, table, key):
    """ Delete entry in table and validate configuration """

    cfg = db.get_config()
    cfg.setdefault(table, {})
    if key not in cfg[table]:
        raise Exception(f"{key} does not exist")

    cfg[table].pop(key)

    validate_config_or_raise(cfg)
    db.set_entry(table, key, None)


def add_list_entry_validated(db, table, key, attr, data):
    """ Add new entry into list in table and validate configuration"""

    cfg = db.get_config()
    cfg.setdefault(table, {})
    if key not in cfg[table]:
        raise Exception(f"{key} does not exist")
    cfg[table][key].setdefault(attr, [])
    for entry in data:
        if entry in cfg[table][key][attr]:
            raise Exception(f"{entry} already exists")
        cfg[table][key][attr].append(entry)

    validate_config_or_raise(cfg)
    db.set_entry(table, key, cfg[table][key])


def del_list_entry_validated(db, table, key, attr, data):
    """ Delete entry from list in table and validate configuration"""

    cfg = db.get_config()
    cfg.setdefault(table, {})
    if key not in cfg[table]:
        raise Exception(f"{key} does not exist")
    cfg[table][key].setdefault(attr, [])
    for entry in data:
        if entry not in cfg[table][key][attr]:
            raise Exception(f"{entry} does not exist")
        cfg[table][key][attr].remove(entry)
    if not cfg[table][key][attr]:
        cfg[table][key].pop(attr)

    validate_config_or_raise(cfg)
    db.set_entry(table, key, cfg[table][key])


def clear_list_entry_validated(db, table, key, attr):
    """ Clear list in object and validate configuration"""

    update_entry_validated(db, table, key, {attr: None})





































@click.group(name="pbh-hash-field",
             cls=clicommon.AliasedGroup)
def PBH_HASH_FIELD():
    """ PBH_HASH_FIELD part of config_db.json """

    pass












@PBH_HASH_FIELD.command(name="add")

@click.argument(
    "hash-field-name",
    nargs=1,
    required=True,
)

@click.option(
    "--hash-field",
    help="Configures native hash field for this hash field[mandatory]",
)
@click.option(
    "--ip-mask",
    help="Configures IPv4/IPv6 address mask for this hash field[mandatory]",
)
@click.option(
    "--sequence-id",
    help="Configures in which order the fields are hashed and defines which fields should be associative[mandatory]",
)
@clicommon.pass_db
def PBH_HASH_FIELD_add(db, hash_field_name, hash_field, ip_mask, sequence_id):
    """ Add object in PBH_HASH_FIELD. """

    table = "PBH_HASH_FIELD"
    key = hash_field_name
    data = {}
    if hash_field is not None:
        data["hash_field"] = hash_field
    if ip_mask is not None:
        data["ip_mask"] = ip_mask
    if sequence_id is not None:
        data["sequence_id"] = sequence_id

    try:
        add_entry_validated(db.cfgdb, table, key, data)
    except Exception as err:
        exit_with_error(f"Error: {err}", fg="red")


@PBH_HASH_FIELD.command(name="update")

@click.argument(
    "hash-field-name",
    nargs=1,
    required=True,
)

@click.option(
    "--hash-field",
    help="Configures native hash field for this hash field[mandatory]",
)
@click.option(
    "--ip-mask",
    help="Configures IPv4/IPv6 address mask for this hash field[mandatory]",
)
@click.option(
    "--sequence-id",
    help="Configures in which order the fields are hashed and defines which fields should be associative[mandatory]",
)
@clicommon.pass_db
def PBH_HASH_FIELD_update(db, hash_field_name, hash_field, ip_mask, sequence_id):
    """ Add object in PBH_HASH_FIELD. """

    table = "PBH_HASH_FIELD"
    key = hash_field_name
    data = {}
    if hash_field is not None:
        data["hash_field"] = hash_field
    if ip_mask is not None:
        data["ip_mask"] = ip_mask
    if sequence_id is not None:
        data["sequence_id"] = sequence_id

    try:
        update_entry_validated(db.cfgdb, table, key, data)
    except Exception as err:
        exit_with_error(f"Error: {err}", fg="red")


@PBH_HASH_FIELD.command(name="delete")

@click.argument(
    "hash-field-name",
    nargs=1,
    required=True,
)
@clicommon.pass_db
def PBH_HASH_FIELD_delete(db, hash_field_name):
    """ Delete object in PBH_HASH_FIELD. """

    table = "PBH_HASH_FIELD"
    key = hash_field_name
    try:
        del_entry_validated(db.cfgdb, table, key)
    except Exception as err:
        exit_with_error(f"Error: {err}", fg="red")















@click.group(name="pbh-hash",
             cls=clicommon.AliasedGroup)
def PBH_HASH():
    """ PBH_HASH part of config_db.json """

    pass












@PBH_HASH.command(name="add")

@click.argument(
    "hash-name",
    nargs=1,
    required=True,
)

@click.option(
    "--hash-field-list",
    help="The list of hash fields to apply with this hash",
)
@clicommon.pass_db
def PBH_HASH_add(db, hash_name, hash_field_list):
    """ Add object in PBH_HASH. """

    table = "PBH_HASH"
    key = hash_name
    data = {}
    if hash_field_list is not None:
        data["hash_field_list"] = hash_field_list.split(",")

    try:
        add_entry_validated(db.cfgdb, table, key, data)
    except Exception as err:
        exit_with_error(f"Error: {err}", fg="red")


@PBH_HASH.command(name="update")

@click.argument(
    "hash-name",
    nargs=1,
    required=True,
)

@click.option(
    "--hash-field-list",
    help="The list of hash fields to apply with this hash",
)
@clicommon.pass_db
def PBH_HASH_update(db, hash_name, hash_field_list):
    """ Add object in PBH_HASH. """

    table = "PBH_HASH"
    key = hash_name
    data = {}
    if hash_field_list is not None:
        data["hash_field_list"] = hash_field_list.split(",")

    try:
        update_entry_validated(db.cfgdb, table, key, data)
    except Exception as err:
        exit_with_error(f"Error: {err}", fg="red")


@PBH_HASH.command(name="delete")

@click.argument(
    "hash-name",
    nargs=1,
    required=True,
)
@clicommon.pass_db
def PBH_HASH_delete(db, hash_name):
    """ Delete object in PBH_HASH. """

    table = "PBH_HASH"
    key = hash_name
    try:
        del_entry_validated(db.cfgdb, table, key)
    except Exception as err:
        exit_with_error(f"Error: {err}", fg="red")







@PBH_HASH.group(name="hash-field-list",
                   cls=clicommon.AliasedGroup)
def PBH_HASH_hash_field_list():
    """ Add/Delete hash_field_list in PBH_HASH """

    pass


@PBH_HASH_hash_field_list.command(name="add")

@click.argument(
    "hash-name",
    nargs=1,
    required=True,
)
@click.argument(
    "hash-field-list",
    nargs=-1,
    required=True,
)
@clicommon.pass_db
def PBH_HASH_hash_field_list_add(
    db,
    hash_name, hash_field_list
):
    """ Add hash_field_list in PBH_HASH """

    table = "PBH_HASH"
    key = hash_name
    attr = "hash_field_list"
    data = hash_field_list

    try:
        add_list_entry_validated(db.cfgdb, table, key, attr, data)
    except Exception as err:
        exit_with_error(f"Error: {err}", fg="red")



@PBH_HASH_hash_field_list.command(name="delete")

@click.argument(
    "hash-name",
    nargs=1,
    required=True,
)
@click.argument(
    "hash-field-list",
    nargs=-1,
    required=True,
)
@clicommon.pass_db
def PBH_HASH_hash_field_list_delete(
    db, 
    hash_name, hash_field_list
):
    """ Delete hash_field_list in PBH_HASH """

    table = "PBH_HASH"
    key = hash_name
    attr = "hash_field_list"
    data = hash_field_list

    try:
        del_list_entry_validated(db.cfgdb, table, key, attr, data)
    except Exception as err:
        exit_with_error(f"Error: {err}", fg="red")



@PBH_HASH_hash_field_list.command(name="clear")

@click.argument(
    "hash-name",
    nargs=1,
    required=True,
)
@clicommon.pass_db
def PBH_HASH_hash_field_list_clear(
    db, 
    hash_name
):
    """ Clear hash_field_list in PBH_HASH """

    table = "PBH_HASH"
    key = hash_name
    attr = "hash_field_list"

    try:
        clear_list_entry_validated(db.cfgdb, table, key, attr)
    except Exception as err:
        exit_with_error(f"Error: {err}", fg="red")










@click.group(name="pbh-rule",
             cls=clicommon.AliasedGroup)
def PBH_RULE():
    """ PBH_RULE part of config_db.json """

    pass












@PBH_RULE.command(name="add")

@click.argument(
    "table-name",
    nargs=1,
    required=True,
)
@click.argument(
    "rule-name",
    nargs=1,
    required=True,
)

@click.option(
    "--priority",
    help="Configures priority for this rule[mandatory]",
)
@click.option(
    "--gre-key",
    help="Configures packet match for this rule: GRE key (value/mask)",
)
@click.option(
    "--ip-protocol",
    help="Configures packet match for this rule: IP protocol (value/mask)",
)
@click.option(
    "--ipv6-next-header",
    help="Configures packet match for this rule: IPv6 Next header (value/mask)",
)
@click.option(
    "--l4-dst-port",
    help="Configures packet match for this rule: L4 destination port (value/mask)",
)
@click.option(
    "--inner-ether-type",
    help="Configures packet match for this rule: inner EtherType (value/mask)",
)
@click.option(
    "--hash",
    help="The hash to apply with this rule[mandatory]",
)
@click.option(
    "--packet-action",
    help="Configures packet action for this rule",
)
@click.option(
    "--flow-counter",
    help="Enables/Disables packet/byte counter for this rule",
)
@clicommon.pass_db
def PBH_RULE_add(db, table_name, rule_name, priority, gre_key, ip_protocol, ipv6_next_header, l4_dst_port, inner_ether_type, hash, packet_action, flow_counter):
    """ Add object in PBH_RULE. """

    table = "PBH_RULE"
    key = table_name, rule_name
    data = {}
    if priority is not None:
        data["priority"] = priority
    if gre_key is not None:
        data["gre_key"] = gre_key
    if ip_protocol is not None:
        data["ip_protocol"] = ip_protocol
    if ipv6_next_header is not None:
        data["ipv6_next_header"] = ipv6_next_header
    if l4_dst_port is not None:
        data["l4_dst_port"] = l4_dst_port
    if inner_ether_type is not None:
        data["inner_ether_type"] = inner_ether_type
    if hash is not None:
        data["hash"] = hash
    if packet_action is not None:
        data["packet_action"] = packet_action
    if flow_counter is not None:
        data["flow_counter"] = flow_counter

    try:
        add_entry_validated(db.cfgdb, table, key, data)
    except Exception as err:
        exit_with_error(f"Error: {err}", fg="red")


@PBH_RULE.command(name="update")

@click.argument(
    "table-name",
    nargs=1,
    required=True,
)
@click.argument(
    "rule-name",
    nargs=1,
    required=True,
)

@click.option(
    "--priority",
    help="Configures priority for this rule[mandatory]",
)
@click.option(
    "--gre-key",
    help="Configures packet match for this rule: GRE key (value/mask)",
)
@click.option(
    "--ip-protocol",
    help="Configures packet match for this rule: IP protocol (value/mask)",
)
@click.option(
    "--ipv6-next-header",
    help="Configures packet match for this rule: IPv6 Next header (value/mask)",
)
@click.option(
    "--l4-dst-port",
    help="Configures packet match for this rule: L4 destination port (value/mask)",
)
@click.option(
    "--inner-ether-type",
    help="Configures packet match for this rule: inner EtherType (value/mask)",
)
@click.option(
    "--hash",
    help="The hash to apply with this rule[mandatory]",
)
@click.option(
    "--packet-action",
    help="Configures packet action for this rule",
)
@click.option(
    "--flow-counter",
    help="Enables/Disables packet/byte counter for this rule",
)
@clicommon.pass_db
def PBH_RULE_update(db, table_name, rule_name, priority, gre_key, ip_protocol, ipv6_next_header, l4_dst_port, inner_ether_type, hash, packet_action, flow_counter):
    """ Add object in PBH_RULE. """

    table = "PBH_RULE"
    key = table_name, rule_name
    data = {}
    if priority is not None:
        data["priority"] = priority
    if gre_key is not None:
        data["gre_key"] = gre_key
    if ip_protocol is not None:
        data["ip_protocol"] = ip_protocol
    if ipv6_next_header is not None:
        data["ipv6_next_header"] = ipv6_next_header
    if l4_dst_port is not None:
        data["l4_dst_port"] = l4_dst_port
    if inner_ether_type is not None:
        data["inner_ether_type"] = inner_ether_type
    if hash is not None:
        data["hash"] = hash
    if packet_action is not None:
        data["packet_action"] = packet_action
    if flow_counter is not None:
        data["flow_counter"] = flow_counter

    try:
        update_entry_validated(db.cfgdb, table, key, data)
    except Exception as err:
        exit_with_error(f"Error: {err}", fg="red")


@PBH_RULE.command(name="delete")

@click.argument(
    "table-name",
    nargs=1,
    required=True,
)
@click.argument(
    "rule-name",
    nargs=1,
    required=True,
)
@clicommon.pass_db
def PBH_RULE_delete(db, table_name, rule_name):
    """ Delete object in PBH_RULE. """

    table = "PBH_RULE"
    key = table_name, rule_name
    try:
        del_entry_validated(db.cfgdb, table, key)
    except Exception as err:
        exit_with_error(f"Error: {err}", fg="red")



























@click.group(name="pbh-table",
             cls=clicommon.AliasedGroup)
def PBH_TABLE():
    """ PBH_TABLE part of config_db.json """

    pass












@PBH_TABLE.command(name="add")

@click.argument(
    "table-name",
    nargs=1,
    required=True,
)

@click.option(
    "--description",
    help="The description of this table[mandatory]",
)
@click.option(
    "--interface-list",
    help="Interfaces to which this table is applied",
)
@clicommon.pass_db
def PBH_TABLE_add(db, table_name, description, interface_list):
    """ Add object in PBH_TABLE. """

    table = "PBH_TABLE"
    key = table_name
    data = {}
    if description is not None:
        data["description"] = description
    if interface_list is not None:
        data["interface_list"] = interface_list.split(",")

    try:
        add_entry_validated(db.cfgdb, table, key, data)
    except Exception as err:
        exit_with_error(f"Error: {err}", fg="red")


@PBH_TABLE.command(name="update")

@click.argument(
    "table-name",
    nargs=1,
    required=True,
)

@click.option(
    "--description",
    help="The description of this table[mandatory]",
)
@click.option(
    "--interface-list",
    help="Interfaces to which this table is applied",
)
@clicommon.pass_db
def PBH_TABLE_update(db, table_name, description, interface_list):
    """ Add object in PBH_TABLE. """

    table = "PBH_TABLE"
    key = table_name
    data = {}
    if description is not None:
        data["description"] = description
    if interface_list is not None:
        data["interface_list"] = interface_list.split(",")

    try:
        update_entry_validated(db.cfgdb, table, key, data)
    except Exception as err:
        exit_with_error(f"Error: {err}", fg="red")


@PBH_TABLE.command(name="delete")

@click.argument(
    "table-name",
    nargs=1,
    required=True,
)
@clicommon.pass_db
def PBH_TABLE_delete(db, table_name):
    """ Delete object in PBH_TABLE. """

    table = "PBH_TABLE"
    key = table_name
    try:
        del_entry_validated(db.cfgdb, table, key)
    except Exception as err:
        exit_with_error(f"Error: {err}", fg="red")









@PBH_TABLE.group(name="interface-list",
                   cls=clicommon.AliasedGroup)
def PBH_TABLE_interface_list():
    """ Add/Delete interface_list in PBH_TABLE """

    pass


@PBH_TABLE_interface_list.command(name="add")

@click.argument(
    "table-name",
    nargs=1,
    required=True,
)
@click.argument(
    "interface-list",
    nargs=-1,
    required=True,
)
@clicommon.pass_db
def PBH_TABLE_interface_list_add(
    db,
    table_name, interface_list
):
    """ Add interface_list in PBH_TABLE """

    table = "PBH_TABLE"
    key = table_name
    attr = "interface_list"
    data = interface_list

    try:
        add_list_entry_validated(db.cfgdb, table, key, attr, data)
    except Exception as err:
        exit_with_error(f"Error: {err}", fg="red")



@PBH_TABLE_interface_list.command(name="delete")

@click.argument(
    "table-name",
    nargs=1,
    required=True,
)
@click.argument(
    "interface-list",
    nargs=-1,
    required=True,
)
@clicommon.pass_db
def PBH_TABLE_interface_list_delete(
    db, 
    table_name, interface_list
):
    """ Delete interface_list in PBH_TABLE """

    table = "PBH_TABLE"
    key = table_name
    attr = "interface_list"
    data = interface_list

    try:
        del_list_entry_validated(db.cfgdb, table, key, attr, data)
    except Exception as err:
        exit_with_error(f"Error: {err}", fg="red")



@PBH_TABLE_interface_list.command(name="clear")

@click.argument(
    "table-name",
    nargs=1,
    required=True,
)
@clicommon.pass_db
def PBH_TABLE_interface_list_clear(
    db, 
    table_name
):
    """ Clear interface_list in PBH_TABLE """

    table = "PBH_TABLE"
    key = table_name
    attr = "interface_list"

    try:
        clear_list_entry_validated(db.cfgdb, table, key, attr)
    except Exception as err:
        exit_with_error(f"Error: {err}", fg="red")











def register(cli):
    cli_node = PBH_HASH_FIELD
    if cli_node.name in cli.commands:
        raise Exception(f"{cli_node.name} already exists in CLI")
    cli.add_command(PBH_HASH_FIELD)
    cli_node = PBH_HASH
    if cli_node.name in cli.commands:
        raise Exception(f"{cli_node.name} already exists in CLI")
    cli.add_command(PBH_HASH)
    cli_node = PBH_RULE
    if cli_node.name in cli.commands:
        raise Exception(f"{cli_node.name} already exists in CLI")
    cli.add_command(PBH_RULE)
    cli_node = PBH_TABLE
    if cli_node.name in cli.commands:
        raise Exception(f"{cli_node.name} already exists in CLI")
    cli.add_command(PBH_TABLE)