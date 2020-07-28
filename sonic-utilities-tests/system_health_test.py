#! /usr/bin/python -u

import sys
import os
import click
from click.testing import CliRunner
import mock_tables.dbconnector

test_path = os.path.dirname(os.path.abspath(__file__))
modules_path = os.path.dirname(test_path)
scripts_path = os.path.join(modules_path, "scripts")
sys.path.insert(0, modules_path)

class MockerConfig(object):
    ignore_devices = []
    ignore_services = []

class MockerManager(object):
    STATE_BOOTING = 'booting'
    STATE_RUNNING = 'running'
    counter = 0
    
    def __init__(self):
        self.config = MockerConfig()

    def check(self, chassis):
        if MockerManager.counter == 0:
            state = MockerManager.STATE_BOOTING
            stats = {}
        elif MockerManager.counter == 1:
            state = MockerManager.STATE_RUNNING
            stats = {'Services': {'neighsyncd': {'status': 'OK', 'message': '', 'type': 'Process'}, 'vrfmgrd': {'status': 'OK', 'message': '', 'type': 'Process'}, 'telemetry': {'status': 'Not OK', 'message': 'telemetry is not Running', 'type': 'Process'}, 'dialout_client': {'status': 'OK', 'message': '', 'type': 'Process'}, 'zebra': {'status': 'OK', 'message': '', 'type': 'Process'}, 'rsyslog': {'status': 'OK', 'message': '', 'type': 'Process'}, 'snmpd': {'status': 'OK', 'message': '', 'type': 'Process'}, 'redis_server': {'status': 'OK', 'message': '', 'type': 'Process'}, 'intfmgrd': {'status': 'OK', 'message': '', 'type': 'Process'}, 'orchagent': {'status': 'OK', 'message': '', 'type': 'Process'}, 'vxlanmgrd': {'status': 'OK', 'message': '', 'type': 'Process'}, 'lldpd_monitor': {'status': 'OK', 'message': '', 'type': 'Process'}, 'portsyncd': {'status': 'OK', 'message': '', 'type': 'Process'}, 'var-log': {'status': 'OK', 'message': '', 'type': 'Filesystem'}, 'lldpmgrd': {'status': 'OK', 'message': '', 'type': 'Process'}, 'syncd': {'status': 'OK', 'message': '', 'type': 'Process'}, 'sonic': {'status': 'OK', 'message': '', 'type': 'System'}, 'buffermgrd': {'status': 'OK', 'message': '', 'type': 'Process'}, 'portmgrd': {'status': 'OK', 'message': '', 'type': 'Process'}, 'staticd': {'status': 'OK', 'message': '', 'type': 'Process'}, 'bgpd': {'status': 'OK', 'message': '', 'type': 'Process'}, 'lldp_syncd': {'status': 'OK', 'message': '', 'type': 'Process'}, 'bgpcfgd': {'status': 'OK', 'message': '', 'type': 'Process'}, 'snmp_subagent': {'status': 'Not OK', 'message': 'snmp_subagent is not Running', 'type': 'Process'}, 'root-overlay': {'status': 'OK', 'message': '', 'type': 'Filesystem'}, 'fpmsyncd': {'status': 'OK', 'message': '', 'type': 'Process'}, 'sflowmgrd': {'status': 'OK', 'message': '', 'type': 'Process'}, 'vlanmgrd': {'status': 'OK', 'message': '', 'type': 'Process'}, 'nbrmgrd': {'status': 'OK', 'message': '', 'type': 'Process'}}, 'Hardware': {'psu_1_fan_1': {'status': 'OK', 'message': '', 'type': 'Fan'}, 'psu_2_fan_1': {'status': 'OK', 'message': '', 'type': 'Fan'}, 'PSU 1': {'status': 'OK', 'message': '', 'type': 'PSU'}, 'fan10': {'status': 'OK', 'message': '', 'type': 'Fan'}, 'PSU 2': {'status': 'OK', 'message': '', 'type': 'PSU'}, 'ASIC': {'status': 'OK', 'message': '', 'type': 'ASIC'}, 'fan1': {'status': 'OK', 'message': '', 'type': 'Fan'}, 'fan3': {'status': 'OK', 'message': '', 'type': 'Fan'}, 'fan2': {'status': 'OK', 'message': '', 'type': 'Fan'}, 'fan5': {'status': 'OK', 'message': '', 'type': 'Fan'}, 'fan4': {'status': 'OK', 'message': '', 'type': 'Fan'}, 'fan7': {'status': 'OK', 'message': '', 'type': 'Fan'}, 'fan6': {'status': 'OK', 'message': '', 'type': 'Fan'}, 'fan9': {'status': 'OK', 'message': '', 'type': 'Fan'}, 'fan8': {'status': 'OK', 'message': '', 'type': 'Fan'}}}
        elif MockerManager.counter == 2:
            state = MockerManager.STATE_RUNNING
            stats = {'Services': {'neighsyncd': {'status': 'OK', 'message': '', 'type': 'Process'}, 'vrfmgrd': {'status': 'OK', 'message': '', 'type': 'Process'}, 'telemetry': {'status': 'OK', 'message': '', 'type': 'Process'}, 'dialout_client': {'status': 'OK', 'message': '', 'type': 'Process'}, 'zebra': {'status': 'OK', 'message': '', 'type': 'Process'}, 'rsyslog': {'status': 'OK', 'message': '', 'type': 'Process'}, 'snmpd': {'status': 'OK', 'message': '', 'type': 'Process'}, 'redis_server': {'status': 'OK', 'message': '', 'type': 'Process'}, 'intfmgrd': {'status': 'OK', 'message': '', 'type': 'Process'}, 'orchagent': {'status': 'OK', 'message': '', 'type': 'Process'}, 'vxlanmgrd': {'status': 'OK', 'message': '', 'type': 'Process'}, 'lldpd_monitor': {'status': 'OK', 'message': '', 'type': 'Process'}, 'portsyncd': {'status': 'OK', 'message': '', 'type': 'Process'}, 'var-log': {'status': 'OK', 'message': '', 'type': 'Filesystem'}, 'lldpmgrd': {'status': 'OK', 'message': '', 'type': 'Process'}, 'syncd': {'status': 'OK', 'message': '', 'type': 'Process'}, 'sonic': {'status': 'OK', 'message': '', 'type': 'System'}, 'buffermgrd': {'status': 'OK', 'message': '', 'type': 'Process'}, 'portmgrd': {'status': 'OK', 'message': '', 'type': 'Process'}, 'staticd': {'status': 'OK', 'message': '', 'type': 'Process'}, 'bgpd': {'status': 'OK', 'message': '', 'type': 'Process'}, 'lldp_syncd': {'status': 'OK', 'message': '', 'type': 'Process'}, 'bgpcfgd': {'status': 'OK', 'message': '', 'type': 'Process'}, 'snmp_subagent': {'status': 'OK', 'message': '', 'type': 'Process'}, 'root-overlay': {'status': 'OK', 'message': '', 'type': 'Filesystem'}, 'fpmsyncd': {'status': 'OK', 'message': '', 'type': 'Process'}, 'sflowmgrd': {'status': 'OK', 'message': '', 'type': 'Process'}, 'vlanmgrd': {'status': 'OK', 'message': '', 'type': 'Process'}, 'nbrmgrd': {'status': 'OK', 'message': '', 'type': 'Process'}}, 'Hardware': {'psu_1_fan_1': {'status': 'OK', 'message': '', 'type': 'Fan'}, 'psu_2_fan_1': {'status': 'OK', 'message': '', 'type': 'Fan'}, 'PSU 1': {'status': 'OK', 'message': '', 'type': 'PSU'}, 'fan10': {'status': 'OK', 'message': '', 'type': 'Fan'}, 'PSU 2': {'status': 'OK', 'message': '', 'type': 'PSU'}, 'ASIC': {'status': 'OK', 'message': '', 'type': 'ASIC'}, 'fan1': {'status': 'OK', 'message': '', 'type': 'Fan'}, 'fan3': {'status': 'OK', 'message': '', 'type': 'Fan'}, 'fan2': {'status': 'OK', 'message': '', 'type': 'Fan'}, 'fan5': {'status': 'OK', 'message': '', 'type': 'Fan'}, 'fan4': {'status': 'OK', 'message': '', 'type': 'Fan'}, 'fan7': {'status': 'OK', 'message': '', 'type': 'Fan'}, 'fan6': {'status': 'OK', 'message': '', 'type': 'Fan'}, 'fan9': {'status': 'OK', 'message': '', 'type': 'Fan'}, 'fan8': {'status': 'OK', 'message': '', 'type': 'Fan'}}}
        elif MockerManager.counter == 3:
            state = MockerManager.STATE_RUNNING
            stats = {'Services': {'neighsyncd': {'status': 'OK', 'message': '', 'type': 'Process'}, 'vrfmgrd': {'status': 'OK', 'message': '', 'type': 'Process'}, 'telemetry': {'status': 'Not OK', 'message': 'telemetry is not Running', 'type': 'Process'}, 'dialout_client': {'status': 'OK', 'message': '', 'type': 'Process'}, 'zebra': {'status': 'OK', 'message': '', 'type': 'Process'}, 'rsyslog': {'status': 'OK', 'message': '', 'type': 'Process'}, 'snmpd': {'status': 'OK', 'message': '', 'type': 'Process'}, 'redis_server': {'status': 'OK', 'message': '', 'type': 'Process'}, 'intfmgrd': {'status': 'OK', 'message': '', 'type': 'Process'}, 'orchagent': {'status': 'OK', 'message': '', 'type': 'Process'}, 'vxlanmgrd': {'status': 'OK', 'message': '', 'type': 'Process'}, 'lldpd_monitor': {'status': 'OK', 'message': '', 'type': 'Process'}, 'portsyncd': {'status': 'OK', 'message': '', 'type': 'Process'}, 'var-log': {'status': 'OK', 'message': '', 'type': 'Filesystem'}, 'lldpmgrd': {'status': 'OK', 'message': '', 'type': 'Process'}, 'syncd': {'status': 'OK', 'message': '', 'type': 'Process'}, 'sonic': {'status': 'OK', 'message': '', 'type': 'System'}, 'buffermgrd': {'status': 'OK', 'message': '', 'type': 'Process'}, 'portmgrd': {'status': 'OK', 'message': '', 'type': 'Process'}, 'staticd': {'status': 'OK', 'message': '', 'type': 'Process'}, 'bgpd': {'status': 'OK', 'message': '', 'type': 'Process'}, 'lldp_syncd': {'status': 'OK', 'message': '', 'type': 'Process'}, 'bgpcfgd': {'status': 'OK', 'message': '', 'type': 'Process'}, 'snmp_subagent': {'status': 'OK', 'message': '', 'type': 'Process'}, 'root-overlay': {'status': 'OK', 'message': '', 'type': 'Filesystem'}, 'fpmsyncd': {'status': 'OK', 'message': '', 'type': 'Process'}, 'sflowmgrd': {'status': 'Not OK', 'message': 'sflowmgrd is not Running', 'type': 'Process'}, 'vlanmgrd': {'status': 'OK', 'message': '', 'type': 'Process'}, 'nbrmgrd': {'status': 'OK', 'message': '', 'type': 'Process'}}, 'Hardware': {'PSU 2': {'status': 'OK', 'message': '', 'type': 'PSU'}, 'psu_1_fan_1': {'status': 'OK', 'message': '', 'type': 'Fan'}, 'psu_2_fan_1': {'status': 'OK', 'message': '', 'type': 'Fan'}, 'fan11': {'status': 'OK', 'message': '', 'type': 'Fan'}, 'fan10': {'status': 'OK', 'message': '', 'type': 'Fan'}, 'fan12': {'status': 'OK', 'message': '', 'type': 'Fan'}, 'ASIC': {'status': 'OK', 'message': '', 'type': 'ASIC'}, 'fan1': {'status': 'OK', 'message': '', 'type': 'Fan'}, 'PSU 1': {'status': 'OK', 'message': '', 'type': 'PSU'}, 'fan3': {'status': 'OK', 'message': '', 'type': 'Fan'}, 'fan2': {'status': 'OK', 'message': '', 'type': 'Fan'}, 'fan5': {'status': 'OK', 'message': '', 'type': 'Fan'}, 'fan4': {'status': 'OK', 'message': '', 'type': 'Fan'}, 'fan7': {'status': 'OK', 'message': '', 'type': 'Fan'}, 'fan6': {'status': 'OK', 'message': '', 'type': 'Fan'}, 'fan9': {'status': 'OK', 'message': '', 'type': 'Fan'}, 'fan8': {'status': 'OK', 'message': '', 'type': 'Fan'}}}
        elif MockerManager.counter == 4:
            state = MockerManager.STATE_RUNNING
            stats = {'Services': {'neighsyncd': {'status': 'OK', 'message': '', 'type': 'Process'}, 'vrfmgrd': {'status': 'OK', 'message': '', 'type': 'Process'}, 'telemetry': {'status': 'Not OK', 'message': 'telemetry is not Running', 'type': 'Process'}, 'dialout_client': {'status': 'OK', 'message': '', 'type': 'Process'}, 'zebra': {'status': 'OK', 'message': '', 'type': 'Process'}, 'rsyslog': {'status': 'OK', 'message': '', 'type': 'Process'}, 'snmpd': {'status': 'OK', 'message': '', 'type': 'Process'}, 'redis_server': {'status': 'OK', 'message': '', 'type': 'Process'}, 'intfmgrd': {'status': 'OK', 'message': '', 'type': 'Process'}, 'orchagent': {'status': 'OK', 'message': '', 'type': 'Process'}, 'vxlanmgrd': {'status': 'OK', 'message': '', 'type': 'Process'}, 'lldpd_monitor': {'status': 'OK', 'message': '', 'type': 'Process'}, 'portsyncd': {'status': 'OK', 'message': '', 'type': 'Process'}, 'var-log': {'status': 'OK', 'message': '', 'type': 'Filesystem'}, 'lldpmgrd': {'status': 'OK', 'message': '', 'type': 'Process'}, 'syncd': {'status': 'OK', 'message': '', 'type': 'Process'}, 'sonic': {'status': 'OK', 'message': '', 'type': 'System'}, 'buffermgrd': {'status': 'OK', 'message': '', 'type': 'Process'}, 'portmgrd': {'status': 'OK', 'message': '', 'type': 'Process'}, 'staticd': {'status': 'OK', 'message': '', 'type': 'Process'}, 'bgpd': {'status': 'OK', 'message': '', 'type': 'Process'}, 'lldp_syncd': {'status': 'OK', 'message': '', 'type': 'Process'}, 'bgpcfgd': {'status': 'OK', 'message': '', 'type': 'Process'}, 'snmp_subagent': {'status': 'OK', 'message': '', 'type': 'Process'}, 'root-overlay': {'status': 'OK', 'message': '', 'type': 'Filesystem'}, 'fpmsyncd': {'status': 'OK', 'message': '', 'type': 'Process'}, 'sflowmgrd': {'status': 'Not OK', 'message': 'sflowmgrd is not Running', 'type': 'Process'}, 'vlanmgrd': {'status': 'OK', 'message': '', 'type': 'Process'}, 'nbrmgrd': {'status': 'OK', 'message': '', 'type': 'Process'}}, 'Hardware': {'PSU 2': {'status': 'Not OK', 'message': 'Failed to get voltage minimum threshold data for PSU 2', 'type': 'PSU'}, 'psu_1_fan_1': {'status': 'OK', 'message': '', 'type': 'Fan'}, 'psu_2_fan_1': {'status': 'OK', 'message': '', 'type': 'Fan'}, 'fan11': {'status': 'OK', 'message': '', 'type': 'Fan'}, 'fan10': {'status': 'OK', 'message': '', 'type': 'Fan'}, 'fan12': {'status': 'OK', 'message': '', 'type': 'Fan'}, 'ASIC': {'status': 'OK', 'message': '', 'type': 'ASIC'}, 'fan1': {'status': 'OK', 'message': '', 'type': 'Fan'}, 'PSU 1': {'status': 'Not OK', 'message': 'Failed to get voltage minimum threshold data for PSU 1', 'type': 'PSU'}, 'fan3': {'status': 'OK', 'message': '', 'type': 'Fan'}, 'fan2': {'status': 'OK', 'message': '', 'type': 'Fan'}, 'fan5': {'status': 'OK', 'message': '', 'type': 'Fan'}, 'fan4': {'status': 'OK', 'message': '', 'type': 'Fan'}, 'fan7': {'status': 'OK', 'message': '', 'type': 'Fan'}, 'fan6': {'status': 'OK', 'message': '', 'type': 'Fan'}, 'fan9': {'status': 'OK', 'message': '', 'type': 'Fan'}, 'fan8': {'status': 'OK', 'message': '', 'type': 'Fan'}}}
        elif MockerManager.counter == 5:
            state = MockerManager.STATE_RUNNING
            stats = {'Services': {'neighsyncd': {'status': 'OK', 'message': '', 'type': 'Process'}, 'vrfmgrd': {'status': 'OK', 'message': '', 'type': 'Process'}, 'telemetry': {'status': 'Not OK', 'message': 'telemetry is not Running', 'type': 'Process'}, 'dialout_client': {'status': 'OK', 'message': '', 'type': 'Process'}, 'zebra': {'status': 'OK', 'message': '', 'type': 'Process'}, 'rsyslog': {'status': 'OK', 'message': '', 'type': 'Process'}, 'snmpd': {'status': 'OK', 'message': '', 'type': 'Process'}, 'redis_server': {'status': 'OK', 'message': '', 'type': 'Process'}, 'intfmgrd': {'status': 'OK', 'message': '', 'type': 'Process'}, 'orchagent': {'status': 'OK', 'message': '', 'type': 'Process'}, 'vxlanmgrd': {'status': 'OK', 'message': '', 'type': 'Process'}, 'lldpd_monitor': {'status': 'OK', 'message': '', 'type': 'Process'}, 'portsyncd': {'status': 'OK', 'message': '', 'type': 'Process'}, 'var-log': {'status': 'OK', 'message': '', 'type': 'Filesystem'}, 'lldpmgrd': {'status': 'OK', 'message': '', 'type': 'Process'}, 'syncd': {'status': 'OK', 'message': '', 'type': 'Process'}, 'sonic': {'status': 'OK', 'message': '', 'type': 'System'}, 'buffermgrd': {'status': 'OK', 'message': '', 'type': 'Process'}, 'portmgrd': {'status': 'OK', 'message': '', 'type': 'Process'}, 'staticd': {'status': 'OK', 'message': '', 'type': 'Process'}, 'bgpd': {'status': 'OK', 'message': '', 'type': 'Process'}, 'lldp_syncd': {'status': 'OK', 'message': '', 'type': 'Process'}, 'bgpcfgd': {'status': 'OK', 'message': '', 'type': 'Process'}, 'snmp_subagent': {'status': 'OK', 'message': '', 'type': 'Process'}, 'root-overlay': {'status': 'OK', 'message': '', 'type': 'Filesystem'}, 'fpmsyncd': {'status': 'OK', 'message': '', 'type': 'Process'}, 'sflowmgrd': {'status': 'Not OK', 'message': 'sflowmgrd is not Running', 'type': 'Process'}, 'vlanmgrd': {'status': 'OK', 'message': '', 'type': 'Process'}, 'nbrmgrd': {'status': 'OK', 'message': '', 'type': 'Process'}}, 'Hardware': {'PSU 2': {'status': 'OK', 'message': '', 'type': 'PSU'}, 'psu_1_fan_1': {'status': 'OK', 'message': '', 'type': 'Fan'}, 'psu_2_fan_1': {'status': 'OK', 'message': '', 'type': 'Fan'}, 'fan11': {'status': 'OK', 'message': '', 'type': 'Fan'}, 'fan10': {'status': 'OK', 'message': '', 'type': 'Fan'}, 'fan12': {'status': 'OK', 'message': '', 'type': 'Fan'}, 'ASIC': {'status': 'OK', 'message': '', 'type': 'ASIC'}, 'fan1': {'status': 'OK', 'message': '', 'type': 'Fan'}, 'PSU 1': {'status': 'OK', 'message': '', 'type': 'PSU'}, 'fan3': {'status': 'OK', 'message': '', 'type': 'Fan'}, 'fan2': {'status': 'OK', 'message': '', 'type': 'Fan'}, 'fan5': {'status': 'OK', 'message': '', 'type': 'Fan'}, 'fan4': {'status': 'OK', 'message': '', 'type': 'Fan'}, 'fan7': {'status': 'OK', 'message': '', 'type': 'Fan'}, 'fan6': {'status': 'OK', 'message': '', 'type': 'Fan'}, 'fan9': {'status': 'OK', 'message': '', 'type': 'Fan'}, 'fan8': {'status': 'OK', 'message': '', 'type': 'Fan'}}}
        else:
            state = MockerManager.STATE_RUNNING
            stats = {}
        MockerManager.counter += 1

        return state, stats

class MockerChassis(object):
    counter = 0

    def initizalize_system_led(self):
        return

    def get_status_led(self):
        if MockerChassis.counter == 1:
            MockerChassis.counter += 1
            return "green"
        else:
            MockerChassis.counter += 1
            return "red"

import show.main as show

class TestHealth(object):
    @classmethod
    def setup_class(cls):
        print("SETUP")
        os.environ["PATH"] += os.pathsep + scripts_path
        os.environ["UTILITIES_UNIT_TESTING"] = "1"

    def test_health_summary(self):
        runner = CliRunner()
        result = runner.invoke(show.cli.commands["system-health"].commands["summary"])
        click.echo(result.output)
        expected = """System is currently booting...\n"""
        assert result.output == expected
        result = runner.invoke(show.cli.commands["system-health"].commands["summary"])
        expected = """System status summary\n\n  System status LED  red\n  Services:\n    Status: Not OK\n    Not Running: 'telemetry', 'snmp_subagent'\n  Hardware:\n    Status: OK\n"""
        click.echo(result.output)
        assert result.output == expected
        result = runner.invoke(show.cli.commands["system-health"].commands["summary"])
        click.echo(result.output)
        expected = """System status summary\n\n  System status LED  green\n  Services:\n    Status: OK\n  Hardware:\n    Status: OK\n"""
        assert result.output == expected
   
    def test_health_monitor(self):
        runner = CliRunner()
        result = runner.invoke(show.cli.commands["system-health"].commands["monitor-list"])
        click.echo(result.output)
        expected = """\nSystem services and devices monitor list\n\nName            Status    Type\n--------------  --------  ----------\ntelemetry       Not OK    Process\nsflowmgrd       Not OK    Process\nneighsyncd      OK        Process\nvrfmgrd         OK        Process\ndialout_client  OK        Process\nzebra           OK        Process\nrsyslog         OK        Process\nsnmpd           OK        Process\nredis_server    OK        Process\nintfmgrd        OK        Process\norchagent       OK        Process\nvxlanmgrd       OK        Process\nlldpd_monitor   OK        Process\nportsyncd       OK        Process\nvar-log         OK        Filesystem\nlldpmgrd        OK        Process\nsyncd           OK        Process\nsonic           OK        System\nbuffermgrd      OK        Process\nportmgrd        OK        Process\nstaticd         OK        Process\nvlanmgrd        OK        Process\nlldp_syncd      OK        Process\nbgpcfgd         OK        Process\nsnmp_subagent   OK        Process\nroot-overlay    OK        Filesystem\nfpmsyncd        OK        Process\nbgpd            OK        Process\nnbrmgrd         OK        Process\nfan12           OK        Fan\npsu_1_fan_1     OK        Fan\npsu_2_fan_1     OK        Fan\nfan11           OK        Fan\nfan10           OK        Fan\nPSU 2           OK        PSU\nASIC            OK        ASIC\nfan1            OK        Fan\nPSU 1           OK        PSU\nfan3            OK        Fan\nfan2            OK        Fan\nfan5            OK        Fan\nfan4            OK        Fan\nfan7            OK        Fan\nfan6            OK        Fan\nfan9            OK        Fan\nfan8            OK        Fan\n"""
        assert result.output == expected

    def test_health_detail(self):
        runner = CliRunner()
        result = runner.invoke(show.cli.commands["system-health"].commands["detail"])
        click.echo(result.output)
        expected = """System status summary\n\n  System status LED  red\n  Services:\n    Status: Not OK\n    Not Running: 'telemetry', 'sflowmgrd'\n  Hardware:\n    Status: Not OK\n    Reasons: Failed to get voltage minimum threshold data for PSU 1\n\t     Failed to get voltage minimum threshold data for PSU 2\n\nSystem services and devices monitor list\n\nName            Status    Type\n--------------  --------  ----------\ntelemetry       Not OK    Process\nsflowmgrd       Not OK    Process\nneighsyncd      OK        Process\nvrfmgrd         OK        Process\ndialout_client  OK        Process\nzebra           OK        Process\nrsyslog         OK        Process\nsnmpd           OK        Process\nredis_server    OK        Process\nintfmgrd        OK        Process\norchagent       OK        Process\nvxlanmgrd       OK        Process\nlldpd_monitor   OK        Process\nportsyncd       OK        Process\nvar-log         OK        Filesystem\nlldpmgrd        OK        Process\nsyncd           OK        Process\nsonic           OK        System\nbuffermgrd      OK        Process\nportmgrd        OK        Process\nstaticd         OK        Process\nvlanmgrd        OK        Process\nlldp_syncd      OK        Process\nbgpcfgd         OK        Process\nsnmp_subagent   OK        Process\nroot-overlay    OK        Filesystem\nfpmsyncd        OK        Process\nbgpd            OK        Process\nnbrmgrd         OK        Process\nPSU 2           Not OK    PSU\nPSU 1           Not OK    PSU\nfan12           OK        Fan\npsu_1_fan_1     OK        Fan\npsu_2_fan_1     OK        Fan\nfan11           OK        Fan\nfan10           OK        Fan\nASIC            OK        ASIC\nfan1            OK        Fan\nfan3            OK        Fan\nfan2            OK        Fan\nfan5            OK        Fan\nfan4            OK        Fan\nfan7            OK        Fan\nfan6            OK        Fan\nfan9            OK        Fan\nfan8            OK        Fan\n\nSystem services and devices ignore list\n\nName    Status    Type\n------  --------  ------\n"""
        assert result.output == expected
        MockerConfig.ignore_devices.insert(0, "psu.voltage")
        result = runner.invoke(show.cli.commands["system-health"].commands["detail"])
        click.echo(result.output)
        expected = """System status summary\n\n  System status LED  red\n  Services:\n    Status: Not OK\n    Not Running: 'telemetry', 'sflowmgrd'\n  Hardware:\n    Status: OK\n\nSystem services and devices monitor list\n\nName            Status    Type\n--------------  --------  ----------\ntelemetry       Not OK    Process\nsflowmgrd       Not OK    Process\nneighsyncd      OK        Process\nvrfmgrd         OK        Process\ndialout_client  OK        Process\nzebra           OK        Process\nrsyslog         OK        Process\nsnmpd           OK        Process\nredis_server    OK        Process\nintfmgrd        OK        Process\norchagent       OK        Process\nvxlanmgrd       OK        Process\nlldpd_monitor   OK        Process\nportsyncd       OK        Process\nvar-log         OK        Filesystem\nlldpmgrd        OK        Process\nsyncd           OK        Process\nsonic           OK        System\nbuffermgrd      OK        Process\nportmgrd        OK        Process\nstaticd         OK        Process\nvlanmgrd        OK        Process\nlldp_syncd      OK        Process\nbgpcfgd         OK        Process\nsnmp_subagent   OK        Process\nroot-overlay    OK        Filesystem\nfpmsyncd        OK        Process\nbgpd            OK        Process\nnbrmgrd         OK        Process\nfan12           OK        Fan\npsu_1_fan_1     OK        Fan\npsu_2_fan_1     OK        Fan\nfan11           OK        Fan\nfan10           OK        Fan\nPSU 2           OK        PSU\nASIC            OK        ASIC\nfan1            OK        Fan\nPSU 1           OK        PSU\nfan3            OK        Fan\nfan2            OK        Fan\nfan5            OK        Fan\nfan4            OK        Fan\nfan7            OK        Fan\nfan6            OK        Fan\nfan9            OK        Fan\nfan8            OK        Fan\n\nSystem services and devices ignore list\n\nName         Status    Type\n-----------  --------  ------\npsu.voltage  Ignored   Device\n"""
        assert result.output == expected
        
    @classmethod
    def teardown_class(cls):
        print("TEARDOWN")
        os.environ["PATH"] = os.pathsep.join(os.environ["PATH"].split(os.pathsep)[:-1])
        os.environ["UTILITIES_UNIT_TESTING"] = "0"
