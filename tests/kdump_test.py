from click.testing import CliRunner
from utilities_common.db import Db


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

    def test_config_kdump_remote(self, get_cmd_module):
        (config, show) = get_cmd_module
        db = Db()
        runner = CliRunner()

        # Simulate command execution for 'remote enable'
        result = runner.invoke(config.config.commands["kdump"].commands["remote"], ["enable"], obj=db)
        assert result.exit_code == 0

        # Check if remote feature is enabled
        kdump_table = db.cfgdb.get_table("KDUMP")
        assert kdump_table["config"].get("remote", "false") == "true"

        # Simulate command execution for 'remote disable'
        result = runner.invoke(config.config.commands["kdump"].commands["remote"], ["disable"], obj=db)
        assert result.exit_code == 0

        # Check if remote feature is disabled
        kdump_table = db.cfgdb.get_table("KDUMP")
        assert kdump_table["config"].get("remote", "false") == "false"

        # Delete the 'KDUMP' table to test error case
        db.cfgdb.delete_table("KDUMP")
        result = runner.invoke(config.config.commands["kdump"].commands["remote"], ["enable"], obj=db)
        assert result.exit_code == 1
    @classmethod
    def teardown_class(cls):
        print("TEARDOWN")
