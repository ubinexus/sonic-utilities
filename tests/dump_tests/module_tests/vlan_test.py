import json, os, sys
import jsonpatch
import unittest
import pytest
from deepdiff import DeepDiff
from mock import patch
from dump.helper import create_template_dict, sort_lists
from dump.plugins.vlan import Vlan

from .mock_sonicv2connector import MockSonicV2Connector

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

def mock_connector(namespace, use_unix_socket_path=True):
    return MockSonicV2Connector(dedicated_dbs, namespace=namespace, use_unix_socket_path=use_unix_socket_path)

@pytest.fixture(scope="module", autouse=True)
def verbosity_setup():
    print("SETUP")
    os.environ["VERBOSE"] = "1"
    yield
    print("TEARDOWN")
    os.environ["VERBOSE"] = "0"


@patch("dump.match_infra.SonicV2Connector", mock_connector)
class TestVlanModule(unittest.TestCase):
    
    def test_working_state(self):
        params = {}
        params[Vlan.ARG_NAME] = "Vlan4"
        params["namespace"] = ""
        m_vlan = Vlan()
        returned = m_vlan.execute(params)
        expect = create_template_dict(dbs=["CONFIG_DB", "APPL_DB", "ASIC_DB", "STATE_DB"])
        expect["CONFIG_DB"]["keys"].append("VLAN|Vlan4")
        expect["CONFIG_DB"]["keys"].append("VLAN_MEMBER|Vlan4|Ethernet16")
        expect["CONFIG_DB"]["keys"].append("VLAN_MEMBER|Vlan4|Ethernet24")
        expect["CONFIG_DB"]["keys"].append("VLAN_INTERFACE|Vlan4|192.168.1.2/24")
        expect["CONFIG_DB"]["keys"].append("VLAN_INTERFACE|Vlan4")
        expect["CONFIG_DB"]["tables_not_found"].append("VLAN_SUB_INTERFACE")
        expect["APPL_DB"]["keys"].append("VLAN_TABLE:Vlan4")
        expect["APPL_DB"]["keys"].append("VLAN_MEMBER_TABLE:Vlan4:Ethernet16")
        expect["APPL_DB"]["keys"].append("VLAN_MEMBER_TABLE:Vlan4:Ethernet24")
        expect["STATE_DB"]["keys"].append("VLAN_TABLE|Vlan4")
        expect["STATE_DB"]["keys"].append("VLAN_MEMBER_TABLE|Vlan4|Ethernet16")
        expect["STATE_DB"]["keys"].append("VLAN_MEMBER_TABLE|Vlan4|Ethernet24")
        expect["ASIC_DB"]["keys"].append("ASIC_STATE:SAI_OBJECT_TYPE_VLAN:oid:0x260000000005e5")
        expect["ASIC_DB"]["keys"].append("ASIC_STATE:SAI_OBJECT_TYPE_VLAN_MEMBER:oid:0x270000000005e7")
        expect["ASIC_DB"]["keys"].append("ASIC_STATE:SAI_OBJECT_TYPE_VLAN_MEMBER:oid:0x270000000005e9")
        ddiff = DeepDiff(sort_lists(returned), sort_lists(expect), ignore_order=True)
        assert not ddiff, ddiff
        
    def test_missing_interface(self):
        params = {}
        params[Vlan.ARG_NAME] = "Vlan3"
        params["namespace"] = ""
        m_vlan = Vlan()
        returned = m_vlan.execute(params)
        expect = create_template_dict(dbs=["CONFIG_DB", "APPL_DB", "ASIC_DB", "STATE_DB"])
        expect["CONFIG_DB"]["keys"].append("VLAN|Vlan3")
        expect["CONFIG_DB"]["keys"].append("VLAN_MEMBER|Vlan3|Ethernet0")
        expect["CONFIG_DB"]["keys"].append("VLAN_MEMBER|Vlan3|Ethernet8")
        expect["CONFIG_DB"]["tables_not_found"].append("VLAN_INTERFACE")
        expect["CONFIG_DB"]["tables_not_found"].append("VLAN_SUB_INTERFACE")
        expect["APPL_DB"]["keys"].append("VLAN_TABLE:Vlan3")
        expect["APPL_DB"]["keys"].append("VLAN_MEMBER_TABLE:Vlan3:Ethernet0")
        expect["APPL_DB"]["keys"].append("VLAN_MEMBER_TABLE:Vlan3:Ethernet8")
        expect["STATE_DB"]["keys"].append("VLAN_TABLE|Vlan3")
        expect["STATE_DB"]["keys"].append("VLAN_MEMBER_TABLE|Vlan3|Ethernet0")
        expect["STATE_DB"]["keys"].append("VLAN_MEMBER_TABLE|Vlan3|Ethernet8")
        expect["ASIC_DB"]["keys"].append("ASIC_STATE:SAI_OBJECT_TYPE_VLAN:oid:0x260000000005e0")
        expect["ASIC_DB"]["keys"].append("ASIC_STATE:SAI_OBJECT_TYPE_VLAN_MEMBER:oid:0x270000000005e4")
        expect["ASIC_DB"]["keys"].append("ASIC_STATE:SAI_OBJECT_TYPE_VLAN_MEMBER:oid:0x270000000005e2")
        ddiff = DeepDiff(sort_lists(returned), sort_lists(expect), ignore_order=True)
        assert not ddiff, ddiff
    
    def test_missing_memebers_and_interface(self):
        params = {}
        params[Vlan.ARG_NAME] = "Vlan2"
        params["namespace"] = ""
        m_vlan = Vlan()
        returned = m_vlan.execute(params)
        expect = create_template_dict(dbs=["CONFIG_DB", "APPL_DB", "ASIC_DB", "STATE_DB"])
        expect["CONFIG_DB"]["keys"].append("VLAN|Vlan2")
        expect["CONFIG_DB"]["tables_not_found"].append("VLAN_MEMBER")
        expect["CONFIG_DB"]["tables_not_found"].append("VLAN_INTERFACE")
        expect["CONFIG_DB"]["tables_not_found"].append("VLAN_SUB_INTERFACE")
        expect["APPL_DB"]["keys"].append("VLAN_TABLE:Vlan2")
        expect["APPL_DB"]["tables_not_found"].append("VLAN_MEMBER_TABLE")
        expect["STATE_DB"]["keys"].append("VLAN_TABLE|Vlan2")
        expect["STATE_DB"]["tables_not_found"].append("VLAN_MEMBER_TABLE")
        expect["ASIC_DB"]["keys"].append("ASIC_STATE:SAI_OBJECT_TYPE_VLAN:oid:0x260000000005df")
        expect["ASIC_DB"]["tables_not_found"].append("ASIC_STATE:SAI_OBJECT_TYPE_VLAN_MEMBER")
        ddiff = DeepDiff(returned, expect, ignore_order=True)
        assert not ddiff, ddiff
    
    def test_wrong_case_vlan(self):
        params = {}
        params[Vlan.ARG_NAME] = "VLAN4"
        params["namespace"] = ""
        m_vlan = Vlan()
        returned = m_vlan.execute(params)
        expect = create_template_dict(dbs=["CONFIG_DB", "APPL_DB", "ASIC_DB", "STATE_DB"])
        expect["CONFIG_DB"]["tables_not_found"].append("VLAN")
        expect["CONFIG_DB"]["tables_not_found"].append("VLAN_MEMBER")
        expect["CONFIG_DB"]["tables_not_found"].append("VLAN_INTERFACE")
        expect["CONFIG_DB"]["tables_not_found"].append("VLAN_SUB_INTERFACE")
        expect["APPL_DB"]["tables_not_found"].append("VLAN_TABLE")
        expect["APPL_DB"]["tables_not_found"].append("VLAN_MEMBER_TABLE")
        expect["STATE_DB"]["tables_not_found"].append("VLAN_TABLE")
        expect["STATE_DB"]["tables_not_found"].append("VLAN_MEMBER_TABLE")
        expect["ASIC_DB"]["tables_not_found"].append("ASIC_STATE:SAI_OBJECT_TYPE_VLAN")
        expect["ASIC_DB"]["tables_not_found"].append("ASIC_STATE:SAI_OBJECT_TYPE_VLAN_MEMBER")
        ddiff = DeepDiff(returned, expect, ignore_order=True)
        assert not ddiff, ddiff
    
    def test_unconfigured_vlan(self):
        params = {}
        params[Vlan.ARG_NAME] = "Vlan5"
        params["namespace"] = ""
        m_vlan = Vlan()
        returned = m_vlan.execute(params)
        expect = create_template_dict(dbs=["CONFIG_DB", "APPL_DB", "ASIC_DB", "STATE_DB"])
        expect["CONFIG_DB"]["tables_not_found"].append("VLAN")
        expect["CONFIG_DB"]["tables_not_found"].append("VLAN_MEMBER")
        expect["CONFIG_DB"]["tables_not_found"].append("VLAN_INTERFACE")
        expect["CONFIG_DB"]["tables_not_found"].append("VLAN_SUB_INTERFACE")
        expect["APPL_DB"]["tables_not_found"].append("VLAN_TABLE")
        expect["APPL_DB"]["tables_not_found"].append("VLAN_MEMBER_TABLE")
        expect["STATE_DB"]["tables_not_found"].append("VLAN_TABLE")
        expect["STATE_DB"]["tables_not_found"].append("VLAN_MEMBER_TABLE")
        expect["ASIC_DB"]["tables_not_found"].append("ASIC_STATE:SAI_OBJECT_TYPE_VLAN")
        expect["ASIC_DB"]["tables_not_found"].append("ASIC_STATE:SAI_OBJECT_TYPE_VLAN_MEMBER")
        ddiff = DeepDiff(returned, expect, ignore_order=True)
        assert not ddiff, ddiff
    
    def test_garbage_vlan(self):
        params = {}
        params[Vlan.ARG_NAME] = "garbage"
        params["namespace"] = ""
        m_vlan = Vlan()
        returned = m_vlan.execute(params)
        expect = create_template_dict(dbs=["CONFIG_DB", "APPL_DB", "ASIC_DB", "STATE_DB"])
        expect["CONFIG_DB"]["tables_not_found"].append("VLAN")
        expect["CONFIG_DB"]["tables_not_found"].append("VLAN_MEMBER")
        expect["CONFIG_DB"]["tables_not_found"].append("VLAN_INTERFACE")
        expect["CONFIG_DB"]["tables_not_found"].append("VLAN_SUB_INTERFACE")
        expect["APPL_DB"]["tables_not_found"].append("VLAN_TABLE")
        expect["APPL_DB"]["tables_not_found"].append("VLAN_MEMBER_TABLE")
        expect["STATE_DB"]["tables_not_found"].append("VLAN_TABLE")
        expect["STATE_DB"]["tables_not_found"].append("VLAN_MEMBER_TABLE")
        expect["ASIC_DB"]["tables_not_found"].append("ASIC_STATE:SAI_OBJECT_TYPE_VLAN")
        expect["ASIC_DB"]["tables_not_found"].append("ASIC_STATE:SAI_OBJECT_TYPE_VLAN_MEMBER")
        ddiff = DeepDiff(returned, expect, ignore_order=True)
        assert not ddiff, ddiff
    
    def test_all_args(self):
        params = {}
        m_vlan = Vlan()
        returned = m_vlan.get_all_args("")
        expect = ["Vlan2", "Vlan3", "Vlan4"]
        ddiff = DeepDiff(expect, returned, ignore_order=True)
        assert not ddiff, ddiff 
