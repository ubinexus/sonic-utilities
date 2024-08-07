import os
import tempfile
import pytest
from unittest.mock import patch
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

    def test_add_kdump_item(self, get_cmd_module):
        (config, show) = get_cmd_module
        db = Db()
        runner = CliRunner()

        # Case 1: Try to add ssh_string when remote mode is disabled
        db.cfgdb.mod_entry("KDUMP", "config", {"remote": "false"})
        result = runner.invoke(config.config.commands["kdump"].commands["add"], ["ssh_string", "ssh_value"], obj=db)
        print(result.output)
        assert result.exit_code == 0
        assert "Error: Enable remote mode first." in result.output

        # Case 2: Enable remote mode and add ssh_string
        db.cfgdb.mod_entry("KDUMP", "config", {"remote": "true"})
        result = runner.invoke(config.config.commands["kdump"].commands["add"], ["ssh_string", "ssh_value"], obj=db)
        print(result.output)
        assert result.exit_code == 0
        assert db.cfgdb.get_entry("KDUMP", "config")["ssh_string"] == "ssh_value"

        # Case 3: Add ssh_string when it is already added
        result = runner.invoke(config.config.commands["kdump"].commands["add"], ["ssh_string", "new_ssh_value"], obj=db)
        print(result.output)
        assert result.exit_code == 0
        assert "Error: ssh_string is already added." in result.output

        # Case 4: Add ssh_key_path when remote mode is enabled
        result = runner.invoke(config.config.commands["kdump"].commands["add"], ["ssh_path", "ssh_key_value"], obj=db)
        print(result.output)
        assert result.exit_code == 0
        assert db.cfgdb.get_entry("KDUMP", "config")["ssh_path"] == "ssh_key_value"

        # Case 5: Add ssh_key_path when it is already added
        result = runner.invoke(config.config.commands["kdump"].commands["add"], ["ssh_path", "new_ssh_key_value"], obj=db)
        print(result.output)
        assert result.exit_code == 0
        assert "Error: ssh_path is already added." in result.output

        # Reset the configuration
        db.cfgdb.mod_entry("KDUMP", "config", {"remote": "false", "ssh_string": "", "ssh_key": ""})

    def test_config_kdump_remote(self, get_cmd_module):
        (config, show) = get_cmd_module
        db = Db()
        runner = CliRunner()

        # Create a temporary file to simulate /etc/default/kdump-tools
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            file_path = temp_file.name

        # Ensure the temporary file is cleaned up after the test
        def cleanup():
            os.remove(file_path)
        import atexit
        atexit.register(cleanup)

        def write_to_file(content):
            with open(file_path, 'w') as file:
                file.write(content)

        def read_from_file():
            with open(file_path, 'r') as file:
                return file.readlines()

        def mock_open_func(file, mode='r', *args, **kwargs):
            if file == '/etc/default/kdump-tools':
                return open(file_path, mode, *args, **kwargs)
            else:
                return open(file, mode, *args, **kwargs)

        # Patch the open function in the config module to use the temporary file
        with patch('builtins.open', mock_open_func):
            # Case 1: Enable remote mode
            db.cfgdb.mod_entry("KDUMP", "config", {"remote": "false"})
            result = runner.invoke(config.config.commands["kdump"].commands["remote"], ["enable"], obj=db)
            assert result.exit_code == 1
            assert db.cfgdb.get_entry("KDUMP", "config")["remote"] == "true"

            # Verify file updates
            write_to_file("#SSH=\n#SSH_KEY=\n")
            result = runner.invoke(config.config.commands["kdump"].commands["remote"], ["enable"], obj=db)
            lines = read_from_file()
            assert 'SSH="<user at server>"\n' in lines
            assert 'SSH_KEY="<path>"\n' in lines

            # Case 2: Enable remote mode when already enabled
            result = runner.invoke(config.config.commands["kdump"].commands["remote"], ["enable"], obj=db)
            assert result.exit_code == 0
            assert "Error: Kdump Remote Mode is already enabled." in result.output

            # Case 3: Disable remote mode
            db.cfgdb.mod_entry("KDUMP", "config", {"remote": "true"})
            result = runner.invoke(config.config.commands["kdump"].commands["remote"], ["disable"], obj=db)
            assert result.exit_code == 0
            assert db.cfgdb.get_entry("KDUMP", "config")["remote"] == "false"

            # Verify file updates
            write_to_file('SSH="<user at server>"\nSSH_KEY="<path>"\n')
            result = runner.invoke(config.config.commands["kdump"].commands["remote"], ["disable"], obj=db)
            lines = read_from_file()
            assert '#SSH=<user at server>\n' in lines
            assert '#SSH_KEY=<path>\n' in lines

            # Case 4: Disable remote mode when already disabled
            result = runner.invoke(config.config.commands["kdump"].commands["remote"], ["disable"], obj=db)
            assert result.exit_code == 0
            assert "Error: Kdump Remote Mode is already disabled." in result.output

            # Case 5: Disable remote mode with ssh_string and ssh_key set
            db.cfgdb.mod_entry("KDUMP", "config", {"remote": "true", "ssh_string": "value", "ssh_key": "value"})
            result = runner.invoke(config.config.commands["kdump"].commands["remote"], ["disable"], obj=db)
            assert result.exit_code == 0
            assert "Error: Remove SSH_string and SSH_key from Config DB before disabling Kdump Remote Mode." in result.output

            # Reset the configuration
            db.cfgdb.mod_entry("KDUMP", "config", {"remote": "false", "ssh_string": "", "ssh_key": ""})

    @classmethod
    def teardown_class(cls):
        print("TEARDOWN")
