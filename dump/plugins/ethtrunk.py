from dump.match_infra import MatchRequest
from dump.helper import create_template_dict
from dump.match_helper import fetch_ethtrunk_oid
from .executor import Executor


class Ethtrunk(Executor):
    """
    Debug Dump Plugin for EthTrunk Module
    """
    ARG_NAME = "ethtrunk_name"

    def __init__(self, match_engine=None):
        super().__init__(match_engine)
        self.ns = ''
        self.ethtrunk_members = set()

    def get_all_args(self, ns=""):
        req = MatchRequest(db="CONFIG_DB", table="ETHTRUNK", key_pattern="*", ns=ns)
        ret = self.match_engine.fetch(req)
        all_ethtrunks = ret["keys"]
        return [key.split("|")[-1] for key in all_ethtrunks]

    def execute(self, params_dict):
        self.ret_temp = create_template_dict(dbs=["CONFIG_DB", "APPL_DB", "ASIC_DB", "STATE_DB"])
        self.ethtrunk_name = params_dict[Ethtrunk.ARG_NAME]
        self.ns = params_dict["namespace"]
        # CONFIG_DB
        self.init_ethtrunk_config_info()
        # APPL_DB
        self.init_ethtrunk_appl_info()
        # STATE_DB
        self.init_ethtrunk_state_info()
        # ASIC_DB
        self.init_ethtrunk_asic_info()
        return self.ret_temp

    def init_ethtrunk_config_info(self):
        req = MatchRequest(db="CONFIG_DB", table="ETHTRUNK", key_pattern=self.ethtrunk_name, ns=self.ns)
        ret = self.match_engine.fetch(req)
        return self.add_to_ret_template(req.table, req.db, ret["keys"], ret["error"])

    def init_ethtrunk_appl_info(self):
        req = MatchRequest(db="APPL_DB", table="ETHTRUNK_TABLE", key_pattern=self.ethtrunk_name, ns=self.ns)
        ret = self.match_engine.fetch(req)
        return self.add_to_ret_template(req.table, req.db, ret["keys"], ret["error"])

    def init_ethtrunk_state_info(self):
        req = MatchRequest(db="STATE_DB", table="ETHTRUNK_TABLE", key_pattern=self.ethtrunk_name, ns=self.ns)
        ret = self.match_engine.fetch(req)
        return self.add_to_ret_template(req.table, req.db, ret["keys"], ret["error"])

    def init_ethtrunk_asic_info(self):
        # Fetch EthTrunk Type Asic Obj from CFG DB given ethtrunk name
        asic_obj = fetch_ethtrunk_oid(self.match_engine, self.ethtrunk_name, self.ns)
        req = MatchRequest(db="ASIC_DB", table="ASIC_STATE:SAI_OBJECT_TYPE_NEXT_HOP_GROUP", key_pattern=asic_obj, ns=self.ns)
        ret = self.match_engine.fetch(req)
        self.add_to_ret_template(req.table, req.db, ret["keys"], ret["error"])
