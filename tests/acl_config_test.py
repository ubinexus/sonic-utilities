from config.main import expand_vlan_ports, parse_acl_table_info


class TestConfigAcl(object):
    def test_expand_vlan(self):
        assert set(expand_vlan_ports("Vlan1000")) == {"Ethernet4", "Ethernet8", "Ethernet12", "Ethernet16"}

    def test_expand_lag(self):
        assert set(expand_vlan_ports("PortChannel1001")) == {"PortChannel1001"}

    def test_expand_physical_interface(self):
        assert set(expand_vlan_ports("Ethernet4")) == {"Ethernet4"}

    def test_parse_table_with_vlan_expansion(self):
        table_info = parse_acl_table_info("TEST", "L3", None, "Vlan1000", "egress", True)
        assert table_info["type"] == "L3"
        assert table_info["policy_desc"] == "TEST"
        assert table_info["stage"] == "egress"

        port_list = table_info["ports@"].split(",")
        assert set(port_list) == {"Ethernet4", "Ethernet8", "Ethernet12", "Ethernet16"}

    def test_parse_table_with_vlan_and_duplicates(self):
        table_info = parse_acl_table_info("TEST", "L3", None, "Ethernet4,Vlan1000", "egress", True)
        assert table_info["type"] == "L3"
        assert table_info["policy_desc"] == "TEST"
        assert table_info["stage"] == "egress"

        # Since Ethernet4 is a member of Vlan1000 we should not include it twice in the output
        port_list = table_info["ports@"].split(",")
        assert len(port_list) == 4
        assert set(port_list) == {"Ethernet4", "Ethernet8", "Ethernet12", "Ethernet16"}

    def test_parse_table_no_expansion(self):
        table_info = parse_acl_table_info("TEST", "L3", None, "Ethernet4,Vlan1000", "egress", False)
        assert table_info["type"] == "L3"
        assert table_info["policy_desc"] == "TEST"
        assert table_info["stage"] == "egress"

        port_list = table_info["ports@"].split(",")
        assert set(port_list) == {"Ethernet4", "Vlan1000"}
