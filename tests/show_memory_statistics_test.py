import unittest
from unittest.mock import patch, MagicMock
import socket
import os

from show.memory_statistics import (
    Config,
    Dict2Obj,
    SonicDBConnector,
    SocketManager,
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

    # def test_connection_failure_max_retries(self):
    #     """Test connection failure after max retries"""
    #     self.mock_config_db.connect.side_effect = Exception("Connection failed")
    #     with self.assertRaises(ConnectionError) as context:
    #         SonicDBConnector()
    #     self.assertEqual(
    #         str(context.exception),
    #         "Failed to connect to SONiC config database after 3 attempts. Last error: Connection failed"
    #     )
    #     self.assertEqual(self.mock_config_db.connect.call_count, 3)

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

    # @patch('os.path.exists')
    # def test_validate_socket_path_failure(self, mock_exists):
    #     """Test socket path validation failure"""
    #     mock_exists.return_value = False
    #     with self.assertRaises(ConnectionError) as context:
    #         self.socket_manager._validate_socket_path()
    #     self.assertEqual(
    #         str(context.exception),
    #         f"Socket directory {os.path.dirname(self.socket_path)} does not exist"
    #     )

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

    # @patch('socket.socket')
    # def test_connect_failure_max_retries(self, mock_socket):
    #     """Test connection failure after max retries"""
    #     mock_sock = MagicMock()
    #     mock_socket.return_value = mock_sock
    #     mock_sock.connect.side_effect = socket.error("Connection refused")
    #     with self.assertRaises(ConnectionError) as context:
    #         self.socket_manager.connect()
    #     self.assertEqual(
    #         str(context.exception),
    #         f"Failed to connect to memory statistics service after {Config.MAX_RETRIES} "
    #         f"attempts. Last error: Connection refused. "
    #         f"Please verify that the service is running and socket file exists at {self.socket_path}"
    #     )
    #     self.assertEqual(mock_sock.connect.call_count, Config.MAX_RETRIES)

    # def test_receive_all_no_connection(self):
    #     """Test receive_all with no active connection"""
    #     with self.assertRaises(ConnectionError) as context:
    #         self.socket_manager.receive_all()
    #     self.assertEqual(str(context.exception), "No active socket connection")

    @patch('socket.socket')
    def test_receive_all_success(self, mock_socket):
        """Test successful data reception"""
        mock_sock = MagicMock()
        mock_socket.return_value = mock_sock
        mock_sock.recv.side_effect = [b'test', b'data', b'']
        self.socket_manager.sock = mock_sock
        result = self.socket_manager.receive_all()
        self.assertEqual(result, 'testdata')

    # @patch('socket.socket')
    # def test_receive_all_timeout(self, mock_socket):
    #     """Test receive timeout handling"""
    #     mock_sock = MagicMock()
    #     mock_socket.return_value = mock_sock
    #     mock_sock.recv.side_effect = socket.timeout()
    #     self.socket_manager.sock = mock_sock
    #     with self.assertRaises(ConnectionError) as context:
    #         self.socket_manager.receive_all()
    #     self.assertEqual(
    #         str(context.exception),
    #         f"Socket operation timed out after {Config.SOCKET_TIMEOUT} seconds"
    #     )

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


if __name__ == '__main__':
    unittest.main()
