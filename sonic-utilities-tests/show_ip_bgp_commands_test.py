import imp
import pytest

from click.testing import CliRunner

show_bgp_summary_v4 = """\

IPv4 Unicast Summary:
BGP router identifier 10.1.0.32, local AS number 65100 vrf-id 0
BGP table version 12811
RIB entries 12817, using 2358328 bytes of memory
Peers 24, using 502080 KiB of memory
Peer groups 4, using 256 bytes of memory


Neighbhor      V     AS    MsgRcvd    MsgSent    TblVer    InQ    OutQ  Up/Down    State/PfxRcd    NeighborName
-----------  ---  -----  ---------  ---------  --------  -----  ------  ---------  --------------  --------------
10.0.0.1       4  65200       5919       2717         0      0       0  1d21h11m   6402            ARISTA01T2
10.0.0.5       4  65200       5916       2714         0      0       0  1d21h10m   6402            ARISTA03T2
10.0.0.9       4  65200       5915       2713         0      0       0  1d21h09m   6402            ARISTA05T2
10.0.0.13      4  65200       5917       2716         0      0       0  1d21h11m   6402            ARISTA07T2
10.0.0.17      4  65200       5916       2713         0      0       0  1d21h09m   6402            ARISTA09T2
10.0.0.21      4  65200       5917       2716         0      0       0  1d21h11m   6402            ARISTA11T2
10.0.0.25      4  65200       5917       2716         0      0       0  1d21h11m   6402            ARISTA13T2
10.0.0.29      4  65200       5916       2714         0      0       0  1d21h10m   6402            ARISTA15T2
10.0.0.33      4  64001          0          0         0      0       0  never      Active          ARISTA01T0
10.0.0.35      4  64002          0          0         0      0       0  never      Active          ARISTA02T0
10.0.0.37      4  64003          0          0         0      0       0  never      Active          ARISTA03T0
10.0.0.39      4  64004          0          0         0      0       0  never      Active          ARISTA04T0
10.0.0.41      4  64005          0          0         0      0       0  never      Active          ARISTA05T0
10.0.0.43      4  64006          0          0         0      0       0  never      Active          ARISTA06T0
10.0.0.45      4  64007          0          0         0      0       0  never      Active          ARISTA07T0
10.0.0.47      4  64008          0          0         0      0       0  never      Active          ARISTA08T0
10.0.0.49      4  64009          0          0         0      0       0  never      Active          ARISTA09T0
10.0.0.51      4  64010          0          0         0      0       0  never      Active          ARISTA10T0
10.0.0.53      4  64011          0          0         0      0       0  never      Active          ARISTA11T0
10.0.0.55      4  64012          0          0         0      0       0  never      Active          ARISTA12T0
10.0.0.57      4  64013          0          0         0      0       0  never      Active          ARISTA13T0
10.0.0.59      4  64014          0          0         0      0       0  never      Active          ARISTA14T0
10.0.0.61      4  64015          0          0         0      0       0  never      Active          INT_NEIGH0
10.0.0.63      4  64016          0          0         0      0       0  never      Active          INT_NEIGH1

Total number of neighbors 24
"""

show_bgp_summary_v6 = """\

IPv6 Unicast Summary:
BGP router identifier 10.1.0.32, local AS number 65100 vrf-id 0
BGP table version 8972
RIB entries 12817, using 2358328 bytes of memory
Peers 24, using 502080 KiB of memory
Peer groups 4, using 256 bytes of memory


Neighbhor      V     AS    MsgRcvd    MsgSent    TblVer    InQ    OutQ  Up/Down    State/PfxRcd    NeighborName
-----------  ---  -----  ---------  ---------  --------  -----  ------  ---------  --------------  --------------
fc00::1a       4  65200       6665       6672         0      0       0  2d09h39m   6402            ARISTA07T2
fc00::2        4  65200       6666       7913         0      0       0  2d09h39m   6402            ARISTA01T2
fc00::2a       4  65200       6666       7913         0      0       0  2d09h39m   6402            ARISTA11T2
fc00::3a       4  65200       6666       7912         0      0       0  2d09h39m   6402            ARISTA15T2
fc00::4a       4  64003          0          0         0      0       0  never      Active          ARISTA03T0
fc00::4e       4  64004          0          0         0      0       0  never      Active          ARISTA04T0
fc00::5a       4  64007          0          0         0      0       0  never      Active          ARISTA07T0
fc00::5e       4  64008          0          0         0      0       0  never      Active          ARISTA08T0
fc00::6a       4  64011          0          0         0      0       0  never      Connect         ARISTA11T0
fc00::6e       4  64012          0          0         0      0       0  never      Active          ARISTA12T0
fc00::7a       4  64015          0          0         0      0       0  never      Active          ARISTA15T0
fc00::7e       4  64016          0          0         0      0       0  never      Active          ARISTA16T0
fc00::12       4  65200       6666       7915         0      0       0  2d09h39m   6402            ARISTA05T2
fc00::22       4  65200       6667       7915         0      0       0  2d09h39m   6402            ARISTA09T2
fc00::32       4  65200       6663       6669         0      0       0  2d09h36m   6402            ARISTA13T2
fc00::42       4  64001          0          0         0      0       0  never      Active          ARISTA01T0
fc00::46       4  64002          0          0         0      0       0  never      Active          ARISTA02T0
fc00::52       4  64005          0          0         0      0       0  never      Active          ARISTA05T0
fc00::56       4  64006          0          0         0      0       0  never      Active          ARISTA06T0
fc00::62       4  64009          0          0         0      0       0  never      Active          ARISTA09T0
fc00::66       4  64010          0          0         0      0       0  never      Active          ARISTA10T0
fc00::72       4  64013          0          0         0      0       0  never      Active          ARISTA13T0
fc00::76       4  64014          0          0         0      0       0  never      Active          INT_NEIGH0
fc00::a        4  65200       6665       6671         0      0       0  2d09h38m   6402            INT_NEIGH1

Total number of neighbors 24
"""

show_error_invalid_json = """\
Usage: summary [OPTIONS]
Try 'summary --help' for help.

Error: bgp summary from bgp container not in json format
"""

show_ipv4_bgp_summary_frontend = """\

IPv4 Unicast Summary:
asic0: BGP router identifier 10.1.0.32, local AS number 65100 vrf-id 0
BGP table version 12172
asic1: BGP router identifier 8.0.0.4, local AS number 65100 vrf-id 0
BGP table version 54717
RIB entries 25676, using 4724384 bytes of memory
Peers 8, using 167360 KiB of memory
Peer groups 6, using 384 bytes of memory


Neighbhor      V     AS    MsgRcvd    MsgSent    TblVer    InQ    OutQ  Up/Down    State/PfxRcd    NeighborName
-----------  ---  -----  ---------  ---------  --------  -----  ------  ---------  --------------  --------------
1.1.1.1        4  65100          0          0         0      0       0  never      Connect         bgp_monitor
10.0.0.1       4  65200       3191          5         0      0       0  00:01:29   6370            ARISTA01T2
10.0.0.5       4  65200       3191          5         0      0       0  00:01:29   6370            ARISTA03T2

Total number of neighbors 3
"""

show_ipv4_bgp_summary_all = """\

IPv4 Unicast Summary:
asic0: BGP router identifier 10.1.0.32, local AS number 65100 vrf-id 0
BGP table version 12172
asic1: BGP router identifier 8.0.0.4, local AS number 65100 vrf-id 0
BGP table version 54717
RIB entries 25676, using 4724384 bytes of memory
Peers 8, using 167360 KiB of memory
Peer groups 6, using 384 bytes of memory


Neighbhor      V     AS    MsgRcvd    MsgSent    TblVer    InQ    OutQ  Up/Down    State/PfxRcd    NeighborName
-----------  ---  -----  ---------  ---------  --------  -----  ------  ---------  --------------  --------------
1.1.1.1        4  65100          0          0         0      0       0  never      Connect         bgp_monitor
10.0.0.1       4  65200       3191          5         0      0       0  00:01:29   6370            ARISTA01T2
10.0.0.5       4  65200       3191          5         0      0       0  00:01:29   6370            ARISTA03T2
10.1.0.1       4  65100       3344      24107         0      0       0  00:07:26   6377            ASIC0
10.1.0.2       4  65100          0          0         0      0       0  never      Active          ASIC1

Total number of neighbors 5
"""

show_ipv4_bgp_summary_asic_all = """\

IPv4 Unicast Summary:
asic0: BGP router identifier 10.1.0.32, local AS number 65100 vrf-id 0
BGP table version 12172
RIB entries 12751, using 2346184 bytes of memory
Peers 4, using 83680 KiB of memory
Peer groups 4, using 256 bytes of memory


Neighbhor      V     AS    MsgRcvd    MsgSent    TblVer    InQ    OutQ  Up/Down    State/PfxRcd    NeighborName
-----------  ---  -----  ---------  ---------  --------  -----  ------  ---------  --------------  --------------
10.0.0.1       4  65200       3191          5         0      0       0  00:01:29   6370            ARISTA01T2
10.0.0.5       4  65200       3191          5         0      0       0  00:01:29   6370            ARISTA03T2
10.1.0.2       4  65100          0          0         0      0       0  never      Active          ASIC1

Total number of neighbors 3
"""

show_ipv6_bgp_summary_frontend = """\

IPv6 Unicast Summary:
asic0: BGP router identifier 10.1.0.32, local AS number 65100 vrf-id 0
BGP table version 8185
asic1: BGP router identifier 8.0.0.4, local AS number 65100 vrf-id 0
BGP table version 12148
RIB entries 25770, using 4741680 bytes of memory
Peers 8, using 167360 KiB of memory
Peer groups 6, using 384 bytes of memory


Neighbhor      V     AS    MsgRcvd    MsgSent    TblVer    InQ    OutQ  Up/Down      State/PfxRcd  NeighborName
-----------  ---  -----  ---------  ---------  --------  -----  ------  ---------  --------------  --------------
fc00::2        4  65200       3192         12         0      0       0  00:02:13             6370  ARISTA01T2
fc00::6        4  65200       3192         12         0      0       0  00:02:13             6370  ARISTA03T2

Total number of neighbors 2
"""

show_ipv6_bgp_summary_all = """\

IPv6 Unicast Summary:
asic0: BGP router identifier 10.1.0.32, local AS number 65100 vrf-id 0
BGP table version 8185
asic1: BGP router identifier 8.0.0.4, local AS number 65100 vrf-id 0
BGP table version 12148
RIB entries 25770, using 4741680 bytes of memory
Peers 8, using 167360 KiB of memory
Peer groups 6, using 384 bytes of memory


Neighbhor             V     AS    MsgRcvd    MsgSent    TblVer    InQ    OutQ  Up/Down      State/PfxRcd  NeighborName
------------------  ---  -----  ---------  ---------  --------  -----  ------  ---------  --------------  --------------
2603:10e2:400:1::1    4  65100       6265       3591         0      0       0  00:02:14             6445  ASIC1
2603:10e2:400:1::2    4  65100       4887       6052         0      0       0  00:09:37             6380  ASIC0
fc00::2               4  65200       3192         12         0      0       0  00:02:13             6370  ARISTA01T2
fc00::6               4  65200       3192         12         0      0       0  00:02:13             6370  ARISTA03T2

Total number of neighbors 4
"""

show_ipv6_bgp_summary_asic_all = """\

IPv6 Unicast Summary:
asic0: BGP router identifier 10.1.0.32, local AS number 65100 vrf-id 0
BGP table version 8185
RIB entries 12885, using 2370840 bytes of memory
Peers 4, using 83680 KiB of memory
Peer groups 4, using 256 bytes of memory


Neighbhor             V     AS    MsgRcvd    MsgSent    TblVer    InQ    OutQ  Up/Down      State/PfxRcd  NeighborName
------------------  ---  -----  ---------  ---------  --------  -----  ------  ---------  --------------  --------------
2603:10e2:400:1::1    4  65100       6265       3591         0      0       0  00:02:14             6445  ASIC1
fc00::2               4  65200       3192         12         0      0       0  00:02:13             6370  ARISTA01T2
fc00::6               4  65200       3192         12         0      0       0  00:02:13             6370  ARISTA03T2

Total number of neighbors 3
"""

class TestBgpCommands(object):
    @classmethod
    def setup_class(cls):
        print("SETUP")
        import mock_tables.dbconnector


    @pytest.mark.parametrize('setup_single_bgp_instance',
                             ['v4'], indirect=['setup_single_bgp_instance'])
    def test_bgp_summary_v4(
            self,
            setup_bgp_commands,
            setup_single_bgp_instance):
        show = setup_bgp_commands
        runner = CliRunner()
        result = runner.invoke(
            show.cli.commands["ip"].commands["bgp"].commands["summary"], [])
        print("{}".format(result.output))
        assert result.exit_code == 0
        assert result.output == show_bgp_summary_v4

    @pytest.mark.parametrize('setup_single_bgp_instance',
                             ['v6'], indirect=['setup_single_bgp_instance'])
    def test_bgp_summary_v6(
            self,
            setup_bgp_commands,
            setup_single_bgp_instance):
        show = setup_bgp_commands
        runner = CliRunner()
        result = runner.invoke(
            show.cli.commands["ipv6"].commands["bgp"].commands["summary"], [])
        print("{}".format(result.output))
        assert result.exit_code == 0
        assert result.output == show_bgp_summary_v6

    @pytest.mark.parametrize('setup_single_bgp_instance',
                             [' '], indirect=['setup_single_bgp_instance'])
    def test_bgp_summary_error(
            self,
            setup_bgp_commands,
            setup_single_bgp_instance):
        show = setup_bgp_commands
        runner = CliRunner()
        result = runner.invoke(
            show.cli.commands["ipv6"].commands["bgp"].commands["summary"], [])
        print("{}".format(result.output))
        assert result.exit_code == 2
        assert result.output == show_error_invalid_json


@pytest.mark.usefixtures('setup_multi_asic_display_options')
class TestBgpCommandsMultiAsic(object):

    @pytest.mark.parametrize('setup_multi_asic_bgp_instance',
                                ['v4'],
                                indirect=['setup_multi_asic_bgp_instance']
                            )
    def test_bgp_summary_v4(
            self,
            setup_bgp_commands,
            setup_multi_asic_bgp_instance,
            setup_multi_asic_display_options
            ):
        show = setup_bgp_commands
        runner = CliRunner()
        result = runner.invoke(
            show.cli.commands["ip"].commands["bgp"].commands["summary"], [])
        print("{}".format(result.output))
        assert result.exit_code == 0
        assert result.output == show_ipv4_bgp_summary_frontend

    @pytest.mark.parametrize('setup_multi_asic_bgp_instance',
                             ['v4'], indirect=['setup_multi_asic_bgp_instance'])
    def test_bgp_summary_v4_frontend(
            self,
            setup_bgp_commands,
            setup_multi_asic_bgp_instance,
            ):
        show = setup_bgp_commands
        runner = CliRunner()
        result = runner.invoke(
            show.cli.commands["ip"].commands["bgp"].commands["summary"], ["-dfrontend"])
        print("{}".format(result.output))
        assert result.exit_code == 0
        assert result.output == show_ipv4_bgp_summary_frontend


    @pytest.mark.parametrize('setup_multi_asic_bgp_instance',
                             ['v4'], indirect=['setup_multi_asic_bgp_instance'])
    def test_bgp_summary_v4_all(
            self,
            setup_bgp_commands,
            setup_multi_asic_bgp_instance,
            ):
        show = setup_bgp_commands
        runner = CliRunner()
        result = runner.invoke(
            show.cli.commands["ip"].commands["bgp"].commands["summary"], ["-dall"])
        print("{}".format(result.output))
        assert result.exit_code == 0
        assert result.output == show_ipv4_bgp_summary_all


    @pytest.mark.parametrize('setup_multi_asic_bgp_instance',
                             ['v4'], indirect=['setup_multi_asic_bgp_instance'])
    def test_bgp_summary_v4_all_asic(
            self,
            setup_bgp_commands,
            setup_multi_asic_bgp_instance,
            ):
        show = setup_bgp_commands
        runner = CliRunner()
        result = runner.invoke(
            show.cli.commands["ip"].commands["bgp"].commands["summary"], ["-nasic0", "-dall"])
        print("{}".format(result.output))
        assert result.exit_code == 0
        assert result.output == show_ipv4_bgp_summary_asic_all

    @pytest.mark.parametrize('setup_multi_asic_bgp_instance',
                             ['v6'], indirect=['setup_multi_asic_bgp_instance'])
    def test_bgp_summary_v6(
            self,
            setup_bgp_commands,
            setup_multi_asic_bgp_instance,
            ):
        show = setup_bgp_commands
        runner = CliRunner()
        result = runner.invoke(
            show.cli.commands["ipv6"].commands["bgp"].commands["summary"], [])
        print("{}".format(result.output))
        assert result.exit_code == 0
        assert result.output == show_ipv6_bgp_summary_frontend

    @pytest.mark.parametrize('setup_multi_asic_bgp_instance',
                             ['v6'], indirect=['setup_multi_asic_bgp_instance'])
    def test_bgp_summary_v6_frontend(
            self,
            setup_bgp_commands,
            setup_multi_asic_bgp_instance,
            ):
        show = setup_bgp_commands
        runner = CliRunner()
        result = runner.invoke(
            show.cli.commands["ipv6"].commands["bgp"].commands["summary"], ["-dfrontend"])
        print("{}".format(result.output))
        assert result.exit_code == 0
        assert result.output == show_ipv6_bgp_summary_frontend

    @pytest.mark.parametrize('setup_multi_asic_bgp_instance',
                             ['v6'],
                             indirect=['setup_multi_asic_bgp_instance'])
    def test_bgp_summary_v6_all(
            self,
            setup_bgp_commands,
            setup_multi_asic_bgp_instance,
            ):
        show = setup_bgp_commands
        runner = CliRunner()
        result = runner.invoke(
            show.cli.commands["ipv6"].commands["bgp"].commands["summary"], ["-dall"])
        print("{}".format(result.output))
        assert result.exit_code == 0
        assert result.output == show_ipv6_bgp_summary_all


    @pytest.mark.parametrize('setup_multi_asic_bgp_instance',
                             ['v6'], indirect=['setup_multi_asic_bgp_instance'])
    def test_bgp_summary_v6_all_asic(
            self,
            setup_bgp_commands,
            setup_multi_asic_bgp_instance,
            ):
        show = setup_bgp_commands
        runner = CliRunner()
        result = runner.invoke(
            show.cli.commands["ipv6"].commands["bgp"].commands["summary"], ["-nasic0", "-dall"])
        print("{}".format(result.output))
        assert result.exit_code == 0
        assert result.output == show_ipv6_bgp_summary_asic_all

    @classmethod
    def teardown_class(cls):
        print("TEARDOWN")
        import mock_tables.mock_single_asic
        imp.reload(mock_tables.mock_single_asic)
        mock_tables.dbconnector.load_database_config()


