from click.testing import CliRunner

from utilities_common.db import Db

show_feature_status_output="""\
Feature     State     AutoRestart    SystemState    UpdateTime    ContainerId    ContainerVersion    CurrentOwner    RemoteState
----------  --------  -------------  -------------  ------------  -------------  ------------------  --------------  -------------
bgp         enabled   enabled                                                                                        none
database    enabled   disabled                                                                                       none
dhcp_relay  enabled   enabled                                                                                        none
lldp        enabled   enabled                                                                                        none
nat         enabled   enabled                                                                                        none
pmon        enabled   enabled                                                                                        none
radv        enabled   enabled                                                                                        none
restapi     disabled  enabled                                                                                        none
sflow       disabled  enabled                                                                                        none
snmp        enabled   enabled                                                                                        none
swss        enabled   enabled                                                                                        none
syncd       enabled   enabled                                                                                        none
teamd       enabled   enabled                                                                                        none
telemetry   enabled   enabled                                                                                        none
"""

show_feature_config_output="""\
Feature     State     AutoRestart    Owner    no-fallback
----------  --------  -------------  -------  -------------
bgp         enabled   enabled        local    false
database    enabled   disabled       local    false
dhcp_relay  enabled   enabled        kube     false
lldp        enabled   enabled        kube     false
nat         enabled   enabled        local    false
pmon        enabled   enabled        kube     false
radv        enabled   enabled        kube     false
restapi     disabled  enabled        local    false
sflow       disabled  enabled        local    false
snmp        enabled   enabled        kube     false
swss        enabled   enabled        local    false
syncd       enabled   enabled        local    false
teamd       enabled   enabled        local    false
telemetry   enabled   enabled        kube     false
"""

show_feature_bgp_status_output="""\
Feature    State    AutoRestart    SystemState    UpdateTime    ContainerId    ContainerVersion    CurrentOwner    RemoteState
---------  -------  -------------  -------------  ------------  -------------  ------------------  --------------  -------------
bgp        enabled  enabled                                                                                        none
"""

show_feature_bgp_disabled_status_output="""\
Feature    State     AutoRestart    SystemState    UpdateTime    ContainerId    ContainerVersion    CurrentOwner    RemoteState
---------  --------  -------------  -------------  ------------  -------------  ------------------  --------------  -------------
bgp        disabled  enabled                                                                                        none
"""
show_feature_snmp_config_owner_output="""\
Feature    State    AutoRestart    Owner    no-fallback
---------  -------  -------------  -------  -------------
snmp       enabled  enabled        local    false
"""

show_feature_snmp_config_fallback_output="""\
Feature    State    AutoRestart    Owner    no-fallback
---------  -------  -------------  -------  -------------
snmp       enabled  enabled        kube     true
"""

show_feature_autorestart_output="""\
Feature     AutoRestart
----------  -------------
bgp         enabled
database    disabled
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

class TestFeature(object):
    @classmethod
    def setup_class(cls):
        print("SETUP")

    def test_show_feature_status(self, get_cmd_module):
        (config, show) = get_cmd_module
        runner = CliRunner()
        result = runner.invoke(show.cli.commands["feature"].commands["status"], [])
        print(result.exit_code)
        print(result.output)
        assert result.exit_code == 0
        assert result.output == show_feature_status_output

    def test_show_feature_config(self, get_cmd_module):
        (config, show) = get_cmd_module
        runner = CliRunner()
        result = runner.invoke(show.cli.commands["feature"].commands["config"], [])
        print(result.exit_code)
        print(result.output)
        assert result.exit_code == 0
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
        assert result.exit_code == 0
        result = runner.invoke(show.cli.commands["feature"].commands["config"], ["snmp"], obj=db)
        print(result.output)
        assert result.exit_code == 0
        assert result.output == show_feature_snmp_config_owner_output

    def test_config_snmp_feature_fallback(self, get_cmd_module):
        (config, show) = get_cmd_module
        db = Db()
        runner = CliRunner()
        result = runner.invoke(config.config.commands["feature"].commands["no-fallback"], ["snmp", "on"], obj=db)
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

    def test_config_unknown_feature(self, get_cmd_module):
        (config, show) = get_cmd_module
        runner = CliRunner()
        result = runner.invoke(config.config.commands["feature"].commands['state'], ["foo", "enabled"])
        print(result.output)
        assert result.exit_code == 1

    @classmethod
    def teardown_class(cls):
        print("TEARDOWN")
