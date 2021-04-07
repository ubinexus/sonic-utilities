import os
import traceback

from click.testing import CliRunner

import config.main as config
import show.main as show
from utilities_common.db import Db


MCLAG_DOMAIN_ID = "123"
MCLAG_SRC_IP    = "12.1.1.1"
MCLAG_PEER_IP   = "12.1.1.2"
MCLAG_PEER_LINK = "PortChannel12"
MCLAG_INVALID_SRC_IP1  = "12::1111"
MCLAG_INVALID_SRC_IP2  = "224.1.1.1"
MCLAG_INVALID_PEER_IP1  = "12::1112"
MCLAG_INVALID_PEER_IP2  = "224.1.1.2"

class TestMclag(object):
    @classmethod
    def setup_class(cls):
        os.environ['UTILITIES_UNIT_TESTING'] = "1"
        print("SETUP")

    def test_add_mclag_with_invalid_src_ip(self):
        runner = CliRunner()
        db = Db()
        obj = {'db':db.cfgdb}

        # add mclag with invalid src
        result = runner.invoke(config.config.commands["mclag"].commands["add"], [MCLAG_DOMAIN_ID, MCLAG_INVALID_SRC_IP1, MCLAG_PEER_IP, MCLAG_PEER_LINK], obj=obj)
        print(result.exit_code)
        print(result.output)
        assert result.exit_code != 0
        assert "Error: mclag src ip is invalid'" in result.output

    def test_add_mclag_with_invalid_src_mcast_ip(self):
        runner = CliRunner()
        db = Db()
        obj = {'db':db.cfgdb}

        # add mclag with invalid src
        result = runner.invoke(config.config.commands["mclag"].commands["add"], [MCLAG_DOMAIN_ID, MCLAG_INVALID_SRC_IP2, MCLAG_PEER_IP, MCLAG_PEER_LINK], obj=obj)
        print(result.exit_code)
        print(result.output)
        assert result.exit_code != 0
        assert "Error: mclag src ip is invalid'" in result.output



    @classmethod
    def teardown_class(cls):
        os.environ['UTILITIES_UNIT_TESTING'] = "0"
        print("TEARDOWN")
