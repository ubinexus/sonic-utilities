import imp
import os
import sys
import pytest

import acl_loader.main as acl_loader_show
from acl_loader import *
from acl_loader.main import *

from click.testing import CliRunner
from utilities_common.db import Db
import mock_tables.dbconnector

class TestShowAcl(object):
    def test_show_ctrl_table(self):
        runner = CliRunner()
        aclloader = AclLoader()
        aclloader.configdb.set_entry("ACL_TABLE", "CTRL_TEST", {"type": "CTRLPLANE", "policy_desc": "CTRL_TEST", "services": ["SNMP","NTP"]})
        aclloader.read_tables_info()
        context = {
            "acl_loader": aclloader
        }
        result = runner.invoke(acl_loader_show.cli.commands['show'].commands['table'], ['CTRL_TEST'], obj=context)
        assert result.exit_code == 0
        assert "CTRL_TEST" in result.output

    def test_show_ctrl_table_without_services(self):
        runner = CliRunner()
        aclloader = AclLoader()
        aclloader.configdb.set_entry("ACL_TABLE", "CTRL_TEST", {"type": "CTRLPLANE", "policy_desc": "CTRL_TEST"})
        aclloader.read_tables_info()
        context = {
            "acl_loader": aclloader
        }
        result = runner.invoke(acl_loader_show.cli.commands['show'].commands['table'], ['CTRL_TEST'], obj=context)
        assert result.exit_code == 0
        assert "CTRL_TEST" in result.output
