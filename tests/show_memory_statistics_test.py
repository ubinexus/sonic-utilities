import pytest
from unittest.mock import patch
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
    with patch("utilities_common.cli", autospec=True) as mock_clicommon:
        # Dynamically add `get_db_connector` to the mock module
        get_db_connector_patch = patch(
            "utilities_common.cli.get_db_connector", side_effect=AttributeError
        )
        mock_clicommon.get_db_connector = get_db_connector_patch.start()

        with patch("syslog.syslog") as mock_syslog:
            result = runner.invoke(cli)
            assert "Error: 'utilities_common.cli' does not have 'get_db_connector' function." in result.output
            mock_syslog.assert_called_with(
                3, "Error: 'utilities_common.cli' does not have 'get_db_connector' function."
            )
            assert result.exit_code == 1
