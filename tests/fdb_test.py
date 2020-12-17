import os
import traceback
from unittest import mock

from click.testing import CliRunner

import config.main as config
import show.main as show
from utilities_common.db import Db

show_mac_aging_time="""\
Mac Aging-Time : 300 seconds

"""

show_mac_config_add="""\
Vlan     MAC                Port
-------  -----------------  ---------
Vlan100  00:00:00:00:00:01  Ethernet4
"""

show_mac_config_del="""\
Vlan    MAC    Port
------  -----  ------
"""

class TestFdb(object):
    @classmethod
    def setup_class(cls):
        os.environ['UTILITIES_UNIT_TESTING'] = "1"
        print("SETUP")

    def test_fdb_aging_time(self):
        runner = CliRunner()
        db = Db()
        result = runner.invoke(config.config.commands["mac"].commands["aging_time"], ["300"], obj=db)
        print(result.exit_code)
        print(result.output)
        assert result.exit_code == 0
        result = runner.invoke(show.cli.commands["mac"].commands["aging-time"], [], obj=db)
        print(result.exit_code)
        print(result.output)
        assert result.exit_code == 0
        assert result.output == show_mac_aging_time

    def test_fdb_mac_add(self):
        runner = CliRunner()
        db = Db()
        result = runner.invoke(config.config.commands["vlan"].commands["add"], ["100"], obj=db)
        result = runner.invoke(config.config.commands["vlan"].commands["member"].commands["add"], ["100", "Ethernet4"], obj=db)
        result = runner.invoke(config.config.commands["mac"].commands["add"], ["00:00:00:00:00:01", "100", "Ethernet4"], obj=db)
        print(result.exit_code)
        print(result.output)
        assert result.exit_code == 0
        result = runner.invoke(show.cli.commands["mac"].commands["config"], [], obj=db)
        print(result.exit_code)
        print(result.output)
        assert result.exit_code == 0
        assert result.output == show_mac_config_add
        result = runner.invoke(config.config.commands["mac"].commands["del"], ["00:00:00:00:00:01", "100"], obj=db)
        print(result.exit_code)
        print(result.output)
        assert result.exit_code == 0
        result = runner.invoke(show.cli.commands["mac"].commands["config"], [], obj=db)
        print(result.exit_code)
        print(result.output)
        assert result.exit_code == 0
        assert result.output == show_mac_config_del

    @classmethod
    def teardown_class(cls):
        os.environ['UTILITIES_UNIT_TESTING'] = "0"
        print("TEARDOWN")
