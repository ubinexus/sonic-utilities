import unittest
from unittest.mock import patch, MagicMock, Mock
import socket
import os
import click
from click.testing import CliRunner
from io import StringIO
import json
# import syslog
# import pytest

from show.memory_statistics import (
    Config,
    Dict2Obj,
    SonicDBConnector,
    SocketManager,
    send_data,
    display_config,
    display_statistics,
    main,
    show,
    format_field_value,
    clean_and_print,
    validate_command,
)


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


class TestCLIEntryPoint(unittest.TestCase):

    @patch('sys.argv', ['memory_statistics.py', 'show'])
    @patch('show.memory_statistics.cli')
    def test_main_valid_command(self, mock_cli):
        """Test main() with a valid 'show' command."""
        mock_cli.add_command = MagicMock()
        mock_cli.return_value = None

        try:
            main()
        except SystemExit:
            pass  # CLI might call sys.exit()

        mock_cli.add_command.assert_called_once_with(show)
        mock_cli.assert_called_once()  # Ensure cli() is invoked

    # @patch('sys.argv', ['memory_statistics.py', 'invalid_command'])
    # @patch('syslog.syslog')
    # def test_main_invalid_command(self, mock_syslog):
    #     """Test main() with an invalid command."""
    #     with self.assertRaises(click.UsageError) as context:
    #         main()

    #     self.assertIn("Error: Invalid command", str(context.exception))
    #     mock_syslog.assert_called_once_with(
    #         syslog.LOG_ERR, "Error: Invalid command 'invalid_command'."
    #     )

    @patch('sys.argv', ['memory_statistics.py'])
    @patch('show.memory_statistics.cli')
    def test_main_no_command(self, mock_cli):
        """Test main() with no command-line arguments."""
        try:
            main()
        except SystemExit:
            pass  # CLI might call sys.exit()

        mock_cli.add_command.assert_called_once_with(show)
        mock_cli.assert_called_once()  # Ensure cli() is invoked


class TestMemoryStatisticsCLI(unittest.TestCase):

    @patch('sys.stdout', new_callable=StringIO)
    @patch('sys.argv', new=['main.py', 'show', 'memory-stats'])
    def test_show_memory_stats_valid(self, mock_stdout):
        """Test the valid 'show memory-stats' command."""
        with patch('show.memory_statistics.SocketManager.get_memory_stats',
                   return_value={'total_memory': 4096, 'used_memory': 2048}), \
             patch('show.memory_statistics.SonicDBConnector.fetch_config',
                   return_value={'enabled': 'true', 'sampling_interval': 5, 'retention_period': 15}):
            main()

        output = mock_stdout.getvalue()
        self.assertIn("total_memory", output)
        self.assertIn("used_memory", output)

    @patch('sys.stdout', new_callable=StringIO)
    @patch('sys.argv', new=['main.py', 'show', 'memory-stats', '--from', '10 minutes ago', '--to', 'now'])
    def test_show_memory_stats_with_time_range(self, mock_stdout):
        """Test the 'show memory-stats' command with --from and --to options."""
        with patch('show.memory_statistics.SocketManager.get_memory_stats',
                   return_value={'total_memory': 4096, 'used_memory': 2048}):
            main()

        output = mock_stdout.getvalue()
        self.assertIn("total_memory", output)
        self.assertIn("used_memory", output)
        self.assertIn("10 minutes ago", output)

    @patch('sys.stdout', new_callable=StringIO)
    @patch('sys.argv', new=['main.py', 'show', 'memory-stats', '--select', 'total_memory'])
    def test_show_memory_stats_with_select_option(self, mock_stdout):
        """Test the 'show memory-stats' command with --select option."""
        with patch('show.memory_statistics.SocketManager.get_memory_stats', return_value={'total_memory': 4096}):
            main()

        output = mock_stdout.getvalue()
        self.assertIn("total_memory", output)
        self.assertNotIn("used_memory", output)

    @patch('sys.stdout', new_callable=StringIO)
    @patch('sys.argv', new=['main.py', 'show', 'memory-stats', 'config'])
    def test_show_memory_stats_config(self, mock_stdout):
        """Test the 'show memory-stats config' command."""
        with patch('show.memory_statistics.SonicDBConnector.fetch_config',
                   return_value={'enabled': 'true', 'sampling_interval': 5, 'retention_period': 15}):
            main()

        output = mock_stdout.getvalue()
        self.assertIn("enabled", output)
        self.assertIn("sampling_interval", output)

    @patch('sys.stdout', new_callable=StringIO)
    @patch('sys.argv', new=['main.py', 'invalid_command'])
    def test_invalid_command(self, mock_stdout):
        """Test an invalid command."""
        with self.assertRaises(SystemExit):
            main()
        output = mock_stdout.getvalue()
        self.assertIn("Error: Invalid command", output)

    @patch('sys.stdout', new_callable=StringIO)
    @patch('sys.argv', new=['main.py', 'show'])
    def test_missing_required_argument(self, mock_stdout):
        """Test a missing required argument."""
        with self.assertRaises(SystemExit):
            main()

        output = mock_stdout.getvalue()
        self.assertIn("Error", output)

    @patch('sys.stdout', new_callable=StringIO)
    @patch('sys.argv', new=['main.py', 'show', 'memory-stats', '--from', 'invalid_time'])
    def test_invalid_time_range(self, mock_stdout):
        """Test invalid time range input."""
        with self.assertRaises(SystemExit):
            main()

        output = mock_stdout.getvalue()
        self.assertIn("Invalid value for", output)

    @patch('sys.stdout', new_callable=StringIO)
    @patch('sys.argv', new=['main.py', 'show', 'memory-stats', '--select', 'invalid_metric'])
    def test_invalid_select_option(self, mock_stdout):
        """Test invalid --select option."""
        with self.assertRaises(SystemExit):
            main()

        output = mock_stdout.getvalue()
        self.assertIn("Invalid value for", output)

    @patch('sys.stdout', new_callable=StringIO)
    @patch('sys.argv', new=['main.py', 'show', 'memory-stats'])
    def test_show_memory_stats_no_args(self, mock_stdout):
        """Test the 'show memory-stats' command with no options."""
        with patch('show.memory_statistics.SocketManager.get_memory_stats',
                   return_value={'total_memory': 4096, 'used_memory': 2048}):
            main()

        output = mock_stdout.getvalue()
        self.assertIn("total_memory", output)
        self.assertIn("used_memory", output)


class TestMemoryStatisticsCLI2(unittest.TestCase):

    # @patch('show.memory_statistics.SocketManager.connect')
    # @patch('show.memory_statistics.SocketManager.receive_all')
    # def test_send_data_success(self, mock_receive_all, mock_connect):
    #     """Test successful data sending and response handling."""
    #     mock_receive_all.return_value = json.dumps({"status": True, "data": "OK"})

    #     response = send_data("test_command", {"param": "value"})
    #     self.assertEqual(response.data, "OK")
    #     mock_connect.assert_called_once()

    # @patch('show.memory_statistics.SocketManager.connect')
    # def test_send_data_connection_failure(self, mock_connect):
    #     """Test socket connection failure scenario."""
    #     mock_connect.side_effect = ConnectionError("Connection failed")

    #     with self.assertRaises(ConnectionError):
    #         send_data("test_command", {"param": "value"})

    # @patch('show.memory_statistics.SonicDBConnector.get_memory_statistics_config')
    # @patch('click.echo')
    # def test_display_config_success(self, mock_echo, mock_get_config):
    #     """Test display_config with successful data retrieval."""
    #     mock_get_config.return_value = {
    #         "enabled": "true",
    #         "sampling_interval": "5",
    #         "retention_period": "15"
    #     }

    #     db_connector = Mock()
    #     display_config(db_connector)
    #     mock_echo.assert_any_call("Enabled                         true")

    # def test_format_field_value(self):
    #     """Test formatting field values."""
    #     result = format_field_value("enabled", "true")
    #     self.assertEqual(result, "true")

    # @patch('show.memory_statistics.send_data')
    # @patch('click.echo')
    # def test_display_statistics_success(self, mock_echo, mock_send_data):
    #     """Test display_statistics with valid data."""
    #     mock_send_data.return_value = Dict2Obj({"items": [{"metric": "usage", "value": 50}]})

    #     ctx = MagicMock()
    #     display_statistics(ctx, "2024-01-01", "2024-01-02", "usage")
    #     mock_echo.assert_called()

    @patch('show.memory_statistics.send_data')
    def test_display_statistics_no_response(self, mock_send_data):
        """Test display_statistics with no response."""
        mock_send_data.side_effect = click.ClickException("No data")

        ctx = MagicMock()
        with self.assertRaises(click.ClickException):
            display_statistics(ctx, "2024-01-01", "2024-01-02", "usage")


if __name__ == '__main__':
    unittest.main()
