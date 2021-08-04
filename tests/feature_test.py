import importlib

from click.testing import CliRunner

from utilities_common.db import Db

show_feature_status_output="""\
Feature     State           AutoRestart     HighMemRestart    MemThreshold    SetOwner
----------  --------------  --------------  ----------------  --------------  ----------
bgp         enabled         enabled         disabled          314572800       local
database    always_enabled  always_enabled  disabled          157286400       local
dhcp_relay  enabled         enabled         disabled          83886080        kube
lldp        enabled         enabled         disabled          104857600       kube
nat         enabled         enabled         disabled          104857600       local
pmon        enabled         enabled         disabled          209715200       kube
radv        enabled         enabled         disabled          104857600       kube
restapi     disabled        enabled         disabled          104857600       local
sflow       disabled        enabled         disabled          104857600       local
snmp        enabled         enabled         disabled          157286400       kube
swss        enabled         enabled         disabled          104857600       local
syncd       enabled         enabled         disabled          629145600       local
teamd       enabled         enabled         disabled          104857600       local
telemetry   enabled         enabled         disabled          209715200       kube
"""

show_feature_status_output_with_remote_mgmt="""\
Feature     State           AutoRestart     HighMemRestart    MemThreshold    SystemState    UpdateTime           ContainerId    Version       SetOwner    CurrentOwner    RemoteState
----------  --------------  --------------  ----------------  --------------  -------------  -------------------  -------------  ------------  ----------  --------------  -------------
bgp         enabled         enabled         disabled          314572800                                                                        local
database    always_enabled  always_enabled  disabled          157286400                                                                        local
dhcp_relay  enabled         enabled         disabled          83886080                                                                         kube
lldp        enabled         enabled         disabled          104857600                                                                        kube
nat         enabled         enabled         disabled          104857600                                                                        local
pmon        enabled         enabled         disabled          209715200                                                                        kube
radv        enabled         enabled         disabled          104857600                                                                        kube
restapi     disabled        enabled         disabled          104857600                                                                        local
sflow       disabled        enabled         disabled          104857600                                                                        local
snmp        enabled         enabled         disabled          157286400       up             2020-11-12 23:32:56  aaaabbbbcccc   20201230.100  kube        kube            kube
swss        enabled         enabled         disabled          104857600                                                                        local
syncd       enabled         enabled         disabled          629145600                                                                        local
teamd       enabled         enabled         disabled          104857600                                                                        local
telemetry   enabled         enabled         disabled          209715200                                                                        kube
"""

show_feature_config_output="""\
Feature     State     AutoRestart    HighMemRestart    MemThreshold    Owner
----------  --------  -------------  ----------------  --------------  -------
bgp         enabled   enabled        disabled          314572800       local
database    enabled   disabled       disabled          157286400       local
dhcp_relay  enabled   enabled        disabled          83886080        kube
lldp        enabled   enabled        disabled          104857600       kube
nat         enabled   enabled        disabled          104857600       local
pmon        enabled   enabled        disabled          209715200       kube
radv        enabled   enabled        disabled          104857600       kube
restapi     disabled  enabled        disabled          104857600       local
sflow       disabled  enabled        disabled          104857600       local
snmp        enabled   enabled        disabled          157286400       kube
swss        enabled   enabled        disabled          104857600       local
syncd       enabled   enabled        disabled          629145600       local
teamd       enabled   enabled        disabled          104857600       local
telemetry   enabled   enabled        disabled          209715200       kube
"""

show_feature_config_output_with_remote_mgmt="""\
Feature     State           AutoRestart     HighMemRestart    MemThreshold    Owner
----------  --------------  --------------  ----------------  --------------  -------
bgp         enabled         enabled         disabled          314572800       local
database    always_enabled  always_enabled  disabled          157286400       local
dhcp_relay  enabled         enabled         disabled          83886080        kube
lldp        enabled         enabled         disabled          104857600       kube
nat         enabled         enabled         disabled          104857600       local
pmon        enabled         enabled         disabled          209715200       kube
radv        enabled         enabled         disabled          104857600       kube
restapi     disabled        enabled         disabled          104857600       local
sflow       disabled        enabled         disabled          104857600       local
snmp        enabled         enabled         disabled          157286400       kube
swss        enabled         enabled         disabled          104857600       local
syncd       enabled         enabled         disabled          629145600       local
teamd       enabled         enabled         disabled          104857600       local
telemetry   enabled         enabled         disabled          209715200       kube
"""

show_feature_bgp_status_output="""\
Feature    State    AutoRestart    HighMemRestart    MemThreshold    SetOwner
---------  -------  -------------  ----------------  --------------  ----------
bgp        enabled  enabled        disabled          314572800       local
"""

show_feature_bgp_disabled_status_output="""\
Feature    State     AutoRestart    HighMemRestart    MemThreshold    SetOwner
---------  --------  -------------  ----------------  --------------  ----------
bgp        disabled  enabled        disabled          314572800       local
"""
show_feature_snmp_config_owner_output="""\
Feature    State    AutoRestart    HighMemRestart    MemThreshold    Owner    fallback
---------  -------  -------------  ----------------  --------------  -------  ----------
snmp       enabled  enabled        disabled          157286400       local    true
"""

show_feature_snmp_config_fallback_output="""\
Feature    State    AutoRestart    HighMemRestart    MemThreshold    Owner    fallback
---------  -------  -------------  ----------------  --------------  -------  ----------
snmp       enabled  enabled        disabled          157286400       kube     false
"""

show_feature_autorestart_output="""\
Feature     AutoRestart
----------  --------------
bgp         enabled
database    always_enabled
dhcp_relay  enabled
lldp        enabled
nat         enabled
pmon        enabled
radv        enabled
restapi     enabled
sflow       enabled
snmp        enabled
swss        enabled
syncd       enabled
teamd       enabled
telemetry   enabled
"""

show_feature_high_mem_restart_output="""\
Feature     HighMemRestart
----------  ----------------
bgp         disabled
database    disabled
dhcp_relay  disabled
lldp        disabled
nat         disabled
pmon        disabled
radv        disabled
restapi     disabled
sflow       disabled
snmp        disabled
swss        disabled
syncd       disabled
teamd       disabled
telemetry   disabled
"""

show_feature_high_mem_restart_lldp_output="""\
Feature    HighMemRestart
---------  ----------------
lldp       disabled
"""

show_feature_high_mem_restart_lldp_enabled_output="""\
Feature    HighMemRestart
---------  ----------------
lldp       enabled
"""

show_feature_mem_threshold_output="""\
Feature       MemThreshold
----------  --------------
bgp              314572800
database         157286400
dhcp_relay        83886080
lldp             104857600
nat              104857600
pmon             209715200
radv             104857600
restapi          104857600
sflow            104857600
snmp             157286400
swss             104857600
syncd            629145600
teamd            104857600
telemetry        209715200
"""

show_feature_mem_threshold_lldp_output="""\
Feature      MemThreshold
---------  --------------
lldp            104857600
"""

show_feature_mem_threshold_lldp_updated_output="""\
Feature      MemThreshold
---------  --------------
lldp                 2048
"""

show_feature_bgp_autorestart_output="""\
Feature    AutoRestart
---------  -------------
bgp        enabled
"""

show_feature_bgp_disabled_autorestart_output="""\
Feature    AutoRestart
---------  -------------
bgp        disabled
"""

show_feature_bgp_high_mem_restart_disabled_output="""\
Feature    HighMemRestart
---------  ----------------
bgp        disabled
"""

show_feature_bgp_high_mem_restart_enabled_output="""\
Feature    HighMemRestart
---------  ----------------
bgp        enabled
"""

show_feature_bgp_mem_threshold_output="""\
Feature      MemThreshold
---------  --------------
bgp             104857600
"""

show_feature_database_always_enabled_state_output="""\
Feature    State           AutoRestart     HighMemRestart    MemThreshold    SetOwner
---------  --------------  --------------  ----------------  --------------  ----------
database   always_enabled  always_enabled  disabled          157286400       local
"""

show_feature_database_always_enabled_autorestart_output="""\
Feature    AutoRestart
---------  --------------
database   always_enabled
"""

config_feature_bgp_inconsistent_state_output="""\
Feature 'bgp' state is not consistent across namespaces
"""

config_feature_bgp_inconsistent_autorestart_output="""\
Feature 'bgp' auto-restart is not consistent across namespaces
"""

config_feature_inconsistent_high_mem_restart_output="""\
High memory restart status of feature 'bgp' is not consistent across namespaces.
"""

config_feature_inconsistent_mem_threshold_output="""\
Memory threshold of feature 'bgp' is not consistent across namespaces.
"""


class TestFeature(object):
    @classmethod
    def setup_class(cls):
        print("SETUP")

    def test_show_feature_status_no_kube_status(self, get_cmd_module):
        (config, show) = get_cmd_module
        runner = CliRunner()
        result = runner.invoke(show.cli.commands["feature"].commands["status"], [])
        print(result.exit_code)
        print(result.output)
        assert result.exit_code == 0
        assert result.output == show_feature_status_output

    def test_show_feature_status(self, get_cmd_module):
        (config, show) = get_cmd_module
        db = Db()
        dbconn = db.db
        for (key, val) in [("system_state", "up"), ("current_owner", "kube"),
                ("container_id", "aaaabbbbcccc"), ("update_time", "2020-11-12 23:32:56"),
                ("container_version", "20201230.100"), ("remote_state", "kube")]:
            dbconn.set(dbconn.STATE_DB, "FEATURE|snmp", key, val)
        runner = CliRunner()
        result = runner.invoke(show.cli.commands["feature"].commands["status"], ["snmp"], obj=db)
        print(result.exit_code)
        assert result.exit_code == 0

        result = runner.invoke(show.cli.commands["feature"].commands["status"], [], obj=db)
        print(result.exit_code)
        print(result.output)
        assert result.exit_code == 0
        assert result.output == show_feature_status_output_with_remote_mgmt

    def test_show_feature_config(self, get_cmd_module):
        (config, show) = get_cmd_module
        runner = CliRunner()
        result = runner.invoke(show.cli.commands["feature"].commands["config"], [])
        print(result.exit_code)
        print(result.output)
        print(show_feature_config_output_with_remote_mgmt)
        assert result.exit_code == 0
        if "Owner" in result.output:
            assert result.output == show_feature_config_output_with_remote_mgmt
        else:
            assert result.output == show_feature_config_output

    def test_show_feature_status_abbrev_cmd(self, get_cmd_module):
        (config, show) = get_cmd_module
        runner = CliRunner()
        result = runner.invoke(show.cli.commands["feature"], ["st"])
        print(result.exit_code)
        print(result.output)
        assert result.exit_code == 0
        assert result.output == show_feature_status_output

    def test_show_bgp_feature_status(self, get_cmd_module):
        (config, show) = get_cmd_module
        runner = CliRunner()
        result = runner.invoke(show.cli.commands["feature"].commands["status"], ["bgp"])
        print(result.exit_code)
        print(result.output)
        assert result.exit_code == 0
        assert result.output == show_feature_bgp_status_output

    def test_show_unknown_feature_status(self, get_cmd_module):
        (config, show) = get_cmd_module
        runner = CliRunner()
        result = runner.invoke(show.cli.commands["feature"].commands["status"], ["foo"])
        print(result.exit_code)
        print(result.output)
        assert result.exit_code == 1

    def test_show_feature_autorestart(self, get_cmd_module):
        (config, show) = get_cmd_module
        runner = CliRunner()
        result = runner.invoke(show.cli.commands["feature"].commands["autorestart"], [])
        print(result.exit_code)
        print(result.output)
        assert result.exit_code == 0
        assert result.output == show_feature_autorestart_output

    def test_show_feature_high_mem_restart(self, get_cmd_module):
        (config, show) = get_cmd_module
        runner = CliRunner()
        db = Db()

        result = runner.invoke(show.cli.commands["feature"].commands["high_mem_restart"], [])
        print(result.exit_code)
        print(result.output)
        assert result.exit_code == 0
        assert result.output == show_feature_high_mem_restart_output

        result = runner.invoke(show.cli.commands["feature"].commands["high_mem_restart"], ["lldp"])
        print(result.exit_code)
        print(result.output)
        print(show_feature_high_mem_restart_lldp_output)
        assert result.exit_code == 0
        assert result.output == show_feature_high_mem_restart_lldp_output

        result = runner.invoke(show.cli.commands["feature"].commands["high_mem_restart"], ["not_existing_container"])
        print(result.exit_code)
        print(result.output)
        assert result.exit_code == 3

    def test_show_feature_mem_threshold(self, get_cmd_module):
        (config, show) = get_cmd_module
        runner = CliRunner()
        db = Db()

        result = runner.invoke(show.cli.commands["feature"].commands["mem_threshold"], [])
        print(result.exit_code)
        print(result.output)
        assert result.exit_code == 0
        assert result.output == show_feature_mem_threshold_output

        result = runner.invoke(show.cli.commands["feature"].commands["mem_threshold"], ["lldp"])
        print(result.exit_code)
        print(result.output)
        assert result.exit_code == 0
        assert result.output == show_feature_mem_threshold_lldp_output

        result = runner.invoke(show.cli.commands["feature"].commands["mem_threshold"], ["non_existing_container"])
        print(result.exit_code)
        print(result.output)
        assert result.exit_code == 5

    def test_fail_autorestart(self, get_cmd_module):
        (config, show) = get_cmd_module
        runner = CliRunner()
        db = Db()

        # Try setting auto restart for non-existing feature
        result = runner.invoke(config.config.commands["feature"].commands["autorestart"], ["foo", "disabled"])
        print(result.exit_code)
        assert result.exit_code == 1

        # Delete Feature table
        db.cfgdb.delete_table("FEATURE")

        # Try setting auto restart when no FEATURE table
        result = runner.invoke(config.config.commands["feature"].commands["autorestart"], ["bgp", "disabled"], obj=db)
        print(result.exit_code)
        assert result.exit_code == 1


    def test_show_bgp_autorestart_status(self, get_cmd_module):
        (config, show) = get_cmd_module
        runner = CliRunner()
        result = runner.invoke(show.cli.commands["feature"].commands["autorestart"], ["bgp"])
        print(result.exit_code)
        print(result.output)
        assert result.exit_code == 0
        assert result.output == show_feature_bgp_autorestart_output

    def test_show_unknown_autorestart_status(self, get_cmd_module):
        (config, show) = get_cmd_module
        runner = CliRunner()
        result = runner.invoke(show.cli.commands["feature"].commands["autorestart"], ["foo"])
        print(result.exit_code)
        print(result.output)
        assert result.exit_code == 1

    def test_config_bgp_feature_state(self, get_cmd_module):
        (config, show) = get_cmd_module
        db = Db()
        runner = CliRunner()
        result = runner.invoke(config.config.commands["feature"].commands["state"], ["bgp", "disabled"], obj=db)
        print(result.exit_code)
        print(result.output)
        assert result.exit_code == 0
        result = runner.invoke(show.cli.commands["feature"].commands["status"], ["bgp"], obj=db)
        print(result.output)
        assert result.exit_code == 0
        assert result.output == show_feature_bgp_disabled_status_output

    def test_config_snmp_feature_owner(self, get_cmd_module):
        (config, show) = get_cmd_module
        db = Db()
        runner = CliRunner()
        result = runner.invoke(config.config.commands["feature"].commands["owner"], ["snmp", "local"], obj=db)
        print(result.exit_code)
        print(result.output)
        result = runner.invoke(config.config.commands["feature"].commands["fallback"], ["snmp", "on"], obj=db)
        print(result.exit_code)
        print(result.output)
        assert result.exit_code == 0

        result = runner.invoke(show.cli.commands["feature"].commands["config"], ["foo"], obj=db)
        print(result.exit_code)
        assert result.exit_code == 1

        result = runner.invoke(show.cli.commands["feature"].commands["config"], ["snmp"], obj=db)
        print(result.output)
        assert result.exit_code == 0
        assert result.output == show_feature_snmp_config_owner_output

    def test_config_unknown_feature_owner(self, get_cmd_module):
        (config, show) = get_cmd_module
        runner = CliRunner()
        result = runner.invoke(config.config.commands["feature"].commands["owner"], ["foo", "local"])
        print(result.exit_code)
        print(result.output)
        assert result.exit_code == 1

    def test_config_snmp_feature_fallback(self, get_cmd_module):
        (config, show) = get_cmd_module
        db = Db()
        runner = CliRunner()
        result = runner.invoke(config.config.commands["feature"].commands["fallback"], ["snmp", "off"], obj=db)
        print(result.exit_code)
        print(result.output)
        assert result.exit_code == 0
        result = runner.invoke(show.cli.commands["feature"].commands["config"], ["snmp"], obj=db)
        print(result.output)
        assert result.exit_code == 0
        assert result.output == show_feature_snmp_config_fallback_output

    def test_config_bgp_autorestart(self, get_cmd_module):
        (config, show) = get_cmd_module
        db = Db()
        runner = CliRunner()
        result = runner.invoke(config.config.commands["feature"].commands["autorestart"], ["bgp", "disabled"], obj=db)
        print(result.exit_code)
        print(result.output)
        assert result.exit_code == 0
        result = runner.invoke(show.cli.commands["feature"].commands["autorestart"], ["bgp"], obj=db)
        print(result.output)
        assert result.exit_code == 0
        assert result.output == show_feature_bgp_disabled_autorestart_output

    def test_config_database_feature_state(self, get_cmd_module):
        (config, show) = get_cmd_module
        db = Db()
        runner = CliRunner()
        result = runner.invoke(config.config.commands["feature"].commands["state"], ["database", "disabled"], obj=db)
        print(result.exit_code)
        print(result.output)
        result = runner.invoke(show.cli.commands["feature"].commands["status"], ["database"], obj=db)
        print(result.output)
        assert result.exit_code == 0
        assert result.output == show_feature_database_always_enabled_state_output
        result = runner.invoke(config.config.commands["feature"].commands["state"], ["database", "enabled"], obj=db)
        print(result.exit_code)
        print(result.output)
        result = runner.invoke(show.cli.commands["feature"].commands["status"], ["database"], obj=db)
        print(result.output)
        assert result.exit_code == 0
        assert result.output == show_feature_database_always_enabled_state_output

    def test_config_database_feature_autorestart(self, get_cmd_module):
        (config, show) = get_cmd_module
        db = Db()
        runner = CliRunner()
        result = runner.invoke(config.config.commands["feature"].commands["autorestart"], ["database", "disabled"], obj=db)
        print(result.exit_code)
        print(result.output)
        result = runner.invoke(show.cli.commands["feature"].commands["autorestart"], ["database"], obj=db)
        print(result.output)
        assert result.exit_code == 0
        assert result.output == show_feature_database_always_enabled_autorestart_output
        result = runner.invoke(config.config.commands["feature"].commands["autorestart"], ["database", "enabled"], obj=db)
        print(result.exit_code)
        print(result.output)
        result = runner.invoke(show.cli.commands["feature"].commands["autorestart"], ["database"], obj=db)
        print(result.output)
        assert result.exit_code == 0
        assert result.output == show_feature_database_always_enabled_autorestart_output

    def test_config_unknown_feature(self, get_cmd_module):
        (config, show) = get_cmd_module
        runner = CliRunner()
        result = runner.invoke(config.config.commands["feature"].commands['state'], ["foo", "enabled"])
        print(result.output)
        print(result.exit_code)
        assert result.exit_code == 1

    def test_config_feature_high_mem_restart(self, get_cmd_module):
        (config, show) = get_cmd_module
        db = Db()
        runner = CliRunner()

        result = runner.invoke(config.config.commands["feature"].commands["high_mem_restart"], ["lldp", "enabled"], obj=db)
        print(result.exit_code)
        print(result.output)
        assert result.exit_code == 0

        result = runner.invoke(show.cli.commands["feature"].commands["high_mem_restart"], ["lldp"], obj=db)
        print(result.exit_code)
        print(result.output)
        assert result.exit_code == 0
        assert result.output == show_feature_high_mem_restart_lldp_enabled_output

        result = runner.invoke(config.config.commands["feature"].commands["high_mem_restart"], ["non_existing_container", "enabled"], obj=db)
        print(result.exit_code)
        print(result.output)
        assert result.exit_code == 3

        # Delete the 'FEATURE' table.
        db.cfgdb.delete_table("FEATURE")

        result = runner.invoke(config.config.commands["feature"].commands["high_mem_restart"], ["lldp", "enabled"], obj=db)
        print(result.exit_code)
        print(result.output)
        assert result.exit_code == 2

    def test_config_feature_mem_threshold(self, get_cmd_module):
        (config, show) = get_cmd_module
        db = Db()
        runner = CliRunner()

        result = runner.invoke(config.config.commands["feature"].commands["mem_threshold"], ["lldp", "2048"], obj=db)
        print(result.exit_code)
        print(result.output)
        assert result.exit_code == 0

        result = runner.invoke(show.cli.commands["feature"].commands["mem_threshold"], ["lldp"], obj=db)
        print(result.exit_code)
        print(result.output)
        assert result.exit_code == 0
        assert result.output == show_feature_mem_threshold_lldp_updated_output

        result = runner.invoke(config.config.commands["feature"].commands["mem_threshold"], ["non_existing_container", "2048"], obj=db)
        print(result.exit_code)
        print(result.output)
        assert result.exit_code == 6

        # Delete the 'FEATURE' table.
        db.cfgdb.delete_table("FEATURE")

        result = runner.invoke(config.config.commands["feature"].commands["mem_threshold"], ["lldp", "2048"], obj=db)
        print(result.exit_code)
        print(result.output)
        assert result.exit_code == 5

    @classmethod
    def teardown_class(cls):
        print("TEARDOWN")

class TestFeatureMultiAsic(object):
    @classmethod
    def setup_class(cls):
        print("SETUP")

    def test_config_bgp_feature_inconsistent_state(self, get_cmd_module):
        from .mock_tables import dbconnector
        from .mock_tables import mock_multi_asic_3_asics
        importlib.reload(mock_multi_asic_3_asics)
        dbconnector.load_namespace_config()
        (config, show) = get_cmd_module
        db = Db()
        runner = CliRunner()
        result = runner.invoke(config.config.commands["feature"].commands["state"], ["bgp", "disabled"], obj=db)
        print(result.exit_code)
        print(result.output)
        assert result.exit_code == 1
        assert result.output == config_feature_bgp_inconsistent_state_output
        result = runner.invoke(config.config.commands["feature"].commands["state"], ["bgp", "enabled"], obj=db)
        print(result.exit_code)
        print(result.output)
        assert result.exit_code == 1
        assert result.output == config_feature_bgp_inconsistent_state_output

    def test_config_bgp_feature_inconsistent_autorestart(self, get_cmd_module):
        from .mock_tables import dbconnector
        from .mock_tables import mock_multi_asic_3_asics
        importlib.reload(mock_multi_asic_3_asics)
        dbconnector.load_namespace_config()
        (config, show) = get_cmd_module
        db = Db()
        runner = CliRunner()
        result = runner.invoke(config.config.commands["feature"].commands["autorestart"], ["bgp", "disabled"], obj=db)
        print(result.exit_code)
        print(result.output)
        assert result.exit_code == 1
        assert result.output == config_feature_bgp_inconsistent_autorestart_output
        result = runner.invoke(config.config.commands["feature"].commands["autorestart"], ["bgp", "enabled"], obj=db)
        print(result.exit_code)
        print(result.output)
        assert result.exit_code == 1
        assert result.output == config_feature_bgp_inconsistent_autorestart_output

    def test_config_feature_inconsistent_high_mem_restart(self, get_cmd_module):
        from .mock_tables import dbconnector
        from .mock_tables import mock_multi_asic_3_asics
        importlib.reload(mock_multi_asic_3_asics)
        dbconnector.load_namespace_config()
        (config, show) = get_cmd_module
        db = Db()
        runner = CliRunner()

        result = runner.invoke(config.config.commands["feature"].commands["high_mem_restart"], ["bgp", "disabled"], obj=db)
        print(result.exit_code)
        print(result.output)
        assert result.exit_code == 4
        assert result.output == config_feature_inconsistent_high_mem_restart_output

        result = runner.invoke(config.config.commands["feature"].commands["high_mem_restart"], ["bgp", "enabled"], obj=db)
        print(result.exit_code)
        print(result.output)
        assert result.exit_code == 4
        assert result.output == config_feature_inconsistent_high_mem_restart_output

    def test_config_feature_inconsistent_mem_threshold(self, get_cmd_module):
        from .mock_tables import dbconnector
        from .mock_tables import mock_multi_asic_3_asics
        importlib.reload(mock_multi_asic_3_asics)
        dbconnector.load_namespace_config()
        (config, show) = get_cmd_module
        db = Db()
        runner = CliRunner()

        result = runner.invoke(config.config.commands["feature"].commands["mem_threshold"], ["bgp", "104857600"], obj=db)
        print(result.exit_code)
        print(result.output)
        assert result.exit_code == 7
        assert result.output == config_feature_inconsistent_mem_threshold_output

    def test_config_bgp_feature_consistent_state(self, get_cmd_module):
        from .mock_tables import dbconnector
        from .mock_tables import mock_multi_asic
        importlib.reload(mock_multi_asic)
        dbconnector.load_namespace_config()
        (config, show) = get_cmd_module
        db = Db()
        runner = CliRunner()
        result = runner.invoke(config.config.commands["feature"].commands["state"], ["bgp", "disabled"], obj=db)
        print(result.exit_code)
        assert result.exit_code == 0
        result = runner.invoke(show.cli.commands["feature"].commands["status"], ["bgp"], obj=db)
        print(result.output)
        assert result.exit_code == 0
        assert result.output == show_feature_bgp_disabled_status_output
        result = runner.invoke(config.config.commands["feature"].commands["state"], ["bgp", "enabled"], obj=db)
        print(result.exit_code)
        print(result.output)
        assert result.exit_code == 0
        result = runner.invoke(show.cli.commands["feature"].commands["status"], ["bgp"], obj=db)
        print(result.output)
        assert result.exit_code == 0
        assert result.output == show_feature_bgp_status_output

    def test_config_bgp_feature_consistent_autorestart(self, get_cmd_module):
        from .mock_tables import dbconnector
        from .mock_tables import mock_multi_asic
        importlib.reload(mock_multi_asic)
        dbconnector.load_namespace_config()
        (config, show) = get_cmd_module
        db = Db()
        runner = CliRunner()
        result = runner.invoke(config.config.commands["feature"].commands["autorestart"], ["bgp", "disabled"], obj=db)
        print(result.exit_code)
        assert result.exit_code == 0
        result = runner.invoke(show.cli.commands["feature"].commands["autorestart"], ["bgp"], obj=db)
        print(result.output)
        print(result.exit_code)
        assert result.exit_code == 0
        assert result.output == show_feature_bgp_disabled_autorestart_output
        result = runner.invoke(config.config.commands["feature"].commands["autorestart"], ["bgp", "enabled"], obj=db)
        print(result.exit_code)
        assert result.exit_code == 0
        result = runner.invoke(show.cli.commands["feature"].commands["autorestart"], ["bgp"], obj=db)
        print(result.output)
        print(result.exit_code)
        assert result.exit_code == 0
        assert result.output == show_feature_bgp_autorestart_output
 
    def test_config_feature_consistent_high_mem_restart(self, get_cmd_module):
        from .mock_tables import dbconnector
        from .mock_tables import mock_multi_asic
        importlib.reload(mock_multi_asic)
        dbconnector.load_namespace_config()
        (config, show) = get_cmd_module
        db = Db()
        runner = CliRunner()

        result = runner.invoke(config.config.commands["feature"].commands["high_mem_restart"], ["bgp", "disabled"], obj=db)
        print(result.exit_code)
        assert result.exit_code == 0

        result = runner.invoke(show.cli.commands["feature"].commands["high_mem_restart"], ["bgp"], obj=db)
        print(result.output)
        print(result.exit_code)
        assert result.exit_code == 0
        assert result.output == show_feature_bgp_high_mem_restart_disabled_output

        result = runner.invoke(config.config.commands["feature"].commands["high_mem_restart"], ["bgp", "enabled"], obj=db)
        print(result.exit_code)
        assert result.exit_code == 0

        result = runner.invoke(show.cli.commands["feature"].commands["high_mem_restart"], ["bgp"], obj=db)
        print(result.output)
        print(result.exit_code)
        assert result.exit_code == 0
        assert result.output == show_feature_bgp_high_mem_restart_enabled_output
 
    def test_config_feature_consistent_mem_threshold(self, get_cmd_module):
        from .mock_tables import dbconnector
        from .mock_tables import mock_multi_asic
        importlib.reload(mock_multi_asic)
        dbconnector.load_namespace_config()
        (config, show) = get_cmd_module
        db = Db()
        runner = CliRunner()

        result = runner.invoke(config.config.commands["feature"].commands["mem_threshold"], ["bgp", "104857600"], obj=db)
        print(result.exit_code)
        assert result.exit_code == 0

        result = runner.invoke(show.cli.commands["feature"].commands["mem_threshold"], ["bgp"], obj=db)
        print(result.output)
        print(result.exit_code)
        assert result.exit_code == 0
        assert result.output == show_feature_bgp_mem_threshold_output

    @classmethod
    def teardown_class(cls):
        print("TEARDOWN")
        from .mock_tables import mock_single_asic
        importlib.reload(mock_single_asic)
