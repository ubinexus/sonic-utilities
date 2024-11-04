from click.testing import CliRunner

from show.memory_statistics import memory_statistics


class MockConfigDBConnector:
    def __init__(self, data):
        self.data = data

    def get_table(self, table_name):
        return self.data.get(table_name, {})


def test_show_memory_statistics_logs():
    # Prepare mock data with some example log entries
    mock_data = {
        "MEMORY_STATISTICS": {
            "memory_statistics": {
                "log1": {"time": "2024-11-04 10:00:00", "statistic": "Usage", "value": "512 MB"},
                "log2": {"time": "2024-11-04 10:05:00", "statistic": "Usage", "value": "514 MB"},
            }
        }
    }

    # Create a mock database connector with the prepared data
    mock_db = MockConfigDBConnector(data=mock_data)

    # Use CliRunner to invoke the CLI command with the mock database
    runner = CliRunner()
    result = runner.invoke(memory_statistics.show_memory_statistics_logs,
                           ["--starting_time", "2024-11-04 09:00:00", "--ending_time", "2024-11-04 11:00:00"],
                           obj={"db_connector": mock_db})

    # Assertions to verify the output matches the mock data
    assert result.exit_code == 0
    assert "Memory Statistics logs" in result.output  # Adjust according to expected output


def test_show_memory_statistics_config():
    # Prepare mock data for configuration
    mock_data = {
        "MEMORY_STATISTICS": {
            "memory_statistics": {
                "enabled": "true",
                "retention_period": "30",
                "sampling_interval": "10",
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
    assert "Memory Statistics retention time (days): 30" in result.output
    assert "Memory Statistics sampling interval (minutes): 10" in result.output
