import os
import traceback
from unittest import mock

from click.testing import CliRunner

import config.main as config
import show.main as show
from utilities_common.db import Db

show_vxlan_interface_output="""\
VTEP Information:

        VTEP Name : vtep1, SIP  : 1.1.1.1
        NVO Name  : nvo1,  VTEP : vtep1
"""

show_vxlan_vlanvnimap_output="""\
+---------+-------+
| VLAN    |   VNI |
+=========+=======+
| Vlan100 |   100 |
+---------+-------+
| Vlan101 |   101 |
+---------+-------+
| Vlan102 |   102 |
+---------+-------+
| Vlan200 |   200 |
+---------+-------+
Total count : 4

"""

show_vxlan_tunnel_output="""\
+---------+-------------+-------------------+--------------+
| SIP     | DIP         | Creation Source   | OperStatus   |
+=========+=============+===================+==============+
| 1.1.1.1 | 25.25.25.25 | EVPN              | oper_down    |
+---------+-------------+-------------------+--------------+
| 1.1.1.1 | 25.25.25.26 | EVPN              | oper_down    |
+---------+-------------+-------------------+--------------+
| 1.1.1.1 | 25.25.25.27 | EVPN              | oper_down    |
+---------+-------------+-------------------+--------------+
Total count : 3

"""

show_vxlan_remotevni_output="""\
+---------+--------------+-------+
| VLAN    | RemoteVTEP   |   VNI |
+=========+==============+=======+
| Vlan200 | 25.25.25.25  |  2000 |
+---------+--------------+-------+
| Vlan200 | 25.25.25.26  |  2000 |
+---------+--------------+-------+
| Vlan200 | 25.25.25.27  |  2000 |
+---------+--------------+-------+
Total count : 3

"""

show_vxlan_remotevni_specific_output="""\
+---------+--------------+-------+
| VLAN    | RemoteVTEP   |   VNI |
+=========+==============+=======+
| Vlan200 | 25.25.25.27  |  2000 |
+---------+--------------+-------+
Total count : 1

"""
show_vxlan_vlanvnimap_cnt_output="""\
Total count : 4

"""

show_vxlan_tunnel_cnt_output="""\
Total count : 3

"""

show_vxlan_remotevni_cnt_output="""\
Total count : 3

"""

show_vxlan_remotevni_specific_cnt_output="""\
Total count : 1

"""

class TestVxlan(object):
    @classmethod
    def setup_class(cls):
        os.environ['UTILITIES_UNIT_TESTING'] = "1"
        print("SETUP")

    def test_show_vxlan_interface(self):
        runner = CliRunner()
        result = runner.invoke(show.cli.commands["vxlan"].commands["interface"], [])
        print(result.exit_code)
        print(result.output)
        assert result.exit_code == 0
        assert result.output == show_vxlan_interface_output

    def test_show_vxlan_vlanvnimap(self):
        runner = CliRunner()
        result = runner.invoke(show.cli.commands["vxlan"].commands["vlanvnimap"], [])
        print(result.exit_code)
        print(result.output)
        assert result.exit_code == 0
        assert result.output == show_vxlan_vlanvnimap_output

    def test_show_vxlan_tunnel(self):
        runner = CliRunner()
        result = runner.invoke(show.cli.commands["vxlan"].commands["tunnel"], [])
        print(result.exit_code)
        print(result.output)
        assert result.exit_code == 0
        assert result.output == show_vxlan_tunnel_output

    def test_show_vxlan_remotevni(self):
        runner = CliRunner()
        result = runner.invoke(show.cli.commands["vxlan"].commands["remote-vni all"], [])
        print(result.exit_code)
        print(result.output)
        assert result.exit_code == 0
        assert result.output == show_vxlan_remotevni_output

    def test_show_vxlan_remotevni_specific(self):
        runner = CliRunner()
        result = runner.invoke(show.cli.commands["vxlan"].commands["remote-vni 25.25.25.27"], [])
        print(result.exit_code)
        print(result.output)
        assert result.exit_code == 0
        assert result.output == show_vxlan_remotevni_specific_output

    def test_show_vxlan_vlanvnimap_cnt(self):
        runner = CliRunner()
        result = runner.invoke(show.cli.commands["vxlan"].commands["vlanvnimap count"], [])
        print(result.exit_code)
        print(result.output)
        assert result.exit_code == 0
        assert result.output == show_vxlan_vlanvnimap_cnt_output

    def test_show_vxlan_tunnel_cnt(self):
        runner = CliRunner()
        result = runner.invoke(show.cli.commands["vxlan"].commands["tunnel count"], [])
        print(result.exit_code)
        print(result.output)
        assert result.exit_code == 0
        assert result.output == show_vxlan_tunnel_cnt_output

    def test_show_vxlan_remotevni_cnt(self):
        runner = CliRunner()
        result = runner.invoke(show.cli.commands["vxlan"].commands["remote-vni all count"], [])
        print(result.exit_code)
        print(result.output)
        assert result.exit_code == 0
        assert result.output == show_vxlan_remotevni_cnt_output

    def test_show_vxlan_remotevni_specific_cnt(self):
        runner = CliRunner()
        result = runner.invoke(show.cli.commands["vxlan"].commands["remote-vni 25.25.25.27 count"], [])
        print(result.exit_code)
        print(result.output)
        assert result.exit_code == 0
        assert result.output == show_vxlan_remotevni_specific_cnt_output

    @classmethod
    def teardown_class(cls):
        os.environ['UTILITIES_UNIT_TESTING'] = "0"
        print("TEARDOWN")
