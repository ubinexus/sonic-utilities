import pytest
import config.main as config
from click.testing import CliRunner
from utilities_common.db import Db

class TestConfigInterfaceMtu(object):
    def test_interface_mtu_check(self):
        runner = CliRunner()
        db = Db()
        result = runner.invoke(config.config.commands["interface"].commands["mtu"],
            ["Ethernet0", "68"], obj=db)
        assert result.exit_code != 0

        result1 = runner.invoke(config.config.commands["interface"].commands["mtu"],
            ["Ethernet0", "9216"], obj=db)
        assert result1.exit_code != 0

    def test_interface_invalid_mtu_check(self):
        runner = CliRunner()
        db = Db()
        result = runner.invoke(config.config.commands["interface"].commands["mtu"],
            ["Ethernet0", "67"], obj=db)
        assert not 'Usage: mtu [OPTIONS] <interface_name> <interface_mtu>\nTry "mtu --help" for help.\n\nError: Invalid value for "<interface_mtu>": 67 is not in the valid range of 68 to 9216.\n' in result.output

        result1 = runner.invoke(config.config.commands["interface"].commands["mtu"],
            ["Ethernet0", "9217"], obj=db)
        assert not 'Usage: mtu [OPTIONS] <interface_name> <interface_mtu>\nTry "mtu --help" for help.\n\nError: Invalid value for "<interface_mtu>": 9217 is not in the valid range of 68 to 9216.\n' in result1.output
