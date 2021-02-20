import sys
import os
from unittest import mock

from click.testing import CliRunner


test_path = os.path.dirname(os.path.abspath(__file__))
modules_path = os.path.dirname(test_path)
sys.path.insert(0, modules_path)
import show.main as show


class TestShowPlatformPsu(object):
    """
        Note: `show platform psustatus` simply calls the `psushow` utility and
        passes a variety of options. Here we test that the utility is called
        with the appropriate option(s). The functionality of the underlying
        `psushow` utility is expected to be tested by a separate suite of unit tests
    """
    def test_all_psus(self):
        with mock.patch('utilities_common.cli.run_command') as mock_run_command:
            CliRunner().invoke(show.cli.commands['platform'].commands['psustatus'], [])
        assert mock_run_command.call_count == 1
        mock_run_command.assert_called_with('psushow -s', display_cmd=False)

    def test_all_psus_json(self):
        with mock.patch('utilities_common.cli.run_command') as mock_run_command:
            CliRunner().invoke(show.cli.commands['platform'].commands['psustatus'], ['--json'])
        assert mock_run_command.call_count == 1
        mock_run_command.assert_called_with('psushow -s -j', display_cmd=False)

    def test_single_psu(self):
        with mock.patch('utilities_common.cli.run_command') as mock_run_command:
            CliRunner().invoke(show.cli.commands['platform'].commands['psustatus'], ['--index=1'])
        assert mock_run_command.call_count == 1
        mock_run_command.assert_called_with('psushow -s -i 1', display_cmd=False)

    def test_single_psu_json(self):
        with mock.patch('utilities_common.cli.run_command') as mock_run_command:
            CliRunner().invoke(show.cli.commands['platform'].commands['psustatus'], ['--index=1', '--json'])
        assert mock_run_command.call_count == 1
        mock_run_command.assert_called_with('psushow -s -i 1 -j', display_cmd=False)

    def test_verbose(self):
        with mock.patch('utilities_common.cli.run_command') as mock_run_command:
            CliRunner().invoke(show.cli.commands['platform'].commands['psustatus'], ['--verbose'])
        assert mock_run_command.call_count == 1
        mock_run_command.assert_called_with('psushow -s', display_cmd=True)
