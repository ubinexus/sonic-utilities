import os
import sys
import pytest
import show.main as show
from click.testing import CliRunner
from unittest import mock
from utilities_common import constants
from unittest.mock import call, MagicMock, patch

EXPECTED_BASE_COMMAND = 'sudo '
EXPECTED_BASE_COMMAND_LIST = ['sudo']

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
        "cli_arguments0,expected0",
        [
            ([], 'cat /var/log/syslog'),
            (['xcvrd'], "cat /var/log/syslog | grep 'xcvrd'"),
            (['-l', '10'], 'cat /var/log/syslog | tail -10'),
        ]
)
@pytest.mark.parametrize(
        "cli_arguments1,expected1",
        [
            (['-f'], ['tail', '-F', '/var/log/syslog']),
        ]
)
def test_show_logging_default(run_command, cli_arguments0, expected0, cli_arguments1, expected1):
    runner = CliRunner()
    runner.invoke(show.cli.commands["logging"], cli_arguments0)
    run_command.assert_called_with(EXPECTED_BASE_COMMAND + expected0, display_cmd=False, shell=True)
    runner.invoke(show.cli.commands["logging"], cli_arguments1)
    run_command.assert_called_with(EXPECTED_BASE_COMMAND_LIST + expected1, display_cmd=False)

@patch('show.main.run_command')
@patch('os.path.isfile', MagicMock(return_value=True))
@pytest.mark.parametrize(
        "cli_arguments0,expected0",
        [
            ([], 'cat /var/log/syslog.1 /var/log/syslog'),
            (['xcvrd'], "cat /var/log/syslog.1 /var/log/syslog | grep 'xcvrd'"),
            (['-l', '10'], 'cat /var/log/syslog.1 /var/log/syslog | tail -10'),
        ]
)
@pytest.mark.parametrize(
        "cli_arguments1,expected1",
        [
            (['-f'], ['tail', '-F', '/var/log/syslog']),
        ]
)
def test_show_logging_syslog_1(run_command, cli_arguments0, expected0, cli_arguments1, expected1):
    runner = CliRunner()
    runner.invoke(show.cli.commands["logging"], cli_arguments0)
    run_command.assert_called_with(EXPECTED_BASE_COMMAND + expected0, display_cmd=False, shell=True)
    runner.invoke(show.cli.commands["logging"], cli_arguments1)
    run_command.assert_called_with(EXPECTED_BASE_COMMAND_LIST + expected1, display_cmd=False)

@patch('show.main.run_command')
@patch('os.path.exists', MagicMock(return_value=True))
@pytest.mark.parametrize(
        "cli_arguments0,expected0",
        [
            ([], 'cat /var/log.tmpfs/syslog'),
            (['xcvrd'], "cat /var/log.tmpfs/syslog | grep 'xcvrd'"),
            (['-l', '10'], 'cat /var/log.tmpfs/syslog | tail -10'),
        ]
)
@pytest.mark.parametrize(
        "cli_arguments1,expected1",
        [
            (['-f'], ['tail', '-F', '/var/log.tmpfs/syslog']),
        ]
)
def test_show_logging_tmpfs(run_command, cli_arguments0, expected0, cli_arguments1, expected1):
    runner = CliRunner()
    runner.invoke(show.cli.commands["logging"], cli_arguments0)
    run_command.assert_called_with(EXPECTED_BASE_COMMAND + expected0, display_cmd=False, shell=True)
    runner.invoke(show.cli.commands["logging"], cli_arguments1)
    run_command.assert_called_with(EXPECTED_BASE_COMMAND_LIST + expected1, display_cmd=False)

@patch('show.main.run_command')
@patch('os.path.isfile', MagicMock(return_value=True))
@patch('os.path.exists', MagicMock(return_value=True))
@pytest.mark.parametrize(
        "cli_arguments0,expected0",
        [
            ([], 'cat /var/log.tmpfs/syslog.1 /var/log.tmpfs/syslog'),
            (['xcvrd'], "cat /var/log.tmpfs/syslog.1 /var/log.tmpfs/syslog | grep 'xcvrd'"),
            (['-l', '10'], 'cat /var/log.tmpfs/syslog.1 /var/log.tmpfs/syslog | tail -10'),
        ]
)
@pytest.mark.parametrize(
        "cli_arguments1,expected1",
        [
            (['-f'], ['tail', '-F', '/var/log.tmpfs/syslog']),
        ]
)
def test_show_logging_tmpfs_syslog_1(run_command, cli_arguments0, expected0, cli_arguments1, expected1):
    runner = CliRunner()
    runner.invoke(show.cli.commands["logging"], cli_arguments0)
    run_command.assert_called_with(EXPECTED_BASE_COMMAND + expected0, display_cmd=False, shell=True)
    runner.invoke(show.cli.commands["logging"], cli_arguments1)
    run_command.assert_called_with(EXPECTED_BASE_COMMAND_LIST + expected1, display_cmd=False)

def side_effect_subprocess_popen(*args, **kwargs):
    mock = MagicMock()
    if ' '.join(args[0]) == "uptime":
        mock.stdout.read.return_value = "05:58:07 up 25 days"
    elif ' '.join(args[0]).startswith("sudo docker images"):
        mock.stdout.read.return_value = "REPOSITORY   TAG"
    return mock

@patch('sonic_py_common.device_info.get_sonic_version_info', MagicMock(return_value={
        "build_version": "release-1.1-7d94c0c28",
        "sonic_os_version": "11",
        "debian_version": "11.6",
        "kernel_version": "5.10",
        "commit_id": "7d94c0c28",
        "build_date": "Wed Feb 15 06:17:08 UTC 2023",
        "built_by": "AzDevOps"}))
@patch('sonic_py_common.device_info.get_platform_info', MagicMock(return_value={
        "platform": "x86_64-kvm_x86_64-r0",
        "hwsku": "Force10-S6000",
        "asic_type": "vs",
        "asic_count": 1}))
@patch('sonic_py_common.device_info.get_chassis_info', MagicMock(return_value={
        "serial": "N/A",
        "model": "N/A",
        "revision": "N/A"}))
@patch('subprocess.Popen', MagicMock(side_effect=side_effect_subprocess_popen))
def test_show_version():
    runner = CliRunner()
    result = runner.invoke(show.cli.commands["version"])
    assert "SONiC OS Version: 11" in result.output


class TestShowQuagga(object):
    def setup(self):
        print('SETUP')

    @patch('show.main.run_command')
    @patch('show.main.get_routing_stack', MagicMock(return_value='quagga'))
    def test_show_ip_bgp(self, mock_run_command):
        from show.bgp_quagga_v4 import bgp
        runner = CliRunner()

        result = runner.invoke(show.cli.commands["ip"].commands['bgp'].commands['summary'])
        assert result.exit_code == 0
        mock_run_command.assert_called_with(['sudo', constants.RVTYSH_COMMAND, '-c', "show ip bgp summary"], return_cmd=True)

        result = runner.invoke(show.cli.commands["ip"].commands['bgp'].commands['neighbors'])
        assert result.exit_code == 0
        mock_run_command.assert_called_with(['sudo', constants.RVTYSH_COMMAND, '-c', "show ip bgp neighbor"])

        result = runner.invoke(show.cli.commands["ip"].commands['bgp'].commands['neighbors'], ['0.0.0.0', 'routes'])
        assert result.exit_code == 0
        mock_run_command.assert_called_with(['sudo', constants.RVTYSH_COMMAND, '-c', "show ip bgp neighbor 0.0.0.0 routes"])

    @patch('show.main.run_command')
    @patch('show.main.get_routing_stack', MagicMock(return_value='quagga'))
    def test_show_ipv6_bgp(self, mock_run_command):
        from show.bgp_quagga_v6 import bgp
        runner = CliRunner()

        result = runner.invoke(show.cli.commands["ipv6"].commands['bgp'].commands['summary'])
        assert result.exit_code == 0
        mock_run_command.assert_called_with(['sudo', constants.RVTYSH_COMMAND, '-c', "show ipv6 bgp summary"], return_cmd=True)

        result = runner.invoke(show.cli.commands["ipv6"].commands['bgp'].commands['neighbors'], ['0.0.0.0', 'routes'])
        assert result.exit_code == 0
        mock_run_command.assert_called_with(['sudo', constants.RVTYSH_COMMAND, '-c', "show ipv6 bgp neighbor 0.0.0.0 routes"])

    def teardown(self):
        print('TEAR DOWN')


class TestShow(object):
    def setup(self):
        print('SETUP')

    @patch('show.main.run_command')
    def test_show_arp(self, mock_run_command):
        runner = CliRunner()
        result = runner.invoke(show.cli.commands["arp"], ['0.0.0.0', '-if', 'Ethernet0', '--verbose'])
        assert result.exit_code == 0
        mock_run_command.assert_called_with(['nbrshow', '-4', '-ip', '0.0.0.0', '-if', 'Ethernet0'], display_cmd=True)

    @patch('show.main.run_command')
    def test_show_ndp(self, mock_run_command):
        runner = CliRunner()
        result = runner.invoke(show.cli.commands["ndp"], ['0.0.0.0', '-if', 'Ethernet0', '--verbose'])
        assert result.exit_code == 0
        mock_run_command.assert_called_with(['nbrshow', '-6', '-ip', '0.0.0.0', '-if', 'Ethernet0'], display_cmd=True)

    @patch('show.main.run_command')
    @patch('show.main.is_mgmt_vrf_enabled', MagicMock(return_value=True))
    def test_show_mgmt_vrf_routes(self, mock_run_command):
        runner = CliRunner()
        result = runner.invoke(show.cli.commands["mgmt-vrf"], ['routes'])
        assert result.exit_code == 0
        mock_run_command.assert_called_with(['ip', 'route', 'show', 'table', '5000'])

    @patch('show.main.run_command')
    @patch('show.main.is_mgmt_vrf_enabled', MagicMock(return_value=True))
    def test_show_mgmt_vrf(self, mock_run_command):
        runner = CliRunner()
        result = runner.invoke(show.cli.commands["mgmt-vrf"])
        assert result.exit_code == 0
        assert mock_run_command.call_args_list == [
            call(['ip', '-d', 'link', 'show', 'mgmt']),
            call(['ip', 'link', 'show', 'vrf', 'mgmt'])
        ]

    @patch('show.main.run_command')
    def test_show_pfc_priority(self, mock_run_command):
        runner = CliRunner()
        result = runner.invoke(show.cli.commands["pfc"].commands['priority'], ['Ethernet0'])
        assert result.exit_code == 0
        mock_run_command.assert_called_with(['pfc', 'show', 'priority', 'Ethernet0'])

    @patch('show.main.run_command')
    def test_show_pfc_asymmetric(self, mock_run_command):
        runner = CliRunner()
        result = runner.invoke(show.cli.commands["pfc"].commands['asymmetric'], ['Ethernet0'])
        assert result.exit_code == 0
        mock_run_command.assert_called_with(['pfc', 'show', 'asymmetric', 'Ethernet0'])

    @patch('show.main.run_command')
    def test_show_pfcwd_config(self, mock_run_command):
        runner = CliRunner()
        result = runner.invoke(show.cli.commands["pfcwd"].commands['config'], ['--verbose'])
        assert result.exit_code == 0
        mock_run_command.assert_called_with(['pfcwd', 'show', 'config', '-d', 'all'], display_cmd=True)

    @patch('show.main.run_command')
    def test_show_pfcwd_stats(self, mock_run_command):
        runner = CliRunner()
        result = runner.invoke(show.cli.commands["pfcwd"].commands['stats'], ['--verbose'])
        assert result.exit_code == 0
        mock_run_command.assert_called_with(['pfcwd', 'show', 'stats', '-d', 'all'], display_cmd=True)

    @patch('show.main.run_command')
    def test_show_watermark_telemetry_interval(self, mock_run_command):
        runner = CliRunner()
        result = runner.invoke(show.cli.commands["watermark"].commands['telemetry'].commands['interval'])
        assert result.exit_code == 0
        mock_run_command.assert_called_with(['watermarkcfg', '--show-interval'])

    @patch('show.main.run_command')
    def test_show_route_map(self, mock_run_command):
        runner = CliRunner()
        result = runner.invoke(show.cli.commands["route-map"], ['BGP', '--verbose'])
        assert result.exit_code == 0
        mock_run_command.assert_called_with(['sudo', constants.RVTYSH_COMMAND, '-c', 'show route-map BGP'], display_cmd=True)

    @patch('show.main.run_command')
    def test_show_ip_prefix_list(self, mock_run_command):
        runner = CliRunner()
        result = runner.invoke(show.cli.commands['ip'].commands["prefix-list"], ['0.0.0.0', '--verbose'])
        assert result.exit_code == 0
        mock_run_command.assert_called_with(['sudo', constants.RVTYSH_COMMAND, '-c', 'show ip prefix-list 0.0.0.0'], display_cmd=True)

    @patch('show.main.run_command')
    def test_show_ip_protocol(self, mock_run_command):
        runner = CliRunner()
        result = runner.invoke(show.cli.commands['ip'].commands["protocol"], ['--verbose'])
        assert result.exit_code == 0
        mock_run_command.assert_called_with(['sudo', constants.RVTYSH_COMMAND, '-c', 'show ip protocol'], display_cmd=True)

    @patch('show.main.run_command')
    def test_show_ip_fib(self, mock_run_command):
        runner = CliRunner()
        result = runner.invoke(show.cli.commands['ip'].commands["fib"], ['0.0.0.0', '--verbose'])
        assert result.exit_code == 0
        mock_run_command.assert_called_with(['fibshow', '-4', '-ip', '0.0.0.0'], display_cmd=True)

    @patch('show.main.run_command')
    def test_show_ipv6_prefix_list(self, mock_run_command):
        runner = CliRunner()
        result = runner.invoke(show.cli.commands['ipv6'].commands["prefix-list"], ['0.0.0.0', '--verbose'])
        assert result.exit_code == 0
        mock_run_command.assert_called_with(['sudo', constants.RVTYSH_COMMAND, '-c', 'show ipv6 prefix-list 0.0.0.0'], display_cmd=True)

    @patch('show.main.run_command')
    def test_show_ipv6_protocol(self, mock_run_command):
        runner = CliRunner()
        result = runner.invoke(show.cli.commands['ipv6'].commands["protocol"], ['--verbose'])
        assert result.exit_code == 0
        mock_run_command.assert_called_with(['sudo', constants.RVTYSH_COMMAND, '-c', 'show ipv6 protocol'], display_cmd=True)

    @patch('show.main.run_command')
    def test_show_ipv6_fib(self, mock_run_command):
        runner = CliRunner()
        result = runner.invoke(show.cli.commands['ipv6'].commands["fib"], ['0.0.0.0', '--verbose'])
        assert result.exit_code == 0
        mock_run_command.assert_called_with(['fibshow', '-6', '-ip', '0.0.0.0'], display_cmd=True)

    @patch('show.main.run_command')
    def test_show_ipv6_fib(self, mock_run_command):
        runner = CliRunner()
        result = runner.invoke(show.cli.commands['ipv6'].commands["fib"], ['0.0.0.0', '--verbose'])
        assert result.exit_code == 0
        mock_run_command.assert_called_with(['fibshow', '-6', '-ip', '0.0.0.0'], display_cmd=True)

    @patch('show.main.run_command')
    def test_show_lldp_neighbors(self, mock_run_command):
        runner = CliRunner()
        result = runner.invoke(show.cli.commands['lldp'].commands["neighbors"], ['Ethernet0', '--verbose'])
        assert result.exit_code == 0
        mock_run_command.assert_called_with(['sudo', 'lldpshow', '-d', '-p' ,'Ethernet0'], display_cmd=True)

    @patch('show.main.run_command')
    def test_show_lldp_table(self, mock_run_command):
        runner = CliRunner()
        result = runner.invoke(show.cli.commands['lldp'].commands["table"], ['--verbose'])
        assert result.exit_code == 0
        mock_run_command.assert_called_with(['sudo', 'lldpshow'], display_cmd=True)

    def test_show_logging_invalid_process(self):
        runner = CliRunner()
        result = runner.invoke(show.cli.commands['logging'], ['systemd | grep ERR'])
        assert result.output == 'Process contains only number, alphabet, and whitespace.\n'

    @patch('show.main.run_command')
    def test_show_environment(self, mock_run_command):
        runner = CliRunner()
        result = runner.invoke(show.cli.commands['environment'], ['--verbose'])
        assert result.exit_code == 0
        mock_run_command.assert_called_with(['sudo', 'sensors'], display_cmd=True)

    @patch('show.main.run_command')
    def test_show_users(self, mock_run_command):
        runner = CliRunner()
        result = runner.invoke(show.cli.commands['users'], ['--verbose'])
        assert result.exit_code == 0
        mock_run_command.assert_called_with(['who'], display_cmd=True)

    @patch('show.main.run_command')
    def test_show_users(self, mock_run_command):
        runner = CliRunner()
        result = runner.invoke(show.cli.commands['users'], ['--verbose'])
        assert result.exit_code == 0
        mock_run_command.assert_called_with(['who'], display_cmd=True)

    @patch('show.main.run_command')
    def test_show_runningconfiguration_acl(self, mock_run_command):
        runner = CliRunner()
        result = runner.invoke(show.cli.commands['runningconfiguration'].commands['acl'], ['--verbose'])
        assert result.exit_code == 0
        mock_run_command.assert_called_with(['sonic-cfggen', '-d', '--var-json', 'ACL_RULE'], display_cmd=True)

    @patch('show.main.run_command')
    def test_show_runningconfiguration_ports(self, mock_run_command):
        runner = CliRunner()
        result = runner.invoke(show.cli.commands['runningconfiguration'].commands['ports'], ['Ethernet0', '--verbose'])
        assert result.exit_code == 0
        mock_run_command.assert_called_with(['sonic-cfggen', '-d', '--var-json', 'PORT', '--key', 'Ethernet0'], display_cmd=True)

    @patch('show.main.run_command')
    def test_show_runningconfiguration_interfaces(self, mock_run_command):
        runner = CliRunner()
        result = runner.invoke(show.cli.commands['runningconfiguration'].commands['interfaces'], ['Ethernet0', '--verbose'])
        assert result.exit_code == 0
        mock_run_command.assert_called_with(['sonic-cfggen', '-d', '--var-json', 'INTERFACE', '--key', 'Ethernet0'], display_cmd=True)

    @patch('show.main.run_command')
    def test_show_uptime(self, mock_run_command):
        runner = CliRunner()
        result = runner.invoke(show.cli.commands['uptime'], ['--verbose'])
        assert result.exit_code == 0
        mock_run_command.assert_called_with(['uptime', '-p'], display_cmd=True)

    @patch('show.main.run_command')
    def test_show_clock(self, mock_run_command):
        runner = CliRunner()
        result = runner.invoke(show.cli.commands['clock'], ['--verbose'])
        assert result.exit_code == 0
        mock_run_command.assert_called_with(['date'], display_cmd=True)

    @patch('show.main.run_command')
    def test_show_system_memory(self, mock_run_command):
        runner = CliRunner()
        result = runner.invoke(show.cli.commands['system-memory'], ['--verbose'])
        assert result.exit_code == 0
        mock_run_command.assert_called_with(['free', '-m'], display_cmd=True)

    @patch('show.main.run_command')
    def test_show_mirror_session(self, mock_run_command):
        runner = CliRunner()
        result = runner.invoke(show.cli.commands['mirror_session'], ['SPAN', '--verbose'])
        assert result.exit_code == 0
        mock_run_command.assert_called_with(['acl-loader', 'show', 'session', 'SPAN'], display_cmd=True)

    @patch('show.main.run_command')
    def test_show_policer(self, mock_run_command):
        runner = CliRunner()
        result = runner.invoke(show.cli.commands['policer'], ['policer0', '--verbose'])
        assert result.exit_code == 0
        mock_run_command.assert_called_with(['acl-loader', 'show', 'policer', 'policer0'], display_cmd=True)

    @patch('show.main.run_command')
    def test_show_mmu(self, mock_run_command):
        runner = CliRunner()
        result = runner.invoke(show.cli.commands['mmu'])
        assert result.exit_code == 0
        mock_run_command.assert_called_with(['mmuconfig', '-l'])

    @patch('show.main.run_command')
    def test_show_lines(self, mock_run_command):
        runner = CliRunner()
        result = runner.invoke(show.cli.commands['line'], ['--brief', '--verbose'])
        assert result.exit_code == 0
        mock_run_command.assert_called_with(['consutil', 'show', '-b'], display_cmd=True)

    @patch('show.main.run_command')
    @patch('os.path.isfile', MagicMock(return_value=True))
    def test_show_ztp(self, mock_run_command):
        runner = CliRunner()
        result = runner.invoke(show.cli.commands['ztp'], ['status', '--verbose'])
        assert result.exit_code == 0
        mock_run_command.assert_called_with(['ztp', 'status', '--verbose'], display_cmd=True)

    def teardown(self):
        print('TEAR DOWN')
