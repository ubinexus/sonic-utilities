import os
import traceback
from unittest import mock

from click.testing import CliRunner

import config.main as config
import show.main as show
from utilities_common.db import Db

show_mac_aging_time="""\
Mac Aging-Time : 300 seconds

"""

class TestFdb(object):
    @classmethod
    def setup_class(cls):
        os.environ['UTILITIES_UNIT_TESTING'] = "1"
        print("SETUP")

    def test_fdb_aging_time(self):
        runner = CliRunner()
        db = Db()
        result = runner.invoke(config.config.commands["mac"].commands["aging_time"], ["300"], obj=db)
        print(result.exit_code)
        print(result.output)
        assert result.exit_code == 0
        result = runner.invoke(show.cli.commands["mac"].commands["aging-time"], [], obj=db)
        print(result.exit_code)
        print(result.output)
        assert result.exit_code == 0
        assert result.output == show_mac_aging_time

    @classmethod
    def teardown_class(cls):
        os.environ['UTILITIES_UNIT_TESTING'] = "0"
        print("TEARDOWN")
