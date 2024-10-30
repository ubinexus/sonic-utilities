import pytest
from unittest.mock import MagicMock, patch
from config.memory_statistics import (
    memory_statistics_enable,
    memory_statistics_disable,
    memory_statistics_retention_period,
    memory_statistics_sampling_interval,
    get_memory_statistics_table,
    check_memory_statistics_table_existence,
)


@pytest.fixture
def mock_db():
    """Fixture for the mock database."""
    with patch("your_config_file.ConfigDBConnector") as MockConfigDBConnector:
        mock_db_instance = MockConfigDBConnector.return_value
        yield mock_db_instance


def test_memory_statistics_enable(mock_db):
    """Test enabling the Memory Statistics feature."""
    mock_db.get_table.return_value = {"memory_statistics": {"enabled": "false"}}

    with patch("click.echo") as mock_echo:
        memory_statistics_enable()
        assert mock_echo.call_count == 2  # Check if the echo function was called twice
        mock_db.mod_entry.assert_called_once_with(
            "MEMORY_STATISTICS", "memory_statistics", {"enabled": "true", "disabled": "false"}
        )


def test_memory_statistics_disable(mock_db):
    """Test disabling the Memory Statistics feature."""
    mock_db.get_table.return_value = {"memory_statistics": {"enabled": "true"}}

    with patch("click.echo") as mock_echo:
        memory_statistics_disable()
        assert mock_echo.call_count == 2  # Check if the echo function was called twice
        mock_db.mod_entry.assert_called_once_with(
            "MEMORY_STATISTICS", "memory_statistics", {"enabled": "false", "disabled": "true"}
        )


def test_memory_statistics_retention_period(mock_db):
    """Test setting the retention period for Memory Statistics."""
    mock_db.get_table.return_value = {"memory_statistics": {}}
    retention_period_value = 30

    with patch("click.echo") as mock_echo:
        memory_statistics_retention_period(retention_period_value)
        assert mock_echo.call_count == 2  # Check if the echo function was called twice
        mock_db.mod_entry.assert_called_once_with(
            "MEMORY_STATISTICS", "memory_statistics", {"retention_period": retention_period_value}
        )


def test_memory_statistics_sampling_interval(mock_db):
    """Test setting the sampling interval for Memory Statistics."""
    mock_db.get_table.return_value = {"memory_statistics": {}}
    sampling_interval_value = 10

    with patch("click.echo") as mock_echo:
        memory_statistics_sampling_interval(sampling_interval_value)
        assert mock_echo.call_count == 2  # Check if the echo function was called twice
        mock_db.mod_entry.assert_called_once_with(
            "MEMORY_STATISTICS", "memory_statistics", {"sampling_interval": sampling_interval_value}
        )


def test_check_memory_statistics_table_existence():
    """Test existence check for MEMORY_STATISTICS table."""
    assert check_memory_statistics_table_existence({"memory_statistics": {}}) is True
    assert check_memory_statistics_table_existence({}) is False


def test_get_memory_statistics_table(mock_db):
    """Test getting MEMORY_STATISTICS table."""
    mock_db.get_table.return_value = {"memory_statistics": {}}

    result = get_memory_statistics_table(mock_db)
    assert result == {"memory_statistics": {}}
