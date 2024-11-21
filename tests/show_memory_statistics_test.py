import pytest
from unittest.mock import patch, MagicMock
from click.testing import CliRunner
from show.memory_statistics import send_data, cli
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


def test_send_data_success(mock_socket):
    """Test send_data with a valid response."""
    mock_response = {"status": True, "data": "Test data"}
    mock_socket.recv.return_value = json.dumps(mock_response).encode("utf-8")

    response = send_data("test_command", {"key": "value"})
    assert response.to_dict() == mock_response


def test_cli_db_connector_attribute_error(runner):
    """Test cli group when clicommon.get_db_connector raises AttributeError."""
    # Mock the entire `utilities_common.cli` module dynamically
    mock_clicommon = MagicMock()
    del mock_clicommon.get_db_connector  # Ensure get_db_connector doesn't exist

    with patch.dict("sys.modules", {"utilities_common.cli": mock_clicommon}), \
         patch("syslog.syslog") as mock_syslog:

        # Run the CLI
        result = runner.invoke(cli)

        # Validate outputs
        expected_error_msg = "Error: 'utilities_common.cli' does not have 'get_db_connector' function."
        assert expected_error_msg in result.output
        mock_syslog.assert_called_once_with(syslog.LOG_ERR, expected_error_msg)
        assert result.exit_code == 1