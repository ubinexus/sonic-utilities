import mock
import paramiko
from io import BytesIO
from click.testing import CliRunner

def mock_exec_command():
    mock_stdout = BytesIO(b"""hello world""")
    return '', mock_stdout, None

def mock_exec_error_cmd():
    mock_stdout = BytesIO()
    mock_stderr = BytesIO(b"""Error""")
    return '', mock_stdout, mock_stderr

MULTI_LC_REXEC_OUTPUT = '''======== LINE-CARD0 output: ========
hello world
======== LINE-CARD1 output: ========
hello world
'''

MULTI_LC_ERR_OUTPUT = '''======== LINE-CARD0 output: ========
Error
======== LINE-CARD1 output: ========
Error
'''

class TestRexecBgpNetwork(object):
    @classmethod
    def setup_class(cls):
        pass

    @mock.patch("sonic_py_common.device_info.is_supervisor", mock.MagicMock(return_value=True))
    @mock.patch("os.getlogin", mock.MagicMock(return_value="admin"))
    @mock.patch("rcli.utils.get_password", mock.MagicMock(return_value="dummy"))
    @mock.patch("rcli.utils.get_all_linecards", mock.MagicMock(return_value=["LINE-CARD0", "LINE-CARD1"]))
    @mock.patch.object(paramiko.SSHClient, 'connect', mock.MagicMock())
    @mock.patch.object(paramiko.SSHClient, 'exec_command', mock.MagicMock(return_value=mock_exec_command()))
    def test_show_ip_bgp_rexec(self, setup_bgp_commands):
        show = setup_bgp_commands
        runner = CliRunner()

        result = runner.invoke(show.cli.commands["ip"].commands["bgp"])
        print(result.output)
        assert result.exit_code == 0, result.output
        assert MULTI_LC_REXEC_OUTPUT == result.output

    @mock.patch("sonic_py_common.device_info.is_supervisor", mock.MagicMock(return_value=True))
    @mock.patch("os.getlogin", mock.MagicMock(return_value="admin"))
    @mock.patch("rcli.utils.get_password", mock.MagicMock(return_value="dummy"))
    @mock.patch("rcli.utils.get_all_linecards", mock.MagicMock(return_value=["LINE-CARD0", "LINE-CARD1"]))
    @mock.patch.object(paramiko.SSHClient, 'connect', mock.MagicMock())
    @mock.patch.object(paramiko.SSHClient, 'exec_command', mock.MagicMock(return_value=mock_exec_error_cmd()))
    def test_show_ip_bgp_error_rexec(self, setup_bgp_commands):
        show = setup_bgp_commands
        runner = CliRunner()

        result = runner.invoke(show.cli.commands["ip"].commands["bgp"])
        print(result.output)
        assert result.exit_code == 0, result.output
        assert MULTI_LC_ERR_OUTPUT == result.output
