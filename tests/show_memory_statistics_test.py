from click.testing import CliRunner
from unittest.mock import patch

from show import memory_statistics


class MockConfigDBConnector:
    def __init__(self, data):
        self.data = data

    def connect(self):
        pass  # Mock connection

    def get_table(self, table_name):
        return self.data.get(table_name, {})


# Test case for `show memory-statistics config` command
def test_show_memory_statistics_config():
    # Prepare mock data for memory statistics config
    mock_data = {
        "MEMORY_STATISTICS": {
            "memory_statistics": {
                "enabled": "true",
                "retention_time": "10",
                "sampling_interval": "15"
            }
        }
    }

    # Create a mock database connector with the prepared data
    mock_db = MockConfigDBConnector(data=mock_data)

    # Use CliRunner to invoke the CLI command with the mock database
    runner = CliRunner()
    result = runner.invoke(memory_statistics.config, obj={"db_connector": mock_db})

    # Assertions to verify the output matches the mock data
    assert result.exit_code == 0
    assert "Memory Statistics administrative mode: Enabled" in result.output
    assert "Memory Statistics retention time (days): 10" in result.output
    assert "Memory Statistics sampling interval (minutes): 15" in result.output


# Test case for `show memory-statistics logs` command
def test_show_memory_statistics_logs():
    # Prepare mock data with some example log entries
    mock_data = {
        "MEMORY_STATISTICS": {
            "log1": {"time": "2024-11-04 10:00:00", "statistic": "Usage", "value": "512 MB"},
            "log2": {"time": "2024-11-04 10:05:00", "statistic": "Usage", "value": "514 MB"},
        }
    }

    # Create a mock database connector with the prepared data
    mock_db = MockConfigDBConnector(data=mock_data)

    # Use CliRunner to invoke the CLI command with the mock database
    runner = CliRunner()
    result = runner.invoke(memory_statistics.show_memory_statistics_logs, obj={"db_connector": mock_db})

    # Assertions to verify the output matches the mock data
    assert result.exit_code == 0
    assert "2024-11-04 10:00:00" in result.output
    assert "Usage" in result.output
    assert "512 MB" in result.output
    assert "514 MB" in result.output
