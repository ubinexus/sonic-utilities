import os
import sys
from click.testing import CliRunner
from swsscommon.swsscommon import SonicV2Connector
from utilities_common.db import Db


import acl_loader.main as acl_loader

test_path = os.path.dirname(os.path.abspath(__file__))
mock_db_path = os.path.join(test_path, "mirror_input")

class TestShowMirror(object):
    @classmethod
    def setup_class(cls):
        print("SETUP")
        os.environ["UTILITIES_UNIT_TESTING"] = "1"

    def test_mirror_show(self):
        from .mock_tables import dbconnector
        jsonfile_config = os.path.join(mock_db_path, "config_db")
        dbconnector.dedicated_dbs['CONFIG_DB'] = jsonfile_config
        runner = CliRunner()
        db = Db()
        expected_output = """\
ERSPAN Sessions
Name    Status    SRC IP    DST IP    GRE    DSCP    TTL    Queue    Policer    Monitor Port    SRC Port    Direction
------  --------  --------  --------  -----  ------  -----  -------  ---------  --------------  ----------  -----------

SPAN Sessions
Name       Status    DST Port    SRC Port    Direction    Queue    Policer
---------  --------  ----------  ----------  -----------  -------  ---------
session1   active    Ethernet30  Ethernet40  both
session2   active    Ethernet7   Ethernet8   both
session11  active    Ethernet9   Ethernet10  rx
session15  active    Ethernet2   Ethernet3   tx
"""

        result = runner.invoke(acl_loader.cli.commands['show'].commands['session'], [], obj=db)
        dbconnector.dedicated_dbs = {}
        assert result.exit_code == 0
        assert result.output == expected_output
