import sys
import os
import pytest

test_path = os.path.dirname(os.path.abspath(__file__))
modules_path = os.path.dirname(test_path)
sys.path.insert(0, modules_path)

from acl_loader import *
from acl_loader.main import *

class TestAclLoader(object):
    @pytest.fixture(scope="class")
    def acl_loader(self):
        yield AclLoader()

    def test_acl_empty(self):
        yang_acl = AclLoader.parse_acl_json(os.path.join(test_path, 'acl_input/empty_acl.json'))
        assert len(yang_acl.acl.acl_sets.acl_set) == 0

    def test_valid(self):
        yang_acl = AclLoader.parse_acl_json(os.path.join(test_path, 'acl_input/acl1.json'))
        assert len(yang_acl.acl.acl_sets.acl_set) == 6

    def test_invalid(self):
        with pytest.raises(AclLoaderException):
            yang_acl = AclLoader.parse_acl_json(os.path.join(test_path, 'acl_input/acl2.json'))

    def test_validate_mirror_action(self, acl_loader):
        ingress_mirror_rule_props = {
            "MIRROR_INGRESS_ACTION": "everflow0"
        }

        egress_mirror_rule_props = {
            "mirror_egress_action": "everflow0"
        }

        # switch capability taken from mock_tables/state_db.json SWITCH_CAPABILITY table
        assert acl_loader.validate_actions("EVERFLOW", ingress_mirror_rule_props)
        assert not acl_loader.validate_actions("EVERFLOW", egress_mirror_rule_props)

        assert not acl_loader.validate_actions("EVERFLOW_EGRESS", ingress_mirror_rule_props)
        assert acl_loader.validate_actions("EVERFLOW_EGRESS", egress_mirror_rule_props)

        forward_packet_action = {
            "PACKET_ACTION": "FORWARD"
        }

        drop_packet_action = {
            "PACKET_ACTION": "DROP"
        }

        # switch capability taken from mock_tables/state_db.json SWITCH_CAPABILITY table
        assert acl_loader.validate_actions("DATAACL", forward_packet_action)
        assert not acl_loader.validate_actions("DATAACL", drop_packet_action)

    def test_vlan_id_translation(self, acl_loader):
        acl_loader.rules_info = {}
        acl_loader.load_rules_from_file(os.path.join(test_path, 'acl_input/acl1.json'))
        assert acl_loader.rules_info[("DATAACL", "RULE_2")]
        assert acl_loader.rules_info[("DATAACL", "RULE_2")]["VLAN_ID"] == 369

    def test_vlan_id_lower_bound(self, acl_loader):
        acl_loader.rules_info = {}
        acl_loader.load_rules_from_file(os.path.join(test_path, 'acl_input/illegal_vlan_0.json'))
        assert not acl_loader.rules_info.get(("DATAACL", "RULE_1"))

    def test_vlan_id_upper_bound(self, acl_loader):
        acl_loader.rules_info = {}
        acl_loader.load_rules_from_file(os.path.join(test_path, 'acl_input/illegal_vlan_9000.json'))
        assert not acl_loader.rules_info.get(("DATAACL", "RULE_1"))

    def test_vlan_id_not_a_number(self, acl_loader):
        acl_loader.rules_info = {}
        acl_loader.load_rules_from_file(os.path.join(test_path, 'acl_input/illegal_vlan_nan.json'))
        assert not acl_loader.rules_info.get(("DATAACL", "RULE_1"))

    def test_icmp_translation(self, acl_loader):
        acl_loader.rules_info = {}
        acl_loader.load_rules_from_file(os.path.join(test_path, 'acl_input/acl1.json'))
        assert acl_loader.rules_info[("DATAACL", "RULE_1")]
        assert acl_loader.rules_info[("DATAACL", "RULE_1")]["ICMP_TYPE"] == 3
        assert acl_loader.rules_info[("DATAACL", "RULE_1")]["ICMP_CODE"] == 0

    def test_icmpv6_translation(self, acl_loader):
        acl_loader.rules_info = {}
        acl_loader.load_rules_from_file(os.path.join(test_path, 'acl_input/acl1.json'))
        assert acl_loader.rules_info[("DATAACLV6", "RULE_1")]
        assert acl_loader.rules_info[("DATAACLV6", "RULE_1")]["ICMPV6_TYPE"] == 1
        assert acl_loader.rules_info[("DATAACLV6", "RULE_1")]["ICMPV6_CODE"] == 0

    def test_icmp_type_lower_bound(self, acl_loader):
        acl_loader.rules_info = {}
        acl_loader.load_rules_from_file(os.path.join(test_path, 'acl_input/illegal_icmp_type_neg_1.json'))
        assert not acl_loader.rules_info.get(("DATAACL", "RULE_1"))

    def test_icmp_type_upper_bound(self, acl_loader):
        acl_loader.rules_info = {}
        acl_loader.load_rules_from_file(os.path.join(test_path, 'acl_input/illegal_icmp_type_300.json'))
        assert not acl_loader.rules_info.get(("DATAACL", "RULE_1"))

    def test_icmp_type_not_a_number(self, acl_loader):
        acl_loader.rules_info = {}
        acl_loader.load_rules_from_file(os.path.join(test_path, 'acl_input/illegal_icmp_type_nan.json'))
        assert not acl_loader.rules_info.get(("DATAACL", "RULE_1"))

    def test_icmp_code_lower_bound(self, acl_loader):
        acl_loader.rules_info = {}
        acl_loader.load_rules_from_file(os.path.join(test_path, 'acl_input/illegal_icmp_code_neg_1.json'))
        assert not acl_loader.rules_info.get(("DATAACL", "RULE_1"))

    def test_icmp_code_upper_bound(self, acl_loader):
        acl_loader.rules_info = {}
        acl_loader.load_rules_from_file(os.path.join(test_path, 'acl_input/illegal_icmp_code_300.json'))
        assert not acl_loader.rules_info.get(("DATAACL", "RULE_1"))

    def test_icmp_code_not_a_number(self, acl_loader):
        acl_loader.rules_info = {}
        acl_loader.load_rules_from_file(os.path.join(test_path, 'acl_input/illegal_icmp_code_nan.json'))
        assert not acl_loader.rules_info.get(("DATAACL", "RULE_1"))
