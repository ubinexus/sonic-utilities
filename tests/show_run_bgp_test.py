
import os

import pytest

from click.testing import CliRunner

from utilities_common import multi_asic
from utilities_common import constants

from unittest.mock import patch

from sonic_py_common import device_info
from .show_run_commands_input.show_run_bgp_test_vector import *

class TestShowRunCommands(object):
    @classmethod
    def setup_class(cls):
        print("SETUP")
        from .mock_tables import dbconnector

    @pytest.mark.parametrize('setup_single_bgp_instance', 'test_vector', 
                             [' '], indirect=['setup_single_bgp_instance'])
    def test_show_run_bgp_single(
            self,
            setup_bgp_commands,
            setup_single_bgp_instance):
        show = setup_bgp_commands
        runner = CliRunner()
        exec_cmd = show.cli.commands["runningconfiguration"].commands["bgp"]
        input = testData['test_vector']
        result = runner.invoke(exec_cmd, input['args'])
        print("{}".format(result.output))
        import pdb; pdb.set_trace()
        assert result.exit_code == 0
        assert result.output == show_run_bgp_sasic
