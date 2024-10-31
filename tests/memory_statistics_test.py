import pytest
from unittest.mock import patch, MagicMock
from click.testing import CliRunner
from config.memory_statistics import (
    memory_statistics_enable,
    memory_statistics_disable,
    memory_statistics_retention_period,
    memory_statistics_sampling_interval,
    get_memory_statistics_table,
    check_memory_statistics_table_existence,
)
from utilities_common.cli import AbbreviationGroup


@pytest.fixture
def mock_db():
    """Fixture for the mock database."""
    with patch("config.memory_statistics.ConfigDBConnector") as MockConfigDBConnector:
        mock_db_instance = MockConfigDBConnector.return_value
        yield mock_db_instance


def test_memory_statistics_enable(mock_db):
    """Test enabling the Memory Statistics feature."""
    mock_db.get_table.return_value = {"memory_statistics": {"enabled": "false"}}
    runner = CliRunner()

    with patch("click.echo") as mock_echo:
        result = runner.invoke(memory_statistics_enable)
        assert result.exit_code == 0  # Ensure the command exits without error
        assert mock_echo.call_count == 2  # Check if the echo function was called twice
        mock_db.mod_entry.assert_called_once_with(
            "MEMORY_STATISTICS", "memory_statistics",
            {"enabled": "true", "disabled": "false"}
        )


def test_memory_statistics_disable(mock_db):
    """Test disabling the Memory Statistics feature."""
    mock_db.get_table.return_value = {"memory_statistics": {"enabled": "true"}}
    runner = CliRunner()

    with patch("click.echo") as mock_echo:
        result = runner.invoke(memory_statistics_disable)
        assert result.exit_code == 0
        assert mock_echo.call_count == 2
        mock_db.mod_entry.assert_called_once_with(
            "MEMORY_STATISTICS", "memory_statistics",
            {"enabled": "false", "disabled": "true"}
        )


def test_abbreviation_group_get_command():
    """Test AbbreviationGroup's get_command method to ensure it retrieves a command correctly."""
    # Create an instance of AbbreviationGroup with a sample command.
    group = AbbreviationGroup()
    group.commands = {"sample_command": MagicMock()}  # Mock command

    # Invoke get_command with an existing command name.
    command = group.get_command(ctx=None, cmd_name="sample_command")

    # Check that the command is correctly returned.
    assert command is group.commands["sample_command"]


def test_memory_statistics_retention_period(mock_db):
    """Test setting the retention period for Memory Statistics."""
    mock_db.get_table.return_value = {"memory_statistics": {}}
    runner = CliRunner()
    retention_period_value = 30

    with patch("click.echo") as mock_echo:
        result = runner.invoke(memory_statistics_retention_period, [str(retention_period_value)])
        assert result.exit_code == 0
        assert mock_echo.call_count == 2
        mock_db.mod_entry.assert_called_once_with(
            "MEMORY_STATISTICS", "memory_statistics",
            {"retention_period": retention_period_value}
        )


def test_memory_statistics_sampling_interval(mock_db):
    """Test setting the sampling interval for Memory Statistics."""
    mock_db.get_table.return_value = {"memory_statistics": {}}
    runner = CliRunner()
    sampling_interval_value = 10

    with patch("click.echo") as mock_echo:
        result = runner.invoke(memory_statistics_sampling_interval, [str(sampling_interval_value)])
        assert result.exit_code == 0
        assert mock_echo.call_count == 2
        mock_db.mod_entry.assert_called_once_with(
            "MEMORY_STATISTICS", "memory_statistics",
            {"sampling_interval": sampling_interval_value}
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
