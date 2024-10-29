import unittest
from unittest.mock import patch, MagicMock
import click

from click.testing import CliRunner

import config.memory_statistics as config

class TestMemoryStatistics(unittest.TestCase):

    @patch('swsscommon.swsscommon.ConfigDBConnector')
    def test_db_connection(self, mock_db_connector):
        mock_db = MagicMock()
        mock_db_connector.return_value = mock_db
        db = ConfigDBConnector()
        db.connect()
        mock_db.connect.assert_called_once()

    def test_check_memory_statistics_table_existence_empty(self):
        result = check_memory_statistics_table_existence({})
        self.assertFalse(result)

    def test_check_memory_statistics_table_existence_missing_key(self):
        result = check_memory_statistics_table_existence({"other_table": {}})
        self.assertFalse(result)

    @patch('swsscommon.swsscommon.ConfigDBConnector')
    def test_enable_memory_statistics(self, mock_db_connector):
        mock_db = MagicMock()
        mock_db_connector.return_value = mock_db
        mock_db.get_table.return_value = {"memory_statistics": {}}
        
        with patch('click.echo') as mock_echo:
            memory_statistics_enable()
            mock_echo.assert_any_call("Memory Statistics feature enabled.")
            mock_db.mod_entry.assert_called_once_with("MEMORY_STATISTICS", "memory_statistics", {"enabled": "true", "disabled": "false"})
    
    @patch('swsscommon.swsscommon.ConfigDBConnector')
    def test_disable_memory_statistics(self, mock_db_connector):
        mock_db = MagicMock()
        mock_db_connector.return_value = mock_db
        mock_db.get_table.return_value = {"memory_statistics": {}}
        
        with patch('click.echo') as mock_echo:
            memory_statistics_disable()
            mock_echo.assert_any_call("Memory Statistics feature disabled.")
            mock_db.mod_entry.assert_called_once_with("MEMORY_STATISTICS", "memory_statistics", {"enabled": "false", "disabled": "true"})

    @patch('swsscommon.swsscommon.ConfigDBConnector')
    def test_set_retention_period(self, mock_db_connector):
        mock_db = MagicMock()
        mock_db_connector.return_value = mock_db
        mock_db.get_table.return_value = {"memory_statistics": {}}
        
        retention_period = 7
        with patch('click.echo') as mock_echo:
            memory_statistics_retention_period(retention_period)
            mock_echo.assert_any_call(f"Memory Statistics retention period set to {retention_period} days.")
            mock_db.mod_entry.assert_called_once_with("MEMORY_STATISTICS", "memory_statistics", {"retention_period": retention_period})

    @patch('swsscommon.swsscommon.ConfigDBConnector')
    def test_set_sampling_interval(self, mock_db_connector):
        mock_db = MagicMock()
        mock_db_connector.return_value = mock_db
        mock_db.get_table.return_value = {"memory_statistics": {}}
        
        sampling_interval = 5
        with patch('click.echo') as mock_echo:
            memory_statistics_sampling_interval(sampling_interval)
            mock_echo.assert_any_call(f"Memory Statistics sampling interval set to {sampling_interval} minutes.")
            mock_db.mod_entry.assert_called_once_with("MEMORY_STATISTICS", "memory_statistics", {"sampling_interval": sampling_interval})

    @patch('swsscommon.swsscommon.ConfigDBConnector')
    def test_error_handling_in_enable(self, mock_db_connector):
        mock_db = MagicMock()
        mock_db_connector.return_value = mock_db
        mock_db.get_table.return_value = {"memory_statistics": {}}
        mock_db.mod_entry.side_effect = Exception("Database error")
        
        with patch('click.echo') as mock_echo:
            memory_statistics_enable()
            mock_echo.assert_any_call("Error enabling Memory Statistics feature: Database error")

if __name__ == "__main__":
    unittest.main()