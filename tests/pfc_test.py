import os
import sys
import pfc.main as pfc
from pfc_input.assert_show_output import pfc_cannot_find_intf, pfc_show_asymmetric_all, \
   pfc_show_asymmetric_intf, pfc_show_priority_all, pfc_show_priority_intf, \
   pfc_config_asymmetric, pfc_config_priority_on, pfc_asym_cannot_find_intf
from utilities_common.db import Db

from click.testing import CliRunner
from importlib import reload

test_path = os.path.dirname(os.path.abspath(__file__))
modules_path = os.path.dirname(test_path)
scripts_path = os.path.join(modules_path, "pfc")
sys.path.insert(0, test_path)
sys.path.insert(0, modules_path)


class TestPfcBase(object):

    @classmethod
    def setup_class(cls):
        print("SETUP")
        os.environ["PATH"] += os.pathsep + scripts_path
        os.environ['UTILITIES_UNIT_TESTING'] = "2"

    def executor(self, cliobj, command, expected_rc=0, expected_output=None, runner=CliRunner()):
        db = Db()
        result = runner.invoke(cliobj, command, obj=db)
        print(result.exit_code)
        print(result.output)

        if result.exit_code != expected_rc:
            print(result.exception)

        assert result.exit_code == expected_rc
        if expected_output:
            assert result.output == expected_output

    @classmethod
    def teardown_class(cls):
        os.environ["PATH"] = os.pathsep.join(os.environ["PATH"].split(os.pathsep)[:-1])
        os.environ["UTILITIES_UNIT_TESTING"] = "0"
        print("TEARDOWN")


class TestPfc(TestPfcBase):

    @classmethod
    def setup_class(cls):
        super().setup_class()
        from mock_tables import dbconnector
        from mock_tables import mock_single_asic
        reload(mock_single_asic)
        dbconnector.load_namespace_config()

    def test_pfc_show_asymmetric_all(self):
        self.executor(pfc.cli, ['show', 'asymmetric'],
                      expected_output=pfc_show_asymmetric_all)

    def test_pfc_show_asymmetric_intf(self):
        self.executor(pfc.cli, ['show', 'asymmetric', 'Ethernet0'],
                      expected_output=pfc_show_asymmetric_intf)

    def test_pfc_show_asymmetric_intf_fake(self):
        self.executor(pfc.cli, ['show', 'asymmetric', 'Ethernet1234'],
                      expected_output=pfc_asym_cannot_find_intf)

    def test_pfc_show_priority_all(self):
        self.executor(pfc.cli, ['show', 'priority'],
                      expected_output=pfc_show_priority_all)

    def test_pfc_show_priority_intf(self):
        self.executor(pfc.cli, ['show', 'priority', 'Ethernet0'],
                      expected_output=pfc_show_priority_intf)

    def test_pfc_show_priority_intf_fake(self):
        self.executor(pfc.cli, ['show', 'priority', 'Ethernet1234'],
                      expected_output=pfc_cannot_find_intf)

    def test_pfc_config_asymmetric(self):
        self.executor(pfc.cli, ['config', 'asymmetric', 'on', 'Ethernet0'],
                      expected_output=pfc_config_asymmetric)

    def test_pfc_config_priority(self):
        self.executor(pfc.cli, ['config', 'priority', 'on', 'Ethernet0', '5'],
                      expected_output=pfc_config_priority_on)
