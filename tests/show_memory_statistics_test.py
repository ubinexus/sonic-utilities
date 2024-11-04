import os
import pytest
from click.testing import CliRunner

# Adjust the import to reflect the correct path to the memory_statistics module
from show.memory_statistics import memory_statistics

EXPECTED_CONFIG_OUTPUT = """Memory Statistics administrative mode: Disabled
Memory Statistics retention time (days): 15
Memory Statistics sampling interval (minutes): 5
"""

@pytest.fixture()
def setup_teardown_single_asic():
    os.environ["UTILITIES_UNIT_TESTING"] = "1"
    yield
    os.environ["UTILITIES_UNIT_TESTING"] = "0"

class TestShowMemoryStatisticsSingleASIC(object):
    def test_memory_statistics_config(self, setup_teardown_single_asic):
        runner = CliRunner()
        result = runner.invoke(memory_statistics, ["config"])

        # Ensure command ran successfully
        assert result.exit_code == 0
        assert result.output.strip() == EXPECTED_CONFIG_OUTPUT.strip()

    def test_memory_statistics_logs_no_filter(self, setup_teardown_single_asic):
        runner = CliRunner()
        result = runner.invoke(memory_statistics, ["logs"])

        # Ensure command ran successfully
        assert result.exit_code == 0
        expected_logs_output = "No memory statistics available for the given parameters."
        assert result.output.strip() == expected_logs_output

    def test_memory_statistics_logs_with_filter(self, setup_teardown_single_asic):
        runner = CliRunner()
        result = runner.invoke(memory_statistics, ["logs", "2024-01-01", "2024-01-31"])

        # Ensure command ran successfully
        assert result.exit_code == 0
        expected_logs_output = """Time      Statistic   Value
        ---------  ----------  ------
        2024-01-10 memory      85%"""
        assert result.output.strip() == expected_logs_output.strip()
