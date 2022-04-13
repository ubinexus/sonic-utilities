#!/usr/bin/env python

import os
import logging
import show.main as show
import config.main as config

from .passw_hardening_input import assert_show_output
from utilities_common.db import Db
from click.testing import CliRunner
from .mock_tables import dbconnector

logger = logging.getLogger(__name__)
test_path = os.path.dirname(os.path.abspath(__file__))
mock_db_path = os.path.join(test_path, "passw_hardening_input")

SUCCESS = 0
ERROR = 1
INVALID_VALUE = 'INVALID'
EXP_GOOD_FLOW = 1
EXP_BAD_FLOW = 0

class TestPasswHardening:
    @classmethod
    def setup_class(cls):
        logger.info("SETUP")
        os.environ['UTILITIES_UNIT_TESTING'] = "2"


    @classmethod
    def teardown_class(cls):
        logger.info("TEARDOWN")
        os.environ['UTILITIES_UNIT_TESTING'] = "0"
        os.environ["UTILITIES_UNIT_TESTING_TOPOLOGY"] = ""
        dbconnector.dedicated_dbs['CONFIG_DB'] = None

    def verify_passw_policies_output(self, db, runner, output, expected=EXP_GOOD_FLOW):
        result = runner.invoke(show.cli.commands["passw-hardening"].commands["policies"], [], obj=db)
        logger.debug("\n" + result.output)
        logger.debug(result.exit_code)

        if expected: # good flow expected (default)
            assert result.exit_code == SUCCESS
            assert result.output == output
        else: # bad flow expected
            assert result.exit_code == ERROR

    def passw_hardening_set_policy(self, runner, db, attr, value, expected=EXP_GOOD_FLOW):
        result = runner.invoke(
            config.config.commands["passw-hardening"].commands["policies"].commands[attr],
            [value], obj=db
        )

        if expected: # good flow expected (default)
            logger.debug("\n" + result.output)
            logger.debug(result.exit_code)
            assert result.exit_code == SUCCESS
        else: # bad flow expected
            assert result.exit_code == ERROR


    ######### PASSW-HARDENING #########

    def test_passw_hardening_default(self):
        dbconnector.dedicated_dbs['CONFIG_DB'] = os.path.join(mock_db_path, 'default_config_db')
        db = Db()
        runner = CliRunner()

        self.verify_passw_policies_output(db, runner, assert_show_output.show_passw_hardening_policies_default)
        
    def test_passw_hardening_feature_enabled(self):
        dbconnector.dedicated_dbs['CONFIG_DB'] = os.path.join(mock_db_path, 'default_config_db')
        db = Db()
        runner = CliRunner()
        
        self.passw_hardening_set_policy(runner, db, "state", "enabled")
    
        self.verify_passw_policies_output(db, runner, assert_show_output.show_passw_hardening_policies_enabled)
        
    def test_passw_hardening_policies_classes_disabled(self):
        """Disable passw hardening classes & reject user passw match policies"""

        dbconnector.dedicated_dbs['CONFIG_DB'] = os.path.join(mock_db_path, 'default_config_db')
        db = Db()
        runner = CliRunner()

        passw_classes = {   "reject-user-passw-match": "false",
                            "digits-class": "false",
                            "lower-class": "false",
                            "special-class": "false",
                            "upper-class": "false"
        }

        for k, v in passw_classes.items():
            self.passw_hardening_set_policy(runner, db, k, v)

        self.verify_passw_policies_output(db, runner, assert_show_output.show_passw_hardening_policies_classes_disabled)
        
    def test_passw_hardening_policies_exp_time(self):
        dbconnector.dedicated_dbs['CONFIG_DB'] = os.path.join(mock_db_path, 'default_config_db')
        db = Db()
        runner = CliRunner()

        self.passw_hardening_set_policy(runner, db, "state", "enabled")
        self.passw_hardening_set_policy(runner, db, "expiration", "100")
        self.passw_hardening_set_policy(runner, db, "expiration-warning", "15")

        self.verify_passw_policies_output(db, runner, assert_show_output.show_passw_hardening_policies_expiration)

    def test_passw_hardening_policies_history(self):
        dbconnector.dedicated_dbs['CONFIG_DB'] = os.path.join(mock_db_path, 'default_config_db')
        db = Db()
        runner = CliRunner()

        self.passw_hardening_set_policy(runner, db, "history-cnt", "40")

        self.verify_passw_policies_output(db, runner, assert_show_output.show_passw_hardening_policies_history_cnt)

    def test_passw_hardening_policies_len_min(self):
        dbconnector.dedicated_dbs['CONFIG_DB'] = os.path.join(mock_db_path, 'default_config_db')
        db = Db()
        runner = CliRunner()

        self.passw_hardening_set_policy(runner, db, "len-min", "30")

        self.verify_passw_policies_output(db, runner, assert_show_output.show_passw_hardening_policies_len_min)

    def test_passw_hardening_policy_expiration_invalid(self):
        dbconnector.dedicated_dbs['CONFIG_DB'] = os.path.join(mock_db_path, 'default_config_db')
        db = Db()
        runner = CliRunner()
        INVALID_EXP_TIME = "600"

        self.passw_hardening_set_policy(runner, db, "expiration", INVALID_EXP_TIME, EXP_BAD_FLOW)

        # expect default values, because invalid values should not succed to modify default configuration
        self.verify_passw_policies_output(db, runner, assert_show_output.show_passw_hardening_policies_default)

    def test_passw_hardening_policy_len_min_invalid(self):
        dbconnector.dedicated_dbs['CONFIG_DB'] = os.path.join(mock_db_path, 'default_config_db')
        db = Db()
        runner = CliRunner()
        INVALID_EXP_LEN = "500"

        self.passw_hardening_set_policy(runner, db, "len-min", INVALID_EXP_LEN, EXP_BAD_FLOW)

        # expect default values, because invalid values should not succed to modify default configuration
        self.verify_passw_policies_output(db, runner, assert_show_output.show_passw_hardening_policies_default)

    def test_passw_hardening_policy_class_invalid(self):
        dbconnector.dedicated_dbs['CONFIG_DB'] = os.path.join(mock_db_path, 'default_config_db')
        db = Db()
        runner = CliRunner()
        INVALID_VALUE = '?'

        self.passw_hardening_set_policy(runner, db, "expiration", INVALID_VALUE, EXP_BAD_FLOW)

        # expect default values, because invalid values should not succed to modify default configuration
        self.verify_passw_policies_output(db, runner, assert_show_output.show_passw_hardening_policies_default)

