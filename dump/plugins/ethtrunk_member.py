from dump.match_infra import MatchRequest
from dump.helper import create_template_dict
from .executor import Executor

class Ethtrunk_Member(Executor):
    """
    Debug Dump Plugin for EthTrunk Module
    """
    ARG_NAME = "ethtrunk_member"

    def __init__(self, match_engine=None):
        super().__init__(match_engine)
        self.ns = ''
        self.ethtrunk_member_key = ''
        self.ethtrunk = ''
        self.port_name = ''

    def get_all_args(self, ns=""):
        req = MatchRequest(db="CONFIG_DB", table="ETHTRUNK_MEMBER", key_pattern="*", ns=ns)
        ret = self.match_engine.fetch(req)
        all_ethtrunk_members = ret["keys"]
        return [key.split("|", 1)[-1] for key in all_ethtrunk_members]

    def execute(self, params_dict):
        self.ret_temp = create_template_dict(dbs=["CONFIG_DB", "APPL_DB", "ASIC_DB", "STATE_DB"])
        self.ethtrunk_member_key = params_dict[Ethtrunk_Member.ARG_NAME]
        if "|" not in self.ethtrunk_member_key:
            return self.ret_temp
        self.ethtrunk, self.port_name = self.ethtrunk_member_key.split("|", 1)
        self.ns = params_dict["namespace"]
        # CONFIG_DB
        self.init_ethtrunk_member_config_info()
        # APPL_DB
        self.init_ethtrunk_member_appl_info()
        # STATE_DB
        self.init_ethtrunk_member_state_info()
        # ASIC_DB
        self.init_ethtrunk_member_type_obj_asic_info()
        return self.ret_temp

    def init_ethtrunk_member_config_info(self):
        req = MatchRequest(db="CONFIG_DB", table="ETHTRUNK_MEMBER", key_pattern=self.ethtrunk_member_key, ns=self.ns)
        ret = self.match_engine.fetch(req)
        return self.add_to_ret_template(req.table, req.db, ret["keys"], ret["error"])

    def init_ethtrunk_member_appl_info(self):
        req = MatchRequest(db="APPL_DB", table="ETHTRUNK_MEMBER_TABLE", key_pattern=self.ethtrunk + ":" + self.port_name, ns=self.ns)
        ret = self.match_engine.fetch(req)
        return self.add_to_ret_template(req.table, req.db, ret["keys"], ret["error"])

    def init_ethtrunk_member_state_info(self):
        req = MatchRequest(db="STATE_DB", table="ETHTRUNK_MEMBER_TABLE", key_pattern=self.ethtrunk_member_key, ns=self.ns)
        ret = self.match_engine.fetch(req)
        return self.add_to_ret_template(req.table, req.db, ret["keys"], ret["error"])

    def init_ethtrunk_member_type_obj_asic_info(self):
        port_asic_obj = self.get_port_asic_obj(self.port_name)
        if not port_asic_obj:
            self.ret_temp["ASIC_DB"]["tables_not_found"].extend(["ASIC_STATE:SAI_OBJECT_TYPE_NEXT_HOP_GROUP"])
            return False
        req = MatchRequest(db="ASIC_DB", table="ASIC_STATE:SAI_OBJECT_TYPE_NEXT_HOP_GROUP", key_pattern="*", field="SAI_NEXT_HOP_GROUP_MEMBER_ATTR_NEXT_HOP_ID",
                           value=port_asic_obj, ns=self.ns)
        ret = self.match_engine.fetch(req)
        return self.add_to_ret_template(req.table, req.db, ret["keys"], ret["error"])

    def get_port_asic_obj(self, port_name):
        req = MatchRequest(db="ASIC_DB", table="ASIC_STATE:SAI_OBJECT_TYPE_HOSTIF", key_pattern="*", field="SAI_HOSTIF_ATTR_NAME",
                           value=port_name, return_fields=["SAI_HOSTIF_ATTR_OBJ_ID"], ns=self.ns)
        ret = self.match_engine.fetch(req)
        asic_port_obj_id = ""
        if not ret["error"] and ret["keys"]:
            sai_hostif_obj_key = ret["keys"][-1]
            if sai_hostif_obj_key in ret["return_values"] and "SAI_HOSTIF_ATTR_OBJ_ID" in ret["return_values"][sai_hostif_obj_key]:
                asic_port_obj_id = ret["return_values"][sai_hostif_obj_key]["SAI_HOSTIF_ATTR_OBJ_ID"]
        return asic_port_obj_id
