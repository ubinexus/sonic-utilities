import imp
import os
import sys
import traceback
import json
from unittest import mock

from click.testing import CliRunner

import config.main as config
import show.main as show

test_path = os.path.dirname(os.path.abspath(__file__))
modules_path = os.path.dirname(test_path)
sys.path.insert(0, test_path)
sys.path.insert(0, modules_path)

import mock_tables.dbconnector

show_radius_default_output="""\
RADIUS global auth_type pap (default)
RADIUS global retransmit 3 (default)
RADIUS global timeout 5 (default)
RADIUS global passkey <EMPTY_STRING> (default)

"""

config_radius_empty_output="""\
"""

config_radius_server_invalidkey_output="""\
--key: Valid chars are ASCII printable except SPACE, '#', and ','
"""

config_radius_invalidipaddress_output="""\
Invalid ip address
"""

class TestRadius(object):
    @classmethod
    def setup_class(cls):
        os.environ['UTILITIES_UNIT_TESTING'] = "1"
        print("SETUP")
        import config.main
        imp.reload(config.main)
        import show.main
        imp.reload(show.main)

    @classmethod
    def teardown_class(cls):
        os.environ['UTILITIES_UNIT_TESTING'] = "0"
        print("TEARDOWN")

    def test_show_radius_default(self):
        runner = CliRunner()
        result = runner.invoke(show.cli.commands["radius"], [])
        print(result.exit_code)
        print(result.output)
        assert result.exit_code == 0
        assert result.output == show_radius_default_output

    def test_config_radius_server(self):
        runner = CliRunner()
        result = runner.invoke(config.config.commands["radius"],\
                               ["add", "10.10.10.10", "-r", "1", "-t", "3",\
                                "-k", "testing123", "-s", "eth0"])
        print(result.exit_code)
        print(result.output)
        assert result.exit_code == 0
        assert result.output == config_radius_empty_output

        result = runner.invoke(config.config.commands["radius"],\
                               ["delete", "10.10.10.10"])
        print(result.exit_code)
        print(result.output)
        assert result.exit_code == 0
        assert result.output == config_radius_empty_output

    def test_config_radius_server_invalidkey(self):
        runner = CliRunner()
        result = runner.invoke(config.config.commands["radius"],\
                               ["add", "10.10.10.10", "-r", "1", "-t", "3",\
                                "-k", "comma,invalid", "-s", "eth0"])
        print(result.exit_code)
        print(result.output)
        assert result.exit_code == 0
        assert result.output == config_radius_server_invalidkey_output

    def test_config_radius_nasip_invalid(self):
        runner = CliRunner()
        result = runner.invoke(config.config.commands["radius"],\
                               ["nasip", "invalid"])
        print(result.exit_code)
        print(result.output)
        assert result.exit_code == 0
        assert result.output == config_radius_invalidipaddress_output

    def test_config_radius_sourceip_invalid(self):
        runner = CliRunner()
        result = runner.invoke(config.config.commands["radius"],\
                               ["sourceip", "invalid"])
        print(result.exit_code)
        print(result.output)
        assert result.exit_code == 0
        assert result.output == config_radius_invalidipaddress_output

    def test_config_radius_authtype(self):
        runner = CliRunner()
        result = runner.invoke(config.config.commands["radius"],\
                               ["authtype", "chap"])
        print(result.exit_code)
        print(result.output)
        assert result.exit_code == 0
        assert result.output == config_radius_empty_output

        result = runner.invoke(config.config.commands["radius"],\
                               ["default", "authtype"])
        print(result.exit_code)
        print(result.output)
        assert result.exit_code == 0
        assert result.output == config_radius_empty_output

