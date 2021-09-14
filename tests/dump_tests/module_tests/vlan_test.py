import json, os, sys
import jsonpatch
import unittest
import pytest
from deepdiff import DeepDiff
from mock import patch
from dump.helper import create_template_dict, sort_lists
from dump.plugins.vlan import Vlan
from dump.match_infra import MatchEngine, ConnectionPool
from swsscommon.swsscommon import SonicV2Connector

module_tests_path = os.path.dirname(__file__)
dump_tests_path = os.path.join(module_tests_path, "../")
tests_path = os.path.join(dump_tests_path, "../")
dump_test_input = os.path.join(tests_path, "dump_input")


# Location for dedicated db's used for UT
vlan_files_path = os.path.join(dump_test_input, "vlan")

dedicated_dbs = {}
dedicated_dbs['CONFIG_DB'] = os.path.join(vlan_files_path, "config_db.json") 
dedicated_dbs['APPL_DB'] = os.path.join(vlan_files_path, "appl_db.json") 
dedicated_dbs['ASIC_DB'] = os.path.join(vlan_files_path, "asic_db.json")
dedicated_dbs['STATE_DB'] = os.path.join(vlan_files_path, "state_db.json")

def verbosity_setup():
    print("SETUP")
    os.environ["VERBOSE"] = "1"
    yield
    print("TEARDOWN")
    os.environ["VERBOSE"] = "0"

def populate_mock(db, db_names):
    for db_name in db_names:
        db.connect(db_name)
        # Delete any default data
        db.delete_all_by_pattern(db_name, "*")
        with open(dedicated_dbs[db_name]) as f:
            mock_json = json.load(f)
        for key in mock_json:
            for field, value in mock_json[key].items():
                db.set(db_name, key, field, value)

@pytest.fixture(scope="class", autouse=True)
def match_engine():

    # Monkey Patch the SonicV2Connector Object
    from ...mock_tables import dbconnector
    db = SonicV2Connector()

    # popualate the db with mock data
    db_names = list(dedicated_dbs.keys())
    try:
        populate_mock(db, db_names)
    except Exception as e:
        assert False, "Mock initialization failed: " + str(e)

    # Initialize connection pool
    conn_pool = ConnectionPool()
    DEF_NS = ''  # Default Namespace
    conn_pool.cache = {DEF_NS: {'conn': db,
                                'connected_to': set(db_names)}}

    # Initialize match_engine
    match_engine = MatchEngine(conn_pool)
    yield match_engine

@pytest.mark.usefixtures("match_engine")
class TestVlanModule:
    
    def test_working_state(self, match_engine):
        params = {}
        params[Vlan.ARG_NAME] = "Vlan4"
        params["namespace"] = ""
        m_vlan = Vlan(match_engine)
        returned = m_vlan.execute(params)
        expect = create_template_dict(dbs=["CONFIG_DB", "APPL_DB", "ASIC_DB", "STATE_DB"])
        expect["CONFIG_DB"]["keys"].append("VLAN|Vlan4")
        expect["CONFIG_DB"]["keys"].append("VLAN_MEMBER|Vlan4|Ethernet16")
        expect["CONFIG_DB"]["keys"].append("VLAN_MEMBER|Vlan4|Ethernet24")
        expect["APPL_DB"]["keys"].append("VLAN_TABLE:Vlan4")
        expect["APPL_DB"]["keys"].append("VLAN_MEMBER_TABLE:Vlan4:Ethernet16")
        expect["APPL_DB"]["keys"].append("VLAN_MEMBER_TABLE:Vlan4:Ethernet24")
        expect["STATE_DB"]["keys"].append("VLAN_TABLE|Vlan4")
        expect["STATE_DB"]["keys"].append("VLAN_MEMBER_TABLE|Vlan4|Ethernet16")
        expect["STATE_DB"]["keys"].append("VLAN_MEMBER_TABLE|Vlan4|Ethernet24")
        expect["ASIC_DB"]["keys"].append("ASIC_STATE:SAI_OBJECT_TYPE_VLAN:oid:0x2600000000062b")
        expect["ASIC_DB"]["keys"].append("ASIC_STATE:SAI_OBJECT_TYPE_VLAN_MEMBER:oid:0x27000000000631")
        expect["ASIC_DB"]["keys"].append("ASIC_STATE:SAI_OBJECT_TYPE_VLAN_MEMBER:oid:0x27000000000633")
        expect["ASIC_DB"]["keys"].append("ASIC_STATE:SAI_OBJECT_TYPE_BRIDGE_PORT:oid:0x3a000000000630")
        expect["ASIC_DB"]["keys"].append("ASIC_STATE:SAI_OBJECT_TYPE_BRIDGE_PORT:oid:0x3a000000000632")
        ddiff = DeepDiff(sort_lists(returned), sort_lists(expect), ignore_order=True)
        assert not ddiff, ddiff
        
    def test_missing_members(self, match_engine):
        params = {}
        params[Vlan.ARG_NAME] = "Vlan2"
        params["namespace"] = ""
        m_vlan = Vlan(match_engine)
        returned = m_vlan.execute(params)
        expect = create_template_dict(dbs=["CONFIG_DB", "APPL_DB", "ASIC_DB", "STATE_DB"])
        expect["CONFIG_DB"]["keys"].append("VLAN|Vlan2")
        expect["CONFIG_DB"]["tables_not_found"].append("VLAN_MEMBER")
        expect["APPL_DB"]["keys"].append("VLAN_TABLE:Vlan2")
        expect["APPL_DB"]["tables_not_found"].append("VLAN_MEMBER_TABLE")
        expect["STATE_DB"]["keys"].append("VLAN_TABLE|Vlan2")
        expect["STATE_DB"]["tables_not_found"].append("VLAN_MEMBER_TABLE")
        expect["ASIC_DB"]["keys"].append("ASIC_STATE:SAI_OBJECT_TYPE_VLAN:oid:0x26000000000629")
        expect["ASIC_DB"]["tables_not_found"].append("ASIC_STATE:SAI_OBJECT_TYPE_VLAN_MEMBER")
        expect["ASIC_DB"]["tables_not_found"].append("ASIC_STATE:SAI_OBJECT_TYPE_BRIDGE_PORT")
        ddiff = DeepDiff(returned, expect, ignore_order=True)
        assert not ddiff, ddiff
    
    def test_wrong_case_vlan(self, match_engine):
        params = {}
        params[Vlan.ARG_NAME] = "VLAN4"
        params["namespace"] = ""
        m_vlan = Vlan(match_engine)
        returned = m_vlan.execute(params)
        expect = create_template_dict(dbs=["CONFIG_DB", "APPL_DB", "ASIC_DB", "STATE_DB"])
        expect["CONFIG_DB"]["tables_not_found"].append("VLAN")
        expect["CONFIG_DB"]["tables_not_found"].append("VLAN_MEMBER")
        expect["APPL_DB"]["tables_not_found"].append("VLAN_TABLE")
        expect["APPL_DB"]["tables_not_found"].append("VLAN_MEMBER_TABLE")
        expect["STATE_DB"]["tables_not_found"].append("VLAN_TABLE")
        expect["STATE_DB"]["tables_not_found"].append("VLAN_MEMBER_TABLE")
        expect["ASIC_DB"]["tables_not_found"].append("ASIC_STATE:SAI_OBJECT_TYPE_VLAN")
        expect["ASIC_DB"]["tables_not_found"].append("ASIC_STATE:SAI_OBJECT_TYPE_VLAN_MEMBER")
        expect["ASIC_DB"]["tables_not_found"].append("ASIC_STATE:SAI_OBJECT_TYPE_BRIDGE_PORT")
        ddiff = DeepDiff(returned, expect, ignore_order=True)
        assert not ddiff, ddiff
    
    def test_unconfigured_vlan(self, match_engine):
        params = {}
        params[Vlan.ARG_NAME] = "Vlan5"
        params["namespace"] = ""
        m_vlan = Vlan(match_engine)
        returned = m_vlan.execute(params)
        expect = create_template_dict(dbs=["CONFIG_DB", "APPL_DB", "ASIC_DB", "STATE_DB"])
        expect["CONFIG_DB"]["tables_not_found"].append("VLAN")
        expect["CONFIG_DB"]["tables_not_found"].append("VLAN_MEMBER")
        expect["APPL_DB"]["tables_not_found"].append("VLAN_TABLE")
        expect["APPL_DB"]["tables_not_found"].append("VLAN_MEMBER_TABLE")
        expect["STATE_DB"]["tables_not_found"].append("VLAN_TABLE")
        expect["STATE_DB"]["tables_not_found"].append("VLAN_MEMBER_TABLE")
        expect["ASIC_DB"]["tables_not_found"].append("ASIC_STATE:SAI_OBJECT_TYPE_VLAN")
        expect["ASIC_DB"]["tables_not_found"].append("ASIC_STATE:SAI_OBJECT_TYPE_VLAN_MEMBER")
        expect["ASIC_DB"]["tables_not_found"].append("ASIC_STATE:SAI_OBJECT_TYPE_BRIDGE_PORT")
        ddiff = DeepDiff(returned, expect, ignore_order=True)
        assert not ddiff, ddiff
    
    def test_garbage_alpha_vlan(self, match_engine):
        params = {}
        params[Vlan.ARG_NAME] = "garbage"
        params["namespace"] = ""
        m_vlan = Vlan(match_engine)
        returned = m_vlan.execute(params)
        expect = create_template_dict(dbs=["CONFIG_DB", "APPL_DB", "ASIC_DB", "STATE_DB"])
        expect["CONFIG_DB"]["tables_not_found"].append("VLAN")
        expect["CONFIG_DB"]["tables_not_found"].append("VLAN_MEMBER")
        expect["APPL_DB"]["tables_not_found"].append("VLAN_TABLE")
        expect["APPL_DB"]["tables_not_found"].append("VLAN_MEMBER_TABLE")
        expect["STATE_DB"]["tables_not_found"].append("VLAN_TABLE")
        expect["STATE_DB"]["tables_not_found"].append("VLAN_MEMBER_TABLE")
        expect["ASIC_DB"]["tables_not_found"].append("ASIC_STATE:SAI_OBJECT_TYPE_VLAN")
        expect["ASIC_DB"]["tables_not_found"].append("ASIC_STATE:SAI_OBJECT_TYPE_VLAN_MEMBER")
        expect["ASIC_DB"]["tables_not_found"].append("ASIC_STATE:SAI_OBJECT_TYPE_BRIDGE_PORT")
        ddiff = DeepDiff(returned, expect, ignore_order=True)
        assert not ddiff, ddiff
    
    def test_garbage_number_vlan(self, match_engine):
        params = {}
        params[Vlan.ARG_NAME] = "614"
        params["namespace"] = ""
        m_vlan = Vlan(match_engine)
        returned = m_vlan.execute(params)
        expect = create_template_dict(dbs=["CONFIG_DB", "APPL_DB", "ASIC_DB", "STATE_DB"])
        expect["CONFIG_DB"]["tables_not_found"].append("VLAN")
        expect["CONFIG_DB"]["tables_not_found"].append("VLAN_MEMBER")
        expect["APPL_DB"]["tables_not_found"].append("VLAN_TABLE")
        expect["APPL_DB"]["tables_not_found"].append("VLAN_MEMBER_TABLE")
        expect["STATE_DB"]["tables_not_found"].append("VLAN_TABLE")
        expect["STATE_DB"]["tables_not_found"].append("VLAN_MEMBER_TABLE")
        expect["ASIC_DB"]["tables_not_found"].append("ASIC_STATE:SAI_OBJECT_TYPE_VLAN")
        expect["ASIC_DB"]["tables_not_found"].append("ASIC_STATE:SAI_OBJECT_TYPE_VLAN_MEMBER")
        expect["ASIC_DB"]["tables_not_found"].append("ASIC_STATE:SAI_OBJECT_TYPE_BRIDGE_PORT")
        ddiff = DeepDiff(returned, expect, ignore_order=True)
        assert not ddiff, ddiff
    
    # Vlan6 is not defined in appl_db
    def test_missing_appl_db(self, match_engine):
        params = {}
        params[Vlan.ARG_NAME] = "Vlan6"
        params["namespace"] = ""
        m_vlan = Vlan(match_engine)
        returned = m_vlan.execute(params)
        expect = create_template_dict(dbs=["CONFIG_DB", "APPL_DB", "ASIC_DB", "STATE_DB"])
        expect["CONFIG_DB"]["keys"].append("VLAN|Vlan6")
        expect["CONFIG_DB"]["keys"].append("VLAN_MEMBER|Vlan6|Ethernet32")
        expect["CONFIG_DB"]["keys"].append("VLAN_MEMBER|Vlan6|Ethernet40")
        expect["APPL_DB"]["tables_not_found"].append("VLAN_TABLE")
        expect["APPL_DB"]["tables_not_found"].append("VLAN_MEMBER_TABLE")
        expect["STATE_DB"]["keys"].append("VLAN_TABLE|Vlan6")
        expect["STATE_DB"]["keys"].append("VLAN_MEMBER_TABLE|Vlan6|Ethernet32")
        expect["STATE_DB"]["keys"].append("VLAN_MEMBER_TABLE|Vlan6|Ethernet40")
        expect["ASIC_DB"]["keys"].append("ASIC_STATE:SAI_OBJECT_TYPE_VLAN:oid:0x2600000000061c")
        expect["ASIC_DB"]["keys"].append("ASIC_STATE:SAI_OBJECT_TYPE_VLAN_MEMBER:oid:0x2700000000061e")
        expect["ASIC_DB"]["keys"].append("ASIC_STATE:SAI_OBJECT_TYPE_VLAN_MEMBER:oid:0x2700000000061f")
        expect["ASIC_DB"]["keys"].append("ASIC_STATE:SAI_OBJECT_TYPE_BRIDGE_PORT:oid:0x3a00000000061d")
        expect["ASIC_DB"]["keys"].append("ASIC_STATE:SAI_OBJECT_TYPE_BRIDGE_PORT:oid:0x3a000000000618")
        ddiff = DeepDiff(sort_lists(returned), sort_lists(expect), ignore_order=True)
        assert not ddiff, ddiff
        
    # Vlan7 is not defined in state_db, but adds bridge port tables in asic_db
    def test_missing_state_db(self, match_engine):
        params = {}
        params[Vlan.ARG_NAME] = "Vlan7"
        params["namespace"] = ""
        m_vlan = Vlan(match_engine)
        returned = m_vlan.execute(params)
        expect = create_template_dict(dbs=["CONFIG_DB", "APPL_DB", "ASIC_DB", "STATE_DB"])
        expect["CONFIG_DB"]["keys"].append("VLAN|Vlan7")
        expect["CONFIG_DB"]["keys"].append("VLAN_MEMBER|Vlan7|Ethernet48")
        expect["CONFIG_DB"]["keys"].append("VLAN_MEMBER|Vlan7|Ethernet56")
        expect["APPL_DB"]["keys"].append("VLAN_TABLE:Vlan7")
        expect["APPL_DB"]["keys"].append("VLAN_MEMBER_TABLE:Vlan7:Ethernet48")
        expect["APPL_DB"]["keys"].append("VLAN_MEMBER_TABLE:Vlan7:Ethernet56")
        expect["STATE_DB"]["tables_not_found"].append("VLAN_TABLE")
        expect["STATE_DB"]["tables_not_found"].append("VLAN_MEMBER_TABLE")
        expect["ASIC_DB"]["keys"].append("ASIC_STATE:SAI_OBJECT_TYPE_VLAN:oid:0x26000000000620")
        expect["ASIC_DB"]["keys"].append("ASIC_STATE:SAI_OBJECT_TYPE_VLAN_MEMBER:oid:0x27000000000623")
        expect["ASIC_DB"]["keys"].append("ASIC_STATE:SAI_OBJECT_TYPE_VLAN_MEMBER:oid:0x27000000000621")
        expect["ASIC_DB"]["keys"].append("ASIC_STATE:SAI_OBJECT_TYPE_BRIDGE_PORT:oid:0x3a000000000622")
        expect["ASIC_DB"]["keys"].append("ASIC_STATE:SAI_OBJECT_TYPE_BRIDGE_PORT:oid:0x3a00000000061a")
        ddiff = DeepDiff(sort_lists(returned), sort_lists(expect), ignore_order=True)
        assert not ddiff, ddiff
        
    # Vlan8 is not defined in asic_db
    def test_missing_asic_db(self, match_engine):
        params = {}
        params[Vlan.ARG_NAME] = "Vlan8"
        params["namespace"] = ""
        m_vlan = Vlan(match_engine)
        returned = m_vlan.execute(params)
        expect = create_template_dict(dbs=["CONFIG_DB", "APPL_DB", "ASIC_DB", "STATE_DB"])
        expect["CONFIG_DB"]["keys"].append("VLAN|Vlan8")
        expect["CONFIG_DB"]["keys"].append("VLAN_MEMBER|Vlan8|Ethernet64")
        expect["CONFIG_DB"]["keys"].append("VLAN_MEMBER|Vlan8|Ethernet72")
        expect["APPL_DB"]["keys"].append("VLAN_TABLE:Vlan8")
        expect["APPL_DB"]["keys"].append("VLAN_MEMBER_TABLE:Vlan8:Ethernet64")
        expect["APPL_DB"]["keys"].append("VLAN_MEMBER_TABLE:Vlan8:Ethernet72")
        expect["STATE_DB"]["keys"].append("VLAN_TABLE|Vlan8")
        expect["STATE_DB"]["keys"].append("VLAN_MEMBER_TABLE|Vlan8|Ethernet64")
        expect["STATE_DB"]["keys"].append("VLAN_MEMBER_TABLE|Vlan8|Ethernet72")
        expect["ASIC_DB"]["tables_not_found"].append("ASIC_STATE:SAI_OBJECT_TYPE_VLAN")
        expect["ASIC_DB"]["tables_not_found"].append("ASIC_STATE:SAI_OBJECT_TYPE_VLAN_MEMBER")
        expect["ASIC_DB"]["tables_not_found"].append("ASIC_STATE:SAI_OBJECT_TYPE_BRIDGE_PORT")
        ddiff = DeepDiff(sort_lists(returned), sort_lists(expect), ignore_order=True)
        assert not ddiff, ddiff
        
    def test_all_args(self, match_engine):
        params = {}
        m_vlan = Vlan(match_engine)
        returned = m_vlan.get_all_args("")
        expect = ["Vlan2", "Vlan3", "Vlan4", "Vlan6", "Vlan7", "Vlan8"]
        ddiff = DeepDiff(expect, returned, ignore_order=True)
        assert not ddiff, ddiff 
