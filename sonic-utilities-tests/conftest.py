import os
import sys

import mock
import pytest

# noinspection PyUnresolvedReferences
import mock_tables.dbconnector


test_path = os.path.dirname(os.path.abspath(__file__))
modules_path = os.path.dirname(test_path)
sys.path.insert(0, modules_path)

@pytest.fixture
def setup_single_bgp_instance(request):
    import utilities_common.bgp_util as bgp_util

    if request.param == 'v4':
        bgp_mocked_json = os.path.join(
            test_path, 'mock_tables', 'ipv4_bgp_summary.json')
    elif request.param == 'v6':
        bgp_mocked_json = os.path.join(
            test_path, 'mock_tables', 'ipv6_bgp_summary.json')
    elif request.param == 'ip_route':
        bgp_mocked_json = os.path.join(
            test_path, 'mock_tables', 'ip_route.json')
    elif request.param == 'ip_specific_route':
        bgp_mocked_json = os.path.join(
            test_path, 'mock_tables', 'ip_specific_route.json')
    elif request.param == 'ip_special_route':
        bgp_mocked_json = os.path.join(
            test_path, 'mock_tables', 'ip_special_route.json')
    elif request.param == 'ipv6_route':
        bgp_mocked_json = os.path.join(
            test_path, 'mock_tables', 'ipv6_route.json')
    elif request.param == 'ipv6_specific_route':
        bgp_mocked_json = os.path.join(
            test_path, 'mock_tables', 'ipv6_specific_route.json')
    else:
        bgp_mocked_json = os.path.join(
            test_path, 'mock_tables', 'dummy.json')

    def mock_run_bgp_command(vtysh_cmd, bgp_namespace):
        if os.path.isfile(bgp_mocked_json):
            with open(bgp_mocked_json) as json_data:
                mock_frr_data = json_data.read()
            return mock_frr_data
        return ""

    def mock_run_bgp_ipv6_err_command(vtysh_cmd, bgp_namespace):
        return "% Unknown command: show ipv6 route garbage"

    if request.param == 'ipv6_route_err':
        bgp_util.run_bgp_command = mock.MagicMock(
            return_value=mock_run_bgp_ipv6_err_command("", ""))
    else:
        bgp_util.run_bgp_command = mock.MagicMock(
            return_value=mock_run_bgp_command("", ""))


@pytest.fixture
def setup_multi_asic_bgp_instance(request):
    import utilities_common.bgp_util as bgp_util

    if request.param == 'ip_route':
        m_asic_json_file = 'ip_route.json'
    elif request.param == 'ip_specific_route':
        m_asic_json_file = 'ip_specific_route.json'
    elif request.param == 'ipv6_specific_route':
        m_asic_json_file = 'ipv6_specific_route.json'
    elif request.param == 'ipv6_route':
        m_asic_json_file = 'ipv6_route.json'
    else:
        m_asic_json_file = os.path.join(
            test_path, 'mock_tables', 'dummy.json')

    def mock_run_bgp_command(vtysh_cmd, bgp_namespace):
        bgp_mocked_json = os.path.join(
            test_path, 'mock_tables', bgp_namespace, m_asic_json_file)
        if os.path.isfile(bgp_mocked_json):
            with open(bgp_mocked_json) as json_data:
                mock_frr_data = json_data.read()
            return mock_frr_data
        else:
            return ""

    _old_run_bgp_command = bgp_util.run_bgp_command
    bgp_util.run_bgp_command = mock_run_bgp_command

    yield

    bgp_util.run_bgp_command = _old_run_bgp_command


@pytest.fixture
def setup_bgp_commands():
    import show.main as show
    from show.bgp_frr_v4 import bgp as bgpv4
    from show.bgp_frr_v6 import bgp as bgpv6

    show.ip.add_command(bgpv4)
    show.ipv6.add_command(bgpv6)
    return show


@pytest.fixture
def setup_ip_route_commands():
    import show.main as show

    return show
