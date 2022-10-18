import os
import sys
from swsscommon.swsscommon import SonicV2Connector
from click.testing import CliRunner
from utilities_common.db import Db

import acl_loader.main as acl_loader_show
from acl_loader import *
from acl_loader.main import *

class TestShowMirror(object):
    def test_mirror_show(self):
        runner = CliRunner()
        aclloader = AclLoader()
        aclloader.configdb.set_entry("MIRROR_SESSION", "session1", {"direction": "BOTH", "dst_port": "Ethernet30", "src_port": "Ethernet40", "type": "SPAN"})
        aclloader.configdb.set_entry("MIRROR_SESSION", "session2", {"direction": "BOTH", "dst_port": "Ethernet7", "src_port": "Ethernet8", "type": "SPAN"})
        aclloader.configdb.set_entry("MIRROR_SESSION", "session11", {"direction": "RX", "dst_port": "Ethernet9", "src_port": "Ethernet10", "type": "SPAN"})
        aclloader.configdb.set_entry("MIRROR_SESSION", "session15", {"direction": "TX", "dst_port": "Ethernet2", "src_port": "Ethernet3", "type": "SPAN"})
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
        assert result.exit_code == 0
        assert result.output == expected_output
