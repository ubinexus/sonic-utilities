import os
import sys
import pytest
from click.testing import CliRunner
from utilities_common.db import Db

test_path = os.path.dirname(os.path.abspath(__file__))
modules_path = os.path.dirname(test_path)
sys.path.insert(0, test_path)
sys.path.insert(0, modules_path)

import show.main as show
import mock_tables.dbconnector

# Expected output for 'show sflow'
show_sflow_output = ''+ \
"""
sFlow Global Information:
  sFlow Admin State:          up
  sFlow Polling Interval:     0
  sFlow AgentID:              eth0

  2 Collectors configured:
    Name: prod                IP addr: fe80::6e82:6aff:fe1e:cd8e UDP port: 6343
    Name: ser5                IP addr: 172.21.35.15    UDP port: 6343
"""

# Expected output for 'show sflow interface'
show_sflow_intf_output = ''+ \
"""
sFlow interface configurations
+-------------+---------------+-----------------+
| Interface   | Admin State   |   Sampling Rate |
+=============+===============+=================+
| Ethernet0   | up            |            2500 |
+-------------+---------------+-----------------+
| Ethernet4   | up            |            1000 |
+-------------+---------------+-----------------+
| Ethernet112 | up            |            1000 |
+-------------+---------------+-----------------+
| Ethernet116 | up            |            5000 |
+-------------+---------------+-----------------+
"""

class TestShowSflow(TestCase):
    @classmethod
    def setup_class(cls):
        print("SETUP")
        os.environ["UTILITIES_UNIT_TESTING"] = "1"

    def setUp(self):
        self.runner = CliRunner()
        self.db = Db()
        self.obj = {'db': self.db}

    def test_show_sflow(self):
        result = self.runner.invoke(show.cli.commands["sflow"], [], obj=self.obj)
        print(sys.stderr, result.output)
        assert result.exit_code == 0
        assert result.output == show_sflow_output

    def test_show_sflow_intf(self):
        result = self.runner.invoke(show.cli.commands["sflow"].commands["interface"], [], obj=self.obj)
        print(sys.stderr, result.output)
        assert result.exit_code == 0
        assert result.output == show_sflow_intf_output

    @classmethod
    def teardown_class(cls):
        print("TEARDOWN")
        os.environ["PATH"] = os.pathsep.join(os.environ["PATH"].split(os.pathsep)[:-1])
        os.environ["UTILITIES_UNIT_TESTING"] = "0"
