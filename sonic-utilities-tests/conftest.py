import os
import sys

import mock
import pytest

# noinspection PyUnresolvedReferences
import mock_tables.dbconnector
import show_ip_route_common

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
    else:
        bgp_mocked_json = os.path.join(
            test_path, 'mock_tables', 'dummy.json')

    def mock_run_bgp_command(vtysh_cmd, bgp_namespace):
        if os.path.isfile(bgp_mocked_json):
            with open(bgp_mocked_json) as json_data:
                mock_frr_data = json_data.read()
            return mock_frr_data
        return ""

    def mock_run_show_ip_route_commands(request):
        if request.param == 'ipv6_route_err':
            return show_ip_route_common.show_ipv6_route_err_expected_output
        elif request.param == 'ip_route':
            return show_ip_route_common.show_ip_route_expected_output
        elif request.param == 'ip_specific_route':
            return show_ip_route_common.show_specific_ip_route_expected_output
        elif request.param == 'ip_special_route':
            return show_ip_route_common.show_special_ip_route_expected_output
        elif request.param == 'ipv6_route':
            return show_ip_route_common.show_ipv6_route_expected_output
        elif request.param == 'ipv6_specific_route':
            return show_ip_route_common.show_ipv6_route_single_json_expected_output
        else:
            return ""

    if any ([request.param == 'ipv6_route_err', request.param == 'ip_route',\
             request.param == 'ip_specific_route', request.param == 'ip_special_route',\
             request.param == 'ipv6_route', request.param == 'ipv6_specific_route']):
        bgp_util.run_bgp_command = mock.MagicMock(
            return_value=mock_run_show_ip_route_commands(request))
    else:
        bgp_util.run_bgp_command = mock.MagicMock(
            return_value=mock_run_bgp_command("", ""))


@pytest.fixture
def setup_multi_asic_bgp_instance(request):
    import utilities_common.bgp_util as bgp_util

    if request.param == 'v4':
        m_asic_json_file = 'ipv4_bgp_summary.json'
    elif request.param == 'v6':
        m_asic_json_file = 'ipv6_bgp_summary.json'
    elif request.param == 'ip_route':
        m_asic_json_file = 'ip_route.json'
    elif request.param == 'ip_specific_route':
        m_asic_json_file = 'ip_specific_route.json'
    elif request.param == 'ipv6_specific_route':
        m_asic_json_file = 'ipv6_specific_route.json'
    elif request.param == 'ipv6_route':
        m_asic_json_file = 'ipv6_route.json'
    elif request.param == 'ip_special_route':
        m_asic_json_file = 'ip_special_route.json'
    elif request.param == 'ip_empty_route':
        m_asic_json_file = 'ip_empty_route.json'
    elif request.param == 'ip_specific_route_on_1_asic':
        m_asic_json_file = 'ip_special_route_asic0_only.json'
    elif request.param == 'ip_route_summary':
        m_asic_json_file = 'ip_route_summary.txt'
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
    reload(show)
    import show.bgp_frr_v4 as bgpv4
    import show.bgp_frr_v6 as bgpv6
    reload(bgpv4)
    reload(bgpv6)

    show.ip.add_command(bgpv4.bgp)
    show.ipv6.add_command(bgpv6.bgp)

    return show


@pytest.fixture
def setup_ip_route_commands():
    import show.main as show

    return show

@pytest.fixture(scope='class')
def setup_multi_asic_display_options():
    from sonic_py_common import multi_asic
    from utilities_common import multi_asic as multi_asic_util
    import mock_tables.dbconnector
    import click
    import show.main as show
    _multi_asic_click_options = multi_asic_util.multi_asic_click_options

    def mock_multi_asic_click_options(func):
        _mock_multi_asic_click_options = [
            click.option('--display',
                         '-d', 'display',
                         default="frontend",
                         show_default=True,
                         type=click.Choice(["all", "frontend"]),
                         help='Show internal interfaces'),
            click.option('--namespace',
                         '-n', 'namespace',
                         default=None,
                         type=click.Choice(["asic0", "asic1"]),
                         show_default=True,
                         help='Namespace name or all'),
        ]
        for option in reversed(_mock_multi_asic_click_options):
            func = option(func)
        return func

    multi_asic.get_num_asics = mock.MagicMock(return_value=2)
    multi_asic.is_multi_asic = mock.MagicMock(return_value=True)
    multi_asic.get_namespace_list = mock.MagicMock(
        return_value=["asic0", "asic1"])

    multi_asic_util.multi_asic_click_options = mock_multi_asic_click_options
    mock_tables.dbconnector.load_namespace_config()
    yield

    multi_asic_util.multi_asic_click_options = _multi_asic_click_options
    mock_tables.dbconnector.load_database_config()

