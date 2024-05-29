from dump.helper import create_template_dict
from dump.match_infra import MatchRequest
from swsscommon.swsscommon import SonicDBConfig
from dash_api.vnet_pb2 import Vnet
from .executor import Executor


APPL_DB_SEPARATOR = SonicDBConfig.getSeparator("APPL_DB")


class Dash_Vnet(Executor):
    """
    Debug Dump Plugin for DASH VNET Mapping
    """
    ARG_NAME = "dash_vnet_table"

    def __init__(self, match_engine=None):
        super().__init__(match_engine)
        self.is_dash_object = True
        self.dash_keys = None

    def get_all_args(self, ns=""):
        req = MatchRequest(db="APPL_DB", table="DASH_VNET_TABLE", key_pattern="*", ns=ns)
        ret = self.match_engine.fetch(req)
        appliance_tables = ret["keys"]
        return [key.split(APPL_DB_SEPARATOR, 1)[1] for key in appliance_tables]

    def execute(self, params):
        self.ret_temp = create_template_dict(dbs=["APPL_DB", "ASIC_DB"])
        dash_vnet_table_name = params[self.ARG_NAME]
        self.ns = params["namespace"]
        self.init_dash_vnet_table_appl_info(dash_vnet_table_name)
        self.init_dash_vnet_table_asic_info(dash_vnet_table_name)
        return self.ret_temp

    def init_dash_vnet_table_appl_info(self, dash_app_table_name):
        req = MatchRequest(db="APPL_DB", table="DASH_VNET_TABLE", key_pattern=dash_app_table_name, return_fields=["type"], ns=self.ns)
        ret = self.match_engine.fetch(req)
        self.dash_keys = ret["keys"]
        self.add_to_ret_template(req.table, req.db, ret["keys"], ret["error"])

    def init_dash_vnet_table_asic_info(self, dash_vnet_table_name):
        req = MatchRequest(db="APPL_DB", table="DASH_VNET_TABLE", key_pattern=dash_vnet_table_name, return_fields=["vni"], ns=self.ns, pb=Vnet())
        ret = self.match_engine.fetch(req)
        if not len(ret['keys']):
            if self.dash_keys:
                self.ret_temp["ASIC_DB"]["tables_not_found"].append("ASIC_STATE:SAI_OBJECT_TYPE_VNET")
            return
        vni = ret['return_values'][ret['keys'][0]]['vni']
        req = MatchRequest(db="ASIC_DB", table="ASIC_STATE", key_pattern="SAI_OBJECT_TYPE_VNET:*", field="SAI_VNET_ATTR_VNI", value=str(vni), ns=self.ns)
        ret = self.match_engine.fetch(req)
        self.add_to_ret_template(req.table, req.db, ret["keys"], ret["error"])

    def return_pb2_obj(self):
        return Vnet()
