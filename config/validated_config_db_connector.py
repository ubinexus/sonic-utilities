import jsonpatch
import subprocess
from jsonpointer import JsonPointer

from sonic_py_common import device_info
from generic_config_updater.generic_updater import GenericUpdater, ConfigFormat
from generic_config_updater.gu_common import EmptyTableError, genericUpdaterLogging

def ValidatedConfigDBConnector(config_db_connector):
    yang_enabled = device_info.is_yang_config_validation_enabled(config_db_connector) 
    if yang_enabled:
        config_db_connector.set_entry = validated_set_entry
        config_db_connector.delete_table = validated_delete_table
    return config_db_connector

def is_table_present_config_db(table):
    cmd = "sonic-cfggen -d --print-data"
    result = subprocess.Popen(cmd, shell=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    text, err = result.communicate()
    return_code = result.returncode
    if return_code: # non-zero means failure
        raise Exception(f"Failed to get running config, Return code: {return_code}, Error: {err}")
    return table in text

def make_path_value_jsonpatch_compatible(table, key, value):
    if type(key) == tuple:
        path = JsonPointer.from_parts([table, '|'.join(key)]).path
    else:
        path = JsonPointer.from_parts([table, key]).path
    if value == {"NULL" : "NULL"}:
        value = {}
    return path, value

def create_gcu_patch(op, table, key=None, value=None):
    gcu_json_input = []
    if op == "add" and not is_table_present_config_db(table):
        gcu_json = {"op": "{}".format(op),
                    "path": "/{}".format(table),
                    "value": {}}
        gcu_json_input.append(gcu_json)

    if key:
        path, value = make_path_value_jsonpatch_compatible(table, key, value)
    else: 
        path = "/{}".format(table)

    gcu_json_input = []
    gcu_json = {"op": "{}".format(op),
                "path": "{}".format(path)}
    if op == "add":
        gcu_json["value"] = value

    gcu_json_input.append(gcu_json)
    gcu_patch = jsonpatch.JsonPatch(gcu_json_input)
    return gcu_patch

def validated_delete_table(table):
    gcu_patch = create_gcu_patch("remove", table)
    format = ConfigFormat.CONFIGDB.name
    config_format = ConfigFormat[format.upper()]
    try:
        GenericUpdater().apply_patch(patch=gcu_patch, config_format=config_format, verbose=False, dry_run=False, ignore_non_yang_tables=False, ignore_paths=None)
    except ValueError as e:
        logger = genericUpdaterLogging.get_logger(title="Patch Applier", print_all_to_console=True)
        logger.log_notice("Unable to remove entry, as doing so will result in invalid config. Error: {}".format(e))

def validated_set_entry(table, key, value):
    if value is not None:
        op = "add"
    else:
        op = "remove"
    
    gcu_patch = create_gcu_patch(op, table, key, value)
    format = ConfigFormat.CONFIGDB.name
    config_format = ConfigFormat[format.upper()]

    try:
        GenericUpdater().apply_patch(patch=gcu_patch, config_format=config_format, verbose=False, dry_run=False, ignore_non_yang_tables=False, ignore_paths=None)
    except EmptyTableError:
        validated_delete_table(table)
