import sys
import os
from unittest import mock

from click.testing import CliRunner

test_path = os.path.dirname(os.path.abspath(__file__))
modules_path = os.path.dirname(test_path)
sys.path.insert(0, modules_path)

import pcieutil.main as pcieutil

pcieutil_pcie_aer_correctable_output = """\
+---------------------+-----------+
| AER - CORRECTABLE   |   00:01.0 |
|                     |    0x0001 |
+=====================+===========+
| RxErr               |         0 |
+---------------------+-----------+
| BadTLP              |         0 |
+---------------------+-----------+
| BadDLLP             |         0 |
+---------------------+-----------+
| Rollover            |         0 |
+---------------------+-----------+
| Timeout             |         0 |
+---------------------+-----------+
| NonFatalErr         |         0 |
+---------------------+-----------+
| CorrIntErr          |         0 |
+---------------------+-----------+
| HeaderOF            |         0 |
+---------------------+-----------+
| TOTAL_ERR_COR       |         0 |
+---------------------+-----------+
"""

pcieutil_pcie_aer_non_fatal_output = """\
+--------------------+-----------+
| AER - NONFATAL     |   00:01.0 |
|                    |    0x0001 |
+====================+===========+
| Undefined          |         0 |
+--------------------+-----------+
| DLP                |         0 |
+--------------------+-----------+
| SDES               |         0 |
+--------------------+-----------+
| TLP                |         0 |
+--------------------+-----------+
| FCP                |         0 |
+--------------------+-----------+
| CmpltTO            |         0 |
+--------------------+-----------+
| CmpltAbrt          |         0 |
+--------------------+-----------+
| UnxCmplt           |         0 |
+--------------------+-----------+
| RxOF               |         0 |
+--------------------+-----------+
| MalfTLP            |         0 |
+--------------------+-----------+
| ECRC               |         0 |
+--------------------+-----------+
| UnsupReq           |         0 |
+--------------------+-----------+
| ACSViol            |         0 |
+--------------------+-----------+
| UncorrIntErr       |         0 |
+--------------------+-----------+
| BlockedTLP         |         0 |
+--------------------+-----------+
| AtomicOpBlocked    |         0 |
+--------------------+-----------+
| TLPBlockedErr      |         0 |
+--------------------+-----------+
| TOTAL_ERR_NONFATAL |         0 |
+--------------------+-----------+
"""

pcieutil_pcie_aer_fatal_output = """\
+-----------------+-----------+
| AER - FATAL     |   00:01.0 |
|                 |    0x0001 |
+=================+===========+
| Undefined       |         0 |
+-----------------+-----------+
| DLP             |         0 |
+-----------------+-----------+
| SDES            |         0 |
+-----------------+-----------+
| TLP             |         0 |
+-----------------+-----------+
| FCP             |         0 |
+-----------------+-----------+
| CmpltTO         |         0 |
+-----------------+-----------+
| CmpltAbrt       |         0 |
+-----------------+-----------+
| UnxCmplt        |         0 |
+-----------------+-----------+
| RxOF            |         0 |
+-----------------+-----------+
| MalfTLP         |         0 |
+-----------------+-----------+
| ECRC            |         0 |
+-----------------+-----------+
| UnsupReq        |         0 |
+-----------------+-----------+
| ACSViol         |         0 |
+-----------------+-----------+
| UncorrIntErr    |         0 |
+-----------------+-----------+
| BlockedTLP      |         0 |
+-----------------+-----------+
| AtomicOpBlocked |         0 |
+-----------------+-----------+
| TLPBlockedErr   |         0 |
+-----------------+-----------+
| TOTAL_ERR_FATAL |         0 |
+-----------------+-----------+
"""


class MockPcieUtil(object):
    def __init__(self):
        self.confInfo = [
            {'bus': '00', 'dev': '01', 'name': 'PCIe Device 1', 'fn': '0', 'id': '0001'}
        ]

    def get_pcie_check(self):
        for item in self.confInfo:
            item['result'] = "Passed"

        return self.confInfo


class TestPcieUtil(object):
    @classmethod
    def setup_class(cls):
        print("SETUP")
        os.environ["UTILITIES_UNIT_TESTING"] = "1"

    def test_aer_correctable(self):
        with mock.patch("pcieutil.main.platform_pcieutil", new_callable=MockPcieUtil):
            runner = CliRunner()
            result = runner.invoke(pcieutil.cli.commands["pcie-aer"].commands["correctable"], [])
            assert pcieutil_pcie_aer_correctable_output == result.output

    def test_aer_non_fatal(self):
        with mock.patch("pcieutil.main.platform_pcieutil", new_callable=MockPcieUtil):
            runner = CliRunner()
            result = runner.invoke(pcieutil.cli.commands["pcie-aer"].commands["non-fatal"], [])
            assert pcieutil_pcie_aer_non_fatal_output == result.output

    def test_aer_fatal(self):
        with mock.patch("pcieutil.main.platform_pcieutil", new_callable=MockPcieUtil):
            runner = CliRunner()
            result = runner.invoke(pcieutil.cli.commands["pcie-aer"].commands["fatal"], [])
            assert pcieutil_pcie_aer_fatal_output == result.output

    @classmethod
    def teardown_class(cls):
        print("TEARDOWN")
        os.environ["UTILITIES_UNIT_TESTING"] = "0"
