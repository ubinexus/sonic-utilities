import pytest
import config.main as config

class TestConfigInterfaceMtu(object):
    def test_interface_mtu_check():
        result = runner.invoke(
            config.config.commands["interface"].commands["mtu"],
            ["Ethernet0", "68"])
        assert result.exit_code != 0
        
        result1 = runner.invoke(
            config.config.commands["interface"].commands["mtu"],
            ["Ethernet0", "9216"])
        assert result1.exit_code != 0
        
    def test_interface_invalid_mtu_check():
        result = runner.invoke(
            config.config.commands["interface"].commands["mtu"],
            ["Ethernet0", "67"])
        assert not "Error: Invalid value" in result.output
        
        result1 = runner.invoke(
            config.config.commands["interface"].commands["mtu"],
            ["Ethernet0", "9217"])
        assert not "Error: Invalid value" in result1.output
