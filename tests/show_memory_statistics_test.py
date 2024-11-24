# import os
# import pytest
# import socket
# import json
# from unittest import mock
# from click.testing import CliRunner
# from dataclasses import dataclass
# import show.memory_statistics


# from show.memory_statistics import (
#     Config,
#     SonicDBConnector,
#     SocketManager,
#     Dict2Obj,
#     show
# )


# @dataclass
# class MockDb:
#     """Mock database for testing"""
#     def __init__(self):
#         self.data = {}

#     def get_table(self, table_name):
#         return self.data.get(table_name, {})

#     def set_entry(self, table_name, key, values):
#         if table_name not in self.data:
#             self.data[table_name] = {}
#         self.data[table_name][key] = values


# class TestMemoryStatistics:
#     @classmethod
#     def setup_class(cls):
#         print("SETUP")
#         os.environ['UTILITIES_UNIT_TESTING'] = "1"

#     @pytest.fixture
#     def mock_config_db(self):
#         """Fixture to provide a mock config database"""
#         db = MockDb()
#         db.set_entry("MEMORY_STATISTICS", "memory_statistics", {
#             "enabled": "true",
#             "retention_period": "7",
#             "sampling_interval": "1"
#         })
#         return db

#     @pytest.fixture
#     def mock_socket_response(self):
#         """Fixture to provide mock socket response data"""
#         return {
#             "status": True,
#             "data": "Memory Usage: 1000MB\nFree Memory: 500MB"
#         }

#     def test_dict2obj_conversion(self):
#         """Test Dict2Obj conversion functionality"""
#         test_dict = {
#             "key1": "value1",
#             "key2": {
#                 "nested_key": "nested_value"
#             },
#             "key3": ["item1", "item2"]
#         }
#         obj = Dict2Obj(test_dict)
#         assert hasattr(obj, "key1")
#         assert obj.key1 == "value1"
#         assert obj.key2.nested_key == "nested_value"
#         assert isinstance(obj.key3, list)

#         converted_dict = obj.to_dict()
#         assert converted_dict == test_dict

#     @mock.patch('memory_statistics.ConfigDBConnector')
#     def test_sonic_db_connector(self, mock_config_db):
#         """Test SonicDBConnector initialization and config retrieval"""
#         mock_config_db.return_value.get_table.return_value = {
#             'memory_statistics': {
#                 'enabled': 'true',
#                 'retention_period': '7',
#                 'sampling_interval': '1'
#             }
#         }

#         db_connector = SonicDBConnector()
#         config = db_connector.get_memory_statistics_config()

#         assert config['enabled'] == 'true'
#         assert config['retention_period'] == '7'
#         assert config['sampling_interval'] == '1'

#     @mock.patch('socket.socket')
#     def test_socket_manager_connection(self, mock_socket):
#         """Test SocketManager connection handling"""
#         socket_manager = SocketManager()
#         socket_manager.connect()

#         mock_socket.assert_called_once()
#         mock_socket.return_value.connect.assert_called_once_with(Config.SOCKET_PATH)

#         mock_socket.reset_mock()
#         mock_socket.return_value.connect.side_effect = [socket.error, None]
#         socket_manager = SocketManager()
#         socket_manager.connect()
#         assert mock_socket.call_count == 2

#     def test_show_memory_stats_basic(self, mock_config_db, mock_socket_response):
#         """Test basic memory statistics display"""
#         runner = CliRunner()

#         with mock.patch('socket.socket') as mock_socket:
#             mock_sock = mock_socket.return_value
#             mock_sock.recv.return_value = json.dumps(mock_socket_response).encode('utf-8')

#             result = runner.invoke(show, ['memory-stats'])
#             assert result.exit_code == 0
#             assert "Memory Usage" in result.output

#     def test_show_memory_stats_with_timerange(self, mock_config_db, mock_socket_response):
#         """Test memory statistics display with time range parameters"""
#         runner = CliRunner()

#         with mock.patch('socket.socket') as mock_socket:
#             mock_sock = mock_socket.return_value
#             mock_sock.recv.return_value = json.dumps(mock_socket_response).encode('utf-8')

#             result = runner.invoke(show, [
#                 'memory-stats',
#                 '--from', '2024-01-01',
#                 '--to', '2024-01-02'
#             ])
#             assert result.exit_code == 0
#             assert "Memory Usage" in result.output

#     def test_show_config(self, mock_config_db):
#         """Test configuration display functionality"""
#         runner = CliRunner()

#         with mock.patch('memory_statistics.SonicDBConnector') as mock_db:
#             mock_db.return_value.get_memory_statistics_config.return_value = {
#                 'enabled': 'true',
#                 'retention_period': '7',
#                 'sampling_interval': '1'
#             }

#             result = runner.invoke(show, ['memory-stats', '--config'])
#             assert result.exit_code == 0
#             assert 'Enabled' in result.output
#             assert 'True' in result.output
#             assert '7' in result.output
#             assert '1' in result.output

#     def test_socket_error_handling(self, mock_config_db):
#         """Test socket error handling"""
#         runner = CliRunner()

#         with mock.patch('socket.socket') as mock_socket:
#             mock_socket.return_value.connect.side_effect = socket.error("Connection refused")

#             result = runner.invoke(show, ['memory-stats'])
#             assert result.exit_code != 0
#             assert "Error" in result.output

#     def test_invalid_command(self):
#         """Test handling of invalid commands"""
#         runner = CliRunner()
#         result = runner.invoke(show, ['invalid-command'])
#         assert result.exit_code != 0
#         assert "Error" in result.output

#     @classmethod
#     def teardown_class(cls):
#         print("TEARDOWN")
#         os.environ['UTILITIES_UNIT_TESTING'] = "0"


# if __name__ == '__main__':
#     pytest.main([__file__])


# import pytest
# import json
# from unittest.mock import patch
# from click.testing import CliRunner
# from show.memory_statistics import cli, send_data  # Correct module import

# # Mock configuration data for tests
# MEMORY_STATS_CONFIG = {
#     "memory_statistics": {
#         "enabled": "true",
#         "sampling_interval": "5",
#         "retention_period": "15"
#     }
# }


# @pytest.fixture
# def mock_config_db():
#     """Mock SONiC ConfigDB connection and data retrieval."""
#     with patch('my_cli_tool.ConfigDBConnector') as mock_connector:
#         mock_instance = mock_connector.return_value
#         mock_instance.connect.return_value = None
#         mock_instance.get_table.return_value = MEMORY_STATS_CONFIG
#         yield mock_instance


# @pytest.fixture
# def mock_socket_manager():
#     with patch('show.memory_statistics.SocketManager') as mock_socket:  # Updated path
#         mock_instance = mock_socket.return_value
#         mock_instance.connect.return_value = None
#         mock_instance.receive_all.return_value = json.dumps({
#             "status": True,
#             "data": "Sample memory data output"
#         })
#         yield mock_instance


# def test_socket_connection_failure():
#     """Test socket connection failure handling."""
#     with patch('my_cli_tool.SocketManager.connect', side_effect=ConnectionError("Connection failed")):
#         with pytest.raises(ConnectionError):
#             send_data("memory_statistics_command_request_handler", {})


# def test_invalid_command():
#     runner = CliRunner()
#     result = runner.invoke(cli, ['invalid-command'])
#     assert result.exit_code != 0
#     assert "No such command" in result.output  # Updated assertion


# def test_missing_socket_response(mock_socket_manager):
#     """Test handling of empty socket responses."""
#     mock_socket_manager.receive_all.return_value = ""

#     with pytest.raises(ConnectionError, match="No response received from memory statistics service"):
#         send_data("memory_statistics_command_request_handler", {})


# def test_invalid_json_response(mock_socket_manager):
#     """Test handling of invalid JSON responses from socket."""
#     mock_socket_manager.receive_all.return_value = "Invalid JSON"

#     with pytest.raises(ValueError, match="Failed to parse server response"):
#         send_data("memory_statistics_command_request_handler", {})


import pytest
import json
from unittest.mock import patch
from click.testing import CliRunner
from show.memory_statistics import cli, send_data

# Mock configuration data for tests
MEMORY_STATS_CONFIG = {
    "memory_statistics": {
        "enabled": "true",
        "sampling_interval": "5",
        "retention_period": "15"
    }
}


@pytest.fixture
def mock_config_db():
    """Mock SONiC ConfigDB connection and data retrieval."""
    with patch('show.memory_statistics.ConfigDBConnector') as mock_connector:
        mock_instance = mock_connector.return_value
        mock_instance.connect.return_value = None
        mock_instance.get_table.return_value = MEMORY_STATS_CONFIG
        yield mock_instance


@pytest.fixture
def mock_socket_manager():
    """Mock SocketManager class for successful responses."""
    with patch('show.memory_statistics.SocketManager') as mock_socket:
        mock_instance = mock_socket.return_value
        mock_instance.connect.return_value = None
        mock_instance.receive_all.return_value = json.dumps({
            "status": True,
            "data": "Sample memory data output"
        })
        yield mock_instance


def test_socket_connection_failure():
    """Test handling of socket connection failures."""
    with patch('show.memory_statistics.SocketManager.connect', side_effect=ConnectionError("Connection failed")):
        with pytest.raises(ConnectionError, match="Connection failed"):
            send_data("memory_statistics_command_request_handler", {})


def test_invalid_command():
    """Test CLI handling of invalid commands."""
    runner = CliRunner()
    result = runner.invoke(cli, ['invalid-command'])

    assert result.exit_code != 0
    assert "No such command" in result.output


def test_missing_socket_response(mock_socket_manager):
    """Test handling when no response is received from the socket."""
    mock_socket_manager.receive_all.return_value = ""

    with pytest.raises(ConnectionError, match="No response received from memory statistics service"):
        send_data("memory_statistics_command_request_handler", {})


def test_invalid_json_response(mock_socket_manager):
    """Test handling of invalid JSON responses from the socket."""
    mock_socket_manager.receive_all.return_value = "Invalid JSON"

    with pytest.raises(ValueError, match="Failed to parse server response"):
        send_data("memory_statistics_command_request_handler", {})


def test_valid_response(mock_socket_manager):
    """Test valid socket response handling."""
    response = send_data("memory_statistics_command_request_handler", {})
    assert response['status'] is True
    assert response['data'] == "Sample memory data output"
