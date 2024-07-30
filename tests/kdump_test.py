import importlib
from unittest import mock

from click.testing import CliRunner
from utilities_common.db import Db

import pytest
from pathlib import Path
from config.main import config


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


    @pytest.fixture
    def db():
        db = mock.MagicMock()
        db.cfgdb = mock.MagicMock()
        return db
    
    def setup_and_teardown(self, db):
        # Mock the file read and write operations
        self.file_path = Path('/etc/default/kdump-tools')
        self.mock_open = mock.mock_open(read_data="")
        self.patcher = mock.patch("builtins.open", self.mock_open)
        self.patcher.start()
        yield
        self.patcher.stop()

    def test_kdump_remote_enable(self, db):
        runner = CliRunner()
        db.cfgdb.get_table.return_value = {"config": {"remote": "false"}}
        result = runner.invoke(config.config.commands["kdump"].commands["remote"], ["enable"], obj=db)
        assert result.exit_code == 0
        db.cfgdb.mod_entry.assert_called_once_with("KDUMP", "config", {"remote": "true"})
        self.mock_open.assert_called_once_with(self.file_path, 'r')
        handle = self.mock_open()
        handle.write.assert_any_call('SSH="your_ssh_value"\n')
        handle.write.assert_any_call('SSH_KEY="your_ssh_key_value"\n')

    def test_kdump_remote_enable_already_enabled(self, db):
        runner = CliRunner()
        db.cfgdb.get_table.return_value = {"config": {"remote": "true"}}
        result = runner.invoke(config.config.commands["kdump"].commands["remote"], ["enable"], obj=db)
        assert result.exit_code == 0
        assert "Error: Kdump Remote Mode is already enabled." in result.output

    def test_kdump_remote_disable(self, db):
        runner = CliRunner()
        db.cfgdb.get_table.return_value = {"config": {"remote": "true"}}
        result = runner.invoke(config.config.commands["kdump"].commands["remote"], ["disable"], obj=db)
        assert result.exit_code == 0
        db.cfgdb.mod_entry.assert_called_once_with("KDUMP", "config", {"remote": "false"})
        self.mock_open.assert_called_once_with(self.file_path, 'r')
        handle = self.mock_open()
        handle.write.assert_any_call('#SSH="your_ssh_value"\n')
        handle.write.assert_any_call('#SSH_KEY="your_ssh_key_value"\n')

    def test_kdump_remote_disable_already_disabled(self, db):
        runner = CliRunner()
        db.cfgdb.get_table.return_value = {"config": {"remote": "false"}}
        result = runner.invoke(config.config.commands["kdump"].commands["remote"], ["disable"], obj=db)
        assert result.exit_code == 0
        assert "Error: Kdump Remote Mode is already disabled." in result.output

    def test_kdump_remote_disable_with_ssh_values(self, db):
        runner = CliRunner()
        db.cfgdb.get_table.return_value = {
            "config": {"remote": "true", "ssh_string": "some_ssh_string", "ssh_key": "some_ssh_key"}
        }
        result = runner.invoke(config.config.commands["kdump"].commands["remote"], ["disable"], obj=db)
        assert result.exit_code == 0
        expected_error_message = (
        "Error: Remove SSH_string and SSH_key from Config DB before disabling "
        "Kdump Remote Mode."
        )
        assert expected_error_message in result.output
    @classmethod
    def teardown_class(cls):
        print("TEARDOWN")
