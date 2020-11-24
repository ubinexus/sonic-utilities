import json
import os
import sys
from unittest import mock

import pytest
from sonic_py_common import device_info
from swsssdk import ConfigDBConnector

from .mock_tables import dbconnector


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

def set_mock_apis():
    import config.main as config
    cwd = os.path.dirname(os.path.realpath(__file__))
    device_info.get_paths_to_platform_and_hwsku_dirs = mock.MagicMock(
        return_value=(
            os.path.join(cwd, "."), os.path.join(cwd, "qos_config_input")
        )
    )
    device_info.get_sonic_version_file = mock.MagicMock(
        return_value=os.path.join(cwd, "qos_config_input/sonic_version.yml")
    )
    config.asic_type = mock.MagicMock(return_value="broadcom")
    config._get_device_type = mock.MagicMock(return_value="ToRRouter")


@pytest.fixture
def setup_single_broadcom_asic():
    import config.main as config
    import show.main as show

    set_mock_apis()
    device_info.get_num_npus = mock.MagicMock(return_value=1)
    config._get_sonic_generated_services = \
        mock.MagicMock(return_value=(generated_services_list, []))


@pytest.fixture
def setup_multi_broadcom_masic():
    import config.main as config
    import show.main as show

    set_mock_apis()
    device_info.get_num_npus = mock.MagicMock(return_value=2)

    yield

    device_info.get_num_npus = mock.MagicMock(return_value=1)


@pytest.fixture
def setup_t1_topo():
    dbconnector.topo = "t1"
    yield
    dbconnector.topo = None

@pytest.fixture
def setup_single_bgp_instance(request):
    import utilities_common.bgp_util as bgp_util

    if request.param == 'v4':
        bgp_summary_json = os.path.join(
            test_path, 'mock_tables', 'ipv4_bgp_summary.json')
    elif request.param == 'v6':
        bgp_summary_json = os.path.join(
            test_path, 'mock_tables', 'ipv6_bgp_summary.json')
    else:
        bgp_summary_json = os.path.join(
            test_path, 'mock_tables', 'dummy.json')

    def mock_run_bgp_command(vtysh_cmd, bgp_namespace):
        if os.path.isfile(bgp_summary_json):
            with open(bgp_summary_json) as json_data:
                mock_frr_data = json_data.read()
            return mock_frr_data
        return ""

    bgp_util.run_bgp_command = mock.MagicMock(
        return_value=mock_run_bgp_command("", ""))


@pytest.fixture
def setup_bgp_commands():
    import show.main as show
    from show.bgp_frr_v4 import bgp as bgpv4
    from show.bgp_frr_v6 import bgp as bgpv6

    show.ip.add_command(bgpv4)
    show.ipv6.add_command(bgpv6)
    return show
