import copy
import json
import os
import tempfile
from swsscommon.swsscommon import ConfigDBConnector
from .gu_common import JsonChange


def get_running_config():
    (_, fname) = tempfile.mkstemp(suffix="_changeApplier")
    os.system("sonic-cfggen -d --print-data > {}".format(fname))
    run_data = {}
    with open(fname, "r") as s:
        run_data = json.load(s)
    if os.path.isfile(fname):
        os.remove(fname)
    return run_data


def get_config_db():
    config_db = ConfigDBConnector()
    config_db.connect()
    return config_db


def set_config(config_db, tbl, key, data):
    config_db.set_entry(tbl, key, data)


class ChangeApplier:
    def __init__(self):
        self.config_db = get_config_db()

    def _upd_data(self, tbl, run_tbl, upd_tbl):
        for key in set(run_tbl.keys()).union(set(upd_tbl.keys())):
            run_data = run_tbl.get(key, None)
            upd_data = upd_tbl.get(key, None)

            if run_data != upd_data:
                set_config(self.config_db, tbl, key, upd_data)


    def apply(self, change):
        run_data = get_running_config()
        upd_data = change.apply(copy.deepcopy(run_data))

        for tbl in set(run_data.keys()).union(set(upd_data.keys())):
            self._upd_data(tbl, run_data.get(tbl, {}), upd_data.get(tbl, {}))

            


