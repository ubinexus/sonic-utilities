import copy
import json
import os
import unittest
from collections import defaultdict
from unittest.mock import patch

import generic_config_updater.change_applier
import generic_config_updater.gu_common

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
DATA_FILE =  os.path.join(SCRIPT_DIR, "files", "change_applier_test.data.json")
CONF_FILE =  os.path.join(SCRIPT_DIR, "files", "change_applier_test.conf.json")
#
# Datafile is structured as 
# "running_config": {....}
# "json_changes": [ {"name": ..., "update": { <tbl>: {<key>: {<new data>}, ...}...},
#                               "remove": { <tbl>: { <key>: {}, ..}, ...} }, ...]
#
# The json_changes is read into global json_changes
# The applier is called with each change
#   The mocked JsonChange.apply applies this diff on given config
#   The applier calls set_entry to update redis
#   But we mock set_entry, and that instead:
#       remove the corresponding changes from json_changes.
#       Updates the global running_config
# 
# At the end of application of all changes, expect global json-changes to
# be empty, which assures that set_entry is called for all expected keys.
# The global running config would reflect the final config
#
# The changes are written in such a way, upon the last change, the config
# will be same as the original config that we started with or as read from
# data file. 
#
# So compare global running_config with read_data for running config
# from the file.
# This compares the integrity of final o/p

# Data read from file
read_data = {}

# Keep a copy of running_config before calling apply
# This is used by service_validate call to verify the args
# Args from change applier: (<config before change>  <config after change>
#                               <affected keys>
start_running_config = {}

# The mock_set_entry (otherwise redis update) reflects the final config
# service_validate calls will verify <config after change > against this
#
running_config = {}

# Copy of changes read. Used by mock JsonChange.apply
# Cleared by mocked set_entry
json_changes = {}

# The index into list of i/p json changes for mock code to use
json_change_index = 0

DB_HANDLE = "config_db"

in_debug = False

def debug_print(msg):
    if in_debug:
        print(msg)


# Mimics os.system call for sonic-cfggen -d --print-data > filename
#
def os_system_cfggen(cmd):
    global running_config

    fname = cmd.split(">")[-1].strip()
    with open(fname, "w") as s:
        s.write(json.dumps(running_config, indent=4))
    debug_print("File created {} type={} cfg={}".format(fname,
        type(running_config), json.dumps(running_config)[1:40]))
    return 0


# mimics config_db.set_entry
#
def set_entry(config_db, tbl, key, data):
    global running_config, json_changes, json_change_index

    assert config_db == DB_HANDLE
    debug_print("set_entry: {} {} {}".format(tbl, key, str(data)))

    json_change = json_changes[json_change_index]
    change_data = json_change["update"] if data != None else json_change["remove"]

    assert tbl in change_data
    assert key in change_data[tbl]

    if data != None:
        if tbl not in running_config:
            running_config[tbl] = {}
        running_config[tbl][key] = data
    else:
        assert tbl in running_config
        assert key in running_config[tbl]
        running_config[tbl].pop(key)
        if not running_config[tbl]:
            running_config.pop(tbl)

    change_data[tbl].pop(key)
    if not change_data[tbl]:
        change_data.pop(tbl)


# mimics JsonChange.apply
#
class mock_obj:
    def apply(self, config):
        json_change = json_changes[json_change_index]

        update = copy.deepcopy(json_change["update"])
        for tbl in update:
            if tbl not in config:
                config[tbl] = {}
            for key in update[tbl]:
                debug_print("apply: tbl={} key={} ".format(tbl, key))
                if key in config[tbl]:
                    config[tbl][key].update(update[tbl][key])
                else:
                    config[tbl][key] = update[tbl][key]

        remove = json_change["remove"]
        for tbl in remove:
            if tbl in config:
                for key in remove[tbl]:
                    config[tbl].pop(key, None)
                    debug_print("apply: popped tbl={} key={}".format(tbl, key))
        return config

def print_diff(expect, ct):
    for tbl in set(expect.keys()).union(set(ct.keys())):
        if tbl not in expect:
            debug_print("Unexpected table in current: {}".format(tbl))
        elif tbl not in ct:
            debug_print("Missing table in current: {}".format(tbl))
        else:
            ex_tbl = expect[tbl]
            ct_tbl = ct[tbl]
            for key in set(ex_tbl.keys()).union(set(ct_tbl.keys())):
                if key not in ex_tbl:
                    debug_print("Unexpected key in current: {}/{}".format(tbl, key))
                elif key not in ct_tbl:
                    debug_print("Missing key in current: {}/{}".format(tbl, key))
                else:
                    ex_val = ex_tbl[key]
                    ct_val = ct_tbl[key]
                    if ex_val != ct_val:
                        debug_print("Val mismatch {}/{} expect:{} ct: {}".format(
                            tbl, key, ex_val, ct_val))
    debug_print("diff is complete")


# Test validators
#
def system_health(old_cfg, new_cfg, keys):
    svc_name = "system_health"
    if old_cfg != new_cfg:
        print_diff(old_cfg, new_cfg)
        assert False, "No change expected"
    svcs = json_changes[json_change_index].get("services_validated", None)
    if svcs != None:
        assert svc_name not in svcs
        svcs.remove(svc_name)


def _validate_keys(keys):
    change = copy.deepcopy(read_data["json_changes"][json_change_index])
    change.update(read_data["json_changes"][json_change_index])

    for tbl in set(change.keys()).union(set(keys.keys())):
        assert tbl in change
        assert tbl in keys
        chg_tbl = change[tbl]
        keys_tbl = keys[tbl]
        for key in set(chg_tbl.keys()).union(set(keys_tbl.keys())):
            assert key not in chg_tbl
            assert key not in keys_tbl

        
def _validate_svc(svc_name, old_cfg, new_cfg, keys):
    if old_cfg != start_running_config:
        print_diff(old_cfg, start_running_config)
        assert False

    if new_cfg != running_config:
        print_diff(old_cfg, running_config)
        assert False

    _validate_keys(keys)

    svcs = json_changes[json_change_index].get("services_validated", None)
    if svcs != None:
        assert svc_name not in svcs
        svcs.remove(svc_name)


def acl_validate(old_cfg, new_cfg, keys):
    _validate_svc("acl_validate", old_cfg, new_cfg, keys)


def vlan_validate(old_cfg, new_cfg, keys):
    _validate_svc("vlan_validate", old_cfg, new_cfg, keys)


class TestChangeApplier(unittest.TestCase):

    @patch("generic_config_updater.gu_common.subprocess.run")
    @patch("generic_config_updater.change_applier.os.system")
    @patch("generic_config_updater.change_applier.get_config_db")
    @patch("generic_config_updater.change_applier.set_config")
        global read_data, running_config, json_changes, json_change_index

        mock_os_sys.side_effect = os_system_cfggen
        mock_db.return_value = DB_HANDLE
        mock_set.side_effect = set_entry

        with open(DATA_FILE, "r") as s:
            read_data = json.load(s)

        running_config = copy.deepcopy(read_data["running_data"])
        json_changes = copy.deepcopy(read_data["json_changes"])

        generic_config_updater.change_applier.UPDATER_CONF_FILE = CONF_FILE
        
        applier = generic_config_updater.change_applier.ChangeApplier()
        debug_print("invoked applier")

        for i in range(len(json_changes)):
            json_change_index = i

            # Take copy for comparison
            start_running_config = copy.deepcopy(running_config)
            
            debug_print("main: json_change_index={}".format(json_change_index))
            applier.apply(mock_obj())

        # All changes are consumed
        for i in range(len(json_changes)):
            debug_print("Checking: index={} update:{} remove:{} svcs:{}".format(i,
                json.dumps(json_changes[i]["update"])[0:20],
                json.dumps(json_changes[i]["remove"])[0:20],
                json.dumps(json_changes[i].get("services_validated", []))[0:20]))
            assert not json_changes[i]["update"]
            assert not json_changes[i]["remove"]
            assert not json_changes[i].get("services_validated", [])

        # Test data is set up in such a way the multiple changes
        # finally brings it back to original config.
        #
        if read_data["running_data"] != running_config:
            print_diff(read_data["running_data"], running_config)

        assert read_data["running_data"] == running_config

        debug_print("all good for applier")


 
