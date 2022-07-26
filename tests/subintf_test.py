import os
import traceback

from click.testing import CliRunner

import config.main as config
import show.main as show
from utilities_common.db import Db


class TestSubinterface(object):
    @classmethod
    def setup_class(cls):
        os.environ['UTILITIES_UNIT_TESTING'] = "1"
        print("SETUP")

    def test_add_del_subintf_short_name(self):
        runner = CliRunner()
        db = Db()
        obj = {'db':db.cfgdb}
        
        result = runner.invoke(config.config.commands["subinterface"].commands["add"], ["Eth0.102", "1002"], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code == 0
        assert ('Eth0.102') in db.cfgdb.get_table('VLAN_SUB_INTERFACE')
        assert db.cfgdb.get_table('VLAN_SUB_INTERFACE')['Eth0.102']['vlan'] == '1002'
        assert db.cfgdb.get_table('VLAN_SUB_INTERFACE')['Eth0.102']['admin_status'] == 'up'

        result = runner.invoke(config.config.commands["subinterface"].commands["add"], ["Po0004.104", "1004"], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code == 0
        assert ('Po0004.104') in db.cfgdb.get_table('VLAN_SUB_INTERFACE')
        assert db.cfgdb.get_table('VLAN_SUB_INTERFACE')['Po0004.104']['vlan'] == '1004'
        assert db.cfgdb.get_table('VLAN_SUB_INTERFACE')['Po0004.104']['admin_status'] == 'up'

        result = runner.invoke(config.config.commands["subinterface"].commands["del"], ["Eth0.102"], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code == 0
        assert ('Eth0.102') not in db.cfgdb.get_table('VLAN_SUB_INTERFACE')

        result = runner.invoke(config.config.commands["subinterface"].commands["del"], ["Po0004.104"], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code == 0
        assert ('Po0004.104') not in db.cfgdb.get_table('VLAN_SUB_INTERFACE')

    def test_add_del_subintf_with_long_name(self):
        runner = CliRunner()
        db = Db()
        obj = {'db':db.cfgdb}
        
        result = runner.invoke(config.config.commands["subinterface"].commands["add"], ["Ethernet0.102"], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code == 0
        assert ('Ethernet0.102') in db.cfgdb.get_table('VLAN_SUB_INTERFACE')
        assert db.cfgdb.get_table('VLAN_SUB_INTERFACE')['Ethernet0.102']['admin_status'] == 'up'

        result = runner.invoke(config.config.commands["subinterface"].commands["add"], ["PortChannel0004.104"], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code == 0
        assert ('PortChannel0004.104') in db.cfgdb.get_table('VLAN_SUB_INTERFACE')
        assert db.cfgdb.get_table('VLAN_SUB_INTERFACE')['PortChannel0004.104']['admin_status'] == 'up'

        result = runner.invoke(config.config.commands["subinterface"].commands["del"], ["Ethernet0.102"], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code == 0
        assert ('Ethernet0.102') not in db.cfgdb.get_table('VLAN_SUB_INTERFACE')

        result = runner.invoke(config.config.commands["subinterface"].commands["del"], ["PortChannel0004.104"], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code == 0
        assert ('PortChannel0004.104') not in db.cfgdb.get_table('VLAN_SUB_INTERFACE')


    def test_add_existing_subintf_again(self):
        runner = CliRunner()
        db = Db()
        obj = {'db':db.cfgdb}
        
        result = runner.invoke(config.config.commands["subinterface"].commands["add"], ["Ethernet0.102"], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code == 0
        assert ('Ethernet0.102') in db.cfgdb.get_table('VLAN_SUB_INTERFACE')
        assert db.cfgdb.get_table('VLAN_SUB_INTERFACE')['Ethernet0.102']['admin_status'] == 'up'

        #Check if same long format subintf creation is rejected
        result = runner.invoke(config.config.commands["subinterface"].commands["add"], ["Ethernet0.102"], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code != 0

        #Check if same short format subintf creation with same encap vlan is rejected
        result = runner.invoke(config.config.commands["subinterface"].commands["add"], ["Eth0.1002", "102"], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code != 0
        assert ('Eth0.1002') not in db.cfgdb.get_table('VLAN_SUB_INTERFACE')


    def test_delete_non_existing_subintf(self):
        runner = CliRunner()
        db = Db()
        obj = {'db':db.cfgdb}
        
        result = runner.invoke(config.config.commands["subinterface"].commands["del"], ["Ethernet0.102"], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code != 0

        result = runner.invoke(config.config.commands["subinterface"].commands["del"], ["Eth0.102"], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code != 0

        result = runner.invoke(config.config.commands["subinterface"].commands["del"], ["PortChannel0004.104"], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code != 0

        result = runner.invoke(config.config.commands["subinterface"].commands["del"], ["Po0004.104"], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code != 0

    def test_invalid_subintf_creation(self):
        runner = CliRunner()
        db = Db()
        obj = {'db':db.cfgdb}

        result = runner.invoke(config.config.commands["subinterface"].commands["add"], ["Ethernet1000.102"], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code != 0

        result = runner.invoke(config.config.commands["subinterface"].commands["add"], ["PortChannel0008.102"], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code != 0

        result = runner.invoke(config.config.commands["subinterface"].commands["add"], ["Ethe0.102"], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code != 0

        #Short format subintf without encap vlan should be rejected
        result = runner.invoke(config.config.commands["subinterface"].commands["add"], ["Eth0.102"], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code != 0

        result = runner.invoke(config.config.commands["subinterface"].commands["add"], ["Po0004.102"], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code != 0

    @classmethod
    def teardown_class(cls):
        os.environ['UTILITIES_UNIT_TESTING'] = "0"
        print("TEARDOWN")
