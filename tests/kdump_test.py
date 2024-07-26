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

    def test_config_kdump_remote_enable(self, get_cmd_module):
        (config, show) = get_cmd_module
        db = Db()
        runner = CliRunner()

        result = runner.invoke(config.config.commands["kdump"].commands["remote"], ["enable"], obj=db)
        print(result.exit_code)
        assert result.exit_code == 0

        # Delete the 'KDUMP' table.
        db.cfgdb.delete_table("KDUMP")

        result = runner.invoke(config.config.commands["kdump"].commands["remote"], ["enable"], obj=db)
        print(result.exit_code)
        assert result.exit_code == 1

    def test_config_kdump_remote_disable(self, get_cmd_module):
        (config, show) = get_cmd_module
        db = Db()
        runner = CliRunner()

        result = runner.invoke(config.config.commands["kdump"].commands["remote"], ["disable"], obj=db)
        print(result.exit_code)
        assert result.exit_code == 0

        # Delete the 'KDUMP' table.
        db.cfgdb.delete_table("KDUMP")

        result = runner.invoke(config.config.commands["kdump"].commands["remote"], ["disable"], obj=db)
        print(result.exit_code)
        assert result.exit_code == 1

    def test_add_ssh_string(self, get_cmd_module):
        (config, show) = get_cmd_module
        db = Db()
        runner = CliRunner()

        # Add SSH string
        result = runner.invoke(config.config.commands["kdump"].commands["add"], ["ssh_string", "user@host"], obj=db)
        print(result.exit_code)
        assert result.exit_code == 0

        # Delete the 'KDUMP' table.
        db.cfgdb.delete_table("KDUMP")

        result = runner.invoke(config.config.commands["kdump"].commands["add"], ["ssh_string", "user@host"], obj=db)
        print(result.exit_code)
        assert result.exit_code == 1

    def test_remove_ssh_string(self, get_cmd_module):
        (config, show) = get_cmd_module
        db = Db()
        runner = CliRunner()

        # Remove SSH string
        result = runner.invoke(config.config.commands["kdump"].commands["remove"], ["ssh_string"], obj=db)
        print(result.exit_code)
        assert result.exit_code == 0

        # Delete the 'KDUMP' table.
        db.cfgdb.delete_table("KDUMP")

        result = runner.invoke(config.config.commands["kdump"].commands["remove"], ["ssh_string"], obj=db)
        print(result.exit_code)
        assert result.exit_code == 1

    def test_add_ssh_path(self, get_cmd_module):
        (config, show) = get_cmd_module
        db = Db()
        runner = CliRunner()

        # Add SSH path
        result = runner.invoke(config.config.commands["kdump"].commands["add"], ["ssh_path", "/path/to/key"], obj=db)
        print(result.exit_code)
        assert result.exit_code == 0

        # Delete the 'KDUMP' table.
        db.cfgdb.delete_table("KDUMP")

        result = runner.invoke(config.config.commands["kdump"].commands["add"], ["ssh_path", "/path/to/key"], obj=db)
        print(result.exit_code)
        assert result.exit_code == 1

    def test_remove_ssh_path(self, get_cmd_module):
        (config, show) = get_cmd_module
        db = Db()
        runner = CliRunner()

        # Remove SSH path
        result = runner.invoke(config.config.commands["kdump"].commands["remove"], ["ssh_path"], obj=db)
        print(result.exit_code)
        assert result.exit_code == 0

        # Delete the 'KDUMP' table.
        db.cfgdb.delete_table("KDUMP")

        result = runner.invoke(config.config.commands["kdump"].commands["remove"], ["ssh_path"], obj=db)
        print(result.exit_code)
        assert result.exit_code == 1

    @classmethod
    def teardown_class(cls):
        print("TEARDOWN")
