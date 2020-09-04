import sys
import os
from click.testing import CliRunner
import mock_tables.dbconnector

test_path = os.path.dirname(os.path.abspath(__file__))
modules_path = os.path.dirname(test_path)
scripts_path = os.path.join(modules_path, "scripts")
sys.path.insert(0, modules_path)

import show.main as show

test_sfp_eeprom_with_dom_output = """\
Ethernet0: SFP EEPROM detected
        Application Advertisement: N/A
        Connector: No separable connector
        Encoding: 64B66B
        Extended Identifier: Power Class 3(2.5W max), CDR present in Rx Tx
        Extended RateSelect Compliance: QSFP+ Rate Select Version 1
        Identifier: QSFP28 or later
        Length Cable Assembly(m): 3
        Nominal Bit Rate(100Mbs): 255
        Specification compliance:
                10/40G Ethernet Compliance Code: 40G Active Cable (XLPPI)
        Vendor Date Code(YYYY-MM-DD Lot): 2017-01-13
        Vendor Name: Mellanox
        Vendor OUI: 00-02-c9
        Vendor PN: MFA1A00-C003
        Vendor Rev: AC
        Vendor SN: MT1706FT02064
        ChannelMonitorValues:
                RX1Power: 0.3802dBm
                RX2Power: -0.4871dBm
                RX3Power: -0.0860dBm
                RX4Power: 0.3830dBm
                TX1Bias: 6.7500mA
                TX2Bias: 6.7500mA
                TX3Bias: 6.7500mA
                TX4Bias: 6.7500mA
        ChannelThresholdValues:
                RxPowerHighAlarm  : 3.4001dBm
                RxPowerHighWarning: 2.4000dBm
                RxPowerLowAlarm   : -13.5067dBm
                RxPowerLowWarning : -9.5001dBm
                TxBiasHighAlarm   : 10.0000mA
                TxBiasHighWarning : 9.5000mA
                TxBiasLowAlarm    : 0.5000mA
                TxBiasLowWarning  : 1.0000mA
        ModuleMonitorValues:
                Temperature: 30.9258C
                Vcc: 3.2824Volts
        ModuleThresholdValues:
                TempHighAlarm  : 75.0000C
                TempHighWarning: 70.0000C
                TempLowAlarm   : -5.0000C
                TempLowWarning : 0.0000C
                VccHighAlarm   : 3.6300Volts
                VccHighWarning : 3.4650Volts
                VccLowAlarm    : 2.9700Volts
                VccLowWarning  : 3.1349Volts
"""

test_sfp_eeprom_output = """\
Ethernet0: SFP EEPROM detected
        Application Advertisement: N/A
        Connector: No separable connector
        Encoding: 64B66B
        Extended Identifier: Power Class 3(2.5W max), CDR present in Rx Tx
        Extended RateSelect Compliance: QSFP+ Rate Select Version 1
        Identifier: QSFP28 or later
        Length Cable Assembly(m): 3
        Nominal Bit Rate(100Mbs): 255
        Specification compliance:
                10/40G Ethernet Compliance Code: 40G Active Cable (XLPPI)
        Vendor Date Code(YYYY-MM-DD Lot): 2017-01-13
        Vendor Name: Mellanox
        Vendor OUI: 00-02-c9
        Vendor PN: MFA1A00-C003
        Vendor Rev: AC
        Vendor SN: MT1706FT02064
"""

test_sfp_eeprom_table_output = """\
Interface    Identifier       Connector               Vendor Name    Model Name    Serial Number      Nominal Bit Rate(100Mbs)
-----------  ---------------  ----------------------  -------------  ------------  ---------------  --------------------------
Ethernet0    QSFP28 or later  No separable connector  Mellanox       MFA1A00-C003  MT1706FT02064                           255
"""

test_sfp_eeprom_with_dom_table_output = """\
Interface    Lane Number    Temp(C)                            Voltage(V)                       Current(mA)                      Tx Power(dBm)                 Rx Power(dBm)
-----------  -------------  ---------------------------------  -------------------------------  -------------------------------  ----------------------------  ---------------------------------
Ethernet32   Lane 1         32.1055 [low=0.0000,high=75.0000]  3.3769 [low=1.0000,high=9.5000]  6.7500 [low=1.0000,high=9.5000]  0.4961 [low=None,high=None]   0.4961 [low=-9.5001,high=2.4000]
             Lane 2         32.1055 [low=0.0000,high=75.0000]  3.3769 [low=1.0000,high=9.5000]  6.7500 [low=1.0000,high=9.5000]  0.3782 [low=None,high=None]   0.3782 [low=-9.5001,high=2.4000]
             Lane 3         32.1055 [low=0.0000,high=75.0000]  3.3769 [low=1.0000,high=9.5000]  6.7500 [low=1.0000,high=9.5000]  0.5918 [low=None,high=None]   -0.0860 [low=-9.5001,high=2.4000]
             Lane 4         32.1055 [low=0.0000,high=75.0000]  3.3769 [low=1.0000,high=9.5000]  6.7500 [low=1.0000,high=9.5000]  -0.1909 [low=None,high=None]  0.5918 [low=-9.5001,high=2.4000]
"""

class TestSFP(object):
    @classmethod
    def setup_class(cls):
        print("SETUP")
        os.environ["PATH"] += os.pathsep + scripts_path
        os.environ["UTILITIES_UNIT_TESTING"] = "2"

    def test_sfp_presence(self):
        runner = CliRunner()
        result = runner.invoke(show.cli.commands["interfaces"].commands["transceiver"].commands["presence"], ["Ethernet0"])
        expected = """Port       Presence
---------  ----------
Ethernet0  Present
"""
        assert result.exit_code == 0
        assert result.output == expected

        result = runner.invoke(show.cli.commands["interfaces"].commands["transceiver"].commands["presence"], ["Ethernet200"])
        expected = """Port         Presence
-----------  -----------
Ethernet200  Not present
"""
        assert result.exit_code == 0
        assert result.output == expected

    def test_sfp_eeprom_with_dom(self):
        runner = CliRunner()
        result = runner.invoke(show.cli.commands["interfaces"].commands["transceiver"].commands["eeprom"], ["Ethernet0 -d"])
        assert result.exit_code == 0
        assert "\n".join([ l.rstrip() for l in result.output.split('\n')]) == test_sfp_eeprom_with_dom_output

    def test_sfp_eeprom_with_dom_table(self):
        runner = CliRunner()
        result = runner.invoke(show.cli.commands["interfaces"].commands["transceiver"].commands["eeprom"], ["Ethernet32 -dt"])
        assert result.exit_code == 0
        assert "\n".join([ l.rstrip() for l in result.output.split('\n')]) == test_sfp_eeprom_with_dom_table_output

    def test_sfp_eeprom(self):
        runner = CliRunner()
        result = runner.invoke(show.cli.commands["interfaces"].commands["transceiver"].commands["eeprom"], ["Ethernet0"])
        assert result.exit_code == 0
        assert "\n".join([ l.rstrip() for l in result.output.split('\n')]) == test_sfp_eeprom_output

        result = runner.invoke(show.cli.commands["interfaces"].commands["transceiver"].commands["eeprom"], ["Ethernet200"])
        result_lines = result.output.strip('\n')
        expected = "Ethernet200: SFP EEPROM Not detected"
        assert result_lines == expected

    def test_sfp_eeprom_table(self):
        runner = CliRunner()
        result = runner.invoke(show.cli.commands["interfaces"].commands["transceiver"].commands["eeprom"], ["Ethernet0 -t"])
        assert result.exit_code == 0
        assert "\n".join([ l.rstrip() for l in result.output.split('\n')]) == test_sfp_eeprom_table_output

    @classmethod
    def teardown_class(cls):
        print("TEARDOWN")
        os.environ["PATH"] = os.pathsep.join(os.environ["PATH"].split(os.pathsep)[:-1])
        os.environ["UTILITIES_UNIT_TESTING"] = "0"
