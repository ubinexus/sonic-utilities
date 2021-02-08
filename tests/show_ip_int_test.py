import os
import pytest
import subprocess
from click.testing import CliRunner

import show.main as show
from .utils import get_result_and_return_code

root_path = os.path.dirname(os.path.abspath(__file__))
modules_path = os.path.dirname(root_path)
scripts_path = os.path.join(modules_path, "scripts")


setup_ip_intfs_single_asic = [
#    # ipv6 is disabled by default ,
    'sudo sysctl -w net.ipv6.conf.all.disable_ipv6=0',
    # this flag is need to stop kernel auto generating Linklocal address
    'sudo sysctl -w net.ipv6.conf.default.addr_gen_mode=1',
    # dummy physical port
    'sudo ip link add Ethernet0 type dummy',
    'sudo ip addr add 20.1.1.1/24 dev Ethernet0',
    'sudo ip -6 address add dev Ethernet0 scope link fe80::64be:a1ff:fe85:c6c4/64',
    'sudo ip -6 addr add aa00::1/64 dev Ethernet0',
    'sudo ip link set Ethernet0 up',

    #dummy portchannel
    'sudo ip link add PortChannel0001 type dummy',
    'sudo ip addr add 30.1.1.1/24 dev PortChannel0001',
    'sudo ip -6 address add dev PortChannel0001 scope link fe80::cc8d:60ff:fe08:139f/64',
    'sudo ip -6 addr add ab00::1/64 dev PortChannel0001',
    'sudo ip link set PortChannel0001 up',

    #dummy Vlan interface
    'sudo ip link add Vlan100 type dummy',
    'sudo ip addr add 40.1.1.1/24 dev Vlan100',
    'sudo ip -6 address add dev Vlan100 scope link fe80::c029:3fff:fe41:cf56/64',
    'sudo ip -6 addr add cc00::1/64 dev Vlan100',
    'sudo ip link set Vlan100 up',

]
cleanup_ip_intfs_single_asic = [
    'sudo ip link del Ethernet0',
    'sudo ip link del PortChannel0001',
    'sudo ip link del Vlan100',
    'sudo sysctl -w net.ipv6.conf.default.addr_gen_mode=1',
    'sudo sysctl -w net.ipv6.conf.all.disable_ipv6=1'

]

show_ip_intf = """Interface        Master    IPv4 address/mask    Admin/Oper    BGP Neighbor    Neighbor IP
---------------  --------  -------------------  ------------  --------------  -------------
Ethernet0                  20.1.1.1/24          error/down    T2-Peer         20.1.1.5
PortChannel0001            30.1.1.1/24          error/down    T0-Peer         30.1.1.5
Vlan100                    40.1.1.1/24          error/down    N/A             N/A
lo                         127.0.0.1/8          error/down    N/A             N/A"""

show_ipv6_intf = """Interface        Master    IPv4 address/mask                             Admin/Oper    BGP Neighbor    Neighbor IP
---------------  --------  --------------------------------------------  ------------  --------------  -------------
Ethernet0                  aa00::1/64                                    error/down    N/A             N/A
                           fe80::64be:a1ff:fe85:c6c4%Ethernet0/64                      N/A             N/A
PortChannel0001            ab00::1/64                                    error/down    N/A             N/A
                           fe80::cc8d:60ff:fe08:139f%PortChannel0001/64                N/A             N/A
Vlan100                    cc00::1/64                                    error/down    N/A             N/A
                           fe80::c029:3fff:fe41:cf56%Vlan100/64                        N/A             N/A
lo                         ::1/128                                       error/down    N/A             N/A"""

show_ipv4_intf_with_multple_ips = """Interface        Master    IPv4 address/mask    Admin/Oper    BGP Neighbor    Neighbor IP
---------------  --------  -------------------  ------------  --------------  -------------
Ethernet0                  20.1.1.1/24          error/down    T2-Peer         20.1.1.5
                           21.1.1.1/24                        N/A             N/A
PortChannel0001            30.1.1.1/24          error/down    T0-Peer         30.1.1.5
Vlan100                    40.1.1.1/24          error/down    N/A             N/A
lo                         127.0.0.1/8          error/down    N/A             N/A"""

show_ipv6_intf_with_multiple_ips = """Interface        Master    IPv4 address/mask                             Admin/Oper    BGP Neighbor    Neighbor IP
---------------  --------  --------------------------------------------  ------------  --------------  -------------
Ethernet0                  2100::1/24                                    error/down    N/A             N/A
                           aa00::1/64                                                  N/A             N/A
                           fe80::64be:a1ff:fe85:c6c4%Ethernet0/64                      N/A             N/A
PortChannel0001            ab00::1/64                                    error/down    N/A             N/A
                           fe80::cc8d:60ff:fe08:139f%PortChannel0001/64                N/A             N/A
Vlan100                    cc00::1/64                                    error/down    N/A             N/A
                           fe80::c029:3fff:fe41:cf56%Vlan100/64                        N/A             N/A
lo                         ::1/128                                       error/down    N/A             N/A"""

show_multi_asic_ip_intf = """Interface        Master    IPv4 address/mask    Admin/Oper    BGP Neighbor    Neighbor IP
---------------  --------  -------------------  ------------  --------------  -------------
Loopback0                  40.1.1.1/32          error/down    N/A             N/A
PortChannel0001            20.1.1.1/24          error/down    T2-Peer         20.1.1.5
eth0                       10.1.1.1/24          error/down    N/A             N/A
"""

show_multi_asic_ip_intf_all = """Interface        Master    IPv4 address/mask    Admin/Oper    BGP Neighbor    Neighbor IP
---------------  --------  -------------------  ------------  --------------  -------------
Loopback0                  40.1.1.1/32          error/down    N/A             N/A
Loopback4096               1.1.1.1/24           error/down    N/A             N/A
                           2.1.1.1/24                         N/A             N/A
PortChannel0001            20.1.1.1/24          error/down    T2-Peer         20.1.1.5
PortChannel0002            30.1.1.1/24          error/down    T0-Peer         30.1.1.5
eth0                       10.1.1.1/24          error/down    N/A             N/A
veth@eth1                  192.1.1.1/24         error/down    N/A             N/A
veth@eth2                  193.1.1.1/24         error/down    N/A             N/A
"""

show_error_invalid_af = """Invalid argument -a ipv5"""


def run_commands(cmds):
    for cmd in cmds:
        print("> {}".format(cmd))
        try:
            subprocess.check_call(cmd, shell=True)
        except subprocess.CalledProcessError:
            return False
    return True

@pytest.fixture(scope="class")
def setup_teardown_single_asic():
    print("setting up the interfaces")
    run_commands(setup_ip_intfs_single_asic)
    os.environ["PATH"] += os.pathsep + scripts_path
    os.environ["UTILITIES_UNIT_TESTING"] = "2"
    yield

    print("cleaning up...")
    run_commands(cleanup_ip_intfs_single_asic)

@pytest.fixture(scope="class")
def setup_teardown_multi_asic():
    os.environ["PATH"] += os.pathsep + scripts_path
    os.environ["UTILITIES_UNIT_TESTING"] = "2"
    os.environ["UTILITIES_UNIT_TESTING_TOPOLOGY"] = "multi_asic"
    yield
    os.environ["UTILITIES_UNIT_TESTING"] = "0"
    os.environ["UTILITIES_UNIT_TESTING_TOPOLOGY"] = ""


@pytest.mark.usefixtures('setup_teardown_single_asic')
class TestShowIpInt(object):
    @classmethod
    def setup_class(cls):
        print("SETUP")

    def verify_output(self, output, expected_output):
        lines = output.splitlines()

        # the output should have line to display the ip address of eth0
        assert len([line for line in lines if line.startswith('eth0')]) == 1

        # ignore the lines with eth0 in them because the ip address keeps on changing
        # difficult to compare
        new_output = '\n'.join([line for line in lines if 'eth0' not in line])
        print(new_output)
        assert new_output == expected_output

    def test_show_ip_intf_v4(self):
        return_code, result = get_result_and_return_code(" ipintutil")
        assert return_code == 0
        self.verify_output(result, show_ip_intf)

    def test_show_ip_intf_v6(self):
        return_code, result = get_result_and_return_code(" ipintutil -a ipv6")

        assert return_code == 0
        self.verify_output(result, show_ipv6_intf)

    def test_show_ip_intf_with_no_ip(self):
        run_commands(['sudo ip link add Ethernet1 type dummy'])

        return_code, result = get_result_and_return_code(" ipintutil -a ipv4")
        run_commands(['sudo ip link del Ethernet1'])

        assert return_code == 0
        self.verify_output(result, show_ip_intf)

    def test_show_ipv4_intf_With_multiple_ips(self):
        run_commands(['sudo ip addr add 21.1.1.1/24 dev Ethernet0 '])
        return_code, result = get_result_and_return_code(" ipintutil -a ipv4")
        print(result)
        assert return_code == 0
        self.verify_output(result, show_ipv4_intf_with_multple_ips)

    def test_show_ipv6_intf_With_multiple_ips(self):
        run_commands(['sudo ip -6 addr add 2100::1/24 dev Ethernet0 '])
        return_code, result = get_result_and_return_code(" ipintutil -a ipv6")
        print(result)
        assert return_code == 0
        self.verify_output(result, show_ipv6_intf_with_multiple_ips)

    def test_show_intf_invalid_af_option(self):
        return_code, result = get_result_and_return_code(" ipintutil -a ipv5")
        assert return_code == 1
        assert result == show_error_invalid_af


@pytest.mark.usefixtures('setup_teardown_multi_asic')
class TestMultiAsicShowIpInt(object):

    def test_show_ip_intf_v4(self):
        return_code, result = get_result_and_return_code("ipintutil")
        assert return_code == 0
        assert result == show_multi_asic_ip_intf

    def test_show_ip_intf_v4_asic0(self):
        return_code, result = get_result_and_return_code("ipintutil -n asic0")
        assert return_code == 0
        assert result == show_multi_asic_ip_intf

    def test_show_ip_intf_v4_all(self):
        return_code, result = get_result_and_return_code("ipintutil -d all")
        assert return_code == 0
        assert result == show_multi_asic_ip_intf_all

    def test_show_intf_invalid_af_option(self):
        return_code, result = get_result_and_return_code(" ipintutil -a ipv5")
        assert return_code == 1
        assert result == show_error_invalid_af
