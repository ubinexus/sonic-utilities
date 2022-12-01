import os
import pytest
import importlib
from click.testing import CliRunner

from utilities_common import multi_asic
from utilities_common import constants

from unittest.mock import patch

from sonic_py_common import device_info
import show.main as show


show_run_bgp_sasic = \
"""
Building configuration...
Current configuration:
!
frr version 8.2.2
frr defaults traditional
hostname str2-7050cx3-acs-02
log syslog informational
log facility local4
agentx
no service integrated-vtysh-config
!
password zebra
enable password zebra
!
router bgp 65100
 bgp router-id 10.1.0.32
 bgp log-neighbor-changes
 no bgp ebgp-requires-policy
 no bgp default ipv4-unicast
 bgp graceful-restart restart-time 240
 bgp graceful-restart select-defer-time 45
 bgp graceful-restart
 bgp graceful-restart preserve-fw-state
 bgp bestpath as-path multipath-relax
 neighbor BGPSLBPassive peer-group
 neighbor BGPSLBPassive remote-as 65432
 neighbor BGPSLBPassive passive
 neighbor BGPSLBPassive ebgp-multihop 255
 neighbor BGPSLBPassive update-source 10.1.0.32
 neighbor BGPVac peer-group
 neighbor BGPVac remote-as 65432
 neighbor BGPVac passive
 neighbor BGPVac ebgp-multihop 255
 neighbor BGPVac update-source 10.1.0.32
 neighbor PEER_V4 peer-group
 neighbor PEER_V6 peer-group
 neighbor 10.0.0.57 remote-as 64600
 neighbor 10.0.0.57 peer-group PEER_V4
 neighbor 10.0.0.57 description ARISTA01T1
 neighbor 10.0.0.57 timers 3 10
 neighbor 10.0.0.57 timers connect 10
 neighbor 10.0.0.59 remote-as 64600
 neighbor 10.0.0.59 peer-group PEER_V4
 neighbor 10.0.0.59 description ARISTA02T1
 neighbor 10.0.0.59 timers 3 10
 neighbor 10.0.0.59 timers connect 10
 neighbor 10.0.0.61 remote-as 64600
 neighbor 10.0.0.61 peer-group PEER_V4
 neighbor 10.0.0.61 description ARISTA03T1
 neighbor 10.0.0.61 timers 3 10
 neighbor 10.0.0.61 timers connect 10
 neighbor 10.0.0.63 remote-as 64600
 neighbor 10.0.0.63 peer-group PEER_V4
 neighbor 10.0.0.63 description ARISTA04T1
 neighbor 10.0.0.63 timers 3 10
 neighbor 10.0.0.63 timers connect 10
 neighbor fc00::72 remote-as 64600
 neighbor fc00::72 peer-group PEER_V6
 neighbor fc00::72 description ARISTA01T1
 neighbor fc00::72 timers 3 10
 neighbor fc00::72 timers connect 10
 neighbor fc00::76 remote-as 64600
 neighbor fc00::76 peer-group PEER_V6
 neighbor fc00::76 description ARISTA02T1
 neighbor fc00::76 timers 3 10
 neighbor fc00::76 timers connect 10
 neighbor fc00::7a remote-as 64600
 neighbor fc00::7a peer-group PEER_V6
 neighbor fc00::7a description ARISTA03T1
 neighbor fc00::7a timers 3 10
 neighbor fc00::7a timers connect 10
 neighbor fc00::7e remote-as 64600
 neighbor fc00::7e peer-group PEER_V6
 neighbor fc00::7e description ARISTA04T1
 neighbor fc00::7e timers 3 10
 neighbor fc00::7e timers connect 10
 bgp listen range 10.255.0.0/25 peer-group BGPSLBPassive
 bgp listen range 192.168.0.0/21 peer-group BGPVac
"""

class TestShowRunCommands(object):
    @classmethod
    def setup_class(cls):
        print("SETUP")
        from .mock_tables import mock_single_asic
        importlib.reload(mock_single_asic)
        from .mock_tables import dbconnector
        dbconnector.load_namespace_config()

    def test_show_run_bgp_single(self):
        runner = CliRunner()
        result = runner.invoke(show.cli.commands["runningconfiguration"].commands["bgp"], [])
        print("{}".format(result.output))
        assert result.exit_code == 0
        assert result.output == show_run_bgp_sasic
        
    @classmethod
    def teardown_class(cls):
        print("TEARDOWN")
        os.environ['UTILITIES_UNIT_TESTING'] = "0"
        from .mock_tables import mock_single_asic
        importlib.reload(mock_single_asic)
        from .mock_tables import dbconnector
        dbconnector.load_database_config()
