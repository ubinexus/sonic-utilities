import os
import sys
import textwrap
import json
from unittest.mock import patch, mock_open

import pytest
from click.testing import CliRunner
import utilities_common.cli as cli

import show.main as show
import config.main as config
import show.plugins.barefoot as bfshow
import config.plugins.barefoot as bfconfig

@pytest.fixture(scope='class')
def config_env():
    os.environ["UTILITIES_UNIT_TESTING"] = "1"
    yield
    os.environ["UTILITIES_UNIT_TESTING"] = "0"

class TestStdout:
    stdout = ""

class TestReturncode:
    returncode = False

class TestShowPlatformBarefoot(object):

    def test_config_barefoot(self):
        runner = CliRunner()
        expected_output = ""
        result = CliRunner().invoke(show.cli.commands["platform"], ["barefoot"])
        assert result.output == expected_output

    def test_config_profile(self):
        runner = CliRunner()
        expected_output = "Swss service will be restarted, continue? [y/N]: \nAborted!\n"
        result = runner.invoke(bfconfig.barefoot.commands['profile'], ['x1'])
        print("result.exit_code:", result.exit_code)
        print("result.output:", result.output)
        assert result.output == expected_output

    def test_check_profile_naming_tf3(self):
        with patch('config.plugins.barefoot.subprocess.run', return_value=0):
            result = bfconfig.check_profile_naming_tf3("y2", "tofino3")
            assert result == 0

    def test_check_profile_naming_tf2(self):
        with patch('config.plugins.barefoot.subprocess.run', return_value=0):
            result = bfconfig.check_profile_naming_tf2("y2")
            assert result == 0

    def test_check_profile_naming_tf3_t(self):
        with patch('config.plugins.barefoot.subprocess.run', return_value=1):
            result = bfconfig.check_profile_naming_tf3("y2", "tofino3")
            assert result == 1

    def test_check_profile_naming_tf2_t(self):
        with patch('config.plugins.barefoot.subprocess.run', return_value=1):
            result = bfconfig.check_profile_naming_tf2("y2")
            assert result == 1

    def test_check_profile_exist1(self):
        completed_process = TestReturncode()
        completed_process.returncode = 0
        with patch('config.plugins.barefoot.check_profile_naming_tf3', return_value=completed_process):
            result = bfconfig.check_profile_exist("x1", "tofino")
            assert result == 0

    def test_check_profile_exist2(self):
        completed_process1  = TestReturncode() 
        completed_process2  = TestReturncode()
        completed_process1.returncode = 1
        completed_process2.returncode = 0
        with patch('config.plugins.barefoot.check_profile_naming_tf3', return_value=completed_process1):
            with patch('config.plugins.barefoot.check_profile_naming_tf2', return_value=completed_process2):
                result = bfconfig.check_profile_exist("x1", "tofino")
                assert result == 1

    def test_show_profile(self):
        runner = CliRunner()
        expected_output = "Current profile: default\n"
        result = runner.invoke(bfshow.barefoot.commands['profile'], [])
        print("result.exit_code:", result.exit_code)
        print("result.output:", result.output)
        assert result.output == expected_output

    def test_get_chip_family1(self):
        with patch('show.plugins.barefoot.device_info.get_path_to_hwsku_dir', return_value=""):
            chip_family = json.dumps({"chip_list": [{"instance": 0,"chip_family": "tofino3"}]})
            with patch('show.plugins.barefoot.open', mock_open(read_data=chip_family)):
                result = bfshow.get_chip_family()
                assert result == "tofino3"

    def test_get_chip_family2(self):
        with patch('config.plugins.barefoot.device_info.get_path_to_hwsku_dir', return_value=""):
            chip_family = json.dumps({"chip_list": [{"instance": 0,"chip_family": "tofino3"}]})
            with patch('show.plugins.barefoot.open', mock_open(read_data=chip_family)):
                result = bfconfig.get_chip_family()
                assert result == "tofino3"

    def test_show_profile_default(self):
        runner = CliRunner()
        expected_output = "Current profile: default\n"
        with patch("show.plugins.barefoot.check_profile", return_value=1):
            print(show.plugins.barefoot.check_profile())
            result = runner.invoke(bfshow.barefoot.commands['profile'], [])
            print("result.exit_code:", result.exit_code)
            print("result.output:", result.output)
            assert result.output == expected_output

    def test_check_profile1(self):
        ret = TestReturncode()
        ret.returncode = 1
        with patch('show.plugins.barefoot.subprocess.run', return_value=ret):
            result = bfshow.check_profile()
            print(result)
            assert result == True

    def test_check_profile2(self):
        ret = TestReturncode()
        ret.returncode = 1
        with patch('config.plugins.barefoot.subprocess.run', return_value=ret):
            result = bfconfig.check_profile()
            print(result)
            assert result == True

    def test_check_profile3(self):
        ret = TestReturncode()
        ret.returncode = 0
        with patch('show.plugins.barefoot.subprocess.run', return_value=ret):
            result = bfshow.check_profile()
            print(result)
            assert result == False

    def test_check_profile4(self):
        ret = TestReturncode()
        ret.returncode = 0
        with patch('config.plugins.barefoot.subprocess.run', return_value=ret):
            result = bfconfig.check_profile()
            print(result)
            assert result == False

    def test_check_supported_profile1(self):
        result = bfconfig.check_supported_profile("x1", "tofino")
        print(result)
        assert result == True
    
    def test_check_supported_profile2(self):
        result = bfconfig.check_supported_profile("y2", "tofino2")
        print(result)
        assert result == True

    def test_check_supported_profile3(self):
        result = bfconfig.check_supported_profile("x1", "tofino2")
        print(result)
        assert result == False

    def test_check_supported_profile4(self):
        result = bfconfig.check_supported_profile("y2", "tofino")
        print(result)
        assert result == False

    def test_get_current_profile(self):
        with patch('show.plugins.barefoot.subprocess.run', return_value="y2"):
            result = bfshow.get_current_profile()
            assert result == "y2"
    
    def test_get_profile_format(self):
        with patch('show.plugins.barefoot.subprocess') as subprocess:
            subprocess.return_value = 0
            result = bfshow.get_profile_format("tofino")
            assert result == "_profile"

    def test_get_available_profiles(self):
        with patch('show.plugins.barefoot.subprocess.run', return_value="x2"):
            result = bfshow.get_available_profiles("install_x1_tofino")
            assert result == "x2"

    def test_show_profile(self):
        runner = CliRunner()
        expected_output = """\
Current profile: y2
Available profile(s):
x1
x2
y2
y3
"""
        with patch("show.plugins.barefoot.check_profile", return_value=False):
            with patch("show.plugins.barefoot.get_chip_family", return_value="tofino"):
                current_profile = TestStdout()
                current_profile.stdout = "y2\n"
                with patch("show.plugins.barefoot.get_current_profile", return_value=current_profile):
                    with patch("show.plugins.barefoot.get_profile_format", return_value="_profile"):
                        available_profile = TestStdout()
                        available_profile.stdout = "x1\nx2\ny2\ny3\n"
                        with patch("show.plugins.barefoot.get_available_profiles", return_value=available_profile):
                            result = runner.invoke(bfshow.barefoot.commands['profile'], [])
                            print("result.exit_code:", result.exit_code)
                            print("result.output:", result.output)
                            assert result.output == expected_output
