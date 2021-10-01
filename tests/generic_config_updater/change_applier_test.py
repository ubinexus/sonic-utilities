import copy
import json
import os
import unittest
from unittest.mock import patch

import generic_config_updater.change_applier
import generic_config_updater.gu_common

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
DATA_FILE =  os.path.join(SCRIPT_DIR, "files", "change_applier_test.data.json")

read_data = {}
running_config = {}
json_changes = {}
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



class TestChangeApplier(unittest.TestCase):

    @patch("generic_config_updater.change_applier.os.system")
    @patch("generic_config_updater.change_applier.get_config_db")
    @patch("generic_config_updater.change_applier.set_config")
    def test_application(self, mock_set, mock_db, mock_os_sys):
        global read_data, running_config, json_changes, json_change_index

        mock_os_sys.side_effect = os_system_cfggen
        mock_db.return_value = DB_HANDLE
        mock_set.side_effect = set_entry

        with open(DATA_FILE, "r") as s:
            read_data = json.load(s)

        running_config = copy.deepcopy(read_data["running_data"])
        json_changes = copy.deepcopy(read_data["json_changes"])

        applier = generic_config_updater.change_applier.ChangeApplier()
        debug_print("invoked applier")

        for i in range(len(json_changes)):
            json_change_index = i
            debug_print("main: json_change_index={}".format(json_change_index))
            applier.apply(mock_obj())

        # All changes are consumed
        for i in range(len(json_changes)):
            debug_print("Checking: index={} update:{} remove:{}".format(i,
                json.dumps(json_changes[i]["update"])[0:20],
                json.dumps(json_changes[i]["remove"])[0:20]))
            assert not json_changes[i]["update"]
            assert not json_changes[i]["remove"]

        # Test data is set up in such a way the multiple changes
        # finally brings it back to original config.
        #
        if read_data["running_data"] != running_config:
            print_diff(read_data["running_data"], running_config)

        assert read_data["running_data"] == running_config

        debug_print("all good for applier")


 
