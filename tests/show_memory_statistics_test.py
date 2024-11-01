import os
import pytest
from click.testing import CliRunner
from importlib import reload

# Import the show module for memory statistics
import memory_statistics_show

# Define expected output for testing
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
        result = runner.invoke(memory_statistics_show.memory_statistics.commands["config"])
        
        # Ensure command ran successfully
        assert result.exit_code == 0
        # Check that output matches expected configuration output
        assert result.output.strip() == EXPECTED_CONFIG_OUTPUT.strip()

    def test_memory_statistics_logs_no_filter(self, setup_teardown_single_asic):
        runner = CliRunner()
        result = runner.invoke(memory_statistics_show.memory_statistics.commands["logs"])
        
        # Ensure command ran successfully
        assert result.exit_code == 0
        # Adjust expected output based on your memory statistics mock data
        expected_logs_output = "No memory statistics available for the given parameters."
        assert result.output.strip() == expected_logs_output

    def test_memory_statistics_logs_with_filter(self, setup_teardown_single_asic):
        runner = CliRunner()
        result = runner.invoke(memory_statistics_show.memory_statistics.commands["logs"], ["2024-01-01", "2024-01-31"])
        
        # Ensure command ran successfully
        assert result.exit_code == 0
        # Define the expected output based on your memory statistics data format
        expected_logs_output = """Time      Statistic   Value
        ---------  ----------  ------
        2024-01-10 memory      85%"""
        # Modify assertions based on the real output format
        assert result.output.strip() == expected_logs_output.strip()
