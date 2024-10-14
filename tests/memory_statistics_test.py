import unittest
from click.testing import CliRunner
from config.memory_statistics import memory_statistics_enable
from config.memory_statistics import memory_statistics_disable
from config.memory_statistics import memory_statistics_retention_period
from config.memory_statistics import memory_statistics_sampling_interval
from show.memory_statistics import config, show_memory_statistics_logs


class TestMemoryStatisticsConfigCommands(unittest.TestCase):

    def setUp(self):
        self.runner = CliRunner()

    def test_memory_statistics_enable(self):
        result = self.runner.invoke(memory_statistics_enable)
        self.assertIn("Memory Statistics feature enabled.", result.output)
        self.assertEqual(result.exit_code, 0)

    def test_memory_statistics_disable(self):
        result = self.runner.invoke(memory_statistics_disable)
        self.assertIn("Memory Statistics feature disabled.", result.output)
        self.assertEqual(result.exit_code, 0)

    def test_memory_statistics_retention_period(self):
        result = self.runner.invoke(memory_statistics_retention_period, ['30'])
        self.assertIn("Memory Statistics retention period set to 30 days.", result.output)
        self.assertEqual(result.exit_code, 0)

    def test_memory_statistics_sampling_interval(self):
        result = self.runner.invoke(memory_statistics_sampling_interval, ['5'])
        self.assertIn("Memory Statistics sampling interval set to 5 minutes.", result.output)
        self.assertEqual(result.exit_code, 0)


class TestMemoryStatisticsShowCommands(unittest.TestCase):

    def setUp(self):
        self.runner = CliRunner()

    def test_memory_statistics_config(self):
        result = self.runner.invoke(config)
        self.assertIn("Memory Statistics administrative mode:", result.output)
        self.assertEqual(result.exit_code, 0)

    def test_memory_statistics_logs(self):
        result = self.runner.invoke(show_memory_statistics_logs, ['2023-10-01', '2023-10-02'])
        self.assertIn("Memory Statistics logs", result.output)
        self.assertEqual(result.exit_code, 0)


if __name__ == '__main__':
    unittest.main()
