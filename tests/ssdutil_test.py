import sys
from unittest.mock import patch, MagicMock
import sonic_platform_base  # noqa: F401

sys.modules['sonic_platform'] = MagicMock()
sys.modules['argparse'] = MagicMock()
sys.modules['sonic_platform_base.sonic_ssd.ssd_generic'] = MagicMock()

import ssdutil.main as ssdutil  # noqa: E402


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
    def test_sonic_ssd_path(self, mock_print):

        sys.modules['sonic_platform_base.sonic_storage.ssd'] = MagicMock(side_effect=ImportError())  # noqa: E501
        ssdutil.ssdutil()
        assert mock_print.call_count == 6

    @patch('sonic_py_common.device_info.get_paths_to_platform_and_hwsku_dirs', MagicMock(return_value=("test_path", "")))  # noqa: E501
    @patch('os.geteuid', MagicMock(return_value=0))
    @patch('builtins.print')
    def test_sonic_storage_path(self, mock_print):

        mock_print.reset_mock()
        sys.modules['sonic_platform_base.sonic_storage.ssd'] = MagicMock(return_value=Ssd())  # noqa: E501
        ssdutil.ssdutil()
        assert mock_print.call_count == 6
