import os
import traceback

from click.testing import CliRunner

from utilities_common.db import Db

load_minigraph_command_output="""\
Stopping SONiC target ...
Running command: /usr/local/bin/sonic-cfggen -H -m --write-to-db
Running command: pfcwd start_default
Running command: config qos reload
Restarting SONiC target ...
Reloading Monit configuration ...
Please note setting loaded from minigraph will be lost after system reboot. To preserve setting, run `config save`.
"""

class TestLoadMinigraph(object):
    @classmethod
    def setup_class(cls):
        os.environ['UTILITIES_UNIT_TESTING'] = "1"
        print("SETUP")

    def test_load_minigraph(self, get_cmd_module, setup_single_broacom_asic):
        (config, show) = get_cmd_module
        runner = CliRunner()
        result = runner.invoke(config.config.commands["load_minigraph"], ["-y"])
        print(result.exit_code)
        print(result.output)
        traceback.print_tb(result.exc_info[2])
        assert result.exit_code == 0
        assert "\n".join([ l.rstrip() for l in result.output.split('\n')]) == load_minigraph_command_output

    @classmethod
    def teardown_class(cls):
        os.environ['UTILITIES_UNIT_TESTING'] = "0"
        print("TEARDOWN")
