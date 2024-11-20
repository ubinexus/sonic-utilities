import pytest
from unittest.mock import patch, MagicMock
from click.testing import CliRunner
import json
import click
from show.memory_statistics import cli, Dict2Obj, send_data, clean_and_print


@pytest.fixture
def runner():
    """Fixture for CLI Runner."""
    return CliRunner()


@pytest.fixture
def mock_socket():
    """Fixture for patching socket connection."""
    with patch("socket.socket") as MockSocket:
        mock_socket_instance = MockSocket.return_value
        yield mock_socket_instance


def test_memory_stats_no_arguments(runner, mock_socket):
    """Test 'show memory-stats' with no arguments."""
    mock_response = {"status": True, "data": "Sample memory stats data"}
    mock_socket.recv.return_value = json.dumps(mock_response).encode("utf-8")

    with patch("show.memory_statistics.send_data", return_value=Dict2Obj(mock_response)) as mock_send_data:
        result = runner.invoke(cli, ["show", "memory-stats"])
        assert result.exit_code == 0
        assert "Memory Statistics" in result.output
        assert "Sample memory stats data" in result.output
        mock_send_data.assert_called_once_with("memory_statistics_command_request_handler", {
            "type": "system", "metric_name": None, "from": None, "to": None
        })


def test_memory_stats_with_arguments(runner, mock_socket):
    """Test 'show memory-stats' with valid arguments."""
    mock_response = {"status": True, "data": "Filtered memory stats"}
    mock_socket.recv.return_value = json.dumps(mock_response).encode("utf-8")

    with patch("show.memory_statistics.send_data", return_value=Dict2Obj(mock_response)) as mock_send_data:
        result = runner.invoke(cli, ["show", "memory-stats", "from", "2023-01-01", "to", "2023-01-02", "select", "cpu"])
        assert result.exit_code == 0
        assert "Filtered memory stats" in result.output
        mock_send_data.assert_called_once_with("memory_statistics_command_request_handler", {
            "type": "system",
            "metric_name": "cpu",
            "from": "2023-01-01",
            "to": "2023-01-02"
        })


def test_memory_stats_invalid_keyword(runner):
    """Test 'show memory-stats' with an invalid keyword."""
    result = runner.invoke(cli, ["show", "memory-stats", "invalid"])
    assert result.exit_code != 0
    assert "Error: Expected 'from' keyword as the first argument." in result.output


def test_memory_statistics_config_valid(runner, mock_socket):
    """Test 'show memory-statistics config' with valid configuration."""
    mock_db_connector = MagicMock()
    mock_db_connector.get_table.return_value = {
        "memory_statistics": {
            "enabled": "true",
            "retention_period": "7",
            "sampling_interval": "5"
        }
    }

    with patch("utilities_common.cli.get_db_connector", return_value=mock_db_connector):
        result = runner.invoke(cli, ["show", "memory-statistics", "config"])
        assert result.exit_code == 0
        assert "Enabled" in result.output
        assert "True" in result.output
        assert "Retention Time (days)" in result.output
        assert "7" in result.output
        assert "Sampling Interval (minutes)" in result.output
        assert "5" in result.output


def test_memory_statistics_config_db_error(runner):
    """Test 'show memory-statistics config' when database connector fails."""
    with patch("utilities_common.cli.get_db_connector", side_effect=Exception("DB error")):
        result = runner.invoke(cli, ["show", "memory-statistics", "config"])
        assert result.exit_code != 0
        assert "Error retrieving configuration: DB error" in result.output


def test_send_data_success(mock_socket):
    """Test send_data with a valid response."""
    mock_response = {"status": True, "data": "Test data"}
    mock_socket.recv.return_value = json.dumps(mock_response).encode("utf-8")

    response = send_data("test_command", {"key": "value"})
    assert response.to_dict() == mock_response


def test_send_data_failure(mock_socket):
    """Test send_data with a failure response."""
    mock_socket.recv.return_value = b""

    with pytest.raises(click.Abort) as excinfo:
        send_data("test_command", {"key": "value"})
    assert "No response from the server" in str(excinfo.value)


def test_clean_and_print_valid():
    """Test clean_and_print with valid data."""
    data = {"data": "Sample memory stats"}
    with patch("builtins.print") as mock_print:
        clean_and_print(data)
        mock_print.assert_any_call("Memory Statistics:\nSample memory stats")


def test_clean_and_print_invalid():
    """Test clean_and_print with invalid data format."""
    data = "Invalid data format"
    with patch("builtins.print") as mock_print:
        clean_and_print(data)
        mock_print.assert_called_once_with("Error: Invalid data format.")
