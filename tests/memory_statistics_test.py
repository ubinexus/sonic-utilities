import pytest
from unittest.mock import patch
from click.testing import CliRunner
import syslog
from config.memory_statistics import (
    memory_statistics_enable,
    memory_statistics_disable,
    memory_statistics_retention_period,
    memory_statistics_sampling_interval,
    check_memory_statistics_table_existence,
)


@pytest.fixture
def mock_db():
    """Fixture for the mock database."""
    with patch("config.memory_statistics.ConfigDBConnector") as MockConfigDBConnector:
        mock_db_instance = MockConfigDBConnector.return_value
        yield mock_db_instance


def test_memory_statistics_enable(mock_db):
    """Test enabling the Memory Statistics feature."""
    runner = CliRunner()

    with patch("config.memory_statistics.update_memory_statistics_status") as mock_update_status:
        mock_update_status.return_value = (True, None)  # Simulate successful update
        with patch("syslog.syslog") as mock_syslog:
            result = runner.invoke(memory_statistics_enable)
            assert result.exit_code == 0
            mock_update_status.assert_called_once_with("true", mock_db)
            mock_syslog.assert_any_call(syslog.LOG_INFO, "Memory statistics enabled successfully.")
            assert "Save SONiC configuration using 'config save' to persist the changes." in result.output


def test_memory_statistics_disable(mock_db):
    """Test disabling the Memory Statistics feature."""
    runner = CliRunner()

    with patch("config.memory_statistics.update_memory_statistics_status") as mock_update_status:
        mock_update_status.return_value = (True, None)  # Simulate successful update
        with patch("syslog.syslog") as mock_syslog:
            result = runner.invoke(memory_statistics_disable)
            assert result.exit_code == 0
            mock_update_status.assert_called_once_with("false", mock_db)
            mock_syslog.assert_any_call(syslog.LOG_INFO, "Memory statistics disabled successfully.")
            assert "Save SONiC configuration using 'config save' to persist the changes." in result.output


def test_memory_statistics_retention_period(mock_db):
    """Test setting the retention period for Memory Statistics."""
    runner = CliRunner()
    retention_period_value = 20  # Within valid range

    with patch("click.echo") as mock_echo, patch("syslog.syslog") as mock_syslog:
        result = runner.invoke(memory_statistics_retention_period, [str(retention_period_value)])
        assert result.exit_code == 0
        mock_echo.assert_any_call(f"Retention period set to {retention_period_value} successfully.")
        mock_db.mod_entry.assert_called_once_with(
            "MEMORY_STATISTICS", "memory_statistics",
            {"retention_period": retention_period_value}
        )
        mock_syslog.assert_any_call(syslog.LOG_INFO, f"Retention period set to {retention_period_value} successfully.")
        assert "Save SONiC configuration using 'config save' to persist the changes." in result.output


def test_memory_statistics_retention_period_invalid(mock_db):
    """Test setting an invalid retention period for Memory Statistics."""
    runner = CliRunner()
    invalid_value = 50  # Out of valid range

    with patch("click.echo") as mock_echo, patch("syslog.syslog") as mock_syslog:
        result = runner.invoke(memory_statistics_retention_period, [str(invalid_value)])
        assert result.exit_code == 0
        mock_echo.assert_any_call("Error: Retention period must be between 1 and 30.", err=True)
        mock_syslog.assert_any_call(syslog.LOG_ERR, "Error: Retention period must be between 1 and 30.")


def test_memory_statistics_sampling_interval(mock_db):
    """Test setting the sampling interval for Memory Statistics."""
    runner = CliRunner()
    sampling_interval_value = 10  # Within valid range

    with patch("click.echo") as mock_echo, patch("syslog.syslog") as mock_syslog:
        result = runner.invoke(memory_statistics_sampling_interval, [str(sampling_interval_value)])
        assert result.exit_code == 0
        mock_echo.assert_any_call(f"Sampling interval set to {sampling_interval_value} successfully.")
        mock_db.mod_entry.assert_called_once_with(
            "MEMORY_STATISTICS", "memory_statistics",
            {"sampling_interval": sampling_interval_value}
        )
        mock_syslog.assert_any_call(
            syslog.LOG_INFO,
            f"Sampling interval set to {sampling_interval_value} successfully."
        )
        assert "Save SONiC configuration using 'config save' to persist the changes." in result.output


def test_check_memory_statistics_table_existence(mock_db):
    """Test checking the existence of MEMORY_STATISTICS table."""
    mock_db.get_table.return_value = {"memory_statistics": {"enabled": "true"}}
    result = check_memory_statistics_table_existence(mock_db.get_table)
    assert result is True

    mock_db.get_table.return_value = {}
    result = check_memory_statistics_table_existence(mock_db.get_table)
    assert result is False
