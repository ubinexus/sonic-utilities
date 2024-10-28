import unittest
from unittest.mock import patch, MagicMock
from click.testing import CliRunner
from config.memory_statistics import (
    memory_statistics_enable,
    memory_statistics_disable,
    memory_statistics_retention_period,
    memory_statistics_sampling_interval
)
from swsscommon.swsscommon import ConfigDBConnector


class TestMemoryStatisticsConfigCommands(unittest.TestCase):

    def setUp(self):
        self.runner = CliRunner()
        self.mock_db = MagicMock()
        # Simulate the MEMORY_STATISTICS table in Config DB
        self.mock_db.get_table.return_value = {
            "memory_statistics": {
                "enabled": "false",
                "retention_period": "15",
                "sampling_interval": "5"
            }
        }
        self.patcher = patch.object(ConfigDBConnector, 'get_table', self.mock_db.get_table)
        self.patcher.start()

    def tearDown(self):
        self.patcher.stop()

    @patch.object(ConfigDBConnector, 'mod_entry')
    def test_memory_statistics_enable(self, mock_mod_entry):
        # Simulate initial state as disabled
        self.mock_db.get_table.return_value["memory_statistics"]["enabled"] = "false"
        result = self.runner.invoke(memory_statistics_enable)
        self.assertIn("Memory Statistics feature enabled.", result.output)
        self.assertEqual(result.exit_code, 0)

        # Ensure the entry was modified correctly
        mock_mod_entry.assert_called_once_with("MEMORY_STATISTICS", "memory_statistics", {"enabled": "true", "disabled": "false"})

    @patch.object(ConfigDBConnector, 'mod_entry')
    def test_memory_statistics_disable(self, mock_mod_entry):
        # Simulate initial state as enabled
        self.mock_db.get_table.return_value["memory_statistics"]["enabled"] = "true"
        result = self.runner.invoke(memory_statistics_disable)
        self.assertIn("Memory Statistics feature disabled.", result.output)
        self.assertEqual(result.exit_code, 0)

        # Ensure the entry was modified correctly
        mock_mod_entry.assert_called_once_with("MEMORY_STATISTICS", "memory_statistics", {"enabled": "false", "disabled": "true"})

    @patch.object(ConfigDBConnector, 'mod_entry')
    def test_memory_statistics_retention_period(self, mock_mod_entry):
        retention_period = 15
        result = self.runner.invoke(memory_statistics_retention_period, [str(retention_period)])
        self.assertIn(f"Memory Statistics retention period set to {retention_period} days.", result.output)
        self.assertEqual(result.exit_code, 0)

        # Ensure the entry was modified correctly
        mock_mod_entry.assert_called_once_with("MEMORY_STATISTICS", "memory_statistics", {"retention_period": retention_period})

    @patch.object(ConfigDBConnector, 'mod_entry')
    def test_memory_statistics_sampling_interval(self, mock_mod_entry):
        sampling_interval = 5
        result = self.runner.invoke(memory_statistics_sampling_interval, [str(sampling_interval)])
        self.assertIn(f"Memory Statistics sampling interval set to {sampling_interval} minutes.", result.output)
        self.assertEqual(result.exit_code, 0)

        # Ensure the entry was modified correctly
        mock_mod_entry.assert_called_once_with("MEMORY_STATISTICS", "memory_statistics", {"sampling_interval": sampling_interval})


if __name__ == "__main__":
    unittest.main()
