import os

from click.testing import CliRunner

import config.main as config
from utilities_common.db import Db


class TestEvpnMh(object):
    @classmethod
    def setup_class(cls):
        print("SETUP")
        os.environ["UTILITIES_UNIT_TESTING"] = "1"

    @classmethod
    def teardown_class(cls):
        os.environ['UTILITIES_UNIT_TESTING'] = "0"
        print("TEARDOWN")

    def test_config_evpn_add_set_del_mh_startup_delay(self):
        runner = CliRunner()
        db = Db()

        result = runner.invoke(config.config.commands["evpn-mh"].commands["startup-delay"].commands["add"],
                               ["-5"], obj=db)
        assert result.exit_code != 0
        assert "no such option" in result.output
        result = runner.invoke(config.config.commands["evpn-mh"].commands["startup-delay"].commands["add"],
                               ["10000"], obj=db)
        assert result.exit_code != 0
        assert "is not in the valid range" in result.output
        result = runner.invoke(config.config.commands["evpn-mh"].commands["startup-delay"].commands["add"],
                               ["2000"], obj=db)
        assert result.exit_code == 0
        assert db.cfgdb.get_entry("EVPN_MH_GLOBAL", "default").get("startup_delay") == "2000"

        result = runner.invoke(config.config.commands["evpn-mh"].commands["startup-delay"].commands["set"],
                               ["2222"], obj=db)
        assert result.exit_code == 0
        assert db.cfgdb.get_entry("EVPN_MH_GLOBAL", "default").get("startup_delay") == "2222"

        result = runner.invoke(config.config.commands["evpn-mh"].commands["startup-delay"].commands["del"],
                               ["2222"], obj=db)
        assert result.exit_code == 0
        assert db.cfgdb.get_entry("EVPN_MH_GLOBAL", "default").get("startup_delay") is None

    def test_config_evpn_add_set_del_mh_mac_holdtime(self):
        runner = CliRunner()
        db = Db()

        result = runner.invoke(config.config.commands["evpn-mh"].commands["mac-holdtime"].commands["add"],
                               ["-400"], obj=db)
        assert result.exit_code != 0
        assert "no such option" in result.output
        result = runner.invoke(config.config.commands["evpn-mh"].commands["mac-holdtime"].commands["add"],
                               ["90000"], obj=db)
        assert result.exit_code != 0
        assert "is not in the valid range" in result.output
        result = runner.invoke(config.config.commands["evpn-mh"].commands["mac-holdtime"].commands["add"],
                               ["50000"], obj=db)
        assert result.exit_code == 0
        assert db.cfgdb.get_entry("EVPN_MH_GLOBAL", "default").get("mac_holdtime") == "50000"

        result = runner.invoke(config.config.commands["evpn-mh"].commands["mac-holdtime"].commands["set"],
                               ["40000"], obj=db)
        assert result.exit_code == 0
        assert db.cfgdb.get_entry("EVPN_MH_GLOBAL", "default").get("mac_holdtime") == "40000"

        result = runner.invoke(config.config.commands["evpn-mh"].commands["mac-holdtime"].commands["del"],
                               ["40000"], obj=db)
        assert result.exit_code == 0
        assert db.cfgdb.get_entry("EVPN_MH_GLOBAL", "default").get("mac_holdtime") is None

    def test_config_evpn_add_set_del_mh_neigh_holdtime(self):
        runner = CliRunner()
        db = Db()

        result = runner.invoke(config.config.commands["evpn-mh"].commands["neigh-holdtime"].commands["add"],
                               ["-400"], obj=db)
        assert result.exit_code != 0
        assert "no such option" in result.output
        result = runner.invoke(config.config.commands["evpn-mh"].commands["neigh-holdtime"].commands["add"],
                               ["90000"], obj=db)
        assert result.exit_code != 0
        assert "is not in the valid range" in result.output
        result = runner.invoke(config.config.commands["evpn-mh"].commands["neigh-holdtime"].commands["add"],
                               ["50000"], obj=db)
        assert result.exit_code == 0
        assert db.cfgdb.get_entry("EVPN_MH_GLOBAL", "default").get("neigh_holdtime") == "50000"

        result = runner.invoke(config.config.commands["evpn-mh"].commands["neigh-holdtime"].commands["set"],
                               ["40000"], obj=db)
        assert result.exit_code == 0
        assert db.cfgdb.get_entry("EVPN_MH_GLOBAL", "default").get("neigh_holdtime") == "40000"

        result = runner.invoke(config.config.commands["evpn-mh"].commands["neigh-holdtime"].commands["del"],
                               ["40000"], obj=db)
        assert result.exit_code == 0
        assert db.cfgdb.get_entry("EVPN_MH_GLOBAL", "default").get("neigh_holdtime") is None
