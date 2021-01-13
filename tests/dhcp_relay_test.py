import os
import traceback

from click.testing import CliRunner

import config.main as config
import show.main as show
from utilities_common.db import Db

show_dhcp_relay_brief_output="""\
+------------------+-----------------------+
| Interface Name   | DHCP Helper Address   |
+==================+=======================+
| Ethernet0        | 12.0.0.1              |
|                  | 12.0.0.2              |
|                  | 12.0.0.3              |
+------------------+-----------------------+
| Vlan1000         | 192.0.0.1             |
|                  | 192.0.0.2             |
|                  | 192.0.0.3             |
|                  | 192.0.0.4             |
+------------------+-----------------------+
| Vlan2000         | 192.0.0.1             |
|                  | 192.0.0.2             |
|                  | 192.0.0.3             |
|                  | 192.0.0.4             |
+------------------+-----------------------+
"""

config_vlan_add_dhcp_relay_output="""\
Added DHCP relay address 192.0.0.4 to Vlan2000
Restarting DHCP relay service...
"""

config_vlan_rem_dhcp_relay_output="""\
Removed DHCP relay address 192.0.0.4 from Vlan1000
Restarting DHCP relay service...
"""

config_physical_add_dhcp_relay_output="""\
Added DHCP relay address 12.0.0.4 to Ethernet0
Restarting DHCP relay service...
"""

config_physical_rem_dhcp_relay_output="""\
Removed DHCP relay address 12.0.0.3 from Ethernet0
Restarting DHCP relay service...
"""

class TestDhcpRelay(object):
    @classmethod
    def setup_class(cls):
        os.environ['UTILITIES_UNIT_TESTING'] = "1"
        print("SETUP")

    def test_show_dhcp_relay_brief(self):
        runner = CliRunner()
        db = Db()
        obj = {'db':db.cfgdb}

        # show brief output
        result = runner.invoke(show.cli.commands["ip"].commands["dhcp-relay"].commands["brief"], [], obj=obj)
        print(result.output)
        assert result.output == show_dhcp_relay_brief_output

    def test_config_add_delete_dhcp_relay_physical_interface(self):
        runner = CliRunner()
        db = Db()
        obj = {'db':db.cfgdb}

        # add a same dhcp relay server address to Ethernet0
        result = runner.invoke(config.config.commands["interface"].commands["ip"].commands["dhcp-relay"].commands["add"], ["Ethernet0", "12.0.0.3"], obj=obj)
        print(result.exit_code)
        print(result.output)
        assert result.exit_code != 0
        assert "Error: IP address 12.0.0.3 is already configured" in result.output

        # remove dhcp relay server address from Ethernet0
        result = runner.invoke(config.config.commands["interface"].commands["ip"].commands["dhcp-relay"].commands["remove"], ["Ethernet0", "12.0.0.3"], obj=obj)
        print(result.exit_code)
        print(result.output)
        assert result.exit_code == 0
        assert result.output == config_physical_rem_dhcp_relay_output

        # add a new dhcp relay server address to Ethernet0
        result = runner.invoke(config.config.commands["interface"].commands["ip"].commands["dhcp-relay"].commands["add"], ["Ethernet0", "12.0.0.4"], obj=obj)
        print(result.exit_code)
        print(result.output)
        assert result.exit_code == 0
        assert result.output == config_physical_add_dhcp_relay_output

    def test_config_add_delete_dhcp_relay_vlan_interface(self):
        runner = CliRunner()
        db = Db()
        obj = {'db':db.cfgdb}

        # add a new dhcp relay server address to Vlan1000
        result = runner.invoke(config.config.commands["interface"].commands["ip"].commands["dhcp-relay"].commands["add"], ["Vlan1000", "192.0.0.5"], obj=obj)
        print(result.exit_code)
        print(result.output)
        assert result.exit_code != 0
        assert "Error: Maximum number of Servers configured on the relay interface Vlan1000" in result.output

        # remove a existing dhcp relay server address from Vlan1000
        result = runner.invoke(config.config.commands["interface"].commands["ip"].commands["dhcp-relay"].commands["remove"], ["Vlan1000", "192.0.0.4"], obj=obj)
        print(result.exit_code)
        print(result.output)
        assert result.exit_code == 0
        assert result.output == config_vlan_rem_dhcp_relay_output

    @classmethod
    def teardown_class(cls):
        os.environ['UTILITIES_UNIT_TESTING'] = "0"
        print("TEARDOWN")
