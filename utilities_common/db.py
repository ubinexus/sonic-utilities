from sonic_py_common import multi_asic
from swsssdk import ConfigDBConnector, SonicV2Connector
from utilities_common.multi_asic import multi_asic_ns_choices


class Db(object):
    def __init__(self):
        self.cfgdb = ConfigDBConnector()
        self.cfgdb.connect()
        self.db = SonicV2Connector(host="127.0.0.1")
        self.db.connect(self.db.APPL_DB)
        self.db.connect(self.db.CONFIG_DB)
        self.db.connect(self.db.STATE_DB)

    def get_data(self, table, key):
        data = self.cfgdb.get_table(table)
        return data[key] if key in data else None


class MasicDb(object):
    """
    Multi ASIC DB object - creates config DB and other redis DB client
    connections for all namespaces. In case of single ASIC platform, DB
    client connections are created for default namespace
    """"
    def __init__(self):
        self.ns_list = multi_asic_ns_choices()
        self.config_db_clients = {}
        self.db_clients = {}
        for ns in self.ns_list:
            self.config_db_clients[ns] = multi_asic.connect_config_db_for_ns(ns)
            self.db_clients[ns] = multi_asic.connect_to_all_dbs_for_ns(ns)
