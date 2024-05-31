import sys
import os
from unittest.mock import patch, MagicMock
sys.modules['sonic_platform'] = MagicMock()
sys.modules['argparse'] = MagicMock()

import ssdutil.main as ssdutil  # noqa: E402

# Add mocked_libs path so that the file under test can load mocked modules from there
tests_path = os.path.dirname(os.path.abspath(__file__))
mocked_libs_path = os.path.join(tests_path, "mocked_libs")
sys.path.insert(0, mocked_libs_path)

from .mocked_libs import sonic_platform_base #.sonic_platform_base.sonic_ssd import ssd_generic
#from .mocked_libs  #.sonic_platform_base.sonic_storage import ssd

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

    @patch('sonic_py_common.device_info.get_paths_to_platform_and_hwsku_dirs',
           MagicMock(return_value=("test_path", "")))
    @patch('os.geteuid', MagicMock(return_value=0))
    @patch('sonic_platform_base.sonic_ssd.ssd_generic.SsdUtil', MagicMock(return_value=Ssd()))
    @patch('sonic_platform_base.sonic_storage.ssd.SsdUtil', MagicMock(return_value=Ssd()))
    def test_happy_path(self):

        ssdutil.ssdutil()
