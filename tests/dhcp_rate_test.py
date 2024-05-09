import os
import imp

from click.testing import CliRunner

import config.main as config
import show.main as show
from utilities_common.db import Db


class TestDHCPRate(object):

    _old_run_bgp_command = None

    @classmethod
    def setup_class(cls):
        os.environ['UTILITIES_UNIT_TESTING'] = "1"
        print("SETUP")
        import config.main
        imp.reload(config.main)
        import show.main
        imp.reload(show.main)

    def test_config_dhcp_rate_add_on_portchannel(self):
        db = Db()
        runner = CliRunner()
        obj = {'config_db': db.cfgdb}
        result = runner.invoke(config.config.commands["interface"].commands["dhcp-mitigation-rate"].commands["add"],
                               ["PortChannel0001", "20"], obj=obj)
        print(result.exit_code)
        print(result.output)
        assert result.exit_code != 0
        assert "Error: PortChannel0001 is a PortChannel!" in result.output

    def test_config_dhcp_rate_del_on_portchannel(self):
        db = Db()
        runner = CliRunner()
        obj = {'config_db': db.cfgdb}
        result = runner.invoke(config.config.commands["interface"].commands["dhcp-mitigation-rate"].commands["del"],
                               ["PortChannel0001", "20"], obj=obj)
        print(result.exit_code)
        print(result.output)
        assert result.exit_code != 0
        assert "Error: PortChannel0001 is a PortChannel!" in result.output

    def test_config_dhcp_rate_add_on_invalid_port(self):
        db = Db()
        runner = CliRunner()
        obj = {'config_db': db.cfgdb}
        intf = "test_fail_case"
        result = runner.invoke(config.config.commands["interface"].commands["dhcp-mitigation-rate"].commands["add"],
                               [intf, "20"], obj=obj)
        print(result.exit_code)
        print(result.output)
        assert result.exit_code != 0
        assert "Error: {} does not exist".format(intf) in result.output

    def test_config_dhcp_rate_del_on_invalid_port(self):
        db = Db()
        runner = CliRunner()
        obj = {'config_db': db.cfgdb}
        intf = "test_fail_case"
        result = runner.invoke(config.config.commands["interface"].commands["dhcp-mitigation-rate"].commands["del"],
                               [intf, "20"], obj=obj)
        print(result.exit_code)
        print(result.output)
        assert result.exit_code != 0
        assert "Error: {} does not exist".format(intf) in result.output

    def test_config_dhcp_rate_add_invalid_rate(self):
        db = Db()
        runner = CliRunner()
        obj = {'config_db': db.cfgdb}
        result = runner.invoke(config.config.commands["interface"].commands["dhcp-mitigation-rate"].commands["add"],
                               ["Ethernet0", "0"], obj=obj)
        print(result.exit_code)
        print(result.output)
        assert result.exit_code != 0
        assert "Error: DHCP rate limit is not valid. \nIt must be greater than 0." in result.output

    def test_config_dhcp_rate_del_invalid_rate(self):
        db = Db()
        runner = CliRunner()
        obj = {'config_db': db.cfgdb}
        result = runner.invoke(config.config.commands["interface"].commands["dhcp-mitigation-rate"].commands["del"],
                               ["Ethernet0", "0"], obj=obj)
        print(result.exit_code)
        print(result.output)
        assert result.exit_code != 0
        assert "Error: DHCP rate limit is not valid. \nIt must be greater than 0." in result.output

    def test_config_dhcp_rate_add_rate_with_exist_rate(self):
        db = Db()
        runner = CliRunner()
        obj = {'config_db': db.cfgdb}
        result = runner.invoke(config.config.commands["interface"].commands["dhcp-mitigation-rate"].commands["add"],
                               ["Ethernet0", "20"], obj=obj)
        print(result.exit_code)
        print(result.output)
        assert result.exit_code != 0
        assert "Error: Ethernet0 has DHCP rate limit configured. \nRemove it to add new DHCP rate limit." \
            in result.output

    def test_config_dhcp_rate_del_rate_with_nonexist_rate(self):
        db = Db()
        runner = CliRunner()
        obj = {'config_db': db.cfgdb}
        result = runner.invoke(config.config.commands["interface"].commands["dhcp-mitigation-rate"].commands["del"],
                               ["Ethernet0", "20"], obj=obj)
        print(result.exit_code)
        print(result.output)
        assert result.exit_code != 0
        assert "Error: 20 DHCP rate limit does not exist on Ethernet0." in result.output

    @classmethod
    def teardown_class(cls):
        os.environ['UTILITIES_UNIT_TESTING'] = "0"
        print("TEARDOWN")
