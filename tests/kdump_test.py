import pytest
from click.testing import CliRunner
from unittest.mock import MagicMock, patch
from config.kdump import  kdump_enable, kdump_disable, kdump_memory, kdump_num_dumps, kdump_remote, add_kdump_item, remove_kdump_item

@pytest.fixture
def runner():
    return CliRunner()

@pytest.fixture
def mock_db():
    return MagicMock()

@pytest.fixture
def mock_check_kdump_table_existence():
    with patch('my_kdump_module.check_kdump_table_existence') as mock:
        yield mock

@pytest.fixture
def mock_echo_reboot_warning():
    with patch('my_kdump_module.echo_reboot_warning') as mock:
        yield mock

@pytest.fixture
def mock_file_operations():
    with patch('builtins.open', create=True) as mock_open:
        with patch('my_kdump_module.Path') as mock_path:
            mock_path.return_value.exists.return_value = True
            yield mock_open

def test_kdump_enable(runner, mock_db, mock_check_kdump_table_existence, mock_echo_reboot_warning):
    mock_db.cfgdb.get_table.return_value = {"config": {"enabled": "false"}}
    result = runner.invoke(kdump_enable, obj={'db': mock_db})
    assert result.exit_code == 0
    mock_db.cfgdb.mod_entry.assert_called_once_with("KDUMP", "config", {"enabled": "true"})
    mock_echo_reboot_warning.assert_called_once()

def test_kdump_disable(runner, mock_db, mock_check_kdump_table_existence, mock_echo_reboot_warning):
    mock_db.cfgdb.get_table.return_value = {"config": {"enabled": "true"}}
    result = runner.invoke(kdump_disable, obj={'db': mock_db})
    assert result.exit_code == 0
    mock_db.cfgdb.mod_entry.assert_called_once_with("KDUMP", "config", {"enabled": "false"})
    mock_echo_reboot_warning.assert_called_once()

def test_kdump_memory(runner, mock_db, mock_check_kdump_table_existence, mock_echo_reboot_warning):
    mock_db.cfgdb.get_table.return_value = {"config": {}}
    result = runner.invoke(kdump_memory, ['256M'], obj={'db': mock_db})
    assert result.exit_code == 0
    mock_db.cfgdb.mod_entry.assert_called_once_with("KDUMP", "config", {"memory": "256M"})
    mock_echo_reboot_warning.assert_called_once()

def test_kdump_num_dumps(runner, mock_db, mock_check_kdump_table_existence, mock_echo_reboot_warning):
    mock_db.cfgdb.get_table.return_value = {"config": {}}
    result = runner.invoke(kdump_num_dumps, [5], obj={'db': mock_db})
    assert result.exit_code == 0
    mock_db.cfgdb.mod_entry.assert_called_once_with("KDUMP", "config", {"num_dumps": 5})
    mock_echo_reboot_warning.assert_called_once()

def test_kdump_remote_enable(runner, mock_db, mock_check_kdump_table_existence, mock_echo_reboot_warning, mock_file_operations):
    mock_db.cfgdb.get_table.return_value = {"config": {"remote": "false"}}
    result = runner.invoke(kdump_remote, ['enable'], obj={'db': mock_db})
    assert result.exit_code == 0
    mock_db.cfgdb.mod_entry.assert_called_once_with("KDUMP", "config", {"remote": "true"})
    mock_echo_reboot_warning.assert_called_once()
    mock_file_operations.assert_called()

def test_kdump_remote_disable(runner, mock_db, mock_check_kdump_table_existence, mock_echo_reboot_warning, mock_file_operations):
    mock_db.cfgdb.get_table.return_value = {"config": {"remote": "true"}}
    result = runner.invoke(kdump_remote, ['disable'], obj={'db': mock_db})
    assert result.exit_code == 0
    mock_db.cfgdb.mod_entry.assert_called_once_with("KDUMP", "config", {"remote": "false"})
    mock_echo_reboot_warning.assert_called_once()
    mock_file_operations.assert_called()

def test_add_kdump_item(runner, mock_db, mock_check_kdump_table_existence, mock_echo_reboot_warning):
    mock_db.cfgdb.get_table.return_value = {"config": {"remote": "true"}}
    result = runner.invoke(add_kdump_item, ['ssh_string', 'user@host'], obj={'db': mock_db})
    assert result.exit_code == 0
    mock_db.cfgdb.mod_entry.assert_called_once_with("KDUMP", "config", {"ssh_string": "user@host"})
    mock_echo_reboot_warning.assert_called_once()

def test_add_kdump_item_remote_not_enabled(runner, mock_db, mock_check_kdump_table_existence):
    mock_db.cfgdb.get_table.return_value = {"config": {"remote": "false"}}
    result = runner.invoke(add_kdump_item, ['ssh_string', 'user@host'], obj={'db': mock_db})
    assert result.exit_code == 0
    assert "Error: Enable remote mode first." in result.output

def test_remove_kdump_item(runner, mock_db, mock_check_kdump_table_existence, mock_echo_reboot_warning):
    mock_db.cfgdb.get_table.return_value = {"config": {"ssh_string": "user@host"}}
    result = runner.invoke(remove_kdump_item, ['ssh_string'], obj={'db': mock_db})
    assert result.exit_code == 0
    mock_db.cfgdb.mod_entry.assert_called_once_with("KDUMP", "config", {"ssh_string": ""})
    mock_echo_reboot_warning.assert_called_once()

def test_remove_kdump_item_not_configured(runner, mock_db, mock_check_kdump_table_existence):
    mock_db.cfgdb.get_table.return_value = {"config": {}}
    result = runner.invoke(remove_kdump_item, ['ssh_string'], obj={'db': mock_db})
    assert result.exit_code == 0
    assert "Error: ssh_string is not configured." in result.output
