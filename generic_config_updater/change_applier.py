import copy
import json
import importlib
import os
import syslog
import tempfile
from collections import defaultdict
from swsscommon.swsscommon import ConfigDBConnector
from .gu_common import log_error, log_debug, log_info


def get_config_db():
    config_db = ConfigDBConnector()
    config_db.connect()
    return config_db


def set_config(config_db, tbl, key, data):
    config_db.set_entry(tbl, key, data)


UPDATER_CONF_FILE = "/etc/sonic/generic_config_updater.conf"
updater_data = None

class ChangeApplier:
    def __init__(self):
        global updater_data, log_level

        self.config_db = get_config_db()
        if updater_data == None:
            with open(UPDATER_CONF_FILE, "r") as s:
                updater_data = json.load(s)


    def _invoke_cmd(cmd, old_cfg, upd_cfg, keys):
        method_name = cmd.split(".")[-1]
        module_name = ".".join(cmd.split(".")[0:-1])

        module = importlib.import_module(module_name, package=None)
        method_to_call = getattr(module, method_name)

        return method_to_call(old_cfg, upd_cfg, keys)


    def _services_validate(old_cfg, upd_cfg, keys):
        lst_svcs = set()
        lst_cmds = set()
        if not keys:
            keys[""] = {}
        for tbl in keys:
            lst_svcs.update(updater_data.get(tbl, {}).get("services_to_validate", []))
        for svc in lst_svcs:
            lst_cmds.update(updater_data.get(svc, {}).get("validate_commands", []))

        for cmd in lst_cmds:
            ret = _invoke_cmd(cmd, old_cfg, upd_cfg, keys)
            if ret:
                return ret
        return 0


    def _upd_data(self, tbl, run_tbl, upd_tbl, upd_keys):
        for key in set(run_tbl.keys()).union(set(upd_tbl.keys())):
            run_data = run_tbl.get(key, None)
            upd_data = upd_tbl.get(key, None)

            if run_data != upd_data:
                set_config(self.config_db, tbl, key, upd_data)
                upd_keys[tbl][key] = {}


    def apply(self, change):
        run_data = self._get_running_config()
        upd_data = change.apply(copy.deepcopy(run_data))
        upd_keys = defaultdict(dict)

        for tbl in set(run_data.keys()).union(set(upd_data.keys())):
            self._upd_data(tbl, run_data.get(tbl, {}),
                    upd_data.get(tbl, {}), upd_keys)

        ret = _services_validate(run_data, upd_data, upd_keys)
        if not ret:
            run_data = self._get_running_config()
            if upd_data != run_data:
                report_mismatch(run_data, upd_data)
                ret = -1
        return ret


    def _get_running_config(self):
        (_, fname) = tempfile.mkstemp(suffix="_changeApplier")
        os.system("sonic-cfggen -d --print-data > {}".format(fname))
        run_data = {}
        with open(fname, "r") as s:
            run_data = json.load(s)
        if os.path.isfile(fname):
            os.remove(fname)
        return run_data


            


