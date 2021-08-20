import pytest

import config.main as config

from click.testing import CliRunner
from config.main import parse_acl_table_info

class TestConfigAcl(object):
    def test_parse_table_with_vlan(self):
        table_info = parse_acl_table_info("TEST", "L3", None, "Vlan1000", "egress")
        assert table_info["type"] == "L3"
        assert table_info["policy_desc"] == "TEST"
        assert table_info["stage"] == "egress"

        port_list = table_info["ports@"].split(",")
        assert set(port_list) == {"Vlan1000"}

    @pytest.mark.skip('TODO')
    def test_parse_table_with_vlan_and_duplicates(self):
        # Shall not bind Ethernet/PortChannel port and VLAN to the same ACL table
        with pytest.raises(ValueError):
            parse_acl_table_info("TEST", "L3", None, "Ethernet4,Vlan1000", "egress")

    def test_parse_table_with_empty_vlan(self):
        table_info = parse_acl_table_info("TEST", "L3", None, "Ethernet4,Vlan3000", "egress")
        assert table_info["type"] == "L3"
        assert table_info["policy_desc"] == "TEST"
        assert table_info["stage"] == "egress"

        port_list = table_info["ports@"].split(",")
        assert set(port_list) == {"Ethernet4", "Vlan3000"}

    def test_parse_table_with_invalid_ports(self):
        with pytest.raises(ValueError):
            parse_acl_table_info("TEST", "L3", None, "Ethernet200", "egress")

    def test_parse_table_with_empty_ports(self):
        with pytest.raises(ValueError):
            parse_acl_table_info("TEST", "L3", None, "", "egress")

    def test_acl_add_table_nonexistent_port(self):
        runner = CliRunner()

        result = runner.invoke(
            config.config.commands["acl"].commands["add"].commands["table"],
            ["TEST", "L3", "-p", "Ethernet200"])

        assert result.exit_code != 0
        assert "Cannot bind ACL to specified port Ethernet200" in result.output

    def test_acl_add_table_empty_string_port_list(self):
        runner = CliRunner()

        result = runner.invoke(
            config.config.commands["acl"].commands["add"].commands["table"],
            ["TEST", "L3", "-p", ""])

        assert result.exit_code != 0
        assert "Cannot bind empty list of ports" in result.output

    def test_acl_add_table_empty_vlan(self):
        runner = CliRunner()

        result = runner.invoke(
            config.config.commands["acl"].commands["add"].commands["table"],
            ["TEST", "L3", "-p", "Vlan3000"])

        assert result.exit_code == 0
