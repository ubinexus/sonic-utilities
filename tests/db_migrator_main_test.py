import os
import sys
import argparse
from unittest import mock
from deepdiff import DeepDiff

from swsscommon.swsscommon import SonicDBConfig
from sonic_py_common import device_info

test_path = os.path.dirname(os.path.abspath(__file__))
mock_db_path = os.path.join(test_path, "db_migrator_input")
modules_path = os.path.dirname(test_path)
scripts_path = os.path.join(modules_path, "scripts")
sys.path.insert(0, test_path)
sys.path.insert(0, modules_path)
sys.path.insert(0, scripts_path)

os.environ["PATH"] += os.pathsep + scripts_path


def mock_SonicDBConfig_isGlobalInit():
    return False


def mock_SonicDBConfig_isInit():
    return False


class TestMain(object):
    @classmethod
    def setup_class(cls):
        os.environ['UTILITIES_UNIT_TESTING'] = "2"

    @classmethod
    def teardown_class(cls):
        os.environ['UTILITIES_UNIT_TESTING'] = "0"

    @mock.patch('argparse.ArgumentParser.parse_args')
    def test_init(self, mock_args):
        mock_args.return_value=argparse.Namespace(namespace=None, operation='get_version', socket=None)
        import db_migrator
        db_migrator.main()

    @mock.patch('argparse.ArgumentParser.parse_args')
    def test_init_no_namespace(self, mock_args):
        SonicDBConfig.isInit = mock_SonicDBConfig_isInit
        mock_args.return_value=argparse.Namespace(namespace=None, operation='version_202405_01', socket=None)
        import db_migrator
        db_migrator.main()

    @mock.patch('argparse.ArgumentParser.parse_args')
    def test_init_namespace(self, mock_args):
        SonicDBConfig.isGlobalInit = mock_SonicDBConfig_isGlobalInit
        mock_args.return_value=argparse.Namespace(namespace="asic0", operation='version_202405_01', socket=None)
        import db_migrator
        db_migrator.main()