import importlib

from click.testing import CliRunner
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
    
    def test_kdump_remote_enable(self, get_cmd_module):
        (config, show) = get_cmd_module
        db = Db()
        runner = CliRunner()

        # Enable remote mode
        result = runner.invoke(config.config.commands["kdump"].commands["remote"], ["enable"], obj=db)
        print(result.exit_code)
        assert result.exit_code == 0

        # Try enabling again
        result = runner.invoke(config.config.commands["kdump"].commands["remote"], ["enable"], obj=db)
        print(result.output)
        assert "Error: Kdump Remote Mode is already enabled." in result.output

    def test_kdump_remote_disable_without_ssh(self, get_cmd_module):
        (config, show) = get_cmd_module
        db = Db()
        runner = CliRunner()

        # Disable remote mode
        result = runner.invoke(config.config.commands["kdump"].commands["remote"], ["disable"], obj=db)
        print(result.exit_code)
        assert result.exit_code == 0

        # Try disabling again
        result = runner.invoke(config.config.commands["kdump"].commands["remote"], ["disable"], obj=db)
        print(result.output)
        assert "Error: Kdump Remote Mode is already disabled." in result.output

    def test_kdump_remote_disable_with_ssh(self, get_cmd_module):
        (config, show) = get_cmd_module
        db = Db()
        runner = CliRunner()

        # Enable remote mode first
        runner.invoke(config.config.commands["kdump"].commands["remote"], ["enable"], obj=db)

        # Add ssh_string and ssh_key to the config DB
        db.cfgdb.mod_entry("KDUMP", "config", {"ssh_string": "ssh_value", "ssh_key": "ssh_key_value"})

        # Try disabling remote mode while ssh_string and ssh_key are still configured
        result = runner.invoke(config.config.commands["kdump"].commands["remote"], ["disable"], obj=db)
        print(result.output)
        assert "Error: Remove SSH_string and SSH_key from Config DB before disabling Kdump Remote Mode." in result.output

        # Remove ssh_string and ssh_key from the config DB
        db.cfgdb.mod_entry("KDUMP", "config", {"ssh_string": "", "ssh_key": ""})

        # Now disable remote mode
        result = runner.invoke(config.config.commands["kdump"].commands["remote"], ["disable"], obj=db)
        print(result.exit_code)
        assert result.exit_code == 0

    def test_add_kdump_item_without_remote_enabled(self, get_cmd_module):
        (config, show) = get_cmd_module
        db = Db()
        runner = CliRunner()

        # Attempt to add ssh_string without enabling remote mode
        result = runner.invoke(config.config.commands["kdump"].commands["add"], ["ssh_string", "test_ssh_string"], obj=db)
        print(result.output)
        assert "Error: Enable remote mode first." in result.output

    def test_add_kdump_item_already_added(self, get_cmd_module):
        (config, show) = get_cmd_module
        db = Db()
        runner = CliRunner()

        # Enable remote mode
        db.cfgdb.mod_entry("KDUMP", "config", {"remote": "true"})

        # Add ssh_string
        result = runner.invoke(config.config.commands["kdump"].commands["add"], ["ssh_string", "test_ssh_string"], obj=db)
        print(result.exit_code)
        assert result.exit_code == 0

        # Attempt to add ssh_string again
        result = runner.invoke(config.config.commands["kdump"].commands["add"], ["ssh_string", "test_ssh_string"], obj=db)
        print(result.output)
        assert "Error: ssh_string is already added." in result.output

    def test_add_kdump_item_success(self, get_cmd_module):
        (config, show) = get_cmd_module
        db = Db()
        runner = CliRunner()

        # Enable remote mode
        db.cfgdb.mod_entry("KDUMP", "config", {"remote": "true"})

        # Add ssh_key
        result = runner.invoke(config.config.commands["kdump"].commands["add"], ["ssh_key", "test_ssh_key"], obj=db)
        print(result.exit_code)
        assert result.exit_code == 0

        # Verify the ssh_key is added in config_db
        kdump_table = db.cfgdb.get_table("KDUMP")
        assert kdump_table["config"]["ssh_key"] == "test_ssh_key"
        

    def test_remove_kdump_item_not_configured(self, get_cmd_module):
        (config, show) = get_cmd_module
        db = Db()
        runner = CliRunner()

        # Attempt to remove ssh_string that is not configured
        result = runner.invoke(config.config.commands["kdump"].commands["remove"], ["ssh_string"], obj=db)
        print(result.output)
        assert "Error: ssh_string is not configured." in result.output

    def test_remove_kdump_item_success(self, get_cmd_module):
        (config, show) = get_cmd_module
        db = Db()
        runner = CliRunner()

        # Add ssh_string to config_db to test removal
        db.cfgdb.mod_entry("KDUMP", "config", {"ssh_string": "test_ssh_string"})

        # Remove ssh_string
        result = runner.invoke(config.config.commands["kdump"].commands["remove"], ["ssh_string"], obj=db)
        print(result.exit_code)
        assert result.exit_code == 0

        # Verify the ssh_string is removed from config_db
        kdump_table = db.cfgdb.get_table("KDUMP")
        assert kdump_table["config"]["ssh_string"] == ""

    def test_remove_kdump_item_success_ssh_key(self, get_cmd_module):
        (config, show) = get_cmd_module
        db = Db()
        runner = CliRunner()

        # Add ssh_key to config_db to test removal
        db.cfgdb.mod_entry("KDUMP", "config", {"ssh_key": "test_ssh_key"})

        # Remove ssh_key
        result = runner.invoke(config.config.commands["kdump"].commands["remove"], ["ssh_key"], obj=db)
        print(result.exit_code)
        assert result.exit_code == 0

        # Verify the ssh_key is removed from config_db
        kdump_table = db.cfgdb.get_table("KDUMP")
        assert kdump_table["config"]["ssh_key"] == ""

    @classmethod
    def teardown_class(cls):
        print("TEARDOWN")
