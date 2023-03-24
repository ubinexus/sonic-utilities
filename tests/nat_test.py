import os
import sys
import pytest
import argparse

# import show.nat as show_nat
from show import main as show_main
from click.testing import CliRunner

from swsssdk import ConfigDBConnector
from swsscommon.swsscommon import SonicV2Connector, SonicDBConfig
from swsscommon.swsscommon import ConfigDBConnector as DBConnector
from utilities_common import cli as clicommon

from imp import load_source
test_path = os.path.dirname(os.path.abspath(__file__))
modules_path = os.path.dirname(test_path)
scripts_path = os.path.join(modules_path, "scripts")
sys.path.insert(0, modules_path)

load_source('natshow', scripts_path+'/natshow')
from natshow import *

class LocalDB(object):
    APPL_DB = 'APPL_DB'
    COUNTERS_DB = 'COUNTERS_DB'
    CONFIG_DB = 'CONFIG_DB'
    STATE_DB = 'STATE_DB'

    def __init__(self, use_unix_socket_path=None, namespace=None):
        self.db = {}
        self.db_cfg = SonicDBConfig()

    def connect(self, db_name=CONFIG_DB, wait_for_init=True, retry_on=False):
        if self.db.get(db_name) == None:
            self.db[db_name] = {}

    def delete_table(self, table, db_name=CONFIG_DB):
        del self.db[db_name][table]

    def set_entry(self, table, key, data, db_name=CONFIG_DB):
        if data is None or len(data) == 0:
            assert key in self.db[db_name][table]
            del self.db[db_name][table][key]

            if len(self.db[db_name][table]) == 0:
                del self.db[db_name][table]
        else:
            if table not in self.db[db_name]:
                self.db[db_name][table] = {}

            self.db[db_name][table][key] = { k:str(v) for k, v in data.items() }

    def mod_entry(self, table, key, data, db_name=CONFIG_DB):
        separator = self.db_cfg.getSeparator(db_name)
        redis_key = separator.join(key)

        if data is None or len(data) == 0:
            assert redis_key in self.db[db_name][table]
            del self.db[db_name][table][redis_key]

            if len(self.db[db_name][table]) == 0:
                del self.db[db_name][table]
        else:
            if table not in self.db[db_name]:
                self.db[db_name][table] = {}

            self.db[db_name][table][redis_key] = { k:str(v) for k, v in data.items() }

    def get_entry(self, table_name, entry, db_name=CONFIG_DB):
        if table_name not in self.db[db_name]:
            return {}

        return self.db[db_name][table_name].get(entry, {})

    def get_table(self, table, db_name=CONFIG_DB):
        ret_tbl = {}
        tbls = self.db[db_name].get(table, {})
        separator = self.db_cfg.getSeparator(db_name)

        for (table_name, table_data) in tbls.items():
            kv = table_name.split(separator)
            if len(kv) > 1:
                table_key = (kv[0], kv[1])
            else:
                table_key = table_name

            ret_tbl[table_key] = {}

            for k, v in table_data.items():
                if (k.endswith('@')):
                    ret_tbl[table_key][k.replace('@', '')] = v.split(',')
                else:
                    ret_tbl[table_key][k] = v

        return ret_tbl

    def mod_config(self, data, db_name=CONFIG_DB):
        self.db[db_name].update(data)

    def get_all(self, db_name, key):
        separator = self.db_cfg.getSeparator(db_name)

        keys = key.split(separator)
        table = keys[0]
        key = separator.join(keys[1:])

        return self.db.get(db_name, {}).get(table, {}).get(key)

    def exists(self, db_name, key):
        if self.get_all(db_name, key):
            return True

        return False

    def keys(self, *args, **kwargs):
        ret_keys = []

        db_name = args[0]
        key = args[1]

        separator = self.db_cfg.getSeparator(db_name)

        keys = key.split(separator)
        table = keys[0]
        key = separator.join(keys[1:])
        key = key.replace('*', '')

        tabel_data = self.db.get(db_name, {}).get(table, {})
        for entry_key in tabel_data.keys():
            if key:
                if entry_key.startswith(key):
                    ret_keys.append(entry_key)
            else:
                ret_keys.append(entry_key)

        return ret_keys


class MockCli(object):
    def __init__(self):
        self.runner = CliRunner()

    @staticmethod
    def mock_run_command(command, display_cmd=False, ignore_error=False):
        params = command.split(' ')
        if command.startswith('sudo natshow'):
            params = command.split()

            MockCli.natshow_cmds(params[2:])
        else:
            raise Exception()

    @staticmethod
    def natshow_cmds(params):
        parser = argparse.ArgumentParser(description='Display the nat information',
                                        formatter_class=argparse.RawTextHelpFormatter,
                                        epilog="""
        Examples:
        natshow -t
        natshow -s
        natshow -c
        """)

        parser.add_argument('-t', '--translations', action='store_true', help='Show the nat translations')
        parser.add_argument('-s', '--statistics', action='store_true', help='Show the nat statistics')
        parser.add_argument('-c', '--count', action='store_true', help='Show the nat translations count')

        args = parser.parse_args(params)

        show_translations = args.translations
        show_statistics = args.statistics
        show_count = args.count

        try:
            if show_translations:
                nat = NatShow()
                nat.fetch_count()
                nat.fetch_translations()
                nat.display_count()
                nat.display_translations()
            elif show_statistics:
                nat = NatShow()
                nat.fetch_statistics()
                nat.display_statistics()
            elif show_count:
                nat = NatShow()
                nat.fetch_count()
                nat.display_count()

        except Exception as e:
            pytest.fail(e)

    def show(self, cmd_str):
        params = cmd_str.split()

        result = self.runner.invoke(show_main.cli, params)
        return result

class TestShowNat:
    @pytest.fixture(scope='function')
    def mock_db(self):
        db = LocalDB()

        orig_connect = ConfigDBConnector.connect
        orig_set_entry = ConfigDBConnector.set_entry
        orig_mod_entry = ConfigDBConnector.mod_entry
        orig_get_table = ConfigDBConnector.get_table
        orig_get_entry = ConfigDBConnector.get_entry
        orig_delete_table = ConfigDBConnector.delete_table

        ConfigDBConnector.connect = db.connect
        ConfigDBConnector.set_entry = db.set_entry
        ConfigDBConnector.mod_entry = db.mod_entry
        ConfigDBConnector.get_table = db.get_table
        ConfigDBConnector.get_entry = db.get_entry
        ConfigDBConnector.delete_table = db.delete_table

        v2_connect = SonicV2Connector.connect
        v2_get_all = SonicV2Connector.get_all
        v2_exists = SonicV2Connector.exists
        v2_keys = SonicV2Connector.keys

        SonicV2Connector.connect = db.connect
        SonicV2Connector.get_all = db.get_all
        SonicV2Connector.exists = db.exists
        SonicV2Connector.keys = db.keys

        db_connect = DBConnector.connect
        db_get_table = DBConnector.get_table
        db_set_entry = DBConnector.set_entry
        db_mod_entry = DBConnector.mod_entry
        db_mod_config = DBConnector.mod_config

        DBConnector.connect = db.connect
        DBConnector.get_table = db.get_table
        DBConnector.set_entry = db.set_entry
        DBConnector.mod_entry = db.mod_entry
        DBConnector.mod_config = db.mod_config

        db.connect(db.COUNTERS_DB)
        db.set_entry('COUNTERS_GLOBAL_NAT', 'Values', {
            'MAX_NAT_ENTRIES': 1023,
            'TIMEOUT': 600,
            'UDP_TIMEOUT': 300,
            'TCP_TIMEOUT': 86400
        }, db_name=db.COUNTERS_DB)

        yield db

        SonicV2Connector.keys = v2_keys
        SonicV2Connector.v2_exists = v2_exists
        SonicV2Connector.connect = v2_connect
        SonicV2Connector.get_all = v2_get_all

        DBConnector.connect = db_connect
        DBConnector.get_table = db_get_table
        DBConnector.set_entry = db_set_entry
        DBConnector.mod_entry = db_mod_entry
        DBConnector.mod_config = db_mod_config

        ConfigDBConnector.set_entry = orig_set_entry
        ConfigDBConnector.mod_entry = orig_mod_entry
        ConfigDBConnector.get_table = orig_get_table
        ConfigDBConnector.get_entry = orig_get_entry
        ConfigDBConnector.delete_table = orig_delete_table
        ConfigDBConnector.connect = orig_connect

    @pytest.fixture(scope='function')
    def cli(self):
        orig_run_command = clicommon.run_command
        clicommon.run_command = MockCli.mock_run_command

        yield MockCli()

        clicommon.run_command = orig_run_command

    def test_show_nat_translation(self, mock_db, cli):
        expect_output = '\n'.join([
            '',
            'Static NAT Entries         ..................... 0',
            'Static NAPT Entries        ..................... 0',
            'Dynamic NAT Entries        ..................... 0',
            'Dynamic NAPT Entries       ..................... 0',
            'Static Twice NAT Entries   ..................... 0',
            'Static Twice NAPT Entries  ..................... 0',
            'Dynamic Twice NAT Entries  ..................... 0',
            'Dynamic Twice NAPT Entries ..................... 0',
            'Total SNAT/SNAPT Entries   ..................... 0',
            'Total DNAT/DNAPT Entries   ..................... 0',
            'Total Entries              ..................... 0',
            '',
            'Protocol    Source    Destination    Translated Source    Translated Destination',
            '----------  --------  -------------  -------------------  ------------------------',
            '',
            ''
        ])

        ret = cli.show('nat translations')
        assert ret.exit_code == 0
        assert ret.output == expect_output

        expect_output = '\n'.join([
            '',
            'Static NAT Entries         ..................... 0',
            'Static NAPT Entries        ..................... 0',
            'Dynamic NAT Entries        ..................... 0',
            'Dynamic NAPT Entries       ..................... 0',
            'Static Twice NAT Entries   ..................... 0',
            'Static Twice NAPT Entries  ..................... 0',
            'Dynamic Twice NAT Entries  ..................... 0',
            'Dynamic Twice NAPT Entries ..................... 0',
            'Total SNAT/SNAPT Entries   ..................... 0',
            'Total DNAT/DNAPT Entries   ..................... 0',
            'Total Entries              ..................... 0',
            '',
            ''
        ])

        ret = cli.show('nat translations count')
        assert ret.exit_code == 0
        assert ret.output == expect_output

    def test_show_nat_statistics(self, mock_db, cli):
        expect_output = '\n'.join([
            '',
            'Protocol    Source    Destination    Packets    Bytes',
            '----------  --------  -------------  ---------  -------',
            '',
            ''
        ])

        ret = cli.show('nat statistics')
        assert ret.exit_code == 0
        assert ret.output == expect_output