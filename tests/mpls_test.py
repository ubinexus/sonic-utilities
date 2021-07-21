import os
from importlib import reload
import sys
import traceback
from unittest import mock

from click.testing import CliRunner

from .mock_tables import dbconnector

import config.main as config
import show.main as show
from utilities_common.db import Db

show_interfaces_mpls_output="""\
Interface     MPLS State
------------  ------------
Ethernet2     enable
Ethernet4     disable
Ethernet8     disable
Ethernet16    disable
Loopback0     disable
PortChannel2  disable
Vlan2         enable
"""

show_interfaces_mpls_output_1="""\
Interface     MPLS State
------------  ------------
Ethernet2     enable
Ethernet4     enable
Ethernet8     disable
Ethernet16    disable
Loopback0     disable
PortChannel2  disable
Vlan2         enable
"""

show_interfaces_mpls_specific_output="""\
Interface    MPLS State
-----------  ------------
Ethernet4    disable
"""

show_interfaces_mpls_output_frontend="""\
Interface     MPLS State
------------  ------------
Ethernet12    disable
Ethernet16    enable
Ethernet28    enable
Ethernet40    disable
Loopback0     disable
PortChannel2  disable
Vlan2         enable
"""

show_interfaces_mpls_output_all="""\
Interface    MPLS State
-----------  ------------
"""

modules_path = os.path.join(os.path.dirname(__file__), "..")
test_path = os.path.join(modules_path, "tests")
scripts_path = os.path.join(modules_path, "scripts")
sys.path.insert(0, modules_path)
sys.path.insert(0, test_path)
mock_db_path = os.path.join(test_path, "mpls_input")
masic_mock_db_path = os.path.join(test_path, "mock_tables")
masic0_mock_db_path = os.path.join(masic_mock_db_path, "asic0")


class TestMpls(object):
    @classmethod
    def setup_class(cls):
        print("SETUP")
        os.environ['UTILITIES_UNIT_TESTING'] = "1"

    def test_config_mpls_add(self):
        runner = CliRunner()
        db = Db()
        obj = {'config_db':db.cfgdb}

        result = runner.invoke(config.config.commands["interface"].commands["mpls"].commands["add"], ["Ethernet4"], obj=obj)
        print(result.exit_code)
        print(result.output)
        assert result.exit_code == 0
        assert db.cfgdb.get_entry("INTERFACE", "Ethernet4") == {"mpls": "enable"}

    def test_config_mpls_masic(self):
        runner = CliRunner()
        db = Db()
        obj = {'config_db':db.cfgdb}

        result = runner.invoke(config.config.commands["interface"].commands["-n"].commands["mpls"].commands["add"], ["Ethernet8"], obj=obj)
        print(result.exit_code)
        print(result.output)
        assert 1 == 0

    def test_show_interfaces_mpls_frontend(self):
        jsonfile = os.path.join(mock_db_path, 'appl_f_db')
        dbconnector.dedicated_dbs['APPL_DB'] = jsonfile
        
        runner = CliRunner()
        result = runner.invoke(show.cli.commands["interfaces"].commands["mpls"], [])
        print(result.output) 
        assert result.exit_code == 0
        assert result.output == show_interfaces_mpls_output_frontend

    def test_show_interfaces_mpls(self):
        jsonfile = os.path.join(mock_db_path, 'appl_db')
        dbconnector.dedicated_dbs['APPL_DB'] = jsonfile

        runner = CliRunner()
        result = runner.invoke(show.cli.commands["interfaces"].commands["mpls"], [])
        print(result.exit_code)
        print(result.output)
        assert result.exit_code == 0
        assert result.output == show_interfaces_mpls_output

    def test_show_interfaces_mpls_frontend_all(self):
        jsonfile = os.path.join(mock_db_path, 'appl_f_db')
        dbconnector.dedicated_dbs['APPL_DB'] = jsonfile

        runner = CliRunner()
        result = runner.invoke(show.cli.commands["interfaces"].commands["mpls"], ["all"])
        print(result.output)
        assert result.exit_code == 0
        assert result.output == show_interfaces_mpls_output_all

    def test_show_interfaces_mpls_dynamic(self):
        jsonfile = os.path.join(mock_db_path, 'appl1_db')
        dbconnector.dedicated_dbs['APPL_DB'] = jsonfile

        runner = CliRunner()
        result = runner.invoke(show.cli.commands["interfaces"].commands["mpls"], [])
        print(result.exit_code)
        print(result.output)
        assert result.exit_code == 0
        assert result.output == show_interfaces_mpls_output_1 
    
    def test_show_interfaces_mpls_specific(self):
        jsonfile = os.path.join(mock_db_path, 'appl_db')
        dbconnector.dedicated_dbs['APPL_DB'] = jsonfile

        runner = CliRunner()
        result = runner.invoke(show.cli.commands["interfaces"].commands["mpls"], ["Ethernet4"])
        print(result.exit_code)
        print(result.output)
        assert result.exit_code == 0
        assert result.output == show_interfaces_mpls_specific_output
    
    def test_config_mpls_remove(self):
        runner = CliRunner()
        db = Db()
        obj = {'config_db':db.cfgdb}

        result = runner.invoke(config.config.commands["interface"].commands["mpls"].commands["remove"], ["Ethernet4"], obj=obj)
        print(result.exit_code)
        print(result.output)
        assert result.exit_code == 0
        assert db.cfgdb.get_entry("INTERFACE", "Ethernet4") == {"mpls": "disable"}


class TestMplsMasic(object):
    @classmethod
    def setup_class(cls):
        print("SETUP")
        os.environ["PATH"] += os.pathsep + scripts_path
        os.environ['UTILITIES_UNIT_TESTING'] = "2"
        os.environ["UTILITIES_UNIT_TESTING_TOPOLOGY"] = "multi_asic"
        dbconnector.load_namespace_config()

    def test_config_mpls_masic(self):
        runner = CliRunner()
        db = Db()
        obj = {'config_db':db.cfgdb}

        #result = runner.invoke(config.config.commands["interface"].commands["-n"].commands["mpls"].commands["add"], ["Ethernet8"], obj=obj)
        #print(result.exit_code)
        #print(result.output)
        assert 1 == 0

    def test_show_interfaces_mpls_frontend(self):
        #import pdb; pdb.set_trace()
        #jsonfile = os.path.join(masic_mock_db_path, 'appl_db')
        #dbconnector.dedicated_dbs['APPL_DB'] = jsonfile


        runner = CliRunner()
        result = runner.invoke(show.cli.commands["interfaces"].commands["mpls"], ["-dall"])
        print(result.output)
        assert result.exit_code == 0
        assert result.output == show_interfaces_mpls_output_frontend

    def test_show_interfaces_mpls(self):
        jsonfile = os.path.join(mock_db_path, 'appl_db')
        dbconnector.dedicated_dbs['APPL_DB'] = jsonfile

        runner = CliRunner()
        result = runner.invoke(show.cli.commands["interfaces"].commands["mpls"], [])
        print(result.exit_code)
        print(result.output)
        assert result.exit_code == 0
        assert result.output == show_interfaces_mpls_output

    def test_show_interfaces_mpls_frontend_all(self):
        jsonfile = os.path.join(mock_db_path, 'appl_f_db')
        dbconnector.dedicated_dbs['APPL_DB'] = jsonfile

        runner = CliRunner()
        result = runner.invoke(show.cli.commands["interfaces"].commands["mpls"], ["all"])
        print(result.output)
        assert result.exit_code == 0
        assert result.output == show_interfaces_mpls_output_all

    def test_show_interfaces_mpls_dynamic(self):
        jsonfile = os.path.join(mock_db_path, 'appl1_db')
        dbconnector.dedicated_dbs['APPL_DB'] = jsonfile

        runner = CliRunner()
        result = runner.invoke(show.cli.commands["interfaces"].commands["mpls"], [])
        print(result.exit_code)
        print(result.output)
        assert result.exit_code == 0
        assert result.output == show_interfaces_mpls_output_1



    @classmethod
    def teardown_class(cls):
        print("TEARDOWN")
        os.environ['UTILITIES_UNIT_TESTING'] = "0"
        dbconnector.dedicated_dbs['APPL_DB'] = None
