import os

from click.testing import CliRunner

import config.main as config
from utilities_common.db import Db


class TestEvpnInterface(object):
    @classmethod
    def setup_class(cls):
        print("SETUP")
        os.environ["UTILITIES_UNIT_TESTING"] = "1"

    @classmethod
    def teardown_class(cls):
        os.environ['UTILITIES_UNIT_TESTING'] = "0"
        print("TEARDOWN")

    def test_config_interface_add_set_del_sys_mac(self):
        runner = CliRunner()
        db = Db()

        result = runner.invoke(config.config.commands["interface"].commands["sys-mac"].commands["add"],
                               ["Ethernet4", "00:11:22:33:44:55"], obj=db)
        assert result.exit_code != 0
        assert "interface_name is invalid, should be PortChannel!" in result.output

        result = runner.invoke(config.config.commands["interface"].commands["sys-mac"].commands["add"],
                               ["PortChannel1", "05:v:nj:00:00:00"], obj=db)
        assert result.exit_code != 0
        assert "MAC address is invalid!" in result.output

        result = runner.invoke(config.config.commands["interface"].commands["sys-mac"].commands["add"],
                               ["PortChannel1", "00:11:22:33:44:55"], obj=db)
        assert result.exit_code != 0
        assert "evpn-esi type for PortChannel1 is not type-3!" in result.output

        result = runner.invoke(config.config.commands["interface"].commands["evpn-esi"].commands["add"],
                               ["PortChannel1", "type-3", "3"], obj=db)
        assert result.exit_code == 0
        result = runner.invoke(config.config.commands["interface"].commands["sys-mac"].commands["add"],
                               ["PortChannel1", "00:11:22:33:44:55"], obj=db)
        assert result.exit_code == 0
        assert db.cfgdb.get_entry("EVPN_ETHERNET_SEGMENT", "PortChannel1").\
            get("type3_system_mac") == "00:11:22:33:44:55"

        result = runner.invoke(config.config.commands["interface"].commands["sys-mac"].commands["set"],
                               ["PortChannel1", "01:12:23:34:45:56"], obj=db)
        assert result.exit_code == 0
        assert db.cfgdb.get_entry("EVPN_ETHERNET_SEGMENT", "PortChannel1").\
            get("type3_system_mac") == "01:12:23:34:45:56"

        result = runner.invoke(config.config.commands["interface"].commands["sys-mac"].commands["del"],
                               ["PortChannel1", "01:12:23:34:45:56"], obj=db)
        assert result.exit_code == 0
        assert db.cfgdb.get_entry("EVPN_ETHERNET_SEGMENT", "PortChannel1").get("type3_system_mac") is None

    def test_config_interface_add_set_del_evpn_esi(self):
        runner = CliRunner()
        db = Db()

        result = runner.invoke(config.config.commands["interface"].commands["evpn-esi"].commands["add"],
                               ["Ethernet23", "type-0", "00:11:22:33:44:55:66:77:88:99"], obj=db)
        assert result.exit_code != 0
        assert "interface_name is invalid, should be PortChannel!" in result.output

        result = runner.invoke(config.config.commands["interface"].commands["evpn-esi"].commands["add"],
                               ["PortChannel1", "type-54", "00:11:22:33:44:55:66:77:88:99"], obj=db)
        assert result.exit_code != 0
        assert "Invalid value for \"<esi_type>\"" in result.output

        result = runner.invoke(config.config.commands["interface"].commands["evpn-esi"].commands["add"],
                               ["PortChannel1", "type-0", "00:11:22:33:44:55:66:77:88:99"], obj=db)
        assert result.exit_code == 0
        assert db.cfgdb.get_entry("EVPN_ETHERNET_SEGMENT", "PortChannel1").get("esi_type") == "0"
        assert db.cfgdb.get_entry("EVPN_ETHERNET_SEGMENT", "PortChannel1").\
            get("type0_operator_config") == "00:11:22:33:44:55:66:77:88:99"

        result = runner.invoke(config.config.commands["interface"].commands["evpn-esi"].commands["set"],
                               ["PortChannel1", "type-0", "01:12:23:34:45:56:67:78:89:90"], obj=db)
        assert result.exit_code == 0
        assert db.cfgdb.get_entry("EVPN_ETHERNET_SEGMENT", "PortChannel1").get("esi_type") == "0"
        assert db.cfgdb.get_entry("EVPN_ETHERNET_SEGMENT", "PortChannel1").\
            get("type0_operator_config") == "01:12:23:34:45:56:67:78:89:90"

        result = runner.invoke(config.config.commands["interface"].commands["evpn-esi"].commands["del"],
                               ["PortChannel1", "type-0", "01:12:23:34:45:56:67:78:89:90"], obj=db)
        assert result.exit_code == 0
        assert db.cfgdb.get_entry("EVPN_ETHERNET_SEGMENT", "PortChannel1").get("esi_type") is None
        assert db.cfgdb.get_entry("EVPN_ETHERNET_SEGMENT", "PortChannel1").get("type0_operator_config") is None

    def test_config_interface_add_set_del_evpn_df_pref(self):
        runner = CliRunner()
        db = Db()

        result = runner.invoke(config.config.commands["interface"].commands["evpn-df-pref"].commands["add"],
                               ["Ethernet4", "5"], obj=db)
        assert result.exit_code != 0
        assert "interface_name is invalid, should be PortChannel!" in result.output

        result = runner.invoke(config.config.commands["interface"].commands["evpn-df-pref"].commands["add"],
                               ["PortChannel1", "100000"], obj=db)
        assert result.exit_code != 0
        assert "Invalid value for \"<df_perf>\"" in result.output

        result = runner.invoke(config.config.commands["interface"].commands["evpn-df-pref"].commands["add"],
                               ["PortChannel1", "20000"], obj=db)
        assert result.exit_code == 0
        assert db.cfgdb.get_entry("EVPN_ETHERNET_SEGMENT", "PortChannel1").get("df-preference") == "20000"

        result = runner.invoke(config.config.commands["interface"].commands["evpn-df-pref"].commands["set"],
                               ["PortChannel1", "22222"], obj=db)
        assert result.exit_code == 0
        assert db.cfgdb.get_entry("EVPN_ETHERNET_SEGMENT", "PortChannel1").get("df-preference") == "22222"

        result = runner.invoke(config.config.commands["interface"].commands["evpn-df-pref"].commands["del"],
                               ["PortChannel1", "22222"], obj=db)
        assert result.exit_code == 0
        assert db.cfgdb.get_entry("EVPN_ETHERNET_SEGMENT", "PortChannel1").get("df-preference") is None

    def test_config_interface_evpn_uplink(self):
        runner = CliRunner()
        db = Db()

        result = runner.invoke(config.config.commands["interface"].commands["evpn-uplink"],
                               ["PortChannel1", "enable"], obj=db)
        assert result.exit_code != 0
        assert "interface_name is invalid, should be Ethernet!" in result.output

        result = runner.invoke(config.config.commands["interface"].commands["evpn-uplink"],
                               ["Ethernet4", "on"], obj=db)
        assert result.exit_code != 0
        assert "Invalid value for \"<uplink>\"" in result.output

        result = runner.invoke(config.config.commands["interface"].commands["evpn-uplink"],
                               ["Ethernet4", "enable"], obj=db)
        assert result.exit_code == 0
        assert db.cfgdb.get_entry("EVPN_ETHERNET_SEGMENT", "Ethernet4").get("mh-uplink") == "true"
