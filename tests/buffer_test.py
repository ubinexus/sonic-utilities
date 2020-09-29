import os
import sys
from click.testing import CliRunner
from unittest import TestCase
from swsssdk import ConfigDBConnector

import mock_tables.dbconnector

import config.main as config
from utilities_common.db import Db

class TestBuffer(object):
    @classmethod
    def setup_class(cls):
        os.environ['UTILITIES_UNIT_TESTING'] = "1"
        print("SETUP")

    def setUp(self):
        self.runner = CliRunner()
        self.config_db = ConfigDBConnector()
        self.config_db.connect()
        self.obj = {'db': self.config_db}

    def test_config_buffer_profile_headroom(self):
        runner = CliRunner()
        result = runner.invoke(config.config.commands["buffer"].commands["profile"].commands["add"],
                               ["testprofile", "--dynamic_th", "3", "--xon", "18432", "--xoff", "32768"])
        print(result.exit_code)
        print(result.output)
        assert result.exit_code == 0

    def test_config_buffer_profile_dynamic_th(self):
        runner = CliRunner()
        result = runner.invoke(config.config.commands["buffer"].commands["profile"].commands["add"],
                               ["testprofile", "--dynamic_th", "3"])
        print(result.exit_code)
        print(result.output)
        assert result.exit_code == 0

    def test_config_buffer_profile_add_existing(self):
        runner = CliRunner()
        result = runner.invoke(config.config.commands["buffer"].commands["profile"].commands["add"],
                               ["headroom_profile", "--dynamic_th", "3"])
        print(result.exit_code)
        print(result.output)
        assert result.exit_code != 0
        assert "Profile headroom_profile already exist" in result.output

    def test_config_buffer_profile_set_non_existing(self):
        runner = CliRunner()
        result = runner.invoke(config.config.commands["buffer"].commands["profile"].commands["set"],
                               ["non_existing_profile", "--dynamic_th", "3"])
        print(result.exit_code)
        print(result.output)
        assert result.exit_code != 0
        assert "Profile non_existing_profile doesn't exist" in result.output

    def test_config_buffer_profile_add_headroom_to_dynamic_profile(self):
        runner = CliRunner()
        result = runner.invoke(config.config.commands["buffer"].commands["profile"].commands["set"],
                               ["alpha_profile", "--dynamic_th", "3", "--xon", "18432", "--xoff", "32768"])
        print(result.exit_code)
        print(result.output)
        assert result.exit_code != 0
        assert "Can't change profile alpha_profile from dynamically calculating headroom to non-dynamically one" in result.output

    @classmethod
    def teardown_class(cls):
        os.environ['UTILITIES_UNIT_TESTING'] = "0"
        print("TEARDOWN")
