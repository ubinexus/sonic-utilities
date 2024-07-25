import importlib

from click.testing import CliRunner
from utilities_common.db import Db
from pathlib import Path


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

    def test_config_kdump_remote_enable(self, get_cmd_module):
        (config, show) = get_cmd_module
        db = Db()
        runner = CliRunner()

        # Ensure KDUMP table exists and is in the right state
        db.cfgdb.mod_entry("KDUMP", "config", {"remote": "false"})
        result = runner.invoke(config.config.commands["kdump"].commands["remote"], ["enable"], obj=db)
        print(result.exit_code)
        assert result.exit_code == 0
        assert "Updated /etc/default/kdump-tools: SSH and SSH_KEY uncommented." in result.output

        # Check the file content
        file_path = Path('/etc/default/kdump-tools')
        content = file_path.read_text()
        assert "SSH" in content
        assert "SSH_KEY" in content

    def test_config_kdump_remote_disable(self, get_cmd_module):
        (config, show) = get_cmd_module
        db = Db()
        runner = CliRunner()

        # Ensure KDUMP table exists and is in the right state
        db.cfgdb.mod_entry("KDUMP", "config", {"remote": "true"})
        result = runner.invoke(config.config.commands["kdump"].commands["remote"], ["disable"], obj=db)
        print(result.exit_code)
        assert result.exit_code == 0
        assert "Updated /etc/default/kdump-tools: SSH and SSH_KEY commented out." in result.output

        # Check the file content
        file_path = Path('/etc/default/kdump-tools')
        content = file_path.read_text()
        assert "SSH" in content
        assert "SSH_KEY" in content

    def test_add_ssh_string(self, get_cmd_module):
        (config, show) = get_cmd_module
        db = Db()
        runner = CliRunner()

        # Set KDUMP remote mode to enabled
        db.cfgdb.mod_entry("KDUMP", "config", {"remote": "true"})

        # Add SSH string
        result = runner.invoke(config.config.commands["kdump"].commands["add"], ["ssh_string", "user@host"], obj=db)
        print(result.exit_code)
        assert result.exit_code == 0
        assert "Updated /etc/default/kdump-tools with new SSH settings." in result.output

        # Check the file content
        file_path = Path('/etc/default/kdump-tools')
        content = file_path.read_text()
        assert 'SSH="user@host"' in content

    def test_remove_ssh_string(self, get_cmd_module):
        (config, show) = get_cmd_module
        db = Db()
        runner = CliRunner()

        # Ensure KDUMP table exists and is in the right state
        db.cfgdb.mod_entry("KDUMP", "config", {"remote": "true", "ssh_string": "user@host"})

        # Remove SSH string
        result = runner.invoke(config.config.commands["kdump"].commands["remove"], ["ssh_string"], obj=db)
        print(result.exit_code)
        assert result.exit_code == 0
        assert "SSH_string removed successfully." in result.output

        # Check the file content
        file_path = Path('/etc/default/kdump-tools')
        content = file_path.read_text()
        assert 'SSH=""' in content

    def test_add_ssh_path(self, get_cmd_module):
        (config, show) = get_cmd_module
        db = Db()
        runner = CliRunner()

        # Set KDUMP remote mode to enabled
        db.cfgdb.mod_entry("KDUMP", "config", {"remote": "true"})

        # Add SSH path
        result = runner.invoke(config.config.commands["kdump"].commands["add"], ["ssh_path", "/path/to/key"], obj=db)
        print(result.exit_code)
        assert result.exit_code == 0
        assert "Updated /etc/default/kdump-tools with new SSH settings." in result.output

        # Check the file content
        file_path = Path('/etc/default/kdump-tools')
        content = file_path.read_text()
        assert 'SSH_KEY="/path/to/key"' in content

    def test_remove_ssh_path(self, get_cmd_module):
        (config, show) = get_cmd_module
        db = Db()
        runner = CliRunner()

        # Ensure KDUMP table exists and is in the right state
        db.cfgdb.mod_entry("KDUMP", "config", {"remote": "true", "ssh_path": "/path/to/key"})

        # Remove SSH path
        result = runner.invoke(config.config.commands["kdump"].commands["remove"], ["ssh_path"], obj=db)
        print(result.exit_code)
        assert result.exit_code == 0
        assert "ssh_path removed successfully." in result.output

        # Check the file content
        file_path = Path('/etc/default/kdump-tools')
        content = file_path.read_text()
        assert 'SSH_KEY=""' in content

    @classmethod
    def teardown_class(cls):
        print("TEARDOWN")
