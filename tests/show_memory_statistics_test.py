import pytest
from click.testing import CliRunner
from unittest.mock import MagicMock
from your_module import cli


@pytest.fixture
def runner():
    """Fixture to set up the Click test runner."""
    return CliRunner()


@pytest.fixture
def mock_db_connector():
    """Fixture to mock db_connector."""
    mock_connector = MagicMock()
    mock_connector.get_table.return_value = {
        'memory_statistics': {
            'enabled': 'true',
            'retention_period': '30',
            'sampling_interval': '10'
        }
    }
    return mock_connector


def test_memory_stats_valid(runner):
    """Test valid memory-stats command."""
    result = runner.invoke(
        cli,
        [
            'show', 'memory-stats', 'from', "'2023-11-01'",
            'to', "'2023-11-02'", 'select', "'used_memory'"
        ]
    )
    print(result.output)  # Debug the output
    assert result.exit_code == 0
    assert "Memory Statistics:" in result.output


def test_memory_stats_invalid_from_keyword(runner):
    """Test memory-stats command with invalid 'from' keyword."""
    result = runner.invoke(cli, ['show', 'memory-stats', 'from_invalid', "'2023-11-01'"])
    print(result.output)  # Debug the output
    assert result.exit_code != 0
    assert "UsageError" in result.output


def test_memory_statistics_config(runner, mock_db_connector):
    """Test the memory-statistics config command."""
    result = runner.invoke(cli, ['show', 'memory-statistics', 'config'])
    print(result.output)  # Debug the output
    assert result.exit_code == 0
    assert "Enabled" in result.output
    assert "Retention Time (days)" in result.output
    assert "Sampling Interval (minutes)" in result.output
