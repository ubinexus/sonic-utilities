from swsscommon.swsscommon import ConfigDBConnector
from click.testing import CliRunner
from unittest.mock import patch
from show import memory_statistics  # Ensure this is correctly imported


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

            # Attempt to invoke the memory_statistics 'config' command
            result = runner.invoke(memory_statistics.cli, ['config'])

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

            # Attempt to invoke the memory_statistics 'logs' command
            result = runner.invoke(memory_statistics.cli, ['logs'])

            assert result.exit_code == 0
            assert "No memory statistics available for the given parameters." in result.output
