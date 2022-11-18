import os
import sys
from unittest import mock
from unittest.mock import patch, call

test_path = os.path.dirname(os.path.abspath(__file__))
modules_path = os.path.dirname(test_path)
sys.path.insert(0, modules_path)
sys.modules['sonic_platform.platform'] = mock.MagicMock()
import fwutil.lib as fwutil_lib

def test_get_current_image():
    expected_call = call(["sonic-installer", "list"], ["grep", 'Current: '], ["cut", "-f2", "-d", ' '])
    with patch('fwutil.lib.check_output_pipe') as mock_check_output_pipe:
        squashfs = fwutil_lib.SquashFs()
        squashfs.get_current_image()
        assert mock_check_output_pipe.call_args == expected_call

def test_get_next_image():
    expected_call = call(["sonic-installer", "list"], ["grep", 'Next: '], ["cut", "-f2", "-d", ' '])
    with patch('fwutil.lib.check_output_pipe') as mock_check_output_pipe:
        squashfs = fwutil_lib.SquashFs()
        squashfs.get_next_image()
        assert mock_check_output_pipe.call_args == expected_call
