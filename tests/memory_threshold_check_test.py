import os
import sys
import pytest
from unittest import mock
from .mock_tables import dbconnector
from utilities_common.general import load_module_from_source

test_path = os.path.dirname(os.path.abspath(__file__))
modules_path = os.path.dirname(test_path)
scripts_path = os.path.join(modules_path, 'scripts')
sys.path.insert(0, scripts_path)

memory_threshold_check_path = os.path.join(scripts_path, 'memory_threshold_check.py')
memory_threshold_check = load_module_from_source('memory_threshold_check.py', memory_threshold_check_path)

@pytest.fixture()
def case_1():
    dbconnector.dedicated_dbs['CONFIG_DB'] = os.path.join(test_path, 'memory_threshold_check', 'config_db')
    dbconnector.dedicated_dbs['STATE_DB'] = os.path.join(test_path, 'memory_threshold_check', 'state_db')


@pytest.fixture()
def case_2():
    memory_threshold_check.MemoryStats.get_sys_memory_stats = mock.Mock(return_value={'MemFree': 10000000, 'MemTotal': 20000000})
    dbconnector.dedicated_dbs['CONFIG_DB'] = os.path.join(test_path, 'memory_threshold_check', 'config_db')
    dbconnector.dedicated_dbs['STATE_DB'] = os.path.join(test_path, 'memory_threshold_check', 'state_db_2')


@pytest.fixture()
def case_3():
    memory_threshold_check.MemoryStats.get_sys_memory_stats = mock.Mock(return_value={'MemFree': 10000000, 'MemTotal': 20000000})
    dbconnector.dedicated_dbs['CONFIG_DB'] = os.path.join(test_path, 'memory_threshold_check', 'config_db')
    dbconnector.dedicated_dbs['STATE_DB'] = os.path.join(test_path, 'memory_threshold_check', 'state_db_3')


def test_memory_check_host_not_crossed(case_1):
    memory_threshold_check.MemoryStats.get_sys_memory_stats = mock.Mock(return_value={'MemFree': 1000000, 'MemTotal': 2000000})
    assert memory_threshold_check.main() == (memory_threshold_check.EXIT_SUCCESS, '')


def test_memory_check_host_less_then_min_required(case_1):
    memory_threshold_check.MemoryStats.get_sys_memory_stats = mock.Mock(return_value={'MemFree': 1000, 'MemTotal': 2000000})
    assert memory_threshold_check.main() == (memory_threshold_check.EXIT_THRESHOLD_CROSSED, '')


def test_memory_check_host_threshold_crossed(case_1):
    memory_threshold_check.MemoryStats.get_sys_memory_stats = mock.Mock(return_value={'MemFree': 2000000, 'MemTotal': 20000000})
    assert memory_threshold_check.main() == (memory_threshold_check.EXIT_THRESHOLD_CROSSED, '')


def test_memory_check_telemetry_threshold_crossed(case_2):
    assert memory_threshold_check.main() == (memory_threshold_check.EXIT_THRESHOLD_CROSSED, 'telemetry')


def test_memory_check_swss_threshold_crossed(case_3):
    assert memory_threshold_check.main() == (memory_threshold_check.EXIT_THRESHOLD_CROSSED, 'swss')