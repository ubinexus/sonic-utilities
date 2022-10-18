import os
import sys
import imp
from swsscommon.swsscommon import SonicV2Connector
from click.testing import CliRunner
from utilities_common.db import Db

import mock_tables.dbconnector
import acl_loader.main as acl_loader_show
from acl_loader import *
from acl_loader.main import *

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
        aclloader = AclLoader()
        context = {
            "acl_loader": aclloader
        }
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
        result = runner.invoke(acl_loader_show.cli.commands['show'].commands['session'], [], obj=context)
        dbconnector.dedicated_dbs = {}
        assert result.exit_code == 0
        assert result.output == expected_output
