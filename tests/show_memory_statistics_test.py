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


def test_send_data_success(mock_socket):
    """Test send_data with a valid response."""
    mock_response = {"status": True, "data": "Test data"}
    mock_socket.recv.return_value = json.dumps(mock_response).encode("utf-8")

    response = send_data("test_command", {"key": "value"})
    assert response.to_dict() == mock_response
