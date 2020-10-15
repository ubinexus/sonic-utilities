import os
import sys
import textwrap

import mock
from click.testing import CliRunner

test_path = os.path.dirname(os.path.abspath(__file__))
modules_path = os.path.dirname(test_path)
sys.path.insert(0, modules_path)

import show.main as show


TEST_REBOOT_CAUSE = "warm-reboot"
TEST_USER = "admin"
TEST_REBOOT_TIME = "Fri Oct  9 04:51:47 UTC 2020"


"""
    Note: The following 'show reboot-cause' commands simply call other SONiC
    CLI utilities, so the unit tests for the other utilities are expected
    to cover testing their functionality:

        show reboot-cause
        show reboot-cause history
"""

class TestShowRebootCause(object):
    @classmethod
    def setup_class(cls):
        print("SETUP")
        os.environ["UTILITIES_UNIT_TESTING"] = "1"

    # Test 'show reboot-cause'
    def test_reboot_cause(self):
        expected_output = "Unknown"
        runner = CliRunner()
        result = runner.invoke(show.cli.commands["reboot-cause"], [])
        assert result.output == textwrap.dedent(expected_output)

    # Test 'show reboot-cause history'
    def test_reboot_cause_history(self):
        expected_output = """\
name                 cause        time                          user    comment
-------------------  -----------  ----------------------------  ------  ---------
2020_10_09_04_53_58  warm-reboot  Fri Oct  9 04:51:47 UTC 2020  admin
2020_10_09_02_33_06  reboot       Fri Oct  9 02:29:44 UTC 2020  admin
"""
        runner = CliRunner()
        result = self.runner.invoke(show.cli.commands["reboot-cause"], ["history"], obj=self.obj)
        assert result.output == expected_output

    @classmethod
    def teardown_class(cls):
        print("TEARDOWN")
        os.environ["PATH"] = os.pathsep.join(os.environ["PATH"].split(os.pathsep)[:-1])
        os.environ["UTILITIES_UNIT_TESTING"] = "0"
