import click
import config.main as config
import show.main as show
import clear.main as clear
import operator
import os
import pytest
import sys

from click.testing import CliRunner
from .mock_tables import dbconnector
from utilities_common.db import Db


test_path = os.path.dirname(os.path.abspath(__file__))
mock_db_path = os.path.join(test_path, "asic_sdk_health_event_input")
modules_path = os.path.dirname(test_path)
sys.path.insert(0, modules_path)


class TestAsicSdkHealthEvent(object):
    @classmethod
    def setup_class(cls):
        print("SETUP")

    @classmethod
    def teardown_class(cls):
        print("TEARDOWN")
        dbconnector.dedicated_dbs['STATE_DB'] = None
        dbconnector.dedicated_dbs['CONFIG_DB'] = None

    @pytest.mark.parametrize("severity,categories", [
        ("fatal", "cpu_hw"),
        ("warning", "asic_hw,software,firmware"),
        ("notice", "cpu_hw,firmware")
        ])
    def test_config_suppress_asic_sdk_health_event(self, severity, categories):
        dbconnector.dedicated_dbs['STATE_DB'] = os.path.join(mock_db_path, 'state_db')

        runner = CliRunner()
        db = Db()

        result = runner.invoke(
            config.config.commands["asic-sdk-health-event"].commands["suppress"],
            [severity, "all"], obj=db)
        assert result.exit_code == 0
        output_categories = db.cfgdb.get_entry("SUPPRESS_ASIC_SDK_HEALTH_EVENT", severity)['categories']
        assert {'asic_hw', 'firmware', 'cpu_hw', 'software'} == set(output_categories)

        result = runner.invoke(
            config.config.commands["asic-sdk-health-event"].commands["suppress"],
            [severity, categories], obj=db)
        assert result.exit_code == 0
        output_categories = db.cfgdb.get_entry("SUPPRESS_ASIC_SDK_HEALTH_EVENT", severity)['categories']
        assert set(categories.split(',')) == set(output_categories)

        result = runner.invoke(
            config.config.commands["asic-sdk-health-event"].commands["suppress"],
            [severity, "none"], obj=db)
        assert result.exit_code == 0
        assert not db.cfgdb.get_entry("SUPPRESS_ASIC_SDK_HEALTH_EVENT", severity)

        result = runner.invoke(
            config.config.commands["asic-sdk-health-event"].commands["suppress"],
            [severity, "unknown"], obj=db)
        assert result.exit_code != 0
        assert "Invalid category(ies): {'unknown'}" in result.output
        assert not db.cfgdb.get_entry("SUPPRESS_ASIC_SDK_HEALTH_EVENT", severity)

    @pytest.mark.parametrize("severity", ["fatal", "warning", "notice"])
    def test_config_suppress_asic_sdk_health_event_unsupported_severity(self, severity):
        dbconnector.dedicated_dbs['STATE_DB'] = os.path.join(mock_db_path, 'state_db_no_' + severity)

        runner = CliRunner()
        db = Db()

        result = runner.invoke(
            config.config.commands["asic-sdk-health-event"].commands["suppress"],
            [severity, "all"], obj=db)
        assert result.exit_code != 0
        assert "Suppressing ASIC/SDK health {} event is not supported on the platform".format(severity) in result.output
        assert not db.cfgdb.get_entry("SUPPRESS_ASIC_SDK_HEALTH_EVENT", severity)

    def test_config_suppress_asic_sdk_health_event_unsupported_event(self):
        dbconnector.dedicated_dbs['STATE_DB'] = os.path.join(mock_db_path, 'state_db_no_event')

        runner = CliRunner()
        db = Db()

        result = runner.invoke(
            config.config.commands["asic-sdk-health-event"].commands["suppress"],
            ["fatal", "all"], obj=db)
        assert result.exit_code != 0
        assert "ASIC/SDK health event is not supported on the platform" in result.output
        assert not db.cfgdb.get_entry("SUPPRESS_ASIC_SDK_HEALTH_EVENT", "fatal")

    def test_show_asic_sdk_health_event_received(self):
        expected_output = \
        "Date                   ASICID  Severity    Category    Description\n"
        "-------------------  --------  ----------  ----------  ---------------------\n"
        "2023-11-22 09:18:12         0  fatal       firmware    ASIC SDK health event\n"
        dbconnector.dedicated_dbs['STATE_DB'] = os.path.join(mock_db_path, 'state_db')

        runner = CliRunner()
        db = Db()

        result = runner.invoke(show.cli.commands["asic-sdk-health-event"].commands["received"], [], obj=db)
        assert result.exit_code == 0
        assert expected_output in result.output

    def test_show_asic_sdk_health_event_suppressed_category_list(self):
        expected_output = \
        'Severity    Suppressed category-list\n'
        '----------  --------------------------\n'
        'fatal       software\n'
        'warning     firmware,asic_hw\n'
        dbconnector.dedicated_dbs['STATE_DB'] = os.path.join(mock_db_path, 'state_db')
        dbconnector.dedicated_dbs['CONFIG_DB'] = os.path.join(mock_db_path, 'config_db')

        runner = CliRunner()
        db = Db()

        result = runner.invoke(show.cli.commands["asic-sdk-health-event"].commands["suppressed-category-list"], [], obj=db)
        assert result.exit_code == 0
        assert expected_output in result.output

    def test_clear_suppress_asic_sdk_health_event(self):
        dbconnector.dedicated_dbs['STATE_DB'] = os.path.join(mock_db_path, 'state_db')

        runner = CliRunner()
        db = Db()

        result = runner.invoke(clear.cli.commands["asic-sdk-health-event"], [], obj=db)
        assert result.exit_code == 0
        assert not db.db.keys(db.db.STATE_DB, "ASIC_SDK_HEALTH_EVENT_TABLE*")
