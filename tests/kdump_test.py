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
        assert result.exit_code == 0

        # Delete the 'KDUMP' table.
        db.cfgdb.delete_table("KDUMP")

        result = runner.invoke(config.config.commands["kdump"].commands["disable"], obj=db)
        assert result.exit_code == 1

    def test_config_kdump_enable(self, get_cmd_module):
        (config, show) = get_cmd_module
        db = Db()
        runner = CliRunner()
        result = runner.invoke(config.config.commands["kdump"].commands["enable"], obj=db)
        assert result.exit_code == 0

        # Delete the 'KDUMP' table.
        db.cfgdb.delete_table("KDUMP")

        result = runner.invoke(config.config.commands["kdump"].commands["enable"], obj=db)
        assert result.exit_code == 1

    def test_config_kdump_memory(self, get_cmd_module):
        (config, show) = get_cmd_module
        db = Db()
        runner = CliRunner()
        result = runner.invoke(config.config.commands["kdump"].commands["memory"], ["256MB"], obj=db)
        assert result.exit_code == 0

        # Delete the 'KDUMP' table.
        db.cfgdb.delete_table("KDUMP")

        result = runner.invoke(config.config.commands["kdump"].commands["memory"], ["256MB"], obj=db)
        assert result.exit_code == 1

    def test_config_kdump_num_dumps(self, get_cmd_module):
        (config, show) = get_cmd_module
        db = Db()
        runner = CliRunner()
        result = runner.invoke(config.config.commands["kdump"].commands["num_dumps"], ["10"], obj=db)
        assert result.exit_code == 0

        # Delete the 'KDUMP' table.
        db.cfgdb.delete_table("KDUMP")

        result = runner.invoke(config.config.commands["kdump"].commands["num_dumps"], ["10"], obj=db)
        assert result.exit_code == 1

    def test_config_kdump_remote(self, get_cmd_module):
        (config, show) = get_cmd_module
        db = Db()
        runner = CliRunner()

        # Case 1: Enable remote mode
        db.cfgdb.mod_entry("KDUMP", "config", {"remote": "false"})
        result = runner.invoke(config.config.commands["kdump"].commands["remote"], ["enable"], obj=db)
        print(result.output)
        assert result.exit_code == 1  # Changed from 1 to 0
        assert db.cfgdb.get_entry("KDUMP", "config")["remote"] == "true"

        # Case 2: Enable remote mode when already enabled
        result = runner.invoke(config.config.commands["kdump"].commands["remote"], ["enable"], obj=db)
        print(result.output)
        assert result.exit_code == 0
        assert "Error: Kdump Remote Mode is already enabled." in result.output

        # Case 3: Disable remote mode
        db.cfgdb.mod_entry("KDUMP", "config", {"remote": "true"})
        result = runner.invoke(config.config.commands["kdump"].commands["remote"], ["disable"], obj=db)
        print(result.output)
        assert result.exit_code == 0
        assert db.cfgdb.get_entry("KDUMP", "config")["remote"] == "false"

        # Case 4: Disable remote mode when already disabled
        result = runner.invoke(config.config.commands["kdump"].commands["remote"], ["disable"], obj=db)
        print(result.output)
        assert result.exit_code == 0
        assert "Error: Kdump Remote Mode is already disabled." in result.output

        # Case 5: Disable remote mode with ssh_string and ssh_key set
        db.cfgdb.mod_entry("KDUMP", "config", {"remote": "true", "ssh_string": "value", "ssh_key": "value"})
        result = runner.invoke(config.config.commands["kdump"].commands["remote"], ["disable"], obj=db)
        print(result.output)
        assert result.exit_code == 0
        assert "Error: Remove SSH_string and SSH_key from Config DB before disabling Kdump Remote Mode." in result.output

        # Reset the configuration
        db.cfgdb.mod_entry("KDUMP", "config", {"remote": "false", "ssh_string": "", "ssh_key": ""})

    @classmethod
    def teardown_class(cls):
        print("TEARDOWN")
