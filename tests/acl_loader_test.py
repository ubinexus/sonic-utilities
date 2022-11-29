import sys
import os
import pytest
from unittest import mock
from sonic_py_common import multi_asic
from swsssdk import ConfigDBConnector

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

        # switch capability taken from mock_tables/state_db.json ACL_STAGE_CAPABILITY_TABLE table
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

        # switch capability taken from mock_tables/state_db.json ACL_STAGE_CAPABILITY_TABLE table
        assert acl_loader.validate_actions("DATAACL", forward_packet_action)
        assert not acl_loader.validate_actions("DATAACL", drop_packet_action)

    def test_vlan_id_translation(self, acl_loader):
        acl_loader.rules_info = {}
        acl_loader.load_rules_from_file(os.path.join(test_path, 'acl_input/acl1.json'))
        assert acl_loader.rules_info[("DATAACL", "RULE_2")]
        assert acl_loader.rules_info[("DATAACL", "RULE_2")] == {
            "VLAN_ID": 369,
            "ETHER_TYPE": "2048",
            "IP_PROTOCOL": 6,
            "SRC_IP": "20.0.0.2/32",
            "DST_IP": "30.0.0.3/32",
            "PACKET_ACTION": "FORWARD",
            "PRIORITY": "9998"
        }

    def test_vlan_id_lower_bound(self, acl_loader):
        with pytest.raises(ValueError):
            acl_loader.rules_info = {}
            acl_loader.load_rules_from_file(os.path.join(test_path, 'acl_input/illegal_vlan_0.json'))

    def test_vlan_id_upper_bound(self, acl_loader):
        with pytest.raises(ValueError):
            acl_loader.rules_info = {}
            acl_loader.load_rules_from_file(os.path.join(test_path, 'acl_input/illegal_vlan_9000.json'))

    def test_vlan_id_not_a_number(self, acl_loader):
        with pytest.raises(ValueError):
            acl_loader.rules_info = {}
            acl_loader.load_rules_from_file(os.path.join(test_path, 'acl_input/illegal_vlan_nan.json'))

    def test_ethertype_translation(self, acl_loader):
        acl_loader.rules_info = {}
        acl_loader.load_rules_from_file(os.path.join(test_path, 'acl_input/acl1.json'))
        assert acl_loader.rules_info[("DATAACL", "RULE_3")]
        assert acl_loader.rules_info[("DATAACL", "RULE_3")] == {
            "VLAN_ID": 369,
            "ETHER_TYPE": 35020,
            "PACKET_ACTION": "FORWARD",
            "PRIORITY": "9997"
        }

    def test_icmp_translation(self, acl_loader):
        acl_loader.rules_info = {}
        acl_loader.load_rules_from_file(os.path.join(test_path, 'acl_input/acl1.json'))
        assert acl_loader.rules_info[("DATAACL", "RULE_1")]
        assert acl_loader.rules_info[("DATAACL", "RULE_1")] == {
            "ICMP_TYPE": 3,
            "ICMP_CODE": 0,
            "IP_PROTOCOL": 1,
            "SRC_IP": "20.0.0.2/32",
            "DST_IP": "30.0.0.3/32",
            "ETHER_TYPE": "2048",
            "PACKET_ACTION": "FORWARD",
            "PRIORITY": "9999"
        }

    def test_icmpv6_translation(self, acl_loader):
        acl_loader.rules_info = {}
        acl_loader.load_rules_from_file(os.path.join(test_path, 'acl_input/acl1.json'))
        print(acl_loader.rules_info)
        assert acl_loader.rules_info[("DATAACL_2", "RULE_1")] == {
            "ICMPV6_TYPE": 1,
            "ICMPV6_CODE": 0,
            "IP_PROTOCOL": 58,
            "SRC_IPV6": "::1/128",
            "DST_IPV6": "::1/128",
            "IP_TYPE": "IPV6ANY",
            "PACKET_ACTION": "FORWARD",
            "PRIORITY": "9999"
        }
        assert acl_loader.rules_info[("DATAACL_2", "RULE_100")] == {
            "ICMPV6_TYPE": 128,
            "IP_PROTOCOL": 58,
            "SRC_IPV6": "::1/128",
            "DST_IPV6": "::1/128",
            "IP_TYPE": "IPV6ANY",
            "PACKET_ACTION": "FORWARD",
            "PRIORITY": "9900"
        }

    def test_ingress_default_deny_rule(self, acl_loader):
        acl_loader.rules_info = {}
        acl_loader.load_rules_from_file(os.path.join(test_path, 'acl_input/acl1.json'))
        print(acl_loader.rules_info)
        assert acl_loader.rules_info[('DATAACL', 'DEFAULT_RULE')] == {
            'PRIORITY': '1',
            'PACKET_ACTION': 'DROP',
            'ETHER_TYPE': '2048'
        }
        assert acl_loader.rules_info[('DATAACL_2', 'DEFAULT_RULE')] == {
            'PRIORITY': '1',
            'PACKET_ACTION': 'DROP',
            'IP_TYPE': 'IPV6ANY'
        }

    def test_egress_no_default_deny_rule(self, acl_loader):
        acl_loader.rules_info = {}
        acl_loader.load_rules_from_file(os.path.join(test_path, 'acl_input/acl_egress.json'))
        print(acl_loader.rules_info)
        assert ('DATAACL_3', 'DEFAULT_RULE') not in acl_loader.rules_info
        assert ('DATAACL_4', 'DEFAULT_RULE') not in acl_loader.rules_info

    def test_icmp_type_lower_bound(self, acl_loader):
        with pytest.raises(ValueError):
            acl_loader.rules_info = {}
            acl_loader.load_rules_from_file(os.path.join(test_path, 'acl_input/illegal_icmp_type_neg_1.json'))

    def test_icmp_type_upper_bound(self, acl_loader):
        with pytest.raises(ValueError):
            acl_loader.rules_info = {}
            acl_loader.load_rules_from_file(os.path.join(test_path, 'acl_input/illegal_icmp_type_300.json'))

    def test_icmp_type_not_a_number(self, acl_loader):
        with pytest.raises(ValueError):
            acl_loader.rules_info = {}
            acl_loader.load_rules_from_file(os.path.join(test_path, 'acl_input/illegal_icmp_type_nan.json'))

    def test_icmp_code_lower_bound(self, acl_loader):
        with pytest.raises(ValueError):
            acl_loader.rules_info = {}
            acl_loader.load_rules_from_file(os.path.join(test_path, 'acl_input/illegal_icmp_code_neg_1.json'))

    def test_icmp_code_upper_bound(self, acl_loader):
        with pytest.raises(ValueError):
            acl_loader.rules_info = {}
            acl_loader.load_rules_from_file(os.path.join(test_path, 'acl_input/illegal_icmp_code_300.json'))

    def test_icmp_code_not_a_number(self, acl_loader):
        with pytest.raises(ValueError):
            acl_loader.rules_info = {}
            acl_loader.load_rules_from_file(os.path.join(test_path, 'acl_input/illegal_icmp_code_nan.json'))

    def test_icmp_fields_with_non_icmp_protocol(self, acl_loader):
        acl_loader.rules_info = {}
        acl_loader.load_rules_from_file(os.path.join(test_path, 'acl_input/icmp_bad_protocol_number.json'))
        assert not acl_loader.rules_info.get("RULE_1")

    def ttest_icmp_fields_with_non_icmpv6_protocol(self, acl_loader):
        acl_loader.rules_info = {}
        acl_loader.load_rules_from_file(os.path.join(test_path, 'acl_input/icmpv6_bad_protocol_number.json'))
        assert not acl_loader.rules_info.get("RULE_1")


    def test_icmp_fields_with_non_tcp_protocol(self, acl_loader):
        acl_loader.rules_info = {}
        acl_loader.load_rules_from_file(os.path.join(test_path, 'acl_input/tcp_bad_protocol_number.json'))
        assert not acl_loader.rules_info.get("RULE_1")

    def test_incremental_update(self, acl_loader):
        acl_loader.rules_info = {}
        acl_loader.tables_db_info['NTP_ACL'] = {
            "stage": "INGRESS",
            "type": "CTRLPLANE"
        }
        acl_loader.load_rules_from_file(os.path.join(test_path, 'acl_input/incremental_1.json'))
        acl_loader.rules_db_info = acl_loader.rules_info
        assert acl_loader.rules_info[(('NTP_ACL', 'RULE_1'))]["PACKET_ACTION"] == "ACCEPT"
        acl_loader.per_npu_configdb = None
        acl_loader.configdb.mod_entry = mock.MagicMock(return_value=True)
        acl_loader.configdb.set_entry = mock.MagicMock(return_value=True)
        acl_loader.load_rules_from_file(os.path.join(test_path, 'acl_input/incremental_2.json'))
        acl_loader.incremental_update()
        assert acl_loader.rules_info[(('NTP_ACL', 'RULE_1'))]["PACKET_ACTION"] == "DROP"

    def test_add_rule(self, acl_loader):
        acl_loader.rules_info = {}
        acl_loader.tables_db_info['DATAACL_ADD_DEL'] = {
            "policy_desc": "DATAACL_ADD_DEL",
            "ports@": "PortChannel0002,PortChannel0005,PortChannel0008,PortChannel0011,PortChannel0014,PortChannel0017,PortChannel0020,PortChannel0023",
            "stage": "INGRESS",
            "type": "L3"
        }
        acl_loader.load_rules_from_file(os.path.join(test_path, 'acl_input/acl_add_1.json'))
        assert acl_loader.rules_info[('DATAACL_ADD_DEL', 'RULE_1')]
        assert acl_loader.rules_info[('DATAACL_ADD_DEL', 'RULE_1')] == {
            'SRC_IP': '20.0.0.2/32',
            'DST_IP': '30.0.0.3/32',
            'ETHER_TYPE': '2048',
            'PACKET_ACTION': 'FORWARD',
            'PRIORITY': '9999'
        }
        assert acl_loader.rules_info[('DATAACL_ADD_DEL', 'RULE_2')]
        assert acl_loader.rules_info[('DATAACL_ADD_DEL', 'RULE_2')] == {
            'SRC_IP': '21.0.0.2/32',
            'DST_IP': '31.0.0.3/32',
            'ETHER_TYPE': '2048',
            'PACKET_ACTION': 'FORWARD',
            'PRIORITY': '9998'
        }

        acl_loader.configdb.mod_entry = mock.MagicMock(return_value=True)
        acl_loader.configdb.set_entry = mock.MagicMock(return_value=True)
        acl_loader.per_npu_configdb = {}
        namespaces = multi_asic.get_front_end_namespaces()
        for namespace in namespaces:
            asic_id = multi_asic.get_asic_index_from_namespace(namespace)
            # replace these with correct macros
            acl_loader.per_npu_configdb[asic_id] = ConfigDBConnector(use_unix_socket_path=True, namespace=namespace)
            acl_loader.per_npu_configdb[asic_id].connect()

        acl_loader.rules_db_info = acl_loader.rules_info

        acl_loader.load_rules_from_file(os.path.join(test_path, 'acl_input/acl_add_2.json'))
        acl_loader.add_rule()
        print(acl_loader.rules_info)
        assert acl_loader.rules_info[('DATAACL_ADD_DEL', 'RULE_1')]
        assert acl_loader.rules_info[('DATAACL_ADD_DEL', 'RULE_2')]
        assert acl_loader.rules_info[("DATAACL_ADD_DEL", "RULE_1")] == {
            "SRC_IP": "30.0.0.2/32",
            "DST_IP": "40.0.0.3/32",
            "ETHER_TYPE": "2048",
            "PACKET_ACTION": "FORWARD",
            "PRIORITY": "9999"
        }
        assert acl_loader.rules_info[('DATAACL_ADD_DEL', 'RULE_1')]
        assert acl_loader.rules_info[('DATAACL_ADD_DEL', 'RULE_2')]
        assert acl_loader.rules_info[('DATAACL_ADD_DEL', 'RULE_3')]
        assert acl_loader.rules_info[('DATAACL_ADD_DEL', 'RULE_3')] == {
            'SRC_IP': '31.0.0.2/32',
            'DST_IP': '41.0.0.3/32',
            'ETHER_TYPE': '2048',
            'PACKET_ACTION': 'FORWARD',
            'PRIORITY': '9997'
        }

