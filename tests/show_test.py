import os
import sys
import pytest
import show.main as show
from click.testing import CliRunner
from unittest import mock
from unittest.mock import call, MagicMock, patch
from datetime import datetime

EXPECTED_BASE_COMMAND = 'sudo '

test_path = os.path.dirname(os.path.abspath(__file__))
modules_path = os.path.dirname(test_path)
sys.path.insert(0, test_path)
sys.path.insert(0, modules_path)


class TestShowRunAllCommands(object):
    @classmethod
    def setup_class(cls):
        print("SETUP")
        os.environ["UTILITIES_UNIT_TESTING"] = "1"

    def test_show_runningconfiguration_all_json_loads_failure(self):
        def get_cmd_output_side_effect(*args, **kwargs):
            return "", 0
        with mock.patch('show.main.get_cmd_output',
                mock.MagicMock(side_effect=get_cmd_output_side_effect)) as mock_get_cmd_output:
            result = CliRunner().invoke(show.cli.commands['runningconfiguration'].commands['all'], [])
        assert result.exit_code != 0

    def test_show_runningconfiguration_all_get_cmd_ouput_failure(self):
        def get_cmd_output_side_effect(*args, **kwargs):
            return "{}", 2
        with mock.patch('show.main.get_cmd_output',
                mock.MagicMock(side_effect=get_cmd_output_side_effect)) as mock_get_cmd_output:
            result = CliRunner().invoke(show.cli.commands['runningconfiguration'].commands['all'], [])
        assert result.exit_code != 0

    def test_show_runningconfiguration_all(self):
        def get_cmd_output_side_effect(*args, **kwargs):
            return "{}", 0
        with mock.patch('show.main.get_cmd_output',
                mock.MagicMock(side_effect=get_cmd_output_side_effect)) as mock_get_cmd_output:
            result = CliRunner().invoke(show.cli.commands['runningconfiguration'].commands['all'], [])
        assert mock_get_cmd_output.call_count == 2
        assert mock_get_cmd_output.call_args_list == [
            call(['sonic-cfggen', '-d', '--print-data']),
            call(['rvtysh', '-c', 'show running-config'])]

    @classmethod
    def teardown_class(cls):
        print("TEARDOWN")
        os.environ["PATH"] = os.pathsep.join(os.environ["PATH"].split(os.pathsep)[:-1])
        os.environ["UTILITIES_UNIT_TESTING"] = "0"

@patch('show.main.run_command')
@pytest.mark.parametrize(
        "cli_arguments,expected",
        [
            ([], 'cat /var/log/syslog'),
            (['xcvrd'], "cat /var/log/syslog | grep 'xcvrd'"),
            (['-l', '10'], 'cat /var/log/syslog | tail -10'),
            (['-f'], 'tail -F /var/log/syslog'),
        ]
)
def test_show_logging_default(run_command, cli_arguments, expected):
    runner = CliRunner()
    result = runner.invoke(show.cli.commands["logging"], cli_arguments)
    run_command.assert_called_with(EXPECTED_BASE_COMMAND + expected, display_cmd=False)

@patch('show.main.run_command')
@patch('os.path.isfile', MagicMock(return_value=True))
@pytest.mark.parametrize(
        "cli_arguments,expected",
        [
            ([], 'cat /var/log/syslog.1 /var/log/syslog'),
            (['xcvrd'], "cat /var/log/syslog.1 /var/log/syslog | grep 'xcvrd'"),
            (['-l', '10'], 'cat /var/log/syslog.1 /var/log/syslog | tail -10'),
            (['-f'], 'tail -F /var/log/syslog'),
        ]
)
def test_show_logging_syslog_1(run_command, cli_arguments, expected):
    runner = CliRunner()
    result = runner.invoke(show.cli.commands["logging"], cli_arguments)
    run_command.assert_called_with(EXPECTED_BASE_COMMAND + expected, display_cmd=False)

@patch('show.main.run_command')
@patch('os.path.exists', MagicMock(return_value=True))
@pytest.mark.parametrize(
        "cli_arguments,expected",
        [
            ([], 'cat /var/log.tmpfs/syslog'),
            (['xcvrd'], "cat /var/log.tmpfs/syslog | grep 'xcvrd'"),
            (['-l', '10'], 'cat /var/log.tmpfs/syslog | tail -10'),
            (['-f'], 'tail -F /var/log.tmpfs/syslog'),
        ]
)
def test_show_logging_tmpfs(run_command, cli_arguments, expected):
    runner = CliRunner()
    result = runner.invoke(show.cli.commands["logging"], cli_arguments)
    run_command.assert_called_with(EXPECTED_BASE_COMMAND + expected, display_cmd=False)

@patch('show.main.run_command')
@patch('os.path.isfile', MagicMock(return_value=True))
@patch('os.path.exists', MagicMock(return_value=True))
@pytest.mark.parametrize(
        "cli_arguments,expected",
        [
            ([], 'cat /var/log.tmpfs/syslog.1 /var/log.tmpfs/syslog'),
            (['xcvrd'], "cat /var/log.tmpfs/syslog.1 /var/log.tmpfs/syslog | grep 'xcvrd'"),
            (['-l', '10'], 'cat /var/log.tmpfs/syslog.1 /var/log.tmpfs/syslog | tail -10'),
            (['-f'], 'tail -F /var/log.tmpfs/syslog'),
        ]
)
def test_show_logging_tmpfs_syslog_1(run_command, cli_arguments, expected):
    runner = CliRunner()
    result = runner.invoke(show.cli.commands["logging"], cli_arguments)
    run_command.assert_called_with(EXPECTED_BASE_COMMAND + expected, display_cmd=False)

def side_effect_subprocess_popen(*args, **kwargs):
    class TestResult:
        stdout
    if args[0] == "uptime":
        return subprocess.Popen(["/bin/bash", "-c", "echo  05:58:07 up 25 days"], shell=True, text=True, stdout=subprocess.PIPE)
    elif args[0].startswith("sudo docker images"):
        return subprocess.Popen(["/bin/bash", "-c", "echo  REPOSITORY	TAG"], shell=True, text=True, stdout=subprocess.PIPE)

@patch('device_info.get_sonic_version_info', MagicMock(return_value={
        "build_version": "release-1.1-7d94c0c28",
        "sonic_os_version": "11",
        "debian_version": "11.6",
        "kernel_version": "5.10",
        "commit_id": "7d94c0c28",
        "build_date": "Wed Feb 15 06:17:08 UTC 2023",
        "built_by": "AzDevOps"}))
@patch('device_info.get_platform_info', MagicMock(return_value={
        "platform": "x86_64-kvm_x86_64-r0",
        "hwsku": "Force10-S6000",
        "asic_type": "vs",
        "asic_count": 1}))
@patch('platform.get_chassis_info', MagicMock(return_value={
        "serial": "N/A",
        "model": "N/A",
        "revision", "N/A"}))
@patch('datetime.now', MagicMock(return_value=datetime(2023, 4, 11, 6, 9, 17, 0)))
@patch('subprocess.Popen', MagicMock(side_effect=side_effect_subprocess_popen))
@pytest.mark.parametrize(
        "cli_arguments,expected",
        [
            ([], '''SONiC Software Version: SONiC.release-1.1-7d94c0c28
SONiC OS Version: 11
Distribution: Debian 11.6
Kernel: 5.10
Build commit: 7d94c0c28
Build date: Wed Feb 15 06:17:08 UTC 2023
Built by: AzDevOps

Platform: x86_64-kvm_x86_64-r0
HwSKU: Force10-S6000
ASIC: vs
ASIC Count: 1
Serial Number: N/A
Model Number: N/A
Hardware Revision: N/A
Uptime: 05:58:07 up 25 days
Date: Tue 11 Apr 2023 06:09:17

Docker images:
REPOSITORY	TAG'''),
        ]
)
def test_show_version(run_command, cli_arguments, expected):
    runner = CliRunner()
    result = runner.invoke(show.cli.commands["version"], cli_arguments)
    run_command.assert_called_with(EXPECTED_BASE_COMMAND + expected, display_cmd=False)
