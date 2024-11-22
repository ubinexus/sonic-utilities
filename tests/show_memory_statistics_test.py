import os
import sys
import pytest
import socket
import json
from unittest import mock
from click.testing import CliRunner
from utilities_common.db import Db
from .mock_tables import dbconnector
import show.memory_statistics

class TestMemoryStatistics(object):
    @classmethod
    def setup_class(cls):
        print("SETUP")
        os.environ['UTILITIES_UNIT_TESTING'] = "1"
        
    @pytest.fixture
    def setup_db(self):
        db = Db()
        db.cfgdb.set_entry("MEMORY_STATISTICS", "memory_statistics", {
            "enabled": "true",
            "retention_period": "7",
            "sampling_interval": "1"
        })
        return db

    @pytest.fixture
    def setup_socket_response(self):
        mock_response = {
            "status": True,
            "data": "Memory Usage: 1000MB\nFree Memory: 500MB"
        }
        return mock_response

    def test_show_memory_stats_basic(self, setup_db, setup_socket_response):
        runner = CliRunner()
        obj = {'db': setup_db.cfgdb}
        
        with mock.patch('socket.socket') as mock_socket:
            mock_sock = mock_socket.return_value
            mock_sock.recv.return_value = json.dumps(setup_socket_response).encode('utf-8')
            
            result = runner.invoke(show.cli.commands["memory-stats"], [], obj=obj)
            print(result.exit_code)
            print(result.output)
            assert result.exit_code == 0
            assert "Memory Usage" in result.output

    def test_show_memory_stats_with_timerange(self, setup_db, setup_socket_response):
        runner = CliRunner()
        obj = {'db': setup_db.cfgdb}
        
        with mock.patch('socket.socket') as mock_socket:
            mock_sock = mock_socket.return_value
            mock_sock.recv.return_value = json.dumps(setup_socket_response).encode('utf-8')
            
            result = runner.invoke(show.cli.commands["memory-stats"], 
                                 ["from", "2024-01-01", "to", "2024-01-02"],
                                 obj=obj)
            print(result.exit_code)
            print(result.output)
            assert result.exit_code == 0

    @mock.patch("validated_config_db_connector.device_info.is_yang_config_validation_enabled", 
                mock.Mock(return_value=True))
    @mock.patch("config.validated_config_db_connector.ValidatedConfigDBConnector.validated_set_entry", 
                mock.Mock(side_effect=ValueError))
    def test_show_memory_stats_yang_validation_error(self, setup_db):
        runner = CliRunner()
        obj = {'db': setup_db.cfgdb}
        
        result = runner.invoke(show.cli.commands["memory-stats"], [], obj=obj)
        print(result.exit_code)
        print(result.output)
        assert "Invalid ConfigDB. Error" in result.output

    def test_show_memory_statistics_config(self, setup_db):
        runner = CliRunner()
        obj = {'db': setup_db.cfgdb}
        
        result = runner.invoke(show.cli.commands["memory-statistics"].commands["config"], 
                             [], obj=obj)
        print(result.exit_code)
        print(result.output)
        assert result.exit_code == 0
        assert "Enabled" in result.output
        assert "True" in result.output
        assert "7" in result.output
        assert "1" in result.output

    def test_socket_connection_error(self, setup_db):
        runner = CliRunner()
        obj = {'db': setup_db.cfgdb}
        
        with mock.patch('socket.socket') as mock_socket:
            mock_sock = mock_socket.return_value
            mock_sock.connect.side_effect = socket.error("Connection refused")
            
            result = runner.invoke(show.cli.commands["memory-stats"], [], obj=obj)
            print(result.exit_code)
            print(result.output)
            assert result.exit_code != 0
            assert "Could not connect to the server" in result.output

    @pytest.fixture
    def setup_dbs_high_memory_usage(self):
        with mock.patch('memory_statistics_cli.MemoryStats.get_sys_memory_stats') as mock_stats:
            mock_stats.return_value = {
                'MemAvailable': 1000000,
                'MemTotal': 20000000
            }
            yield

    def test_memory_threshold_check(self, setup_db, setup_dbs_high_memory_usage):
        runner = CliRunner()
        obj = {'db': setup_db.cfgdb}
        
        result = runner.invoke(show.cli.commands["memory-stats"], [], obj=obj)
        print(result.exit_code)
        print(result.output)
        assert result.exit_code == 0
        assert "Memory Usage" in result.output

    def test_invalid_time_format(self, setup_db):
        runner = CliRunner()
        obj = {'db': setup_db.cfgdb}
        
        result = runner.invoke(show.cli.commands["memory-stats"], 
                             ["from", "invalid-date", "to", "2024-01-02"],
                             obj=obj)
        print(result.exit_code)
        print(result.output)
        assert result.exit_code != 0
        assert "Invalid time format" in result.output

    def test_invalid_metric_selection(self, setup_db):
        runner = CliRunner()
        obj = {'db': setup_db.cfgdb}
        
        result = runner.invoke(show.cli.commands["memory-stats"], 
                             ["select", "invalid_metric"],
                             obj=obj)
        print(result.exit_code)
        print(result.output)
        assert result.exit_code != 0
        assert "Invalid metric" in result.output

    @classmethod
    def teardown_class(cls):
        print("TEARDOWN")
        os.environ['UTILITIES_UNIT_TESTING'] = "0"

if __name__ == '__main__':
    pytest.main([__file__])