import importlib
import os
import sys
from unittest import mock

import pytest
from click.testing import CliRunner


test_path = os.path.dirname(os.path.abspath(__file__))
modules_path = os.path.dirname(test_path)
scripts_path = os.path.join(modules_path, 'scripts')
sys.path.insert(0, modules_path)

sys.modules['sonic_platform'] = mock.MagicMock()

loader = importlib.machinery.SourceFileLoader(
        'psushow',
        '{}/psushow'.format(scripts_path))
spec = importlib.util.spec_from_loader(loader.name, loader)
psushow = importlib.util.module_from_spec(spec)
loader.exec_module(psushow)


class TestPsushow(object):
    def test_get_psu_status_list(self):
        expected_psu_status_list = [
            {
                'index': '1',
                'name': 'PSU 1',
                'presence': 'true',
                'status': 'OK',
                'led_status': 'green',
                'model': '0J6J4K',
                'serial': 'CN-0J6J4K-17972-5AF-0086-A00',
                'voltage': '12.19',
                'current': '8.37',
                'power': '102.1'
            },
            {
                'index': '2',
                'name': 'PSU 2',
                'presence': 'true',
                'status': 'OK',
                'led_status': 'green',
                'model': '0J6J4K',
                'serial': 'CN-0J6J4K-17972-5AF-008M-A00',
                'voltage': '12.18',
                'current': '10.07',
                'power': '122.7'
            }
        ]

        psu_status_list = psushow.get_psu_status_list()
        assert psu_status_list == expected_psu_status_list

    def test_version(self, capsys):
        with pytest.raises(SystemExit) as pytest_wrapped_e:
            with mock.patch('sys.argv', ['sfpshow', '-v']):
                psushow.main()
            assert pytest_wrapped_e.type == SystemExit
            assert pytest_wrapped_e.value.code == 0
            captured = capsys.readouterr()
            assert captured.out == 'sfpshow {}'.format(sfpshow.VERSION)

        with pytest.raises(SystemExit) as pytest_wrapped_e:
            with mock.patch('sys.argv', ['sfpshow', '--version']):
                psushow.main()
            assert pytest_wrapped_e.type == SystemExit
            assert pytest_wrapped_e.value.code == 0
            captured = capsys.readouterr()
            assert captured.out == 'sfpshow {}'.format(sfpshow.VERSION)
