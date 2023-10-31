import imp
import os
import sys
import pytest
import traceback
from unittest import mock

import click
from click.testing import CliRunner
from utilities_common.db import Db
from mock import patch

import show.main as show
import config.main as config
import show.nac as nac
import config.validated_config_db_connector as validated_config_db_connector

test_path = os.path.dirname(os.path.abspath(__file__))
modules_path = os.path.dirname(test_path)
mock_db_path = os.path.join(test_path, "nac_input")
sys.path.insert(0, test_path)
sys.path.insert(0, modules_path)

# Expected output for 'show nac'
show_nac_output = """
NAC Global Information:
  NAC Admin State:            down
  NAC Type       :            port
  NAC Authentication Type :   local
"""

show_nac_output_enable = """
NAC Global Information:
  NAC Admin State:            up
  NAC Type       :            port
  NAC Authentication Type :   local
"""
# Expected output for 'show nac interface Ethernet0'
show_nac_interface_name_output = """\
+-----------------+------------------+-----------------------+------------------+
| InterfaceName   | NAC AdminState   | Authorization State   | Mapped Profile   |
+=================+==================+=======================+==================+
| Ethernet4       | down             | unauthorized          |                  |
+-----------------+------------------+-----------------------+------------------+
"""

show_nac_interface_all_output = """\
+-----------------+------------------+-----------------------+------------------+
| InterfaceName   | NAC AdminState   | Authorization State   | Mapped Profile   |
+=================+==================+=======================+==================+
| Ethernet0       | down             | unauthorized          |                  |
+-----------------+------------------+-----------------------+------------------+
| Ethernet4       | down             | unauthorized          |                  |
+-----------------+------------------+-----------------------+------------------+
"""
class TestShowNac(object):
    @classmethod
    def setup_class(cls):
        print("SETUP")
        os.environ["UTILITIES_UNIT_TESTING"] = "1"
        import config.main
        imp.reload(config.main)
        import show.main
        imp.reload(show.main)

    def test_show_nac(self):
        runner = CliRunner()
        result = runner.invoke(show.cli.commands["nac"], [], obj=Db())
        print(result.exit_code, result.output)
        assert result.exit_code == 0
        assert result.output == show_nac_output

    def test_show_nac_interface_default(self):
        runner = CliRunner()
        db = Db()
        result = runner.invoke(show.cli.commands["nac"].commands["interface"], ["all"], obj=Db())
        print(result.exit_code, result.output)
        assert result.exit_code == 0
        assert "NAC feature not enabled" in result.output

        obj = {'db':db.cfgdb}
        #NAC feature enabled, but NAC configured as disable.
        result = runner.invoke(config.config.commands["nac"].commands["disable"], [], obj=obj)
        assert result.exit_code == 0
        
        result = runner.invoke(show.cli.commands["nac"].commands["interface"], ["all"], obj=Db())
        print(result.exit_code, result.output)
        assert result.exit_code == 0
        assert "NAC feature not enabled" in result.output
        
    def test_show_nac_interface_name(self, get_cmd_module):
        (config, show) = get_cmd_module
        runner = CliRunner()
        db = Db()
        obj = {'db':db.cfgdb}
        #enable
        result = runner.invoke(config.config.commands["nac"].commands["enable"], [], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code == 0
        
        db.cfgdb.mod_entry("NAC_SESSION", "Ethernet4", \
            {'admin_state' : 'down', \
            'nac_status'   : 'unauthorized', \
            } \
        )

        result = runner.invoke(show.cli.commands["nac"].commands["interface"], ["Ethernet4"], obj=db)
        print(result.exit_code, result.output)
        assert result.exit_code == 0
        assert result.output == show_nac_interface_name_output

    def test_show_nac_interface_all(self):
        runner = CliRunner()
        db = Db()
        obj = {'db':db.cfgdb}
        #enable
        result = runner.invoke(config.config.commands["nac"].commands["enable"], [], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code == 0
        
        db.cfgdb.mod_entry("NAC_SESSION", "Ethernet0", \
            {'admin_state' : 'down', \
            'nac_status'   : 'unauthorized', \
            } \
        )
        db.cfgdb.mod_entry("NAC_SESSION", "Ethernet4", \
            {'admin_state' : 'down', \
            'nac_status'   : 'unauthorized', \
            } \
        )

        result = runner.invoke(show.cli.commands["nac"].commands["interface"], ["all"], obj=db)
        print(result.exit_code, result.output)
        assert result.exit_code == 0
        assert result.output == show_nac_interface_all_output 

    def test_config_nac_enable_disable(self):
        db = Db()
        runner = CliRunner()
        obj = {'db':db.cfgdb}
        
        #disable - default check
        result = runner.invoke(config.config.commands["nac"].commands["disable"], [], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code == 0

        #enable
        result = runner.invoke(config.config.commands["nac"].commands["enable"], [], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code == 0

        # change the output
        global show_nac_output
        show_nac_output_local = show_nac_output.replace(
            'NAC Admin State:            down',
            'NAC Admin State:            up')

        # run show and check
        result = runner.invoke(show.cli.commands["nac"], [], obj=db)
        print(result.exit_code, result.output, show_nac_output_local)
        print(result.output, file=sys.stderr)
        traceback.print_tb(result.exc_info[2])
        assert result.exit_code == 0
        assert result.output == show_nac_output_local

        #disable
        result = runner.invoke(config.config.commands["nac"].commands["disable"], [], obj=obj)
        print(result.exit_code, result.output)
        traceback.print_tb(result.exc_info[2])
        assert result.exit_code == 0

        # run show and check
        result = runner.invoke(show.cli.commands["nac"], [], obj=db)
        print(result.exit_code, result.output)
        traceback.print_tb(result.exc_info[2])
        assert result.exit_code == 0
        assert result.output == show_nac_output

        return

    def test_config_nac_type(self):
        db = Db()
        runner = CliRunner()
        obj = {'db':db.cfgdb}

        #mac - default behavior
        result = runner.invoke(config.config.commands["nac"].commands["type"], ["mac"], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code == 0

        #enable
        result = runner.invoke(config.config.commands["nac"].commands["enable"], [], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code == 0
        
        #mac
        result = runner.invoke(config.config.commands["nac"].commands["type"], ["mac"], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code == 0

        # change the output
        global show_nac_output_enable 
        show_nac_output_enable_local = show_nac_output_enable.replace(
            'NAC Type       :            port',
            'NAC Type       :            mac')

        # run show and check
        result = runner.invoke(show.cli.commands["nac"], [], obj=db)
        print(result.exit_code, result.output, show_nac_output_enable_local)
        assert result.exit_code == 0
        assert result.output == show_nac_output_enable_local
        
        #port
        result = runner.invoke(config.config.commands["nac"].commands["type"], ["port"], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code == 0

        # run show and check
        result = runner.invoke(show.cli.commands["nac"], [], obj=db)
        print(result.exit_code, result.output)
        assert result.exit_code == 0
        assert result.output == show_nac_output_enable

        #nac type setting when NAC feature is disabled
        result = runner.invoke(config.config.commands["nac"].commands["disable"], [], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code == 0
        #port
        result = runner.invoke(config.config.commands["nac"].commands["type"], ["port"], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code == 0
        return

    def test_config_nac_interface_name_enable_disable(self):
        runner = CliRunner()
        db = Db()
        obj = {'db':db.cfgdb}
        #enable
        result = runner.invoke(config.config.commands["nac"].commands["enable"], [], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code == 0
        
        #interface enable 
        db.cfgdb.mod_entry("NAC_SESSION", "Ethernet4", \
            {'admin_state' : 'down', \
            'nac_status'   : 'unauthorized', \
            } \
        )
        #invalid interface name
        result = runner.invoke(config.config.commands["nac"].commands["interface"].commands["enable"], ["Eth444"], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code == 0
        assert "Invalid interface name" in result.output
        result = runner.invoke(config.config.commands["nac"].commands["interface"].commands["disable"], ["Eth444"], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code == 0
        assert "Invalid interface name" in result.output

        result = runner.invoke(config.config.commands["nac"].commands["interface"].commands["enable"], ["Ethernet4"], obj=obj)
        print(result.exit_code, result.output)

        # change the output
        global show_nac_interface_name_output
        show_nac_interface_name_output_local = show_nac_interface_name_output.replace(
            'down',
            'up  ')

        # run show and check
        result = runner.invoke(show.cli.commands["nac"].commands["interface"], ["Ethernet4"], obj=db)
        print(result.output, show_nac_interface_name_output_local)
        assert result.exit_code == 0
        assert result.output == show_nac_interface_name_output_local

        #interface disable
        result = runner.invoke(config.config.commands["nac"].commands["interface"].commands["disable"], ["Ethernet4"],obj=obj)
        print(result.exit_code, result.output)

        # run show and check
        result = runner.invoke(show.cli.commands["nac"].commands["interface"], ["Ethernet4"], obj=db)
        print(result.output, show_nac_interface_name_output)
        assert result.exit_code == 0
        assert result.output == show_nac_interface_name_output

        return

    def test_config_nac_interface_all_enable_disable(self):
        db = Db()
        runner = CliRunner()
        obj = {'db':db.cfgdb}
        #-------------enable test
        #config nac interface enable all - when nac feature is not configured
        result = runner.invoke(config.config.commands["nac"].
            commands["interface"].commands["enable"], ["all"], obj=obj)
        assert result.exit_code == 0
        assert "NAC feature not enabled" in result.output
        
        #config nac interface enable all - when nac feature is configured, but disabled
        result = runner.invoke(config.config.commands["nac"].commands["disable"], [], obj=obj)
        assert result.exit_code == 0
        result = runner.invoke(config.config.commands["nac"].
            commands["interface"].commands["enable"], ["all"], obj=obj)
        assert result.exit_code == 0
        assert "NAC feature not enabled" in result.output
        
        #config nac interface enable all - when nac feature is configured, enabled but nac-type is mac
        result = runner.invoke(config.config.commands["nac"].commands["enable"], [], obj=obj)
        assert result.exit_code == 0
        result = runner.invoke(config.config.commands["nac"].commands["type"], ["mac"], obj=obj)
        assert result.exit_code == 0
        result = runner.invoke(config.config.commands["nac"].
            commands["interface"].commands["enable"], ["all"], obj=obj)
        assert result.exit_code == 0
        assert "NAC feature is not configured in port" in result.output
        
        #----------------disable test
        #config nac interface disable all - when nac feature is not configured
        db.cfgdb.delete_table("NAC")
        result = runner.invoke(config.config.commands["nac"].
            commands["interface"].commands["disable"], ["all"], obj=obj)
        assert result.exit_code == 0
        assert "NAC feature not enabled" in result.output
        
        #config nac interface disable all - when nac feature is configured, but disabled
        result = runner.invoke(config.config.commands["nac"].commands["disable"], [], obj=obj)
        assert result.exit_code == 0
        result = runner.invoke(config.config.commands["nac"].
            commands["interface"].commands["disable"], ["all"], obj=obj)
        assert result.exit_code == 0
        assert "NAC feature not enabled" in result.output
        
        #config nac interface disable all - when nac feature is configured, enabled but nac-type is mac
        result = runner.invoke(config.config.commands["nac"].commands["enable"], [], obj=obj)
        assert result.exit_code == 0
        result = runner.invoke(config.config.commands["nac"].commands["type"], ["mac"], obj=obj)
        assert result.exit_code == 0
        result = runner.invoke(config.config.commands["nac"].
            commands["interface"].commands["disable"], ["all"], obj=obj)
        assert result.exit_code == 0
        assert "NAC feature is not configured in port" in result.output
        
        #Functional test : revert to working configuration : nac-type port
        result = runner.invoke(config.config.commands["nac"].commands["type"], ["port"], obj=obj)
        assert result.exit_code == 0
        # intf enable
        result = runner.invoke(config.config.commands["nac"].
            commands["interface"].commands["enable"], ["all"], obj=obj)
        print(result.output, file=sys.stderr)
        traceback.print_tb(result.exc_info[2])
        assert result.exit_code == 0
        # intf disable
        result = runner.invoke(config.config.commands["nac"].
            commands["interface"].commands["disable"], ["all"], obj=obj)
        print(result.output, file=sys.stderr)
        traceback.print_tb(result.exc_info[2])
        assert result.exit_code == 0

        return

    @classmethod
    def teardown_class(cls):
        print("TEARDOWN")
        os.environ["UTILITIES_UNIT_TESTING"] = "0"
