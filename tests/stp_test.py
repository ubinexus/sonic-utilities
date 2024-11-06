import os
import pytest
from click.testing import CliRunner

import config.main as config
import show.main as show
from utilities_common.db import Db


show_spanning_tree = """\
Spanning-tree Mode: PVST

VLAN 100 - STP instance 0
--------------------------------------------------------------------
STP Bridge Parameters:
Bridge           Bridge Bridge Bridge Hold  LastTopology Topology
Identifier       MaxAge Hello  FwdDly Time  Change       Change
hex              sec    sec    sec    sec   sec          cnt
8064b86a97e24e9c 20     2      15     1     0            1

RootBridge       RootPath  DesignatedBridge  RootPort           Max Hel Fwd
Identifier       Cost      Identifier                           Age lo  Dly
hex                        hex                                  sec sec sec
0064b86a97e24e9c 600       806480a235f281ec  Root               20  2   15

STP Port Parameters:
Port             Prio Path      Port Uplink State         Designated  Designated       Designated
Name             rity Cost      Fast Fast                 Cost        Root             Bridge
Ethernet4        128  200       N    N      FORWARDING    400         0064b86a97e24e9c 806480a235f281ec
"""

show_spanning_tree_vlan = """\

VLAN 100 - STP instance 0
--------------------------------------------------------------------
STP Bridge Parameters:
Bridge           Bridge Bridge Bridge Hold  LastTopology Topology
Identifier       MaxAge Hello  FwdDly Time  Change       Change
hex              sec    sec    sec    sec   sec          cnt
8064b86a97e24e9c 20     2      15     1     0            1

RootBridge       RootPath  DesignatedBridge  RootPort           Max Hel Fwd
Identifier       Cost      Identifier                           Age lo  Dly
hex                        hex                                  sec sec sec
0064b86a97e24e9c 600       806480a235f281ec  Root               20  2   15

STP Port Parameters:
Port             Prio Path      Port Uplink State         Designated  Designated       Designated
Name             rity Cost      Fast Fast                 Cost        Root             Bridge
Ethernet4        128  200       N    N      FORWARDING    400         0064b86a97e24e9c 806480a235f281ec
"""

show_spanning_tree_statistics = """\
VLAN 100 - STP instance 0
--------------------------------------------------------------------
PortNum          BPDU Tx        BPDU Rx        TCN Tx         TCN Rx
Ethernet4        10             15             15             5
"""

show_spanning_tree_bpdu_guard = """\
PortNum          Shutdown     Port Shut
                 Configured   due to BPDU guard
-------------------------------------------
Ethernet4        No           NA
"""

show_spanning_tree_root_guard = """\
Root guard timeout: 30 secs

Port             VLAN   Current State
-------------------------------------------
Ethernet4        100    Consistent state
"""


class TestStp(object):
    @classmethod
    def setup_class(cls):
        os.environ['UTILITIES_UNIT_TESTING'] = "1"
        print("SETUP")

    def test_show_spanning_tree(self):
        runner = CliRunner()
        db = Db()
        result = runner.invoke(show.cli.commands["spanning-tree"], [], obj=db)
        print(result.exit_code)
        print(result.output)
        assert result.exit_code == 0
        assert result.output == show_spanning_tree

    def test_show_spanning_tree_vlan(self):
        runner = CliRunner()
        db = Db()
        result = runner.invoke(show.cli.commands["spanning-tree"].commands["vlan"], ["100"], obj=db)
        print(result.exit_code)
        print(result.output)
        assert result.exit_code == 0
        assert result.output == show_spanning_tree_vlan

    def test_show_spanning_tree_statistics(self):
        runner = CliRunner()
        db = Db()
        result = runner.invoke(show.cli.commands["spanning-tree"].commands["statistics"], [], obj=db)
        print(result.exit_code)
        print(result.output)
        assert result.exit_code == 0
        assert result.output == show_spanning_tree_statistics

    def test_show_spanning_tree_statistics_vlan(self):
        runner = CliRunner()
        db = Db()
        result = runner.invoke(
            show.cli.commands["spanning-tree"].commands["statistics"].commands["vlan"], ["100"], obj=db)
        print(result.exit_code)
        print(result.output)
        assert result.exit_code == 0
        assert result.output == show_spanning_tree_statistics

    def test_show_spanning_tree_bpdu_guard(self):
        runner = CliRunner()
        db = Db()
        result = runner.invoke(show.cli.commands["spanning-tree"].commands["bpdu_guard"], [], obj=db)
        print(result.exit_code)
        print(result.output)
        assert result.exit_code == 0
        assert result.output == show_spanning_tree_bpdu_guard

    def test_show_spanning_tree_root_guard(self):
        runner = CliRunner()
        db = Db()
        result = runner.invoke(show.cli.commands["spanning-tree"].commands["root_guard"], [], obj=db)
        print(result.exit_code)
        print(result.output)
        assert result.exit_code == 0
        assert result.output == show_spanning_tree_root_guard

    def test_disable_disable_global_pvst(self):
        runner = CliRunner()
        db = Db()
        command = config.config.commands["spanning-tree"].commands["disable"]
        print("Command Executed:", vars(command))
        result = runner.invoke(command, ["pvst"], obj=db)
        print("exit code {}".format(result.exit_code))
        print("result code {}".format(result.output))
        assert result.exit_code != 0

    # Fixture for initializing the CliRunner
    @pytest.fixture
    def runner():
        return CliRunner()

    # Fixture for initializing the Db
    @pytest.fixture
    def db():
        return Db()

    @pytest.mark.parametrize("command, args, expected_exit_code, expected_output", [
        # Disable PVST
        (config.config.commands["spanning-tree"].commands["disable"], ["pvst"], 0, None),
        # Enable PVST
        (config.config.commands["spanning-tree"].commands["enable"], ["pvst"], 0, None),
        # Add VLAN and member
        (config.config.commands["vlan"].commands["add"], ["100"], 0, None),
        (config.config.commands["vlan"].commands["member"].commands["add"], ["100", "Ethernet4"], 0, None),
        # Attempt to enable PVST when it is already enabled
        (config.config.commands["spanning-tree"].commands["enable"], ["pvst"], 1, "PVST is already configured")
    ])
    def test_disable_enable_global_pvst(self, runner, db, command, args, expected_exit_code, expected_output):
        # Execute the command
        result = runner.invoke(command, args, obj=db)

        # Print for debugging
        print(result.exit_code)
        print(result.output)

        print("Command Executed:", vars(command))
        print("Arguments:", args)
        print("Expected Exit Code:", expected_exit_code)
        print("Actual Exit Code:", result.exit_code)
        print("Output:", result.output)

        # Check the exit code
        assert result.exit_code == expected_exit_code

        # Check the output if an expected output is defined
        if expected_output:
            assert expected_output in result.output

    @pytest.mark.parametrize("command, args, expected_exit_code, expected_output", [
        # Disable pvst
        (config.config.commands["spanning-tree"].commands["disable"], ["pvst"], 0, None),
        # Attempt enabling STP interface without global STP enabled
        (config.config.commands["spanning-tree"].commands["interface"].commands["enable"],
            ["Ethernet4"], 1, "Global STP is not enabled"),
        # Add VLAN and member
        (config.config.commands["vlan"].commands["add"], ["100"], 0, None),
        (config.config.commands["vlan"].commands["member"].commands["add"], ["100", "Ethernet4"], 0, None),
        # Enable pvst
        (config.config.commands["spanning-tree"].commands["enable"], ["pvst"], 0, None),
        # Configure interface priority and cost
        (config.config.commands["spanning-tree"].commands["interface"].commands["priority"],
            ["Ethernet4", "16"], 0, None),
        (config.config.commands["spanning-tree"].commands["interface"].commands["cost"],
            ["Ethernet4", "100"], 0, None),
        # Disable and enable interface spanning tree
        (config.config.commands["spanning-tree"].commands["interface"].commands["disable"], ["Ethernet4"], 0, None),
        (config.config.commands["spanning-tree"].commands["interface"].commands["enable"], ["Ethernet4"], 0, None),
        # Configure portfast disable and enable
        (config.config.commands["spanning-tree"].commands["interface"].commands["portfast"].commands["disable"],
            ["Ethernet4"], 0, None),
        (config.config.commands["spanning-tree"].commands["interface"].commands["portfast"].commands["enable"],
            ["Ethernet4"], 0, None),
        # Configure uplink fast disable and enable
        (config.config.commands["spanning-tree"].commands["interface"].commands["uplink_fast"].commands["disable"],
            ["Ethernet4"], 0, None),
        (config.config.commands["spanning-tree"].commands["interface"].commands["uplink_fast"].commands["enable"],
            ["Ethernet4"], 0, None),
        # Configure BPDU guard enable and disable with shutdown
        (config.config.commands["spanning-tree"].commands["interface"].commands["bpdu_guard"].commands["enable"],
            ["Ethernet4"], 0, None),
        (config.config.commands["spanning-tree"].commands["interface"].commands["bpdu_guard"].commands["disable"],
            ["Ethernet4"], 0, None),
        (config.config.commands["spanning-tree"].commands["interface"].commands["bpdu_guard"].commands["enable"],
            ["Ethernet4", "--shutdown"], 0, None),
        (config.config.commands["spanning-tree"].commands["interface"].commands["bpdu_guard"].commands["disable"],
            ["Ethernet4"], 0, None),
        # Configure root guard enable and disable
        (config.config.commands["spanning-tree"].commands["interface"].commands["root_guard"].commands["enable"],
            ["Ethernet4"], 0, None),
        (config.config.commands["spanning-tree"].commands["interface"].commands["root_guard"].commands["disable"],
            ["Ethernet4"], 0, None),
        # Invalid cost and priority values
        (config.config.commands["spanning-tree"].commands["interface"].commands["cost"], ["Ethernet4", "0"],
            1, "STP interface path cost must be in range 1-200000000"),
        (config.config.commands["spanning-tree"].commands["interface"].commands["cost"], ["Ethernet4", "2000000000"],
            1, "STP interface path cost must be in range 1-200000000"),
        (config.config.commands["spanning-tree"].commands["interface"].commands["priority"], ["Ethernet4", "1000"],
            1, "STP interface priority must be in range 0-240"),
        # Attempt to enable STP on interface with various conflicts
        (config.config.commands["spanning-tree"].commands["interface"].commands["enable"], ["Ethernet4"],
            1, "STP is already enabled for"),
        (config.config.commands["spanning-tree"].commands["interface"].commands["enable"], ["Ethernet0"],
            1, "has ip address"),
        (config.config.commands["spanning-tree"].commands["interface"].commands["enable"], ["Ethernet120"],
            1, "is a portchannel member port"),
        (config.config.commands["spanning-tree"].commands["interface"].commands["enable"], ["Ethernet20"],
            1, "has no VLAN configured")
    ])
    def test_stp_validate_interface_params(self, runner, db, command, args, expected_exit_code, expected_output):
        # runner = CliRunner()
        # db = Db()
        # Execute the command
        result = runner.invoke(command, args, obj=db)

        # Print for debugging
        print(result.exit_code)
        print(result.output)

        # Check the exit code
        assert result.exit_code == expected_exit_code

        # Check the output if an expected output is defined
        if expected_output:
            assert expected_output in result.output

    @pytest.mark.parametrize("command, args, expected_exit_code, expected_output", [
        (config.config.commands["spanning-tree"].commands["disable"], ["pvst"], 0, None),
        (config.config.commands["vlan"].commands["add"], ["100"], 0, None),
        (config.config.commands["vlan"].commands["member"].commands["add"], ["100", "Ethernet4"], 0, None),
        (config.config.commands["spanning-tree"].commands["enable"], ["pvst"], 0, None),
        (config.config.commands["spanning-tree"].commands["vlan"].commands["interface"].commands["cost"],
            ["100", "Ethernet4", "100"], 0, None),
        (config.config.commands["spanning-tree"].commands["vlan"].commands["interface"].commands["priority"],
            ["100", "Ethernet4", "32"], 0, None),
        (config.config.commands["spanning-tree"].commands["vlan"].commands["interface"].commands["cost"],
            ["100", "Ethernet4", "0"], 1, "STP interface path cost must be in range 1-200000000"),
        (config.config.commands["spanning-tree"].commands["vlan"].commands["interface"].commands["cost"],
            ["100", "Ethernet4", "2000000000"], 1, "STP interface path cost must be in range 1-200000000"),
        (config.config.commands["spanning-tree"].commands["vlan"].commands["interface"].commands["priority"],
            ["100", "Ethernet4", "1000"], 1, "STP per vlan port priority must be in range 0-240"),
        (config.config.commands["vlan"].commands["add"], ["101"], 0, None),
        (config.config.commands["spanning-tree"].commands["vlan"].commands["interface"].commands["priority"],
            ["101", "Ethernet4", "16"], 1, "is not member of"),
        (config.config.commands["vlan"].commands["member"].commands["del"], ["100", "Ethernet4"], 0, None),
        (config.config.commands["vlan"].commands["del"], ["100"], 1, None)
    ])
    def test_stp_validate_vlan_interface_params(self, runner, db, command, args, expected_exit_code, expected_output):
        # runner = CliRunner()
        # db = Db()

        # Execute the command
        result = runner.invoke(command, args, obj=db)
        # Output result information
        print(result.exit_code)
        print(result.output)

        # Check exit code
        assert result.exit_code == expected_exit_code

        # If an expected output is defined, check that as well
        if expected_output is not None:
            assert expected_output in result.output

    @pytest.mark.parametrize("command, args, expected_exit_code, expected_output", [
        (config.config.commands["spanning-tree"].commands["disable"], ["pvst"], 0, None),
        (config.config.commands["spanning-tree"].commands["enable"], ["pvst"], 0, None),
        (config.config.commands["vlan"].commands["add"], ["100"], 0, None),
        (config.config.commands["vlan"].commands["member"].commands["add"], ["100", "Ethernet4"], 0, None),
        (config.config.commands["spanning-tree"].commands["vlan"].commands["hello"], ["100", "3"], 0, None),
        (config.config.commands["spanning-tree"].commands["vlan"].commands["max_age"], ["100", "21"], 0, None),
        (config.config.commands["spanning-tree"].commands["vlan"].commands["forward_delay"], ["100", "16"], 0, None),
        (config.config.commands["spanning-tree"].commands["vlan"].commands["priority"], ["100", "4096"], 0, None),
        (config.config.commands["spanning-tree"].commands["vlan"].commands["hello"], ["100", "0"],
            1, "STP hello timer must be in range 1-10"),
        (config.config.commands["spanning-tree"].commands["vlan"].commands["hello"], ["100", "20"],
            1, "STP hello timer must be in range 1-10"),
        (config.config.commands["spanning-tree"].commands["vlan"].commands["forward_delay"], ["100", "2"],
            1, "STP forward delay value must be in range 4-30"),
        (config.config.commands["spanning-tree"].commands["vlan"].commands["forward_delay"], ["100", "42"],
            1, "STP forward delay value must be in range 4-30"),
        (config.config.commands["spanning-tree"].commands["vlan"].commands["max_age"], ["100", "4"],
            1, "STP max age value must be in range 6-40"),
        (config.config.commands["spanning-tree"].commands["vlan"].commands["max_age"], ["100", "45"],
            1, "STP max age value must be in range 6-40"),
        (config.config.commands["spanning-tree"].commands["vlan"].commands["forward_delay"], ["100", "4"],
            1, "2*(forward_delay-1) >= max_age >= 2*(hello_time +1 )"),
        (config.config.commands["spanning-tree"].commands["vlan"].commands["priority"], ["100", "70000"],
            1, "STP bridge priority must be in range 0-61440"),
        (config.config.commands["spanning-tree"].commands["vlan"].commands["priority"], ["100", "8000"],
            1, "STP bridge priority must be multiple of 4096")
    ])
    def test_stp_validate_vlan_timer_and_priority_params(
        self, runner, db, command, args, expected_exit_code, expected_output):
        # runner = CliRunner()
        # db = Db()
        # Execute the command
        result = runner.invoke(command, args, obj=db)

        # Print for debugging
        print(result.exit_code)
        print(result.output)

        # Check the exit code
        assert result.exit_code == expected_exit_code

        # Check the output if there's an expected output
        if expected_output:
            assert expected_output in result.output

    @pytest.mark.parametrize("command, args, expected_exit_code, expected_output", [
        # Disable PVST globally
        (config.config.commands["spanning-tree"].commands["disable"], ["pvst"], 0, None),
        # Add VLAN 100 and assign a member port
        (config.config.commands["vlan"].commands["add"], ["100"], 0, None),
        (config.config.commands["vlan"].commands["member"].commands["add"], ["100", "Ethernet4"], 0, None),
        # Enable PVST globally
        (config.config.commands["spanning-tree"].commands["enable"], ["pvst"], 0, None),
        # Add VLAN 200
        (config.config.commands["vlan"].commands["add"], ["200"], 0, None),
        # Disable and then enable spanning-tree on VLAN 200
        (config.config.commands["spanning-tree"].commands["vlan"].commands["disable"], ["200"], 0, None),
        (config.config.commands["spanning-tree"].commands["vlan"].commands["enable"], ["200"], 0, None),
        # Attempt to delete VLAN 200 while STP is enabled
        (config.config.commands["vlan"].commands["del"], ["200"], 1, None),
        # Enable STP on non-existing VLAN 101
        (config.config.commands["spanning-tree"].commands["vlan"].commands["enable"], ["101"], 1, "doesn't exist"),
        # Disable STP on non-existing VLAN 101
        (config.config.commands["spanning-tree"].commands["vlan"].commands["disable"], ["101"], 1, "doesn't exist"),
    ])
    def test_add_vlan_enable_pvst(self, runner, db, command, args, expected_exit_code, expected_output):
        # runner = CliRunner()
        # db = Db()

        # Execute the command
        result = runner.invoke(command, args, obj=db)

        # Print for debugging
        print(result.exit_code)
        print(result.output)

        # Check the exit code
        assert result.exit_code == expected_exit_code

        # Check the output if an expected output is defined
        if expected_output:
            assert expected_output in result.output

    @pytest.mark.parametrize("command, args, expected_exit_code, expected_output", [
        # Valid cases
        (config.config.commands["spanning-tree"].commands["hello"], ["3"], 0, None),
        (config.config.commands["spanning-tree"].commands["forward_delay"], ["16"], 0, None),
        (config.config.commands["spanning-tree"].commands["max_age"], ["22"], 0, None),
        (config.config.commands["spanning-tree"].commands["priority"], ["8192"], 0, None),
        (config.config.commands["spanning-tree"].commands["root_guard_timeout"], ["100"], 0, None),
        # Invalid hello timer values
        (config.config.commands["spanning-tree"].commands["hello"], ["0"], 1,
            "STP hello timer must be in range 1-10"),
        (config.config.commands["spanning-tree"].commands["hello"], ["20"], 1,
            "STP hello timer must be in range 1-10"),
        # Invalid forward delay values
        (config.config.commands["spanning-tree"].commands["forward_delay"], ["2"], 1,
            "STP forward delay value must be in range 4-30"),
        (config.config.commands["spanning-tree"].commands["forward_delay"], ["50"], 1,
            "STP forward delay value must be in range 4-30"),
        # Invalid max age values
        (config.config.commands["spanning-tree"].commands["max_age"], ["5"], 1,
            "STP max age value must be in range 6-40"),
        (config.config.commands["spanning-tree"].commands["max_age"], ["45"], 1,
            "STP max age value must be in range 6-40"),
        # Consistency check for forward delay and max age
        (config.config.commands["spanning-tree"].commands["forward_delay"], ["4"], 1,
            "2*(forward_delay-1) >= max_age >= 2*(hello_time +1 )"),
        # Invalid root guard timeout values
        (config.config.commands["spanning-tree"].commands["root_guard_timeout"], ["4"], 1,
            "STP root guard timeout must be in range 5-600"),
        (config.config.commands["spanning-tree"].commands["root_guard_timeout"], ["700"], 1,
            "STP root guard timeout must be in range 5-600"),
        # Invalid priority values
        (config.config.commands["spanning-tree"].commands["priority"], ["70000"], 1,
            "STP bridge priority must be in range 0-61440"),
        (config.config.commands["spanning-tree"].commands["priority"], ["8000"], 1,
            "STP bridge priority must be multiple of 4096"),
    ])
    def test_stp_validate_global_timer_and_priority_params(
        self, runner, db, command, args, expected_exit_code, expected_output):
        # runner = CliRunner()
        # db = Db()

        # Execute the command
        result = runner.invoke(command, args, obj=db)

        # Print for debugging
        print(result.exit_code)
        print(result.output)

        # Check the exit code
        assert result.exit_code == expected_exit_code

        # Check the output if an expected output is defined
        if expected_output:
            assert expected_output in result.output

    @classmethod
    def teardown_class(cls):
        os.environ['UTILITIES_UNIT_TESTING'] = "0"
        print("TEARDOWN")
