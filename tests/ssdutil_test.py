import os
import sys
import argparse
import pytest
from collections import namedtuple
from unittest.mock import patch, MagicMock
import sonic_platform_base  # noqa: F401

tests_path = os.path.dirname(os.path.abspath(__file__))

# Add mocked_libs path so that the file under test can load mocked modules from there
mocked_libs_path = os.path.join(tests_path, "mocked_libs")
sys.path.insert(0, mocked_libs_path)

from .mocked_libs import psutil
from .mocked_libs.blkinfo import BlkDiskInfo

sys.modules['os.stat'] = MagicMock()
sys.modules['os.major'] = MagicMock(return_value=8)
sys.modules['sonic_platform'] = MagicMock()
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

    def test_get_default_disk(self):

        class mock_os:
            def __init__(self):
                pass

            def major(self, arg):
                return 8

            class stat():
                def __init__(self):
                    self.st_rdev = 2049

        (default_device , disk_type) = ssdutil.get_default_disk()

        assert default_device == "/dev/sda"
        assert disk_type == 'usb'


    def test_is_number_valueerror(self):
        outcome = ssdutil.is_number("nope")
        assert outcome == False


    @patch('sonic_py_common.device_info.get_paths_to_platform_and_hwsku_dirs', MagicMock(return_value=("test_path", "")))  # noqa: E501
    @patch('os.geteuid', MagicMock(return_value=0))
    def test_sonic_storage_path(self):

        with patch('argparse.ArgumentParser.parse_args', MagicMock()) as mock_args:  # noqa: E501
            sys.modules['sonic_platform_base.sonic_storage.ssd'] = MagicMock(return_value=Ssd())  # noqa: E501
            mock_args.return_value = argparse.Namespace(device='/dev/sda', verbose=True, vendor=True)  # noqa: E501
            ssdutil.ssdutil()
