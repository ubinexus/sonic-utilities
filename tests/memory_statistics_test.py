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
        self.mock_db.get_entry.return_value = {
            "enabled": "false",
            "retention_period": "15",
            "sampling_interval": "5"
        }
        self.patcher = patch.object(ConfigDBConnector, 'get_entry', self.mock_db.get_entry)
        self.patcher.start()

        # Mock the get_memory_statistics_table to return a valid table
        self.mock_db.get_table = MagicMock(return_value={"memory_statistics": {}})
        patch.object(ConfigDBConnector, 'get_table', self.mock_db.get_table).start()

    def tearDown(self):
        self.patcher.stop()

    @patch.object(ConfigDBConnector, 'mod_entry')
    def test_memory_statistics_enable(self, mock_mod_entry):
        # Change the return value to simulate a disabled state
        self.mock_db.get_entry.return_value = {"enabled": "false"}
        result = self.runner.invoke(memory_statistics_enable)
        self.assertIn("Memory Statistics feature enabled.", result.output)
        self.assertEqual(result.exit_code, 0)

        # Ensure the entry was modified correctly
        mock_mod_entry.assert_called_once_with(
            "MEMORY_STATISTICS",
            "memory_statistics",
            {"enabled": "true", "disabled": "false"}
        )

    @patch.object(ConfigDBConnector, 'mod_entry')
    def test_memory_statistics_disable(self, mock_mod_entry):
        # Change the return value to simulate an enabled state
        self.mock_db.get_entry.return_value = {"enabled": "true"}
        result = self.runner.invoke(memory_statistics_disable)
        self.assertIn("Memory Statistics feature disabled.", result.output)
        self.assertEqual(result.exit_code, 0)

        # Ensure the entry was modified correctly
        mock_mod_entry.assert_called_once_with(
            "MEMORY_STATISTICS",
            "memory_statistics",
            {"enabled": "false", "disabled": "true"}
        )

    @patch.object(ConfigDBConnector, 'mod_entry')
    def test_memory_statistics_retention_period(self, mock_mod_entry):
        result = self.runner.invoke(memory_statistics_retention_period, ['15'])
        self.assertIn("Memory Statistics retention period set to 15 days.", result.output)
        self.assertEqual(result.exit_code, 0)

        # Ensure the entry was modified correctly
        mock_mod_entry.assert_called_once_with(
            "MEMORY_STATISTICS",
            "memory_statistics",
            {"retention_period": 15}
        )

    @patch.object(ConfigDBConnector, 'mod_entry')
    def test_memory_statistics_sampling_interval(self, mock_mod_entry):
        result = self.runner.invoke(memory_statistics_sampling_interval, ['5'])
        self.assertIn("Memory Statistics sampling interval set to 5 minutes.", result.output)
        self.assertEqual(result.exit_code, 0)

        # Ensure the entry was modified correctly
        mock_mod_entry.assert_called_once_with(
            "MEMORY_STATISTICS",
            "memory_statistics",
            {"sampling_interval": 5}
        )

    # Missing test cases from the old file
    @patch.object(ConfigDBConnector, 'mod_entry')
    def test_memory_statistics_enable_already_enabled(self, mock_mod_entry):
        self.mock_db.get_entry.return_value = {"enabled": "true"}
        result = self.runner.invoke(memory_statistics_enable)
        self.assertIn("Memory Statistics feature enabled.", result.output)
        self.assertEqual(result.exit_code, 0)

        # Ensure the entry was modified correctly
        mock_mod_entry.assert_not_called()

    @patch.object(ConfigDBConnector, 'mod_entry')
    def test_memory_statistics_disable_already_disabled(self, mock_mod_entry):
        self.mock_db.get_entry.return_value = {"enabled": "false"}
        result = self.runner.invoke(memory_statistics_disable)
        self.assertIn("Memory Statistics feature disabled.", result.output)
        self.assertEqual(result.exit_code, 0)

        # Ensure the entry was modified correctly
        mock_mod_entry.assert_not_called()


if __name__ == "__main__":
    unittest.main()
