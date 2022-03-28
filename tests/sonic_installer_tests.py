from sonic_installer.main import sonic_installer
from click.testing import CliRunner
from unittest.mock import patch, Mock

@patch("sonic_installer.main.run_command")
@patch("sonic_installer.main.SonicV2Connector")
def test_upgrade_docker_use_unix_socket_path(sonicv2connector, run_command, fs):
    runner = CliRunner()
    fs.create_file('docker.gz')
    result = runner.invoke(sonic_installer.commands['upgrade-docker'], ['swss', 'docker.gz', '-y', '--warm', '--dont-wait'])
    sonicv2connector.assert_called_with(use_unix_socket_path=True)
    print(result.exception)
    assert result.exit_code == 0
