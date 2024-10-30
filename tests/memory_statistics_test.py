import unittest
from unittest.mock import MagicMock, patch
from config_file_name import (  # Replace with the actual name of your config file
    check_memory_statistics_table_existence,
    memory_statistics_enable,
    memory_statistics_disable,
    memory_statistics_retention_period,
    memory_statistics_sampling_interval
)

class TestMemoryStatistics(unittest.TestCase):

    # Test case for check_memory_statistics_table_existence function
    def test_check_memory_statistics_table_existence_empty(self):
        result = check_memory_statistics_table_existence({})
        self.assertFalse(result)

    def test_check_memory_statistics_table_existence_missing_key(self):
        result = check_memory_statistics_table_existence({"other_table": {}})
        self.assertFalse(result)

    def test_check_memory_statistics_table_existence_present(self):
        result = check_memory_statistics_table_existence({"MEMORY_STATISTICS": {"memory_statistics": {}}})
        self.assertTrue(result)

    # Test cases for memory_statistics_enable function
    @patch('swsscommon.swsscommon.ConfigDBConnector')
    def test_enable_memory_statistics_success(self, mock_db_connector):
        mock_db = MagicMock()
        mock_db_connector.return_value = mock_db
        mock_db.get_table.return_value = {"memory_statistics": {}}
        
        with patch('click.echo') as mock_echo:
            memory_statistics_enable()
            mock_echo.assert_called_with("Memory statistics enabled successfully.")

    @patch('swsscommon.swsscommon.ConfigDBConnector')
    def test_enable_memory_statistics_already_enabled(self, mock_db_connector):
        mock_db = MagicMock()
        mock_db_connector.return_value = mock_db
        mock_db.get_table.return_value = {"memory_statistics": {"enabled": "true"}}
        
        with patch('click.echo') as mock_echo:
            memory_statistics_enable()
            mock_echo.assert_called_with("Memory statistics feature is already enabled.")

    # Test cases for memory_statistics_disable function
    @patch('swsscommon.swsscommon.ConfigDBConnector')
    def test_disable_memory_statistics_success(self, mock_db_connector):
        mock_db = MagicMock()
        mock_db_connector.return_value = mock_db
        mock_db.get_table.return_value = {"memory_statistics": {"enabled": "true"}}
        
        with patch('click.echo') as mock_echo:
            memory_statistics_disable()
            mock_echo.assert_called_with("Memory statistics disabled successfully.")

    @patch('swsscommon.swsscommon.ConfigDBConnector')
    def test_disable_memory_statistics_already_disabled(self, mock_db_connector):
        mock_db = MagicMock()
        mock_db_connector.return_value = mock_db
        mock_db.get_table.return_value = {"memory_statistics": {"enabled": "false"}}
        
        with patch('click.echo') as mock_echo:
            memory_statistics_disable()
            mock_echo.assert_called_with("Memory statistics feature is already disabled.")

    # Test cases for memory_statistics_retention_period function
    @patch('swsscommon.swsscommon.ConfigDBConnector')
    def test_set_retention_period_success(self, mock_db_connector):
        mock_db = MagicMock()
        mock_db_connector.return_value = mock_db
        mock_db.get_table.return_value = {"memory_statistics": {}}
        
        with patch('click.echo') as mock_echo:
            memory_statistics_retention_period(30)
            mock_echo.assert_called_with("Memory statistics retention period set to 30 minutes.")

    @patch('swsscommon.swsscommon.ConfigDBConnector')
    def test_set_retention_period_invalid_value(self, mock_db_connector):
        with patch('click.echo') as mock_echo:
            memory_statistics_retention_period(-5)
            mock_echo.assert_called_with("Invalid value for retention period. Please provide a positive integer.")

    # Test cases for memory_statistics_sampling_interval function
    @patch('swsscommon.swsscommon.ConfigDBConnector')
    def test_set_sampling_interval_success(self, mock_db_connector):
        mock_db = MagicMock()
        mock_db_connector.return_value = mock_db
        mock_db.get_table.return_value = {"memory_statistics": {}}
        
        with patch('click.echo') as mock_echo:
            memory_statistics_sampling_interval(10)
            mock_echo.assert_called_with("Memory statistics sampling interval set to 10 minutes.")

    @patch('swsscommon.swsscommon.ConfigDBConnector')
    def test_set_sampling_interval_invalid_value(self, mock_db_connector):
        with patch('click.echo') as mock_echo:
            memory_statistics_sampling_interval(-10)
            mock_echo.assert_called_with("Invalid value for sampling interval. Please provide a positive integer.")

if __name__ == "__main__":
    unittest.main()
