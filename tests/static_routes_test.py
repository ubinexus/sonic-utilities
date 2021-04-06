import os
import traceback
from unittest import mock

from click.testing import CliRunner

import config.main as config
import show.main as show
from .utils import get_result_and_return_code
from utilities_common.db import Db

ROUTE_UPDATE_STR = '''
Added static route 1.2.3.4/32
Added static route 2.2.3.4/32
Added static route 3.2.3.4/32
''' 


class TestStaticRoutes(object):
    @classmethod
    def setup_class(cls):
        os.environ['UTILITIES_UNIT_TESTING'] = "1"
        print("SETUP")

    '''Add'''
    def test_add_simple_static_route(self):
        db = Db()
        runner = CliRunner()
        obj = {'config_db':db.cfgdb}

        # config route add prefix 1.2.3.4/32 nexthop 30.0.0.5
        result = runner.invoke(config.config.commands["route"].commands["add"], \
        ["prefix", "1.2.3.4/32", "nexthop", "30.0.0.5"], obj=obj)
        print(result.exit_code, result.output)
        assert ('1.2.3.4/32') in db.cfgdb.get_table('STATIC_ROUTE')
        assert db.cfgdb.get_entry('STATIC_ROUTE', '1.2.3.4/32') == {"nexthop": "30.0.0.5"}

    def test_add_vrf_static_route(self):
        db = Db()
        runner = CliRunner()
        obj = {'config_db':db.cfgdb}

        # config route add prefix 2.2.3.4/32 nexthop 30.0.0.6
        result = runner.invoke(config.config.commands["route"].commands["add"], \
        ["prefix", "vrf", "Vrf-BLUE", "2.2.3.4/32", "nexthop", "30.0.0.6"], obj=obj)
        print(result.exit_code, result.output)
        assert ('Vrf-BLUE|2.2.3.4/32') in db.cfgdb.get_table('STATIC_ROUTE')
        assert db.cfgdb.get_entry('STATIC_ROUTE', 'Vrf-BLUE|2.2.3.4/32') == {'nexthop': '30.0.0.6'}

    def test_add_dest_vrf_static_route(self):
        db = Db()
        runner = CliRunner()
        obj = {'config_db':db.cfgdb}

        # config route add prefix 3.2.3.4/32 nexthop 30.0.0.6
        result = runner.invoke(config.config.commands["route"].commands["add"], \
        ["prefix", "3.2.3.4/32", "nexthop", "vrf", "Vrf-RED", "30.0.0.6"], obj=obj)
        print(result.exit_code, result.output)
        assert ('3.2.3.4/32') in db.cfgdb.get_table('STATIC_ROUTE')
        assert db.cfgdb.get_entry('STATIC_ROUTE', '3.2.3.4/32') == {"nexthop": "30.0.0.6", "nexthop-vrf": "Vrf-RED"}

    '''Del'''
    def test_del_simple_static_route(self):
        db = Db()
        runner = CliRunner()
        obj = {'config_db':db.cfgdb}
        
        # config route del prefix 1.2.3.4/32 nexthop 30.0.0.5
        result = runner.invoke(config.config.commands["route"].commands["del"], \
        ["prefix", "1.2.3.4/32", "nexthop", "30.0.0.5"], obj=obj)
        print(result.exit_code, result.output)
        assert not ('1.2.3.4/32') in db.cfgdb.get_table('STATIC_ROUTE')
 
    def test_del_vrf_static_route(self):
        db = Db()
        runner = CliRunner()
        obj = {'config_db':db.cfgdb}

        # config route del prefix 2.2.3.4/32 nexthop 30.0.0.6
        result = runner.invoke(config.config.commands["route"].commands["del"], \
        ["prefix", "vrf", "Vrf-BLUE", "2.2.3.4/32", "nexthop", "30.0.0.6"], obj=obj)
        print(result.exit_code, result.output)
        assert not ('Vrf-BLUE|2.2.3.4/32') in db.cfgdb.get_table('STATIC_ROUTE')

    def test_del_dest_vrf_static_route(self):
        db = Db()
        runner = CliRunner()
        obj = {'config_db':db.cfgdb}

        # config route del prefix 3.2.3.4/32 nexthop 30.0.0.6
        result = runner.invoke(config.config.commands["route"].commands["del"], \
        ["prefix", "3.2.3.4/32", "nexthop", "vrf", "Vrf-RED", "30.0.0.6"], obj=obj)
        print(result.exit_code, result.output)
        assert not ('3.2.3.4/32') in db.cfgdb.get_table('STATIC_ROUTE')

    @classmethod
    def teardown_class(cls):
        os.environ['UTILITIES_UNIT_TESTING'] = "0"
        print("TEARDOWN") 

