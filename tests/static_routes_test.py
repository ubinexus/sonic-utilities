import os
import traceback
from unittest import mock

from click.testing import CliRunner

import config.main as config
import show.main as show
from .utils import get_result_and_return_code
from utilities_common.db import Db

ERROR_STR = '''
Error: argument is not in pattern prefix [vrf <vrf_name>] <A.B.C.D/M> nexthop <[vrf <vrf_name>] <A.B.C.D>>|<dev <dev_name>>!
''' 


class TestStaticRoutes(object):
    @classmethod
    def setup_class(cls):
        os.environ['UTILITIES_UNIT_TESTING'] = "1"
        print("SETUP")

    def test_simple_static_route(self):
        db = Db()
        runner = CliRunner()
        obj = {'config_db':db.cfgdb}

        # config route add prefix 1.2.3.4/32 nexthop 30.0.0.5
        result = runner.invoke(config.config.commands["route"].commands["add"], \
        ["prefix", "1.2.3.4/32", "nexthop", "30.0.0.5"], obj=obj)
        print(result.exit_code, result.output)
        assert ('1.2.3.4/32') in db.cfgdb.get_table('STATIC_ROUTE')
        assert db.cfgdb.get_entry('STATIC_ROUTE', '1.2.3.4/32') == {"nexthop": "30.0.0.5"}

        # config route del prefix 1.2.3.4/32 nexthop 30.0.0.5
        result = runner.invoke(config.config.commands["route"].commands["del"], \
        ["prefix", "1.2.3.4/32", "nexthop", "30.0.0.5"], obj=obj)
        print(result.exit_code, result.output)
        assert not ('1.2.3.4/32') in db.cfgdb.get_table('STATIC_ROUTE')

    def test_vrf_static_route(self):
        db = Db()
        runner = CliRunner()
        obj = {'config_db':db.cfgdb}

        # config route add prefix 2.2.3.4/32 nexthop 30.0.0.6
        result = runner.invoke(config.config.commands["route"].commands["add"], \
        ["prefix", "vrf", "Vrf-BLUE", "2.2.3.4/32", "nexthop", "30.0.0.6"], obj=obj)
        print(result.exit_code, result.output)
        assert ('Vrf-BLUE', '2.2.3.4/32') in db.cfgdb.get_table('STATIC_ROUTE')
        assert db.cfgdb.get_entry('STATIC_ROUTE', 'Vrf-BLUE|2.2.3.4/32') == {'nexthop': '30.0.0.6'}

        # config route del prefix 2.2.3.4/32 nexthop 30.0.0.6
        result = runner.invoke(config.config.commands["route"].commands["del"], \
        ["prefix", "vrf", "Vrf-BLUE", "2.2.3.4/32", "nexthop", "30.0.0.6"], obj=obj)
        print(result.exit_code, result.output)
        assert not ('Vrf-BLUE', '2.2.3.4/32') in db.cfgdb.get_table('STATIC_ROUTE')

    def test_dest_vrf_static_route(self):
        db = Db()
        runner = CliRunner()
        obj = {'config_db':db.cfgdb}

        # config route add prefix 3.2.3.4/32 nexthop 30.0.0.6
        result = runner.invoke(config.config.commands["route"].commands["add"], \
        ["prefix", "3.2.3.4/32", "nexthop", "vrf", "Vrf-RED", "30.0.0.6"], obj=obj)
        print(result.exit_code, result.output)
        assert ('3.2.3.4/32') in db.cfgdb.get_table('STATIC_ROUTE')
        assert db.cfgdb.get_entry('STATIC_ROUTE', '3.2.3.4/32') == {"nexthop": "30.0.0.6", "nexthop-vrf": "Vrf-RED"}

        # config route del prefix 3.2.3.4/32 nexthop 30.0.0.6
        result = runner.invoke(config.config.commands["route"].commands["del"], \
        ["prefix", "3.2.3.4/32", "nexthop", "vrf", "Vrf-RED", "30.0.0.6"], obj=obj)
        print(result.exit_code, result.output)
        assert not ('3.2.3.4/32') in db.cfgdb.get_table('STATIC_ROUTE')

    def test_several_nexthops_static_route(self):
        db = Db()
        runner = CliRunner()
        obj = {'config_db':db.cfgdb}

        # config route add prefix 3.2.3.4/32 nexthop "30.0.0.6,30.0.0.7"
        result = runner.invoke(config.config.commands["route"].commands["add"], \
        ["prefix", "6.2.3.4/32", "nexthop", "30.0.0.6,30.0.0.7"], obj=obj)
        print(result.exit_code, result.output)
        assert ('6.2.3.4/32') in db.cfgdb.get_table('STATIC_ROUTE')
        assert db.cfgdb.get_entry('STATIC_ROUTE', '6.2.3.4/32') == {"nexthop": "30.0.0.6,30.0.0.7"}

        # config route del prefix 3.2.3.4/32 nexthop "30.0.0.6,30.0.0.7"
        result = runner.invoke(config.config.commands["route"].commands["del"], \
        ["prefix", "6.2.3.4/32", "nexthop", "30.0.0.6,30.0.0.7"], obj=obj)
        print(result.exit_code, result.output)
        assert not ('6.2.3.4/32') in db.cfgdb.get_table('STATIC_ROUTE')

    def test_static_route_miss_prefix(self):
        db = Db()
        runner = CliRunner()
        obj = {'config_db':db.cfgdb}

        # config route add nexthop 30.0.0.6
        result = runner.invoke(config.config.commands["route"].commands["add"], ["nexthop", "30.0.0.6"], obj=obj)
        print(result.exit_code, result.output)
        assert ERROR_STR in result.output

    def test_static_route_miss_nexthop(self):
        db = Db()
        runner = CliRunner()
        obj = {'config_db':db.cfgdb}

        # config route add prefix 7.2.3.4/32
        result = runner.invoke(config.config.commands["route"].commands["add"], ["prefix", "7.2.3.4/32"], obj=obj)
        print(result.exit_code, result.output)
        assert ERROR_STR in result.output

    @classmethod
    def teardown_class(cls):
        os.environ['UTILITIES_UNIT_TESTING'] = "0"
        print("TEARDOWN") 

