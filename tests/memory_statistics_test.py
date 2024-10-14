import pytest
from click.testing import CliRunner
from swsscommon.swsscommon import ConfigDBConnector
from config.memory_statistics import memory_statistics_enable, memory_statistics_disable, memory_statistics_retention_period, memory_statistics_sampling_interval
from show.memory_statistics import config as show_config, show_memory_statistics_logs


# Mocking ConfigDBConnector for all test cases
@pytest.fixture(scope="module")
def mock_db(mocker):
    mocker.patch.object(ConfigDBConnector, 'connect', return_value=None)
    mocker.patch.object(ConfigDBConnector, 'get_table', return_value={
        "memory_statistics": {
            "enabled": "false",
            "retention_time": "30",
            "sampling_interval": "5"
        }
    })
    return ConfigDBConnector()


# Test cases for config commands

def test_memory_statistics_enable(mock_db, mocker):
    runner = CliRunner()
    mock_mod_entry = mocker.patch.object(ConfigDBConnector, 'mod_entry')

    result = runner.invoke(memory_statistics_enable)
    assert result.exit_code == 0
    mock_mod_entry.assert_called_with("MEMORY_STATISTICS", "memory_statistics", {"enabled": "true", "disabled": "false"})
    assert "
