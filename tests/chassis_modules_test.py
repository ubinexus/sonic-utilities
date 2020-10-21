import sys
import os
from click.testing import CliRunner

test_path = os.path.dirname(os.path.abspath(__file__))
modules_path = os.path.dirname(test_path)
sys.path.insert(0, modules_path)

import show.main as show
import config.main as config
import tests.mock_tables.dbconnector
from utilities_common.db import Db

show_linecard0_shutdown_output="""\
LINE-CARD0 line-card 1 Empty down
"""

show_linecard0_startup_output="""\
LINE-CARD0 line-card 1 Empty up
"""

class TestChassisModules(object):
    @classmethod
    def setup_class(cls):
        print("SETUP")
        os.environ["UTILITIES_UNIT_TESTING"] = "1"

    def test_show_all_count_lines(self):
        runner = CliRunner()
        result = runner.invoke(show.cli.commands["chassis-modules"].commands["status"], [])
        print(result.output)
        result_lines = result.output.strip('\n').split('\n')
        modules = ["FABRIC-CARD0", "FABRIC-CARD1", "LINE-CARD0", "LINE-CARD1", "SUPERVISOR0"]
        for i, module in enumerate(modules):
            assert module in result_lines[i+2]
        header_lines = 2
        assert len(result_lines) == header_lines + len(modules)

    def test_show_single_count_lines(self):
        runner = CliRunner()
        result = runner.invoke(show.cli.commands["chassis-modules"].commands["status"], ["LINE-CARD0"])
        print(result.output)
        result_lines = result.output.strip('\n').split('\n')
        modules = ["LINE-CARD0"]
        for i, module in enumerate(modules):
            assert module in result_lines[i+2]
        header_lines = 2
        assert len(result_lines) == header_lines + len(modules)

    def test_show_linecard_down(self):
        runner = CliRunner()
        result = runner.invoke(show.cli.commands["chassis-modules"].commands["status"], ["LINE-CARD1"])
        result_lines = result.output.strip('\n').split('\n')
        assert result.exit_code == 0
        header_lines = 2
        result_out = (result_lines[header_lines]).split()
        assert result_out[4] == 'down'

    def test_config_shutdown_module(self):
        runner = CliRunner()
        db = Db()
        result = runner.invoke(config.config.commands["chassis-modules"].commands["shutdown"], ["LINE-CARD0"], obj=db)
        print(result.exit_code)
        print(result.output)
        assert result.exit_code == 0

        result = runner.invoke(show.cli.commands["chassis-modules"].commands["status"], [], obj=db)
        print(result.exit_code)
        print(result.output)
        result_lines = result.output.strip('\n').split('\n')
        assert result.exit_code == 0
        header_lines = 2
        result_out = " ".join((result_lines[header_lines + 2]).split())
        assert result_out.strip('\n') == show_linecard0_shutdown_output.strip('\n')
        #db.cfgdb.set_entry("CHASSIS_MODULE", "LINE-CARD0", { "admin_status" : "down" })
        #db.get_data("CHASSIS_MODULE", "LINE-CARD0")

    def test_config_startup_module(self):
        runner = CliRunner()
        db = Db()
        result = runner.invoke(config.config.commands["chassis-modules"].commands["startup"], ["LINE-CARD0"], obj=db)
        print(result.exit_code)
        print(result.output)
        assert result.exit_code == 0

        result = runner.invoke(show.cli.commands["chassis-modules"].commands["status"], [], obj=db)
        print(result.exit_code)
        print(result.output)
        result_lines = result.output.strip('\n').split('\n')
        assert result.exit_code == 0
        header_lines = 2
        result_out = " ".join((result_lines[header_lines + 2]).split())
        assert result_out.strip('\n') == show_linecard0_startup_output.strip('\n')

    @classmethod
    def teardown_class(cls):
        print("TEARDOWN")
        os.environ["UTILITIES_UNIT_TESTING"] = "0"
