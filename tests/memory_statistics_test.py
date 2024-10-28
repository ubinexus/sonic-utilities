import unittest
from unittest.mock import patch
from click.testing import CliRunner
from config.memory_statistics import (
    memory_statistics_enable,
    memory_statistics_disable,
    memory_statistics_retention_period,
    memory_statistics_sampling_interval
)
from swsscommon.swsscommon import ConfigDBConnector


class TestMemoryStatisticsConfigCommands(unittest.TestCase):

    @patch.object(ConfigDBConnector, 'mod_entry')
    @patch.object(ConfigDBConnector, 'get_entry')
    def setUp(self, mock_get_entry, mock_mod_entry):
        self.runner = CliRunner()
        self.db = ConfigDBConnector()
        self.db.connect()

        # Mock the return value of get_entry
        mock_get_entry.return_value = {
            "enabled": "false",
            "retention_period": "15",
            "sampling_interval": "5"
        }

        # Ensure a clean state in the MEMORY_STATISTICS table before each test
        self.db.mod_entry("MEMORY_STATISTICS", "memory_statistics", {
            "enabled": "false",
            "retention_period": "15",
            "sampling_interval": "5"
        })

    def tearDown(self):
        # Clean up after each test to avoid side effects
        self.db.mod_entry("MEMORY_STATISTICS", "memory_statistics", {
            "enabled": "false",
            "retention_period": "15",
            "sampling_interval": "5"
        })

    @patch.object(ConfigDBConnector, 'get_entry', return_value={"enabled": "true"})
    def test_memory_statistics_enable(self, mock_get_entry):
        result = self.runner.invoke(memory_statistics_enable)
        self.assertIn("Memory Statistics feature enabled.", result.output)
        self.assertEqual(result.exit_code, 0)

    @patch.object(ConfigDBConnector, 'get_entry', return_value={"enabled": "false"})
    def test_memory_statistics_disable(self, mock_get_entry):
        result = self.runner.invoke(memory_statistics_disable)
        self.assertIn("Memory Statistics feature disabled.", result.output)
        self.assertEqual(result.exit_code, 0)

    @patch.object(ConfigDBConnector, 'get_entry', return_value={"retention_period": "15"})
    def test_memory_statistics_retention_period(self, mock_get_entry):
        result = self.runner.invoke(memory_statistics_retention_period, ['15'])
        self.assertIn("Memory Statistics retention period set to 15 days.", result.output)
        self.assertEqual(result.exit_code, 0)

    @patch.object(ConfigDBConnector, 'get_entry', return_value={"sampling_interval": "5"})
    def test_memory_statistics_sampling_interval(self, mock_get_entry):
        result = self.runner.invoke(memory_statistics_sampling_interval, ['5'])
        self.assertIn("Memory Statistics sampling interval set to 5 minutes.", result.output)
        self.assertEqual(result.exit_code, 0)
