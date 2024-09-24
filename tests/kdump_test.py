from click.testing import CliRunner
from utilities_common.db import Db
import tempfile
import os
from unittest.mock import patch, mock_open


class TestKdump:

    @classmethod
    def setup_class(cls):
        print("SETUP")

    def test_config_kdump_disable(self, get_cmd_module):
        (config, show) = get_cmd_module
        db = Db()
        runner = CliRunner()

        # Simulate command execution for 'disable'
        result = runner.invoke(config.config.commands["kdump"].commands["disable"], obj=db)
        assert result.exit_code == 0

        # Delete the 'KDUMP' table to test error case
        db.cfgdb.delete_table("KDUMP")
        result = runner.invoke(config.config.commands["kdump"].commands["disable"], obj=db)
        assert result.exit_code == 1

    def test_config_kdump_enable(self, get_cmd_module):
        (config, show) = get_cmd_module
        db = Db()
        runner = CliRunner()

        # Simulate command execution for 'enable'
        result = runner.invoke(config.config.commands["kdump"].commands["enable"], obj=db)
        assert result.exit_code == 0

        # Delete the 'KDUMP' table to test error case
        db.cfgdb.delete_table("KDUMP")
        result = runner.invoke(config.config.commands["kdump"].commands["enable"], obj=db)
        assert result.exit_code == 1

    def test_config_kdump_memory(self, get_cmd_module):
        (config, show) = get_cmd_module
        db = Db()
        runner = CliRunner()

        # Simulate command execution for 'memory'
        result = runner.invoke(config.config.commands["kdump"].commands["memory"], ["256MB"], obj=db)
        assert result.exit_code == 0

        # Delete the 'KDUMP' table to test error case
        db.cfgdb.delete_table("KDUMP")
        result = runner.invoke(config.config.commands["kdump"].commands["memory"], ["256MB"], obj=db)
        assert result.exit_code == 1

    def test_config_kdump_num_dumps(self, get_cmd_module):
        (config, show) = get_cmd_module
        db = Db()
        runner = CliRunner()

        # Simulate command execution for 'num_dumps'
        result = runner.invoke(config.config.commands["kdump"].commands["num_dumps"], ["10"], obj=db)
        assert result.exit_code == 0

        # Delete the 'KDUMP' table to test error case
        db.cfgdb.delete_table("KDUMP")
        result = runner.invoke(config.config.commands["kdump"].commands["num_dumps"], ["10"], obj=db)
        assert result.exit_code == 1

    def test_config_kdump_remote_enable(self, get_cmd_module):
        (config, show) = get_cmd_module
        db = Db()
        runner = CliRunner()

        # Simulate command execution for 'remote enable'
        # Assume the current status is disabled (string "false")
        db.cfgdb.set_entry("KDUMP", "config", {"remote": "false"})
        result = runner.invoke(config.config.commands["kdump"].commands["remote"], ["enable"], obj=db)

        # Assert exit code and output
        assert result.exit_code == 0
        assert "Remote kdump feature enabled." in result.output

        # Check if the remote feature was enabled in the database
        assert db.cfgdb.get_entry("KDUMP", "config")["remote"] == "true"  # Should be a string


    def test_config_kdump_remote_disable(self, get_cmd_module):
        (config, show) = get_cmd_module
        db = Db()
        runner = CliRunner()

        # Simulate command execution for 'remote disable'
        # Assume the current status is enabled (string "true")
        db.cfgdb.set_entry("KDUMP", "config", {"remote": "true"})
        result = runner.invoke(config.config.commands["kdump"].commands["remote"], ["disable"], obj=db)

        # Assert exit code and output
        assert result.exit_code == 0
        assert "Remote kdump feature disabled." in result.output

        # Check if the remote feature was disabled in the database
        assert db.cfgdb.get_entry("KDUMP", "config")["remote"] == "false"  # Should be a string


    def test_config_kdump_remote_already_enabled(self, get_cmd_module):
        (config, show) = get_cmd_module
        db = Db()
        runner = CliRunner()

        # Simulate command execution for 'remote enable'
        # Assume the current status is already enabled (string "true")
        db.cfgdb.set_entry("KDUMP", "config", {"remote": "true"})
        result = runner.invoke(config.config.commands["kdump"].commands["remote"], ["enable"], obj=db)

        # Assert exit code and output
        assert result.exit_code == 0
        assert "Remote kdump feature is already enabled." in result.output


    def test_config_kdump_remote_already_disabled(self, get_cmd_module):
        (config, show) = get_cmd_module
        db = Db()
        runner = CliRunner()

        # Simulate command execution for 'remote disable'
        # Assume the current status is already disabled (string "false")
        db.cfgdb.set_entry("KDUMP", "config", {"remote": "false"})
        result = runner.invoke(config.config.commands["kdump"].commands["remote"], ["disable"], obj=db)

        # Assert exit code and output
        assert result.exit_code == 0
        assert "Remote kdump feature is already disabled." in result.output


    def test_config_kdump_remote_invalid_action(self, get_cmd_module):
        (config, show) = get_cmd_module
        db = Db()
        runner = CliRunner()

        # Simulate invalid action for the 'remote' command
        result = runner.invoke(config.config.commands["kdump"].commands["remote"], ["invalid_action"], obj=db)

        # Assert exit code and output
        assert result.exit_code == 0  # Should not fail but handle gracefully
        assert "Invalid action. Use 'enable' or 'disable'." in result.output
    
    '''def test_add_ssh_key(self, get_cmd_module):
        (config, show) = get_cmd_module
        db = Db()
        runner = CliRunner()

        # Simulate that remote KDUMP is enabled
        db.cfgdb.set_entry("KDUMP", "config", {"remote": True})

        # Simulate command execution for adding SSH key
        result = runner.invoke(config.config.commands["kdump"].commands["add"], ["ssh_key", "my_ssh_key"], obj=db)
        assert result.exit_code == 0
        assert "Reboot" in result.output  # Check for reboot warning
        assert db.cfgdb.get_entry("KDUMP", "config")["SSH_KEY"] == "my_ssh_key"

    def test_add_ssh_path(self, get_cmd_module):
        (config, show) = get_cmd_module
        db = Db()
        runner = CliRunner()

        # Simulate that remote KDUMP is enabled
        db.cfgdb.set_entry("KDUMP", "config", {"remote": True})

        # Simulate command execution for adding SSH path
        result = runner.invoke(config.config.commands["kdump"].commands["add"], ["ssh_path", "/path/to/ssh"], obj=db)
        assert result.exit_code == 0
        assert "Reboot" in result.output  # Check for reboot warning
        assert db.cfgdb.get_entry("KDUMP", "config")["SSH_PATH"] == "/path/to/ssh"

    def test_add_ssh_key_remote_disabled(self, get_cmd_module):
        (config, show) = get_cmd_module
        db = Db()
        runner = CliRunner()

        # Simulate that remote KDUMP is disabled
        db.cfgdb.set_entry("KDUMP", "config", {"remote": False})

        # Simulate command execution for adding SSH key
        result = runner.invoke(config.config.commands["kdump"].commands["add"], ["ssh_key", "my_ssh_key"], obj=db)
        assert result.exit_code == 3  # Check for exit code indicating failure
        assert "Remote KDUMP is not enabled." in result.output

    def test_add_ssh_path_remote_disabled(self, get_cmd_module):
        (config, show) = get_cmd_module
        db = Db()
        runner = CliRunner()

        # Simulate that remote KDUMP is disabled
        db.cfgdb.set_entry("KDUMP", "config", {"remote": False})

        # Simulate command execution for adding SSH path
        result = runner.invoke(config.config.commands["kdump"].commands["add"], ["ssh_path", "/path/to/ssh"], obj=db)
        assert result.exit_code == 3  # Check for exit code indicating failure
        assert "Remote KDUMP is not enabled." in result.output
    
    def test_remove_ssh_key(self, get_cmd_module):
        (config, show) = get_cmd_module
        db = Db()
        runner = CliRunner()

        # Simulate existing SSH key in the KDUMP config
        db.cfgdb.set_entry("KDUMP", "config", {"ssh_string": "my_ssh_string"})

        # Simulate command execution for removing SSH key
        result = runner.invoke(config.config.commands["kdump"].commands["remove"], ["ssh_string"], obj=db)
        assert result.exit_code == 0
        assert "ssh_string removed successfully." in result.output
        assert db.cfgdb.get_entry("KDUMP", "config").get("ssh_string") == ""

    def test_remove_ssh_path(self, get_cmd_module):
        (config, show) = get_cmd_module
        db = Db()
        runner = CliRunner()

        # Simulate existing SSH path in the KDUMP config
        db.cfgdb.set_entry("KDUMP", "config", {"ssh_path": "/path/to/ssh"})

        # Simulate command execution for removing SSH path
        result = runner.invoke(config.config.commands["kdump"].commands["remove"], ["ssh_path"], obj=db)
        assert result.exit_code == 0
        assert "ssh_path removed successfully." in result.output
        assert db.cfgdb.get_entry("KDUMP", "config").get("ssh_path") == ""

    def test_remove_non_existing_ssh_key(self, get_cmd_module):
        (config, show) = get_cmd_module
        db = Db()
        runner = CliRunner()

        # Ensure no SSH key is configured
        db.cfgdb.set_entry("KDUMP", "config", {})

        # Simulate command execution for removing non-existing SSH key
        result = runner.invoke(config.config.commands["kdump"].commands["remove"], ["ssh_string"], obj=db)
        assert result.exit_code == 0  # Assuming that the command exits without error
        assert "Error: ssh_string is not configured." in result.output

    def test_remove_non_existing_ssh_path(self, get_cmd_module):
        (config, show) = get_cmd_module
        db = Db()
        runner = CliRunner()

        # Ensure no SSH path is configured
        db.cfgdb.set_entry("KDUMP", "config", {})

        # Simulate command execution for removing non-existing SSH path
        result = runner.invoke(config.config.commands["kdump"].commands["remove"], ["ssh_path"], obj=db)
        assert result.exit_code == 0  # Assuming that the command exits without error
        assert "Error: ssh_path is not configured." in result.output'''

    @classmethod
    def teardown_class(cls):
        print("TEARDOWN")
