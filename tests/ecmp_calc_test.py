import os
import subprocess
import show.main as show
from unittest import mock
from click.testing import CliRunner

FILE_FOUND_RC = 0
FILE_NOT_FOUND_RC= 1
CONTAINER_NAME = 'syncd'
ECMP_CALC = '/usr/bin/ecmp_calc.py'
SHOW_CMD_ARGS = '--ingress-port Ethernet0 --packet /packet.json --vrf Vrf_red --debug'

class TestShowIpEcmpEgressPort(object):
    @classmethod
    def setup_class(cls):
        os.environ["UTILITIES_UNIT_TESTING"] = "1"

    @mock.patch('subprocess.run', mock.MagicMock(return_value = subprocess.CompletedProcess('', FILE_FOUND_RC, None, None)))
    def test_valid_flow(self):
        with mock.patch("show.main.run_command", mock.MagicMock()) as mock_run_command:
             runner = CliRunner()
             result = runner.invoke(show.cli.commands["ip"].commands["ecmp-egress-port"], SHOW_CMD_ARGS.split())
             assert result.exit_code == 0
             assert mock_run_command.call_count == 2
    
             ecmp_calc_cmd = "docker exec {} {} --packet packet.json --interface Ethernet0 --vrf Vrf_red --debug".format(CONTAINER_NAME, ECMP_CALC)
             mock_run_command.assert_called_with(ecmp_calc_cmd, display_cmd=True)

    @mock.patch('subprocess.run', mock.MagicMock(return_value = subprocess.CompletedProcess('', FILE_NOT_FOUND_RC, None, None)))
    def test_binary_not_found(self):
        with mock.patch("show.main.run_command", mock.MagicMock()) as mock_run_command:
            runner = CliRunner()
            result = runner.invoke(show.cli.commands["ip"].commands["ecmp-egress-port"], SHOW_CMD_ARGS.split())
            assert result.exit_code == 0
            assert mock_run_command.call_count == 0

    @classmethod
    def teardown_class(cls):
        os.environ["UTILITIES_UNIT_TESTING"] = "0"
