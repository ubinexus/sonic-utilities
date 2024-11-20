import pytest
from unittest.mock import patch, Mock
from click.testing import CliRunner
from show.memory_statistics import cli, Dict2Obj, send_data
import json


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
    # Mock response data
    mock_response = {"status": True, "data": "Sample memory stats data"}
    mock_socket.recv.return_value = json.dumps(mock_response).encode("utf-8")

    # Patch the necessary methods and functions
    with patch("show.memory_statistics.send_data", return_value=Dict2Obj(mock_response)) as mock_send_data, \
         patch("utilities_common.cli", create=True) as mock_cli:  # Mock the entire cli module if needed

        # Mock `get_db_connector` only if it's accessed in the CLI execution
        mock_cli.get_db_connector = Mock(return_value=Mock())

        # Invoke the CLI command
        result = runner.invoke(cli, ["show", "memory-stats"])

        # Debugging outputs for troubleshooting
        print(f"Exit code: {result.exit_code}")
        print(f"Output: {result.output}")

        # Assertions
        assert result.exit_code == 0, f"Expected exit code 0 but got {result.exit_code}"
        assert "Memory Statistics" in result.output
        assert "Sample memory stats data" in result.output
        mock_send_data.assert_called_once_with(
            "memory_statistics_command_request_handler",
            {"type": "system", "metric_name": None, "from": None, "to": None},
        )


def test_send_data_success(mock_socket):
    """Test send_data with a valid response."""
    mock_response = {"status": True, "data": "Test data"}
    mock_socket.recv.return_value = json.dumps(mock_response).encode("utf-8")

    response = send_data("test_command", {"key": "value"})
    assert response.to_dict() == mock_response
