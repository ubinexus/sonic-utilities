# # import os
# # import pytest
# # import socket
# # import json
# # from unittest import mock
# # from click.testing import CliRunner
# # from dataclasses import dataclass
# # import show.memory_statistics


# # from show.memory_statistics import (
# #     Config,
# #     SonicDBConnector,
# #     SocketManager,
# #     Dict2Obj,
# #     show
# # )


# # @dataclass
# # class MockDb:
# #     """Mock database for testing"""
# #     def __init__(self):
# #         self.data = {}

# #     def get_table(self, table_name):
# #         return self.data.get(table_name, {})

# #     def set_entry(self, table_name, key, values):
# #         if table_name not in self.data:
# #             self.data[table_name] = {}
# #         self.data[table_name][key] = values


# # class TestMemoryStatistics:
# #     @classmethod
# #     def setup_class(cls):
# #         print("SETUP")
# #         os.environ['UTILITIES_UNIT_TESTING'] = "1"

# #     @pytest.fixture
# #     def mock_config_db(self):
# #         """Fixture to provide a mock config database"""
# #         db = MockDb()
# #         db.set_entry("MEMORY_STATISTICS", "memory_statistics", {
# #             "enabled": "true",
# #             "retention_period": "7",
# #             "sampling_interval": "1"
# #         })
# #         return db

# #     @pytest.fixture
# #     def mock_socket_response(self):
# #         """Fixture to provide mock socket response data"""
# #         return {
# #             "status": True,
# #             "data": "Memory Usage: 1000MB\nFree Memory: 500MB"
# #         }

# #     def test_dict2obj_conversion(self):
# #         """Test Dict2Obj conversion functionality"""
# #         test_dict = {
# #             "key1": "value1",
# #             "key2": {
# #                 "nested_key": "nested_value"
# #             },
# #             "key3": ["item1", "item2"]
# #         }
# #         obj = Dict2Obj(test_dict)
# #         assert hasattr(obj, "key1")
# #         assert obj.key1 == "value1"
# #         assert obj.key2.nested_key == "nested_value"
# #         assert isinstance(obj.key3, list)

# #         converted_dict = obj.to_dict()
# #         assert converted_dict == test_dict

# #     @mock.patch('memory_statistics.ConfigDBConnector')
# #     def test_sonic_db_connector(self, mock_config_db):
# #         """Test SonicDBConnector initialization and config retrieval"""
# #         mock_config_db.return_value.get_table.return_value = {
# #             'memory_statistics': {
# #                 'enabled': 'true',
# #                 'retention_period': '7',
# #                 'sampling_interval': '1'
# #             }
# #         }

# #         db_connector = SonicDBConnector()
# #         config = db_connector.get_memory_statistics_config()

# #         assert config['enabled'] == 'true'
# #         assert config['retention_period'] == '7'
# #         assert config['sampling_interval'] == '1'

# #     @mock.patch('socket.socket')
# #     def test_socket_manager_connection(self, mock_socket):
# #         """Test SocketManager connection handling"""
# #         socket_manager = SocketManager()
# #         socket_manager.connect()

# #         mock_socket.assert_called_once()
# #         mock_socket.return_value.connect.assert_called_once_with(Config.SOCKET_PATH)

# #         mock_socket.reset_mock()
# #         mock_socket.return_value.connect.side_effect = [socket.error, None]
# #         socket_manager = SocketManager()
# #         socket_manager.connect()
# #         assert mock_socket.call_count == 2

# #     def test_show_memory_stats_basic(self, mock_config_db, mock_socket_response):
# #         """Test basic memory statistics display"""
# #         runner = CliRunner()

# #         with mock.patch('socket.socket') as mock_socket:
# #             mock_sock = mock_socket.return_value
# #             mock_sock.recv.return_value = json.dumps(mock_socket_response).encode('utf-8')

# #             result = runner.invoke(show, ['memory-stats'])
# #             assert result.exit_code == 0
# #             assert "Memory Usage" in result.output

# #     def test_show_memory_stats_with_timerange(self, mock_config_db, mock_socket_response):
# #         """Test memory statistics display with time range parameters"""
# #         runner = CliRunner()

# #         with mock.patch('socket.socket') as mock_socket:
# #             mock_sock = mock_socket.return_value
# #             mock_sock.recv.return_value = json.dumps(mock_socket_response).encode('utf-8')

# #             result = runner.invoke(show, [
# #                 'memory-stats',
# #                 '--from', '2024-01-01',
# #                 '--to', '2024-01-02'
# #             ])
# #             assert result.exit_code == 0
# #             assert "Memory Usage" in result.output

# #     def test_show_config(self, mock_config_db):
# #         """Test configuration display functionality"""
# #         runner = CliRunner()

# #         with mock.patch('memory_statistics.SonicDBConnector') as mock_db:
# #             mock_db.return_value.get_memory_statistics_config.return_value = {
# #                 'enabled': 'true',
# #                 'retention_period': '7',
# #                 'sampling_interval': '1'
# #             }

# #             result = runner.invoke(show, ['memory-stats', '--config'])
# #             assert result.exit_code == 0
# #             assert 'Enabled' in result.output
# #             assert 'True' in result.output
# #             assert '7' in result.output
# #             assert '1' in result.output

# #     def test_socket_error_handling(self, mock_config_db):
# #         """Test socket error handling"""
# #         runner = CliRunner()

# #         with mock.patch('socket.socket') as mock_socket:
# #             mock_socket.return_value.connect.side_effect = socket.error("Connection refused")

# #             result = runner.invoke(show, ['memory-stats'])
# #             assert result.exit_code != 0
# #             assert "Error" in result.output

# #     def test_invalid_command(self):
# #         """Test handling of invalid commands"""
# #         runner = CliRunner()
# #         result = runner.invoke(show, ['invalid-command'])
# #         assert result.exit_code != 0
# #         assert "Error" in result.output

# #     @classmethod
# #     def teardown_class(cls):
# #         print("TEARDOWN")
# #         os.environ['UTILITIES_UNIT_TESTING'] = "0"


# # if __name__ == '__main__':
# #     pytest.main([__file__])


# # import pytest
# # import json
# # from unittest.mock import patch
# # from click.testing import CliRunner
# # from show.memory_statistics import cli, send_data  # Correct module import

# # # Mock configuration data for tests
# # MEMORY_STATS_CONFIG = {
# #     "memory_statistics": {
# #         "enabled": "true",
# #         "sampling_interval": "5",
# #         "retention_period": "15"
# #     }
# # }


# # @pytest.fixture
# # def mock_config_db():
# #     """Mock SONiC ConfigDB connection and data retrieval."""
# #     with patch('my_cli_tool.ConfigDBConnector') as mock_connector:
# #         mock_instance = mock_connector.return_value
# #         mock_instance.connect.return_value = None
# #         mock_instance.get_table.return_value = MEMORY_STATS_CONFIG
# #         yield mock_instance


# # @pytest.fixture
# # def mock_socket_manager():
# #     with patch('show.memory_statistics.SocketManager') as mock_socket:  # Updated path
# #         mock_instance = mock_socket.return_value
# #         mock_instance.connect.return_value = None
# #         mock_instance.receive_all.return_value = json.dumps({
# #             "status": True,
# #             "data": "Sample memory data output"
# #         })
# #         yield mock_instance


# # def test_socket_connection_failure():
# #     """Test socket connection failure handling."""
# #     with patch('my_cli_tool.SocketManager.connect', side_effect=ConnectionError("Connection failed")):
# #         with pytest.raises(ConnectionError):
# #             send_data("memory_statistics_command_request_handler", {})


# # def test_invalid_command():
# #     runner = CliRunner()
# #     result = runner.invoke(cli, ['invalid-command'])
# #     assert result.exit_code != 0
# #     assert "No such command" in result.output  # Updated assertion


# # def test_missing_socket_response(mock_socket_manager):
# #     """Test handling of empty socket responses."""
# #     mock_socket_manager.receive_all.return_value = ""

# #     with pytest.raises(ConnectionError, match="No response received from memory statistics service"):
# #         send_data("memory_statistics_command_request_handler", {})


# # def test_invalid_json_response(mock_socket_manager):
# #     """Test handling of invalid JSON responses from socket."""
# #     mock_socket_manager.receive_all.return_value = "Invalid JSON"

# #     with pytest.raises(ValueError, match="Failed to parse server response"):
# #         send_data("memory_statistics_command_request_handler", {})


# import pytest
# import json
# from unittest.mock import patch
# from click.testing import CliRunner
# from show.memory_statistics import cli, send_data

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
#     with patch('show.memory_statistics.ConfigDBConnector') as mock_connector:
#         mock_instance = mock_connector.return_value
#         mock_instance.connect.return_value = None
#         mock_instance.get_table.return_value = MEMORY_STATS_CONFIG
#         yield mock_instance


# @pytest.fixture
# def mock_socket_manager():
#     """Mock SocketManager class for successful responses."""
#     with patch('show.memory_statistics.SocketManager') as mock_socket:
#         mock_instance = mock_socket.return_value
#         mock_instance.connect.return_value = None
#         mock_instance.receive_all.return_value = json.dumps({
#             "status": True,
#             "data": "Sample memory data output"
#         })
#         yield mock_instance


# def test_socket_connection_failure():
#     """Test handling of socket connection failures."""
#     with patch('show.memory_statistics.SocketManager.connect', side_effect=ConnectionError("Connection failed")):
#         with pytest.raises(ConnectionError, match="Connection failed"):
#             send_data("memory_statistics_command_request_handler", {})


# def test_invalid_command():
#     """Test CLI handling of invalid commands."""
#     runner = CliRunner()
#     result = runner.invoke(cli, ['invalid-command'])

#     assert result.exit_code != 0
#     assert "No such command" in result.output


# def test_missing_socket_response(mock_socket_manager):
#     """Test handling when no response is received from the socket."""
#     mock_socket_manager.receive_all.return_value = ""

#     with pytest.raises(ConnectionError, match="No response received from memory statistics service"):
#         send_data("memory_statistics_command_request_handler", {})


# def test_invalid_json_response(mock_socket_manager):
#     """Test handling of invalid JSON responses from the socket."""
#     mock_socket_manager.receive_all.return_value = "Invalid JSON"

#     with pytest.raises(ValueError, match="Failed to parse server response"):
#         send_data("memory_statistics_command_request_handler", {})


# def test_valid_response(mock_socket_manager):
#     """Test valid socket response handling."""
#     response = send_data("memory_statistics_command_request_handler", {})
#     assert response['status'] is True
#     assert response['data'] == "Sample memory data output"


import unittest
from unittest.mock import patch
import socket
import json
from click.testing import CliRunner

from show.memory_statistics import (
    Config,
    Dict2Obj,
    SonicDBConnector,
    SocketManager,
    cli
)


class TestConfig(unittest.TestCase):
    """Test cases for Config class"""
    def test_default_values(self):
        """Test if Config class has correct default values"""
        self.assertEqual(Config.SOCKET_PATH, '/var/run/dbus/memstats.socket')
        self.assertEqual(Config.SOCKET_TIMEOUT, 30)
        self.assertEqual(Config.BUFFER_SIZE, 8192)
        self.assertEqual(Config.MAX_RETRIES, 3)
        self.assertEqual(Config.RETRY_DELAY, 1.0)
        self.assertEqual(Config.DEFAULT_CONFIG["enabled"], "false")
        self.assertEqual(Config.DEFAULT_CONFIG["retention_period"], "Unknown")
        self.assertEqual(Config.DEFAULT_CONFIG["sampling_interval"], "Unknown")


class TestDict2Obj(unittest.TestCase):
    """Test cases for Dict2Obj class"""
    def test_dict_conversion(self):
        """Test dictionary to object conversion"""
        test_dict = {
            "name": "test",
            "values": [1, 2, 3],
            "nested": {"key": "value"}
        }
        obj = Dict2Obj(test_dict)
        self.assertEqual(obj.name, "test")
        self.assertEqual(obj.values, [1, 2, 3])
        self.assertEqual(obj.nested.key, "value")

    def test_list_conversion(self):
        """Test list conversion"""
        test_list = [{"a": 1}, {"b": 2}]
        obj = Dict2Obj(test_list)
        self.assertEqual(obj.items[0].a, 1)
        self.assertEqual(obj.items[1].b, 2)

    def test_invalid_input(self):
        """Test invalid input handling"""
        with self.assertRaises(ValueError):
            Dict2Obj("invalid")


class TestSonicDBConnector(unittest.TestCase):
    """Test cases for SonicDBConnector class"""
    @patch('show.memory_statistics.ConfigDBConnector')  # Fixed import path
    def test_successful_connection(self, mock_config_db):
        """Test successful database connection"""
        SonicDBConnector()
        mock_config_db.return_value.connect.assert_called_once()

    @patch('show.memory_statistics.ConfigDBConnector')  # Fixed import path
    def test_connection_failure(self, mock_config_db):
        """Test database connection failure"""
        mock_config_db.return_value.connect.side_effect = Exception("Connection failed")
        with self.assertRaises(ConnectionError):
            SonicDBConnector()

    @patch('show.memory_statistics.ConfigDBConnector')  # Fixed import path
    def test_get_memory_statistics_config(self, mock_config_db):
        """Test retrieving memory statistics configuration"""
        test_config = {
            'memory_statistics': {
                'enabled': 'true',
                'retention_period': '7',
                'sampling_interval': '1'
            }
        }
        mock_config_db.return_value.get_table.return_value = test_config
        connector = SonicDBConnector()
        config = connector.get_memory_statistics_config()
        self.assertEqual(config, test_config['memory_statistics'])

    @patch('show.memory_statistics.ConfigDBConnector')  # Fixed import path
    def test_get_default_config(self, mock_config_db):
        """Test retrieving default configuration when none exists"""
        mock_config_db.return_value.get_table.return_value = {}
        connector = SonicDBConnector()
        config = connector.get_memory_statistics_config()
        self.assertEqual(config, Config.DEFAULT_CONFIG)


class TestSocketManager(unittest.TestCase):
    """Test cases for SocketManager class"""
    def setUp(self):
        self.socket_manager = SocketManager()

    @patch('socket.socket')
    def test_successful_connection(self, mock_socket):
        """Test successful socket connection"""
        mock_socket.return_value.connect.return_value = None
        self.socket_manager.connect()
        mock_socket.assert_called_with(socket.AF_UNIX, socket.SOCK_STREAM)

    @patch('socket.socket')
    def test_connection_retry(self, mock_socket):
        """Test connection retry mechanism"""
        mock_socket.return_value.connect.side_effect = [
            socket.error("Connection failed"),
            None
        ]
        self.socket_manager.connect()
        self.assertEqual(mock_socket.return_value.connect.call_count, 2)

    @patch('socket.socket')
    def test_connection_failure_max_retries(self, mock_socket):
        """Test connection failure after max retries"""
        mock_socket.return_value.connect.side_effect = socket.error("Connection failed")
        with self.assertRaises(ConnectionError):
            self.socket_manager.connect()
        self.assertEqual(mock_socket.return_value.connect.call_count, Config.MAX_RETRIES)

    def test_receive_all_no_connection(self):
        """Test receive_all with no active connection"""
        with self.assertRaises(ConnectionError):
            self.socket_manager.receive_all()


class TestCLICommands(unittest.TestCase):
    """Test cases for CLI commands"""
    def setUp(self):
        self.runner = CliRunner()


    @patch('show.memory_statistics.SonicDBConnector')  # Fixed import path
    def test_show_config(self, mock_db_connector):
        """Test show config command"""
        test_config = {
            'enabled': 'true',
            'retention_period': '7',
            'sampling_interval': '1'
        }
        mock_db_connector.return_value.get_memory_statistics_config.return_value = test_config
        result = self.runner.invoke(cli, ['show', 'memory-stats', '--config'])
        self.assertEqual(result.exit_code, 0)
        self.assertIn('Enabled', result.output)
        self.assertIn('Retention Time', result.output)
        self.assertIn('Sampling Interval', result.output)

    @patch('show.memory_statistics.send_data')  # Fixed import path
    def test_show_statistics(self, mock_send_data):
        """Test show statistics command"""
        mock_response = Dict2Obj({
            'status': True,
            'data': 'Memory Usage: 50%'
        })
        mock_send_data.return_value = mock_response
        result = self.runner.invoke(cli, ['show', 'memory-stats'])
        self.assertEqual(result.exit_code, 0)
        self.assertIn('Memory Statistics', result.output)


class TestIntegration(unittest.TestCase):
    """Integration tests"""
    @patch('show.memory_statistics.SocketManager')  # Fixed import path
    @patch('show.memory_statistics.SonicDBConnector')  # Fixed import path
    def test_end_to_end_flow(self, mock_db_connector, mock_socket_manager):
        """Test end-to-end flow from CLI to socket communication"""
        test_config = {
            'enabled': 'true',
            'retention_period': '7',
            'sampling_interval': '1'
        }
        mock_db_connector.return_value.get_memory_statistics_config.return_value = test_config

        mock_response = {
            'status': True,
            'data': 'Total Memory: 16GB\nUsed Memory: 8GB'
        }
        mock_socket_manager.return_value.receive_all.return_value = json.dumps(mock_response)

        runner = CliRunner()
        result = runner.invoke(cli, ['show', 'memory-stats', '--select', 'total_memory'])
        self.assertEqual(result.exit_code, 0)
        self.assertIn('Memory Statistics', result.output)


if __name__ == '__main__':
    unittest.main()
