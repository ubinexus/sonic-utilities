import socket
from unittest.mock import patch, MagicMock
from click.testing import CliRunner
from show.memory_statistics import memory_stats, Dict2Obj


# Test CLI command memory-stats with valid inputs
def test_memory_stats_valid_arguments():
    runner = CliRunner()

    # Mock send_data to return a successful response
    mock_response = Dict2Obj({'data': 'memory stats data'})
    with patch('show.memory_statistics.send_data', return_value=mock_response):
        result = runner.invoke(memory_stats, ['from', '2024-01-01', 'to', '2024-01-02', 'select', 'metric'])

    # Assert valid command execution
    assert result.exit_code == 0
    assert 'Memory Statistics' in result.output
    assert 'memory stats data' in result.output


# Test CLI command memory-stats with missing 'from' keyword
def test_memory_stats_missing_from_keyword():
    runner = CliRunner()

    # Invoke command without 'from' keyword
    result = runner.invoke(memory_stats, ['2024-01-01', 'to', '2024-01-02', 'select', 'metric'])

    # Assert failure and error message
    assert result.exit_code != 0
    assert "Expected 'from' keyword as the first argument." in result.output


# Test CLI command memory-stats with incorrect 'to' keyword
def test_memory_stats_incorrect_to_keyword():
    runner = CliRunner()

    # Invoke command with incorrect 'to' keyword
    result = runner.invoke(memory_stats, ['from', '2024-01-01', 'to_keyword', '2024-01-02', 'select', 'metric'])

    # Assert failure and error message
    assert result.exit_code != 0
    assert "Expected 'to' keyword before the end time." in result.output
