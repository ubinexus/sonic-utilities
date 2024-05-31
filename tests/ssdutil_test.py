import sys
import os
from unittest.mock import patch, MagicMock
sys.modules['sonic_platform'] = MagicMock()
sys.modules['argparse'] = MagicMock()
sys.modules['subprocess'] = MagicMock()

import ssdutil.main as ssdutil  # noqa: E402

# Add mocked_libs path so that the file can load mocked modules from there
tests_path = os.path.dirname(os.path.abspath(__file__))
mocked_libs_path = os.path.join(tests_path, "mocked_libs")
sys.path.insert(0, mocked_libs_path)

from .mocked_libs import sonic_platform_base  # noqa: E402,F401


test_path = os.path.dirname(os.path.abspath(__file__))
modules_path = os.path.dirname(test_path)
sys.path.insert(0, modules_path)

ssdutil_output = """
Device Model : InnoDisk Corp. - mSATA 3IE3
Health       : 99%
Temperature  : 30C
"""

ssdutil_verbose_output = """
Device Model : InnoDisk Corp. - mSATA 3IE3
Firmware     : S16425cG
Serial       : BCA12310040200027
Health       : 99%
Temperature  : 30C
"""


class Ssd():

    def get_model(self):
        return 'SkyNet'

    def get_firmware(self):
        return 'ABC'

    def get_serial(self):
        return 'T1000'

    def get_health(self):
        return 5

    def get_temperature(self):
        return 3000

    def get_vendor_output(self):
        return 'SONiC Test'


class TestSsdutil:

    @patch('sonic_py_common.device_info.get_paths_to_platform_and_hwsku_dirs', MagicMock(return_value=("test_path", "")))  # noqa: E501
    @patch('os.geteuid', MagicMock(return_value=0))
    @patch('builtins.print')
    def test_sonic_storage_path(self, mock_print):

        ssdutil.ssdutil()
        assert mock_print.call_count == 6

    @patch('sonic_py_common.device_info.get_paths_to_platform_and_hwsku_dirs', MagicMock(return_value=("test_path", "")))  # noqa: E501
    @patch('sonic_platform_base.sonic_storage.ssd', MagicMock(side_effect=ImportError()))  # noqa: E501
    @patch('os.geteuid', MagicMock(return_value=0))
    @patch('builtins.print')
    def test_sonic_ssd_path(self, mock_print):

        ssdutil.ssdutil()
        assert mock_print.call_count == 6
