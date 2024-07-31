import pytest
from click.testing import CliRunner
from unittest import mock
from pathlib import Path
from config.kdump import kdump_disable, kdump_enable, kdump_memory, kdump_num_dumps, kdump_remote


@pytest.fixture
def db():
    db = mock.MagicMock()
    db.cfgdb = mock.MagicMock()
    return db


class TestKdump:
    @classmethod
    def setup_class(cls):
        print("SETUP")

    def test_config_kdump_disable(self, db):
        runner = CliRunner()
        db.cfgdb.get_table.return_value = {"config": {"enabled": "true"}}

        result = runner.invoke(kdump_disable, obj=db)
        assert result.exit_code == 0
        db.cfgdb.mod_entry.assert_called_once_with("KDUMP", "config", {"enabled": "false"})

        db.cfgdb.get_table.return_value = None
        result = runner.invoke(kdump_disable, obj=db)
        assert result.exit_code == 1
        assert "Unable to retrieve 'KDUMP' table from Config DB." in result.output

    def test_config_kdump_enable(self, db):
        runner = CliRunner()
        db.cfgdb.get_table.return_value = {"config": {"enabled": "false"}}

        result = runner.invoke(kdump_enable, obj=db)
        assert result.exit_code == 0
        db.cfgdb.mod_entry.assert_called_once_with("KDUMP", "config", {"enabled": "true"})

        db.cfgdb.get_table.return_value = None
        result = runner.invoke(kdump_enable, obj=db)
        assert result.exit_code == 1
        assert "Unable to retrieve 'KDUMP' table from Config DB." in result.output

    def test_config_kdump_memory(self, db):
        runner = CliRunner()
        db.cfgdb.get_table.return_value = {"config": {"memory": "256MB"}}

        result = runner.invoke(kdump_memory, ["512MB"], obj=db)
        assert result.exit_code == 0
        db.cfgdb.mod_entry.assert_called_once_with("KDUMP", "config", {"memory": "512MB"})

        db.cfgdb.get_table.return_value = None
        result = runner.invoke(kdump_memory, ["512MB"], obj=db)
        assert result.exit_code == 1
        assert "Unable to retrieve 'KDUMP' table from Config DB." in result.output

    def test_config_kdump_num_dumps(self, db):
        runner = CliRunner()
        db.cfgdb.get_table.return_value = {"config": {"num_dumps": "3"}}

        result = runner.invoke(kdump_num_dumps, ["5"], obj=db)
        assert result.exit_code == 0
        db.cfgdb.mod_entry.assert_called_once_with("KDUMP", "config", {"num_dumps": 5})

        db.cfgdb.get_table.return_value = None
        result = runner.invoke(kdump_num_dumps, ["5"], obj=db)
        assert result.exit_code == 1
        assert "Unable to retrieve 'KDUMP' table from Config DB." in result.output

    def test_kdump_remote_enable(self, db):
        runner = CliRunner()
        db.cfgdb.get_table.return_value = {"config": {"remote": "false"}}

        mock_file_path = mock.MagicMock(spec=Path)
        mock_file_path.exists.return_value = True

        m_open = mock.mock_open(read_data="#SSH=\n#SSH_KEY=\n")
        with mock.patch("builtins.open", m_open):
            with mock.patch("your_module_name.Path", return_value=mock_file_path):
                result = runner.invoke(kdump_remote, ["enable"], obj=db)

        assert result.exit_code == 0
        db.cfgdb.mod_entry.assert_called_once_with("KDUMP", "config", {"remote": "true"})
        m_open().write.assert_any_call('SSH="your_ssh_value"\n')
        m_open().write.assert_any_call('SSH_KEY="your_ssh_key_value"\n')
        assert "Updated /etc/default/kdump-tools: SSH and SSH_KEY commented out." in result.output

    def test_kdump_remote_enable_already_enabled(self, db):
        runner = CliRunner()
        db.cfgdb.get_table.return_value = {"config": {"remote": "true"}}

        result = runner.invoke(kdump_remote, ["enable"], obj=db)
        assert result.exit_code == 1
        assert "Error: Kdump Remote Mode is already enabled." in result.output

    def test_kdump_remote_disable(self, db):
        runner = CliRunner()
        db.cfgdb.get_table.return_value = {"config": {"remote": "true"}}

        mock_file_path = mock.MagicMock(spec=Path)
        mock_file_path.exists.return_value = True

        m_open = mock.mock_open(read_data="SSH=your_ssh_value\nSSH_KEY=your_ssh_key_value\n")
        with mock.patch("builtins.open", m_open):
            with mock.patch("your_module_name.Path", return_value=mock_file_path):
                result = runner.invoke(kdump_remote, ["disable"], obj=db)

        assert result.exit_code == 0
        db.cfgdb.mod_entry.assert_called_once_with("KDUMP", "config", {"remote": "false"})
        m_open().write.assert_any_call('#SSH="your_ssh_value"\n')
        m_open().write.assert_any_call('#SSH_KEY="your_ssh_key_value"\n')
        assert "Updated /etc/default/kdump-tools: SSH and SSH_KEY commented out." in result.output

    def test_kdump_remote_disable_already_disabled(self, db):
        runner = CliRunner()
        db.cfgdb.get_table.return_value = {"config": {"remote": "false"}}

        result = runner.invoke(kdump_remote, ["disable"], obj=db)
        assert result.exit_code == 1
        assert "Error: Kdump Remote Mode is already disabled." in result.output

    def test_kdump_remote_disable_with_ssh_values(self, db):
        runner = CliRunner()
        db.cfgdb.get_table.return_value = {
            "config": {"remote": "true", "ssh_string": "some_ssh_string", "ssh_key": "some_ssh_key"}
        }

        result = runner.invoke(kdump_remote, ["disable"], obj=db)
        assert result.exit_code == 1
        expected_output = (
            "Error: Remove SSH_string and SSH_key from Config DB before disabling "
            "Kdump Remote Mode."
        )
        assert expected_output in result.output

    @classmethod
    def teardown_class(cls):
        print("TEARDOWN")
