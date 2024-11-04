import os
import pytest
from click.testing import CliRunner
from unittest.mock import patch
from show import memory_statistics
from swsscommon.swsscommon import ConfigDBConnector


@pytest.fixture
def setup_teardown():
    os.environ["UTILITIES_UNIT_TESTING"] = "1"
    yield
    os.environ["UTILITIES_UNIT_TESTING"] = "0"


class TestMemoryStatisticsConfig:
    def test_memory_statistics_config(self, setup_teardown):
        runner = CliRunner()

        # Mock ConfigDBConnector and its methods
        with patch.object(ConfigDBConnector, 'connect'), \
             patch.object(ConfigDBConnector, 'get_table', return_value={
                 "memory_statistics": {
                     "enabled": "true",
                     "retention_time": "10",
                     "sampling_interval": "15"
                 }
             }):

            result = runner.invoke(memory_statistics.memory_statistics.commands['memory_statitics'].commands['config'])

            assert result.exit_code == 0
            expected_output = (
                "Memory Statistics administrative mode: Enabled\n"
                "Memory Statistics retention time (days): 10\n"
                "Memory Statistics sampling interval (minutes): 15\n"
            )
            assert result.output == expected_output


class TestMemoryStatisticsLogs:
    def test_memory_statistics_logs_empty(self, setup_teardown):
        runner = CliRunner()

        # Mock ConfigDBConnector and its methods
        with patch.object(ConfigDBConnector, 'connect'), \
             patch.object(ConfigDBConnector, 'get_table', return_value={}):

            result = runner.invoke(memory_statistics.memory_statistics.commands['logs'])

            assert result.exit_code == 0
            assert result.output.strip() == "No memory statistics available for the given parameters."
