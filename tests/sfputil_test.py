import sys
import os
from unittest import mock

import pytest
from click.testing import CliRunner

test_path = os.path.dirname(os.path.abspath(__file__))
modules_path = os.path.dirname(test_path)
sys.path.insert(0, modules_path)


@pytest.fixture(autouse=True)
def do_imports():
    with mock.patch.dict("sys.modules", sonic_platform=mock.MagicMock()):
        import sfputil.main as sfputil
        yield


class TestSfputil(object):
    def test_version(self):
        runner = CliRunner()
        result = runner.invoke(sfputil.cli.commands["version"], [])
        assert result.output == "sfputil version {}".format(sfputil.VERSION)
