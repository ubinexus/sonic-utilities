import os
import sys
from click.testing import CliRunner
from unittest import TestCase
import subprocess

from utilities_common.db import Db
import config.main as config
from .utils import get_result_and_return_code

root_path = os.path.dirname(os.path.abspath(__file__))
modules_path = os.path.dirname(root_path)
scripts_path = os.path.join(modules_path, "scripts")

config_intf_mtu_eth0_255_verbose_output = """\
Running command: portconfig -p Ethernet0 -m 255 -vv
Setting mtu 255 on port Ethernet0
"""

config_intf_mtu_eth32_portchannel_member_output = """\
Usage: mtu [OPTIONS] <interface_name> <interface_mtu>
Try "mtu --help" for help.

Error: Ethernet32 is in portchannel!
"""

config_intf_mtu_etp666_bad_alias_output = """\
Usage: mtu [OPTIONS] <interface_name> <interface_mtu>
Try "mtu --help" for help.

Error: Failed to convert alias etp666 to interface name. Result: etp666
"""

config_intf_mtu_invalid_port_type_command = \
"Invalid port type specified"

config_intf_mtu_multiasic_wrong_namespace_portconfig_output = \
"asic666 is not a valid namespace name in configuration file"

config_intf_multiasic_wrong_namespace_output = """\
Usage: interface [OPTIONS] COMMAND [ARGS]...
Try "interface --help" for help.

Error: Invalid value for "-n" / "--namespace": invalid choice: asic666. (choose from asic0, asic1)
"""

config_intf_output = """\
Usage: interface [OPTIONS] COMMAND [ARGS]...
Try "interface --help" for help.

Error: Missing command.
"""

class TestPortconfig(TestCase):
    @classmethod
    def setup_class(cls):
        print("SETUP")
        os.environ["PATH"] += os.pathsep + scripts_path
        os.environ["UTILITIES_UNIT_TESTING"] = "1"

    def setUp(self):
        self.runner = CliRunner()

    def test_config_intf(self):
        runner = CliRunner()

        result = runner.invoke(config.config.commands["interface"],
                               ["--namespace", "asic0"])
        print(result.exit_code, result.output)
        assert result.exit_code == 2
        assert config_intf_output == result.output

    def test_config_intf_multiasic(self):
        runner = CliRunner()

        os.environ["UTILITIES_UNIT_TESTING_TOPOLOGY"] = "multi_asic"
        result = runner.invoke(config.config.commands["interface"],
                               ["--namespace", "asic0"])
        os.environ["UTILITIES_UNIT_TESTING_TOPOLOGY"] = ""
        print(result.exit_code, result.output)
        assert result.exit_code == 2
        assert config_intf_output == result.output

    def test_config_intf_multiasic_bad_namespace(self):
        runner = CliRunner()

        os.environ["UTILITIES_UNIT_TESTING_TOPOLOGY"] = "multi_asic"
        result = runner.invoke(config.config.commands["interface"],
                               ["--namespace", "asic666"])
        os.environ["UTILITIES_UNIT_TESTING_TOPOLOGY"] = ""
        print(result.exit_code, result.output)
        assert result.exit_code == 2
        assert config_intf_multiasic_wrong_namespace_output == result.output

    def test_config_intf_mtu_invalid_port_type(self):
        db = Db()
        runner = CliRunner()
        obj = {'config_db': db.cfgdb, 'namespace': ''}

        result = runner.invoke(config.config.commands["interface"].commands["mtu"],
                               ["Something0", "255"], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code == 1

        return_code, result = get_result_and_return_code('portconfig -p Something0 -m 255')
        print("return_code: {}".format(return_code))
        print("result = {}".format(result))
        assert return_code == 1
        assert result == config_intf_mtu_invalid_port_type_command

    def test_config_intf_mtu_ethernet(self):
        db = Db()
        runner = CliRunner()
        obj = {'config_db': db.cfgdb, 'namespace': ''}

        result = runner.invoke(config.config.commands["interface"].commands["mtu"],
                               ["Ethernet0", "255"], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code == 0

        return_code, result = get_result_and_return_code('portconfig -p Ethernet0 -m 255')
        print("return_code: {}".format(return_code))
        assert return_code == 0

    def test_config_intf_mtu_portchannel(self):
        db = Db()
        runner = CliRunner()
        obj = {'config_db': db.cfgdb, 'namespace': ''}

        result = runner.invoke(config.config.commands["interface"].commands["mtu"],
                               ["PortChannel0001", "255"], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code == 0

        return_code, result = get_result_and_return_code('portconfig -p PortChannel0001 -m 255')
        print("return_code: {}".format(return_code))
        assert return_code == 0

    def test_config_intf_mtu_ethernet_portchannel_member(self):
        db = Db()
        runner = CliRunner()
        obj = {'config_db': db.cfgdb, 'namespace': ''}

        result = runner.invoke(config.config.commands["interface"].commands["mtu"],
                               ["Ethernet32", "255"], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code == 2
        assert config_intf_mtu_eth32_portchannel_member_output == result.output

    def test_config_intf_mtu_ethernet_alias(self):
        db = Db()
        runner = CliRunner()
        obj = {'config_db': db.cfgdb, 'namespace': ''}

        os.environ['SONIC_CLI_IFACE_MODE'] = "alias"
        result = runner.invoke(config.config.commands["interface"].commands["mtu"],
                               ["etp1", "255"], obj=obj)
        os.environ['SONIC_CLI_IFACE_MODE'] = "default"
        print(result.exit_code, result.output)
        assert result.exit_code == 0

    def test_config_intf_mtu_ethernet_alias_bad(self):
        db = Db()
        runner = CliRunner()
        obj = {'config_db': db.cfgdb, 'namespace': ''}

        os.environ['SONIC_CLI_IFACE_MODE'] = "alias"
        result = runner.invoke(config.config.commands["interface"].commands["mtu"],
                               ["etp666", "255"], obj=obj)
        os.environ['SONIC_CLI_IFACE_MODE'] = "default"
        print(result.exit_code, result.output)
        assert result.exit_code == 2
        assert config_intf_mtu_etp666_bad_alias_output == result.output

    def test_config_intf_mtu_ethernet_alias_portchannel_member(self):
        db = Db()
        runner = CliRunner()
        obj = {'config_db': db.cfgdb, 'namespace': ''}

        os.environ['SONIC_CLI_IFACE_MODE'] = "alias"
        result = runner.invoke(config.config.commands["interface"].commands["mtu"],
                               ["etp9", "255"], obj=obj)
        os.environ['SONIC_CLI_IFACE_MODE'] = "default"
        print(result.exit_code, result.output)
        assert result.exit_code == 2
        assert config_intf_mtu_eth32_portchannel_member_output == result.output

    def test_config_intf_mtu_ethernet_verbose(self):
        db = Db()
        runner = CliRunner()
        obj = {'config_db': db.cfgdb, 'namespace': ''}

        result = runner.invoke(config.config.commands["interface"].commands["mtu"],
                               ["Ethernet0", "255", "-v"], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code == 0
        assert result.output == config_intf_mtu_eth0_255_verbose_output

    def test_config_intf_mtu_ethernet_multiasic(self):
        db = Db()
        runner = CliRunner()
        obj = {'config_db': db.cfgdb, 'namespace': 'asic0'}

        os.environ["UTILITIES_UNIT_TESTING_TOPOLOGY"] = "multi_asic"
        result = runner.invoke(config.config.commands["interface"].commands["mtu"],
                               ["Ethernet0", "255"], obj=obj)
        os.environ["UTILITIES_UNIT_TESTING_TOPOLOGY"] = ""
        print(result.exit_code, result.output)
        assert result.exit_code == 0

        os.environ["UTILITIES_UNIT_TESTING_TOPOLOGY"] = "multi_asic"
        return_code, result = get_result_and_return_code('portconfig -p Ethernet0 -n asic0 -m 255')
        os.environ["UTILITIES_UNIT_TESTING_TOPOLOGY"] = ""
        print("return_code: {}".format(return_code))
        assert return_code == 0

    def test_config_intf_mtu_ethernet_multiasic_bad_namespace(self):
        db = Db()
        runner = CliRunner()
        obj = {'config_db': db.cfgdb, 'namespace': 'asic666'}

        os.environ["UTILITIES_UNIT_TESTING_TOPOLOGY"] = "multi_asic"
        return_code, result = get_result_and_return_code('portconfig -p Ethernet0 -n asic666 -m 255')
        os.environ["UTILITIES_UNIT_TESTING_TOPOLOGY"] = ""
        print("return_code: {}".format(return_code))
        print("result = {}".format(result))
        assert return_code == 1
        assert config_intf_mtu_multiasic_wrong_namespace_portconfig_output == result

    @classmethod
    def teardown_class(cls):
        print("TEARDOWN")
        os.environ["PATH"] = os.pathsep.join(os.environ["PATH"].split(os.pathsep)[:-1])
        os.environ["UTILITIES_UNIT_TESTING"] = "0"
        os.environ["UTILITIES_UNIT_TESTING_TOPOLOGY"] = ""
        os.environ['SONIC_CLI_IFACE_MODE'] = "default"
