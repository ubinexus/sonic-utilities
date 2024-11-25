import unittest
from unittest.mock import patch, MagicMock
import socket
import os
import click
from click.testing import CliRunner

from show.memory_statistics import (
    Config,
    Dict2Obj,
    SonicDBConnector,
    SocketManager,
    format_field_value,
    clean_and_print,
    validate_command,
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

    def test_to_dict_conversion(self):
        """Test converting object back to dictionary"""
        test_dict = {
            "name": "test",
            "nested": {"key": "value"},
            "list": [{"item": 1}, {"item": 2}]
        }
        obj = Dict2Obj(test_dict)
        result = obj.to_dict()
        self.assertEqual(result, test_dict)

    def test_repr_method(self):
        """Test string representation of Dict2Obj"""
        test_dict = {"name": "test"}
        obj = Dict2Obj(test_dict)
        expected_repr = "<Dict2Obj {'name': 'test'}>"
        self.assertEqual(repr(obj), expected_repr)


class TestSonicDBConnector(unittest.TestCase):
    def setUp(self):
        self.mock_config_db = MagicMock()
        self.patcher = patch('show.memory_statistics.ConfigDBConnector',
                             return_value=self.mock_config_db)
        self.patcher.start()

    def tearDown(self):
        self.patcher.stop()

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

    def test_successful_connection(self):
        """Test successful database connection on first attempt"""
        SonicDBConnector()
        self.mock_config_db.connect.assert_called_once()

    def test_connection_retry_success(self):
        """Test successful connection after initial failures"""
        self.mock_config_db.connect.side_effect = [Exception("First try"), Exception("Second try"), None]
        SonicDBConnector()
        self.assertEqual(self.mock_config_db.connect.call_count, 3)

    def test_get_memory_statistics_config_success(self):
        """Test successful retrieval of memory statistics configuration"""
        test_config = {
            'memory_statistics': {
                'enabled': 'true',
                'retention_period': '7',
                'sampling_interval': '1'
            }
        }
        connector = SonicDBConnector()
        self.mock_config_db.get_table.return_value = test_config
        config = connector.get_memory_statistics_config()
        self.assertEqual(config, test_config['memory_statistics'])

    def test_get_memory_statistics_config_empty(self):
        """Test handling of empty configuration"""
        connector = SonicDBConnector()
        self.mock_config_db.get_table.return_value = {}
        config = connector.get_memory_statistics_config()
        self.assertEqual(config, Config.DEFAULT_CONFIG)

    def test_get_memory_statistics_config_error(self):
        """Test error handling in configuration retrieval"""
        connector = SonicDBConnector()
        self.mock_config_db.get_table.side_effect = Exception("Database error")
        with self.assertRaises(RuntimeError) as context:
            connector.get_memory_statistics_config()
        self.assertIn("Error retrieving memory statistics configuration", str(context.exception))


class TestSocketManager(unittest.TestCase):
    """Test cases for SocketManager class"""
    def setUp(self):
        self.socket_path = '/tmp/test_socket'
        self.socket_manager = SocketManager(self.socket_path)

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

    @patch('os.path.exists')
    def test_validate_socket_path_success(self, mock_exists):
        """Test successful socket path validation"""
        mock_exists.return_value = True
        self.socket_manager._validate_socket_path()
        mock_exists.assert_called_once_with(os.path.dirname(self.socket_path))

    @patch('socket.socket')
    def test_connect_success(self, mock_socket):
        """Test successful socket connection"""
        mock_sock = MagicMock()
        mock_socket.return_value = mock_sock
        self.socket_manager.connect()
        mock_sock.settimeout.assert_called_with(Config.SOCKET_TIMEOUT)
        mock_sock.connect.assert_called_with(self.socket_path)

    @patch('socket.socket')
    def test_connect_retry_success(self, mock_socket):
        """Test successful connection after retries"""
        mock_sock = MagicMock()
        mock_socket.return_value = mock_sock
        mock_sock.connect.side_effect = [socket.error(), socket.error(), None]
        self.socket_manager.connect()
        self.assertEqual(mock_sock.connect.call_count, 3)

    @patch('socket.socket')
    def test_receive_all_success(self, mock_socket):
        """Test successful data reception"""
        mock_sock = MagicMock()
        mock_socket.return_value = mock_sock
        mock_sock.recv.side_effect = [b'test', b'data', b'']
        self.socket_manager.sock = mock_sock
        result = self.socket_manager.receive_all()
        self.assertEqual(result, 'testdata')

    def test_close_success(self):
        """Test successful socket closure"""
        mock_sock = MagicMock()
        self.socket_manager.sock = mock_sock
        self.socket_manager.close()
        mock_sock.close.assert_called_once()
        self.assertIsNone(self.socket_manager.sock)

    def test_close_with_error(self):
        """Test socket closure with error"""
        mock_sock = MagicMock()
        mock_sock.close.side_effect = Exception("Close error")
        self.socket_manager.sock = mock_sock
        self.socket_manager.close()
        self.assertIsNone(self.socket_manager.sock)

    @patch('socket.socket')
    def test_send_data_success(self, mock_socket):
        """Test successful data sending"""
        mock_sock = MagicMock()
        self.socket_manager.sock = mock_sock
        test_data = "test message"
        self.socket_manager.send(test_data)
        mock_sock.sendall.assert_called_with(test_data.encode('utf-8'))


class TestCLICommands(unittest.TestCase):
    """Test cases for CLI commands"""
    def setUp(self):
        self.runner = CliRunner()
        self.ctx = click.Context(click.Command('test'))

    def test_validate_command_invalid_with_suggestion(self):
        """Test command validation with invalid command but close match"""
        valid_commands = ['show', 'config']
        with self.assertRaises(click.UsageError) as context:
            validate_command('shw', valid_commands)
        self.assertIn("Did you mean 'show'", str(context.exception))

    def test_validate_command_invalid_no_suggestion(self):
        """Test command validation with invalid command and no close match"""
        valid_commands = ['show', 'config']
        with self.assertRaises(click.UsageError) as context:
            validate_command('xyz', valid_commands)
        self.assertIn("Invalid command 'xyz'", str(context.exception))

    def test_format_field_value(self):
        """Test field value formatting"""
        self.assertEqual(format_field_value("enabled", "true"), "True")
        self.assertEqual(format_field_value("enabled", "false"), "False")
        self.assertEqual(format_field_value("retention_period", "Unknown"), "Not configured")
        self.assertEqual(format_field_value("sampling_interval", "5"), "5")

    def test_clean_and_print(self):
        """Test data cleaning and printing"""
        test_data = {
            "data": "Memory Usage: 50%\nSwap Usage: 10%"
        }
        with patch('builtins.print') as mock_print:
            clean_and_print(test_data)
            mock_print.assert_called_with("Memory Statistics:\nMemory Usage: 50%\nSwap Usage: 10%")

    def test_clean_and_print_invalid_data(self):
        """Test clean_and_print with invalid data"""
        with patch('builtins.print') as mock_print:
            clean_and_print("invalid data")
            mock_print.assert_called_with("Error: Invalid data format received")


# class TestMemoryStatsCLI(unittest.TestCase):
#     def setUp(self):
#         self.runner = CliRunner()
#         self.maxDiff = None

#     def test_show_config_error(self):
#         """Test config command when database connection fails"""
#         with patch('show.memory_statistics.SonicDBConnector') as mock_db:
#             mock_db.side_effect = Exception(
#                 "Sonic database config file doesn't exist at /var/run/redis/sonic-db/database_config.json"
#             )

#             result = self.runner.invoke(cli, ['show', 'memory-stats', '--config'])
#             self.assertEqual(result.exit_code, 1)
#             self.assertIn('Error initializing database connection', result.output)


if __name__ == '__main__':
    unittest.main()
