import os
import sys
import json


import mock
import pytest

import mock_tables.dbconnector

from sonic_py_common import device_info
from swsssdk import ConfigDBConnector

test_path = os.path.dirname(os.path.abspath(__file__))
modules_path = os.path.dirname(test_path)
sys.path.insert(0, modules_path)

generated_services_list = [
    'ntp-config.service',
    'warmboot-finalizer.service',
    'watchdog-control.service',
    'rsyslog-config.service',
    'interfaces-config.service',
    'hostcfgd.service',
    'hostname-config.service',
    'topology.service',
    'updategraph.service',
    'config-setup.service',
    'caclmgrd.service',
    'procdockerstatsd.service',
    'pcie-check.service',
    'process-reboot-cause.service',
    'dhcp_relay.service',
    'snmp.service',
    'sflow.service',
    'bgp.service',
    'telemetry.service',
    'swss.service',
    'database.service',
    'database.service',
    'lldp.service',
    'lldp.service',
    'pmon.service',
    'radv.service',
    'mgmt-framework.service',
    'nat.service',
    'teamd.service',
    'syncd.service',
    'snmp.timer',
    'telemetry.timer']

@pytest.fixture
def get_cmd_module():
    import config.main as config
    import show.main as show

    return (config, show)

@pytest.fixture
def get_show_module():
    import show.main as show
    return show

@pytest.fixture
def setup_single_broacom_asic():
    import config.main as config
    import show.main as show

    device_info.get_num_npus = mock.MagicMock(return_value = 1)
    config._get_sonic_generated_services = \
            mock.MagicMock(return_value = (generated_services_list, []))

    config.asic_type = mock.MagicMock(return_value = "broadcom")
    config._get_device_type = mock.MagicMock(return_value = "ToRRouter")

@pytest.fixture
def setup_single_bgp_instance(monkeypatch, request):
    import utilities_common.bgp_util as bgp_util

    if request.param == 'v4':
        bgp_summary_json = 'mock_tables/ipv4_bgp_summary.json'
    else:
        bgp_summary_json = 'mock_tables/ipv6_bgp_summary.json'

    def mock_run_bgp_command(vtysh_cmd, bgp_namespace):
        with open(bgp_summary_json) as json_data:
            mock_frr_data = json_data.read()
        return mock_frr_data

    monkeypatch.setattr(bgp_util, "run_bgp_command", mock_run_bgp_command)

