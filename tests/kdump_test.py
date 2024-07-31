import pytest
from click.testing import CliRunner
from unittest import mock
from config.main import config
from utilities_common.db import Db

class TestKdump(object):
    @classmethod
    def setup_class(cls):
        print("SETUP")

    def test_config_kdump_disable(self, get_cmd_module):
        (config, show) = get_cmd_module
        db = Db()
        runner = CliRunner()
        result = runner.invoke(config.config.commands["kdump"].commands["disable"], obj=db)
        print(result.exit_code)
        assert result.exit_code == 0

        # Delete the 'KDUMP' table.
        db.cfgdb.delete_table("KDUMP")

        result = runner.invoke(config.config.commands["kdump"].commands["disable"], obj=db)
        print(result.exit_code)
        assert result.exit_code == 1

    def test_config_kdump_enable(self, get_cmd_module):
        (config, show) = get_cmd_module
        db = Db()
        runner = CliRunner()
        result = runner.invoke(config.config.commands["kdump"].commands["enable"], obj=db)
        print(result.exit_code)
        assert result.exit_code == 0

        # Delete the 'KDUMP' table.
        db.cfgdb.delete_table("KDUMP")

        result = runner.invoke(config.config.commands["kdump"].commands["enable"], obj=db)
        print(result.exit_code)
        assert result.exit_code == 1

    def test_config_kdump_memory(self, get_cmd_module):
        (config, show) = get_cmd_module
        db = Db()
        runner = CliRunner()
        result = runner.invoke(config.config.commands["kdump"].commands["memory"], ["256MB"], obj=db)
        print(result.exit_code)
        assert result.exit_code == 0

        # Delete the 'KDUMP' table.
        db.cfgdb.delete_table("KDUMP")

        result = runner.invoke(config.config.commands["kdump"].commands["memory"], ["256MB"], obj=db)
        print(result.exit_code)
        assert result.exit_code == 1

    def test_config_kdump_num_dumps(self, get_cmd_module):
        (config, show) = get_cmd_module
        db = Db()
        runner = CliRunner()
        result = runner.invoke(config.config.commands["kdump"].commands["num_dumps"], ["10"], obj=db)
        print(result.exit_code)
        assert result.exit_code == 0

        # Delete the 'KDUMP' table.
        db.cfgdb.delete_table("KDUMP")

        result = runner.invoke(config.config.commands["kdump"].commands["num_dumps"], ["10"], obj=db)
        print(result.exit_code)
        assert result.exit_code == 1

    @classmethod
    def teardown_class(cls):
        print("TEARDOWN")

# Mocking the database and filesystem interactions
@pytest.fixture
def db():
    db = mock.MagicMock()
    db.cfgdb = mock.MagicMock()
    return db

def check_kdump_table_existence(kdump_table):
    """Mock function for checking kdump table existence."""
    pass

class TestKdumpRemote:
    @classmethod
    def setup_class(cls):
        print("SETUP")

    def test_kdump_remote_enable(self, db):
        runner = CliRunner()
        # Mocking the initial state where remote is disabled
        db.cfgdb.get_table.return_value = {"config": {"remote": "false"}}
        
        result = runner.invoke(config.config.commands["kdump"].commands["remote"], ["enable"], obj=db)
        assert result.exit_code == 0
        db.cfgdb.mod_entry.assert_called_once_with("KDUMP", "config", {"remote": "true"})
        assert "Updated /etc/default/kdump-tools: SSH and SSH_KEY commented out." in result.output

    def test_kdump_remote_enable_already_enabled(self, db):
        runner = CliRunner()
        # Mocking the initial state where remote is already enabled
        db.cfgdb.get_table.return_value = {"config": {"remote": "true"}}
        
        result = runner.invoke(config.config.commands["kdump"].commands["remote"], ["enable"], obj=db)
        assert result.exit_code == 0
        assert "Error: Kdump Remote Mode is already enabled." in result.output

    def test_kdump_remote_disable(self, db):
        runner = CliRunner()
        # Mocking the initial state where remote is enabled
        db.cfgdb.get_table.return_value = {"config": {"remote": "true"}}
        
        result = runner.invoke(config.config.commands["kdump"].commands["remote"], ["disable"], obj=db)
        assert result.exit_code == 0
        db.cfgdb.mod_entry.assert_called_once_with("KDUMP", "config", {"remote": "false"})
        assert "Updated /etc/default/kdump-tools: SSH and SSH_KEY commented out." in result.output

    def test_kdump_remote_disable_already_disabled(self, db):
        runner = CliRunner()
        # Mocking the initial state where remote is already disabled
        db.cfgdb.get_table.return_value = {"config": {"remote": "false"}}
        
        result = runner.invoke(config.config.commands["kdump"].commands["remote"], ["disable"], obj=db)
        assert result.exit_code == 0
        assert "Error: Kdump Remote Mode is already disabled." in result.output

    def test_kdump_remote_disable_with_ssh_values(self, db):
        runner = CliRunner()
        # Mocking the initial state where remote is enabled with ssh values
        db.cfgdb.get_table.return_value = {
            "config": {"remote": "true", "ssh_string": "some_ssh_string", "ssh_key": "some_ssh_key"}
        }
        
        result = runner.invoke(config.config.commands["kdump"].commands["remote"], ["disable"], obj=db)
        assert result.exit_code == 0
        expected_output = (
            "Error: Remove SSH_string and SSH_key from Config DB before disabling "
            "Kdump Remote Mode."
        )
        assert expected_output in result.output

    @classmethod
    def teardown_class(cls):
        print("TEARDOWN")

