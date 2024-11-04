from click.testing import CliRunner
from unittest.mock import patch
from show import memory_statistics
from swsscommon.swsscommon import ConfigDBConnector


class TestMemoryStatisticsConfig:
    def test_memory_statistics_config(self):
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

            # Directly invoke the 'config' command under memory_statistics
            result = runner.invoke(memory_statistics.config)

            assert result.exit_code == 0
            assert "Memory Statistics administrative mode: Enabled" in result.output
            assert "Memory Statistics retention time (days): 10" in result.output
            assert "Memory Statistics sampling interval (minutes): 15" in result.output


class TestMemoryStatisticsLogs:
    def test_memory_statistics_logs_empty(self):
        runner = CliRunner()

        # Mock ConfigDBConnector and its methods
        with patch.object(ConfigDBConnector, 'connect'), \
             patch.object(ConfigDBConnector, 'get_table', return_value={}):  # Simulating an empty table

            # Invoke the 'logs' command with empty parameters
            result = runner.invoke(memory_statistics.show_memory_statistics_logs, [])

            assert result.exit_code == 0
            assert "No memory statistics available for the given parameters." in result.output
