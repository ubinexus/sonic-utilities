import unittest
from unittest.mock import patch
from click.testing import CliRunner
from show.memory_statistics import cli


class TestShowCLI(unittest.TestCase):
    def setUp(self):
        self.runner = CliRunner()

    @patch("show.clicommon.get_db_connector", return_value={"dummy_key": "dummy_value"})
    def test_memory_stats_valid(self, mock_get_db_connector):
        result = self.runner.invoke(
            cli,
            [
                "show", "memory-stats", "from", "'2023-11-01'",
                "to", "'2023-11-02'", "select", "'used_memory'"
            ]
        )
        print(result.output)  # Debugging
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Memory Statistics fetched successfully.", result.output)

    @patch("show.clicommon.get_db_connector", return_value={"dummy_key": "dummy_value"})
    def test_memory_stats_invalid_from_keyword(self, mock_get_db_connector):
        result = self.runner.invoke(cli, ["show", "memory-stats", "from_invalid", "'2023-11-01'"])
        print(result.output)  # Debugging
        self.assertNotEqual(result.exit_code, 0)
        self.assertIn("Expected 'from' keyword as the first argument.", result.output)

    @patch("show.clicommon.get_db_connector", return_value={"dummy_key": "dummy_value"})
    def test_memory_statistics_config(self, mock_get_db_connector):
        result = self.runner.invoke(cli, ["show", "memory-statistics", "config"])
        print(result.output)  # Debugging
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Enabled", result.output)
        self.assertIn("Retention Time (days)", result.output)
        self.assertIn("Sampling Interval (minutes)", result.output)


if __name__ == "__main__":
    unittest.main()
