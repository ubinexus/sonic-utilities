from dump.helper import create_template_dict
from dump.match_infra import MatchRequest
from swsscommon.swsscommon import SonicDBConfig
import dash_api
from dash_api.eni_pb2 import Eni
from dash_api.vnet_pb2 import Vnet
from dump.match_helper import fetch_acl_counter_oid
from .executor import Executor
import redis
from dump.match_infra import JsonSource, MatchEngine, CONN
from google.protobuf.json_format import MessageToDict


APPL_DB_SEPARATOR = SonicDBConfig.getSeparator("APPL_DB")


class Dash_Eni(Executor):
    """
    Debug Dump Plugin for DASH VNET Mapping
    """
    ARG_NAME = "dash_eni_value"

    def __init__(self, match_engine=None):
        super().__init__(match_engine)
        self.is_dash_object = True

    def get_all_args(self, ns=""):
        req = MatchRequest(db="APPL_DB", table="DASH_ENI_TABLE", key_pattern="*", ns=ns)
        ret = self.match_engine.fetch(req)
        appliance_tables = ret["keys"]
        return [key.split(APPL_DB_SEPARATOR)[-1] for key in appliance_tables]

    def execute(self, params):
        self.ret_temp = create_template_dict(dbs=["APPL_DB", "ASIC_DB"])
        dash_eni_table_name = params[self.ARG_NAME]
        self.ns = params["namespace"]
        self.init_dash_eni_table_appl_info(dash_eni_table_name)
        self.init_dash_eni_table_asic_info(dash_eni_table_name)
        return self.ret_temp

    def init_dash_eni_table_appl_info(self, dash_eni_table_name):
        req = MatchRequest(db="APPL_DB", table="DASH_ENI_TABLE", key_pattern=dash_eni_table_name,  ns=self.ns,)
        ret = self.match_engine.fetch(req)
        self.add_to_ret_template(req.table, req.db, ret["keys"], ret["error"])

    def init_dash_eni_table_asic_info(self, dash_eni_table_name):
        req = MatchRequest(db="APPL_DB", table="DASH_ENI_TABLE", key_pattern=dash_eni_table_name, return_fields=["vnet"],  ns=self.ns,pb = Eni())
        ret = self.match_engine.fetch(req)
        vnet = ret['return_values'][ret['keys'][0]]['vnet']
        req = MatchRequest(db="APPL_DB", table="DASH_VNET_TABLE", key_pattern=vnet, return_fields=["vni"],  ns=self.ns,pb = Vnet())
        ret = self.match_engine.fetch(req)
        vni = ret['return_values'][ret['keys'][0]]['vni']
        req = MatchRequest(db="ASIC_DB", table="ASIC_STATE", key_pattern="SAI_OBJECT_TYPE_VNET:*",field="SAI_VNET_ATTR_VNI", value=str(vni), ns=self.ns)
        ret = self.match_engine.fetch(req)
        oid = ret['keys'][0]
        oid_key = "oid"+oid.split("oid")[-1]
        req = MatchRequest(db="ASIC_DB", table="ASIC_STATE", key_pattern="SAI_OBJECT_TYPE_ENI:*",field="SAI_ENI_ATTR_VNET_ID", value=str(oid_key), ns=self.ns)
        ret = self.match_engine.fetch(req)
        self.add_to_ret_template(req.table, req.db, ret["keys"], ret["error"])

    def return_pb2_obj(self):
        return Eni()
