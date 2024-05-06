import os
from unittest import mock

from click.testing import CliRunner

import config.main as config
import show.main as show
from utilities_common.db import Db
import utilities_common.bgp_util as bgp_util

test_config_dhcp_rate_add_del_output = """\
Interface    DHCP Mitigation Rate
-----------  --------------------
Ethernet0    300
Ethernet4    300
Ethernet8    300
Ethernet12   300
Ethernet16   300
Ethernet20   300
Ethernet24
Ethernet28   300
Ethernet36   45
Ethernet40   300
Ethernet44   300
Ethernet48   300
Ethernet52   300
Ethernet56   300
Ethernet60   300
Ethernet64   300
Ethernet68   300
Ethernet72   300
Ethernet76   300
Ethernet80   300
Ethernet84   300
Ethernet88   300
Ethernet92   300
Ethernet96   300
Ethernet100  300
Ethernet104  300
Ethernet108  300
Ethernet116  300
Ethernet124  300
"""


class TestDHCPRate(object):

    _old_run_bgp_command = None

    @classmethod
    def setup_class(cls):
        os.environ['UTILITIES_UNIT_TESTING'] = "1"
        cls._old_run_bgp_command = bgp_util.run_bgp_command
        bgp_util.run_bgp_command = mock.MagicMock(
            return_value=cls.mock_run_bgp_command())
        print("SETUP")

    def mock_run_bgp_command():
        return ""

    def test_config_dhcp_rate_add_on_portchannel(self):
        runner = CliRunner()
        result = runner.invoke(config.config.commands["interface"].commands["dhcp-mitigation-rate"].commands["add"],
                               ["PortChannel0001", "20"])
        print(result.exit_code)
        print(result.output)
        assert result.exit_code != 0
        assert "Error: PortChannel0001 is a PortChannel!" in result.output

    def test_config_dhcp_rate_del_on_portchannel(self):
        runner = CliRunner()
        result = runner.invoke(config.config.commands["interface"].commands["dhcp-mitigation-rate"].commands["del"],
                               ["PortChannel0001", "20"])
        print(result.exit_code)
        print(result.output)
        assert result.exit_code != 0
        assert "Error: PortChannel0001 is a PortChannel!" in result.output

    def test_config_dhcp_rate_add_on_invalid_port(self):
        runner = CliRunner()
        intf = "test_fail_case"
        result = runner.invoke(config.config.commands["interface"].commands["dhcp-mitigation-rate"].commands["add"],
                               [intf, "20"])
        print(result.exit_code)
        print(result.output)
        assert result.exit_code != 0
        assert "Error: {} does not exist".format(intf) in result.output

    def test_config_dhcp_rate_del_on_invalid_port(self):
        runner = CliRunner()
        intf = "test_fail_case"
        result = runner.invoke(config.config.commands["interface"].commands["dhcp-mitigation-rate"].commands["del"],
                               [intf, "20"])
        print(result.exit_code)
        print(result.output)
        assert result.exit_code != 0
        assert "Error: {} does not exist".format(intf) in result.output

    def test_config_dhcp_rate_add_invalid_rate(self):
        runner = CliRunner()
        result = runner.invoke(config.config.commands["interface"].commands["dhcp-mitigation-rate"].commands["add"],
                               ["Ethernet0", "0"])
        print(result.exit_code)
        print(result.output)
        assert result.exit_code != 0
        assert "Error: DHCP rate limit is not valid. \nIt must be greater than 0." in result.output

    def test_config_dhcp_rate_del_invalid_rate(self):
        runner = CliRunner()
        result = runner.invoke(config.config.commands["interface"].commands["dhcp-mitigation-rate"].commands["del"],
                               ["Ethernet0", "0"])
        print(result.exit_code)
        print(result.output)
        assert result.exit_code != 0
        assert "Error: DHCP rate limit is not valid. \nIt must be greater than 0." in result.output

    def test_config_dhcp_rate_add_rate_with_exist_rate(self):
        runner = CliRunner()
        result = runner.invoke(config.config.commands["interface"].commands["dhcp-mitigation-rate"].commands["add"],
                               ["Ethernet0", "20"])
        print(result.exit_code)
        print(result.output)
        assert result.exit_code != 0
        assert "Error: Ethernet0 has DHCP rate limit configured. \nRemove it to add new DHCP rate limit." \
            in result.output

    def test_config_dhcp_rate_del_rate_with_nonexist_rate(self):
        runner = CliRunner()
        result = runner.invoke(config.config.commands["interface"].commands["dhcp-mitigation-rate"].commands["del"],
                               ["Ethernet0", "20"])
        print(result.exit_code)
        print(result.output)
        assert result.exit_code != 0
        assert "Error: 20 DHCP rate limit does not exist on Ethernet0." in result.output

    def test_config_dhcp_rate_add_del(self):
        runner = CliRunner()
        db = Db()

        # Remove default DHCP rate limit from Ethernet24
        result = runner.invoke(config.config.commands["interface"].commands["dhcp-mitigation-rate"].commands["del"],
                               ["Ethernet24", "300"], obj=db)
        print(result.exit_code)
        print(result.output)
        assert result.exit_code == 0

        # Remove default DHCP rate limit from Ethernet32
        result = runner.invoke(config.config.commands["interface"].commands["dhcp-mitigation-rate"].commands["del"],
                               ["Ethernet32", "300"], obj=db)
        print(result.exit_code)
        print(result.output)
        assert result.exit_code == 0

        # Add DHCP rate limit 45 on Ethernet32
        result = runner.invoke(config.config.commands["interface"].commands["dhcp-mitigation-rate"].commands["add"],
                               ["Ethernet32", "45"], obj=db)
        print(result.exit_code)
        print(result.output)
        assert result.exit_code == 0

        # show output
        result = runner.invoke(show.cli.commands["interfaces"].commands["dhcp-mitigation-rate"], [], obj=db)
        print(result.exit_code)
        print(result.output)
        assert result.exit_code == 0
        assert result.output == test_config_dhcp_rate_add_del_output
