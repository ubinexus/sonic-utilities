import os
import traceback

from click.testing import CliRunner

import config.main as config
import show.main as show
from utilities_common.db import Db


MCLAG_DOMAIN_ID = "123"
MCLAG_DOMAIN_ID2 = "500"
MCLAG_SRC_IP    = "12.1.1.1"
RESERVED_IP    = "127.1.1.1"
INVALID_IP    = "255.255.255.255"
MCLAG_PEER_IP   = "12.1.1.2"
MCLAG_KEEPALIVE_TIMER  = "5"
MCLAG_SESSION_TIMEOUT  = "10"
MCLAG_MEMBER_PO  = "PortChannel10"
MCLAG_UNIQUE_IP_VLAN  = "Vlan100"

MCLAG_PEER_LINK = "PortChannel12"
MCLAG_INVALID_SRC_IP1  = "12::1111"
MCLAG_INVALID_SRC_IP2  = "224.1.1.1"
MCLAG_INVALID_PEER_IP1  = "12::1112"
MCLAG_INVALID_PEER_IP2  = "224.1.1.2"
MCLAG_INVALID_PEER_LINK1  = "Eth1/3"
MCLAG_INVALID_PEER_LINK2  = "Ethernet257"
MCLAG_INVALID_PEER_LINK3  = "PortChannel123456"
MCLAG_INVALID_PEER_LINK4  = "Lag111"
MCLAG_INVALID_PEER_LINK5  = "Ethernet123456789"
MCLAG_INVALID_KEEPALIVE_TIMER  = "11"
MCLAG_INVALID_SESSION_TIMEOUT = "31"
MCLAG_INVALID_KEEPALIVE_TIMER_LBOUND  = "0"
MCLAG_INVALID_KEEPALIVE_TIMER_UBOUND  = "61"
MCLAG_INVALID_SESSION_TMOUT_LBOUND  = "2"
MCLAG_INVALID_SESSION_TMOUT_UBOUND  = "4000"

MCLAG_INVALID_MCLAG_MEMBER  = "Ethernet4"
MCLAG_INVALID_PORTCHANNEL1  = "portchannel" 
MCLAG_INVALID_PORTCHANNEL2  = "PortChannelabcd" 
MCLAG_INVALID_PORTCHANNEL3  = "PortChannel10000" 
MCLAG_INVALID_PORTCHANNEL4  = "PortChannel1111" 


MCLAG_UNIQUE_IP_INTF_INVALID1  = "Ethernet100"
MCLAG_UNIQUE_IP_INTF_INVALID2  = "Ethernet100"

class TestMclag(object):
    @classmethod
    def setup_class(cls):
        os.environ['UTILITIES_UNIT_TESTING'] = "1"
        print("SETUP")

    def test_add_mclag_with_invalid_src_ip(self):
        runner = CliRunner()
        db = Db()
        obj = {'db':db.cfgdb}

        # add mclag with invalid src
        result = runner.invoke(config.config.commands["mclag"].commands["add"], [MCLAG_DOMAIN_ID, MCLAG_INVALID_SRC_IP1, MCLAG_PEER_IP, MCLAG_PEER_LINK], obj=obj)
        print(result.exit_code)
        print(result.output)
        assert result.exit_code != 0, "Error: invalid local ip address"

    def test_add_mclag_with_invalid_src_mcast_ip(self):
        runner = CliRunner()
        db = Db()
        obj = {'db':db.cfgdb}

        # add mclag with invalid src
        result = runner.invoke(config.config.commands["mclag"].commands["add"], [MCLAG_DOMAIN_ID, MCLAG_INVALID_SRC_IP2, MCLAG_PEER_IP, MCLAG_PEER_LINK], obj=obj)
        print(result.exit_code)
        print(result.output)
        assert result.exit_code != 0, "Error: invalid local ip address"

        result = runner.invoke(config.config.commands["mclag"].commands["add"], [MCLAG_DOMAIN_ID, RESERVED_IP, MCLAG_PEER_IP, MCLAG_PEER_LINK], obj=obj)
        assert result.exit_code != 0, "mclag invalid src ip test caase with code {}:{} Output:{}".format(type(result.exit_code), result.exit_code, result.output)
        result = runner.invoke(config.config.commands["mclag"].commands["add"], [MCLAG_DOMAIN_ID, INVALID_IP, MCLAG_PEER_IP, MCLAG_PEER_LINK], obj=obj)
        assert result.exit_code != 0, "mclag invalid src ip test caase with code {}:{} Output:{}".format(type(result.exit_code), result.exit_code, result.output)

    def test_add_mclag_with_invalid_peer_ip(self):
        runner = CliRunner()
        db = Db()
        obj = {'db':db.cfgdb}

        # add mclag with invalid peer ip
        result = runner.invoke(config.config.commands["mclag"].commands["add"], [MCLAG_DOMAIN_ID, MCLAG_SRC_IP, MCLAG_INVALID_PEER_IP1, MCLAG_PEER_LINK], obj=obj)
        print(result.exit_code)
        print(result.output)
        assert result.exit_code != 0, "Error: invalid local ip address"

        result = runner.invoke(config.config.commands["mclag"].commands["add"], [MCLAG_DOMAIN_ID, MCLAG_SRC_IP, RESERVED_IP, MCLAG_PEER_LINK], obj=obj)
        assert result.exit_code != 0, "mclag invalid src ip test caase with code {}:{} Output:{}".format(type(result.exit_code), result.exit_code, result.output)
        result = runner.invoke(config.config.commands["mclag"].commands["add"], [MCLAG_DOMAIN_ID, MCLAG_SRC_IP, INVALID, MCLAG_PEER_LINK], obj=obj)
        assert result.exit_code != 0, "mclag invalid src ip test caase with code {}:{} Output:{}".format(type(result.exit_code), result.exit_code, result.output)


    def test_add_mclag_with_invalid_peer_mcast_ip(self):
        runner = CliRunner()
        db = Db()
        obj = {'db':db.cfgdb}

        # add mclag with invalid peer ip mcast
        result = runner.invoke(config.config.commands["mclag"].commands["add"], [MCLAG_DOMAIN_ID, MCLAG_SRC_IP, MCLAG_INVALID_PEER_IP2, MCLAG_PEER_LINK], obj=obj)
        print(result.exit_code)
        print(result.output)
        assert result.exit_code != 0, "Error: invalid local ip address"

    def test_add_mclag_with_invalid_peer_link(self):
        runner = CliRunner()
        db = Db()
        obj = {'db':db.cfgdb}

        # add mclag with invalid peer link
        result = runner.invoke(config.config.commands["mclag"].commands["add"], [MCLAG_DOMAIN_ID, MCLAG_SRC_IP, MCLAG_PEER_IP, MCLAG_INVALID_PEER_LINK1], obj=obj)
        print(result.exit_code)
        print(result.output)
        assert result.exit_code != 0, "Error: invalid peer link"

        result = runner.invoke(config.config.commands["mclag"].commands["add"], [MCLAG_DOMAIN_ID, MCLAG_SRC_IP, MCLAG_PEER_IP, MCLAG_INVALID_PEER_LINK2], obj=obj)
        print(result.exit_code)
        print(result.output)
        assert result.exit_code != 0, "Error: invalid peer link"

        result = runner.invoke(config.config.commands["mclag"].commands["add"], [MCLAG_DOMAIN_ID, MCLAG_SRC_IP, MCLAG_PEER_IP, MCLAG_INVALID_PEER_LINK3], obj=obj)
        print(result.exit_code)
        print(result.output)
        assert result.exit_code != 0, "Error: invalid peer link"

        result = runner.invoke(config.config.commands["mclag"].commands["add"], [MCLAG_DOMAIN_ID, MCLAG_SRC_IP, MCLAG_PEER_IP, MCLAG_INVALID_PEER_LINK4], obj=obj)
        assert result.exit_code != 0, "mclag invalid peer link test case failed with code {}:{} Output:{}".format(type(result.exit_code), result.exit_code, result.output)

        result = runner.invoke(config.config.commands["mclag"].commands["add"], [MCLAG_DOMAIN_ID, MCLAG_SRC_IP, MCLAG_PEER_IP, MCLAG_INVALID_PEER_LINK5], obj=obj)
        assert result.exit_code != 0, "mclag invalid peer link test case failed with code {}:{} Output:{}".format(type(result.exit_code), result.exit_code, result.output)

    def test_add_invalid_mclag_domain(self):
        runner = CliRunner()
        db = Db()
        obj = {'db':db.cfgdb}

        # add invalid mclag domain
        result = runner.invoke(config.config.commands["mclag"].commands["add"], [0, MCLAG_SRC_IP, MCLAG_PEER_IP, MCLAG_PEER_LINK], obj=obj)
        assert result.exit_code != 0, "mclag invalid domain test case with code {}:{} Output:{}".format(type(result.exit_code), result.exit_code, result.output)
        # add invalid mclag domain
        result = runner.invoke(config.config.commands["mclag"].commands["add"], [5000, MCLAG_SRC_IP, MCLAG_PEER_IP, MCLAG_PEER_LINK], obj=obj)
        assert result.exit_code != 0, "mclag invalid domain test case with code {}:{} Output:{}".format(type(result.exit_code), result.exit_code, result.output)



    def test_add_mclag_domain(self):
        runner = CliRunner()
        db = Db()
        obj = {'db':db.cfgdb}

        # add valid mclag domain
        result = runner.invoke(config.config.commands["mclag"].commands["add"], [MCLAG_DOMAIN_ID, MCLAG_SRC_IP, MCLAG_PEER_IP, MCLAG_PEER_LINK], obj=obj)
        assert result.exit_code == 0, "mclag creation failed with code {}:{} Output:{}".format(type(result.exit_code), result.exit_code, result.output)

        # add valid mclag domain again
        result = runner.invoke(config.config.commands["mclag"].commands["add"], [MCLAG_DOMAIN_ID2, MCLAG_SRC_IP, MCLAG_PEER_IP, MCLAG_PEER_LINK], obj=obj)
        assert result.exit_code != 0, "test_mclag_domain_add_again with code {}:{} Output:{}".format(type(result.exit_code), result.exit_code, result.output)

    def test_add_invalid_mclag_domain(self):
        runner = CliRunner()
        db = Db()
        obj = {'db':db.cfgdb}

        # add invalid mclag domain
        result = runner.invoke(config.config.commands["mclag"].commands["add"], [0, MCLAG_SRC_IP, MCLAG_PEER_IP, MCLAG_PEER_LINK], obj=obj)
        assert result.exit_code != 0, "mclag invalid domain test case with code {}:{} Output:{}".format(type(result.exit_code), result.exit_code, result.output)
        # add invalid mclag domain
        result = runner.invoke(config.config.commands["mclag"].commands["add"], [5000, MCLAG_SRC_IP, MCLAG_PEER_IP, MCLAG_PEER_LINK], obj=obj)
        assert result.exit_code != 0, "mclag invalid domain test case with code {}:{} Output:{}".format(type(result.exit_code), result.exit_code, result.output)



    def test_add_mclag_domain(self):
        runner = CliRunner()
        db = Db()
        obj = {'db':db.cfgdb}

        # add valid mclag domain
        result = runner.invoke(config.config.commands["mclag"].commands["add"], [MCLAG_DOMAIN_ID, MCLAG_SRC_IP, MCLAG_PEER_IP, MCLAG_PEER_LINK], obj=obj)
        assert result.exit_code == 0, "mclag creation failed with code {}:{} Output:{}".format(type(result.exit_code), result.exit_code, result.output)

        # add valid mclag domain again
        result = runner.invoke(config.config.commands["mclag"].commands["add"], [MCLAG_DOMAIN_ID2, MCLAG_SRC_IP, MCLAG_PEER_IP, MCLAG_PEER_LINK], obj=obj)
        assert result.exit_code != 0, "test_mclag_domain_add_again with code {}:{} Output:{}".format(type(result.exit_code), result.exit_code, result.output)

    def test_add_mclag_domain(self):
        runner = CliRunner()
        db = Db()
        obj = {'db':db.cfgdb}

        # add valid mclag domain
        result = runner.invoke(config.config.commands["mclag"].commands["add"], [MCLAG_DOMAIN_ID, MCLAG_SRC_IP, MCLAG_PEER_IP, MCLAG_PEER_LINK], obj=obj)
        assert result.exit_code == 0, "mclag creation failed with code {}:{} Output:{}".format(type(result.exit_code), result.exit_code, result.output)

        # add valid mclag domain again
        result = runner.invoke(config.config.commands["mclag"].commands["add"], [MCLAG_DOMAIN_ID2, MCLAG_SRC_IP, MCLAG_PEER_IP, MCLAG_PEER_LINK], obj=obj)
        assert result.exit_code != 0, "test_mclag_domain_add_again with code {}:{} Output:{}".format(type(result.exit_code), result.exit_code, result.output)

    def test_mclag_invalid_keepalive_timer(self):
        runner = CliRunner()
        db = Db()
        obj = {'db':db.cfgdb}


        # add valid mclag domain
        result = runner.invoke(config.config.commands["mclag"].commands["add"], [MCLAG_DOMAIN_ID, MCLAG_SRC_IP, MCLAG_PEER_IP, MCLAG_PEER_LINK], obj=obj)
        assert result.exit_code == 0, "mclag creation failed with code {}:{} Output:{}".format(type(result.exit_code), result.exit_code, result.output)

        # configure non multiple keepalive timer
        result = runner.invoke(config.config.commands["mclag"].commands["keepalive-interval"], [MCLAG_DOMAIN_ID, MCLAG_INVALID_KEEPALIVE_TIMER], obj=obj)
        assert result.exit_code != 0, "failed testing of invalid keepalive timer with code {}:{} Output:{}".format(type(result.exit_code), result.exit_code, result.output)

        # add invalid keepalive values
        result = runner.invoke(config.config.commands["mclag"].commands["keepalive-interval"], [MCLAG_DOMAIN_ID, MCLAG_INVALID_KEEPALIVE_TIMER_LBOUND], obj=obj)
        assert result.exit_code != 0, "mclag invalid keepalive failed with code {}:{} Output:{}".format(type(result.exit_code), result.exit_code, result.output)

        # add invalid keepalive values
        result = runner.invoke(config.config.commands["mclag"].commands["keepalive-interval"], [MCLAG_DOMAIN_ID, MCLAG_INVALID_KEEPALIVE_TIMER_UBOUND], obj=obj)
        assert result.exit_code != 0, "mclag creation keepalive failed with code {}:{} Output:{}".format(type(result.exit_code), result.exit_code, result.output)

    def test_mclag_keepalive_timer(self):
        runner = CliRunner()
        db = Db()
        obj = {'db':db.cfgdb}


        # add valid mclag domain
        result = runner.invoke(config.config.commands["mclag"].commands["add"], [MCLAG_DOMAIN_ID, MCLAG_SRC_IP, MCLAG_PEER_IP, MCLAG_PEER_LINK], obj=obj)
        print(result.exit_code)
        print(result.output)
        assert result.exit_code == 0, "mclag creation failed with code {}:{} Output:{}".format(type(result.exit_code), result.exit_code, result.output)

        # configure valid keepalive timer
        result = runner.invoke(config.config.commands["mclag"].commands["keepalive-interval"], [MCLAG_DOMAIN_ID, MCLAG_KEEPALIVE_TIMER], obj=obj)
        print(result.exit_code)
        print(result.output)
        assert result.exit_code == 0, "failed test for setting valid keepalive timer with code {}:{} Output:{}".format(type(result.exit_code), result.exit_code, result.output)

    def test_mclag_invalid_session_timeout(self):
        runner = CliRunner()
        db = Db()
        obj = {'db':db.cfgdb}


        # add valid mclag domain
        result = runner.invoke(config.config.commands["mclag"].commands["add"], [MCLAG_DOMAIN_ID, MCLAG_SRC_IP, MCLAG_PEER_IP, MCLAG_PEER_LINK], obj=obj)
        print(result.exit_code)
        print(result.output)
        assert result.exit_code == 0, "mclag creation failed with code {}:{} Output:{}".format(type(result.exit_code), result.exit_code, result.output)

        # configure valid keepalive timer
        result = runner.invoke(config.config.commands["mclag"].commands["keepalive-interval"], [MCLAG_DOMAIN_ID, MCLAG_KEEPALIVE_TIMER], obj=obj)
        print(result.exit_code)
        print(result.output)
        assert result.exit_code == 0, "failed test for setting valid keepalive timer with code {}:{} Output:{}".format(type(result.exit_code), result.exit_code, result.output)

        # configure non multiple session timeout
        result = runner.invoke(config.config.commands["mclag"].commands["session-timeout"], [MCLAG_DOMAIN_ID, MCLAG_INVALID_SESSION_TIMEOUT], obj=obj)
        print(result.exit_code)
        print(result.output)
        assert result.exit_code != 0, "failed invalid session timeout setting case"

        result = runner.invoke(config.config.commands["mclag"].commands["session-timeout"], [MCLAG_DOMAIN_ID, MCLAG_INVALID_SESSION_TMOUT_LBOUND], obj=obj)
        assert result.exit_code != 0, "mclag session timeout invalid failed with code {}:{} Output:{}".format(type(result.exit_code), result.exit_code, result.output)
        result = runner.invoke(config.config.commands["mclag"].commands["session-timeout"], [MCLAG_DOMAIN_ID, MCLAG_INVALID_SESSION_TMOUT_UBOUND], obj=obj)
        assert result.exit_code != 0, "mclag session timeout invalid failed with code {}:{} Output:{}".format(type(result.exit_code), result.exit_code, result.output)
    
    def test_mclag_session_timeout(self):
        runner = CliRunner()
        db = Db()
        obj = {'db':db.cfgdb}

        # add valid mclag domain
        result = runner.invoke(config.config.commands["mclag"].commands["add"], [MCLAG_DOMAIN_ID, MCLAG_SRC_IP, MCLAG_PEER_IP, MCLAG_PEER_LINK], obj=obj)
        print(result.exit_code)
        print(result.output)
        assert result.exit_code == 0, "mclag creation failed with code {}:{} Output:{}".format(type(result.exit_code), result.exit_code, result.output)

        # configure valid session timeout
        result = runner.invoke(config.config.commands["mclag"].commands["session-timeout"], [MCLAG_DOMAIN_ID, MCLAG_SESSION_TIMEOUT], obj=obj)
        print(result.exit_code)
        print(result.output)
        assert result.exit_code == 0, "failed test for setting valid session timeout with code {}:{} Output:{}".format(type(result.exit_code), result.exit_code, result.output)


    def test_mclag_add_mclag_member_to_nonexisting_domain(self):
        runner = CliRunner()
        db = Db()
        obj = {'db':db.cfgdb}

        # add mclag member to non existing domain
        result = runner.invoke(config.config.commands["mclag"].commands["member"].commands["add"], [MCLAG_DOMAIN_ID2, MCLAG_MEMBER_PO], obj=obj)
        print(result.exit_code)
        print(result.output)
        assert result.exit_code != 0, "testing of adding mclag member to nonexisting domain failed" 


    def test_mclag_add_invalid_member(self):
        runner = CliRunner()
        db = Db()
        obj = {'db':db.cfgdb}

        # add valid mclag domain
        result = runner.invoke(config.config.commands["mclag"].commands["add"], [MCLAG_DOMAIN_ID, MCLAG_SRC_IP, MCLAG_PEER_IP, MCLAG_PEER_LINK], obj=obj)
        print(result.exit_code)
        print(result.output)
        assert result.exit_code == 0, "mclag creation failed with code {}:{} Output:{}".format(type(result.exit_code), result.exit_code, result.output)

        # add invaid mclag member Ethernet instead of PortChannel
        result = runner.invoke(config.config.commands["mclag"].commands["member"].commands["add"], [MCLAG_DOMAIN_ID, MCLAG_INVALID_MCLAG_MEMBER], obj=obj)
        print(result.exit_code)
        print(result.output)
        assert result.exit_code != 0, "testing of adding invalid member failed" 

        # add invaid mclag member Ethernet instead of PortChannel
        result = runner.invoke(config.config.commands["mclag"].commands["member"].commands["add"], [MCLAG_DOMAIN_ID, MCLAG_INVALID_PORTCHANNEL1], obj=obj)
        assert result.exit_code != 0, "mclag invalid member add case failed with code {}:{} Output:{}".format(type(result.exit_code), result.exit_code, result.output)

        # add invaid mclag member Ethernet instead of PortChannel
        result = runner.invoke(config.config.commands["mclag"].commands["member"].commands["add"], [MCLAG_DOMAIN_ID, MCLAG_INVALID_PORTCHANNEL2], obj=obj)
        assert result.exit_code != 0, "mclag invalid member add case failed with code {}:{} Output:{}".format(type(result.exit_code), result.exit_code, result.output)

        # add invaid mclag member Ethernet instead of PortChannel
        result = runner.invoke(config.config.commands["mclag"].commands["member"].commands["add"], [MCLAG_DOMAIN_ID, MCLAG_INVALID_PORTCHANNEL3], obj=obj)
        assert result.exit_code != 0, "mclag invalid member add case failed with code {}:{} Output:{}".format(type(result.exit_code), result.exit_code, result.output)

        # add invaid mclag member Ethernet instead of PortChannel
        result = runner.invoke(config.config.commands["mclag"].commands["member"].commands["add"], [MCLAG_DOMAIN_ID, MCLAG_INVALID_PORTCHANNEL4], obj=obj)
        assert result.exit_code != 0, "mclag invalid member add case failed with code {}:{} Output:{}".format(type(result.exit_code), result.exit_code, result.output)

    def test_mclag_add_member(self):
        runner = CliRunner()
        db = Db()
        obj = {'db':db.cfgdb}


        # add valid mclag domain
        result = runner.invoke(config.config.commands["mclag"].commands["add"], [MCLAG_DOMAIN_ID, MCLAG_SRC_IP, MCLAG_PEER_IP, MCLAG_PEER_LINK], obj=obj)
        assert result.exit_code == 0, "mclag creation failed with code {}:{} Output:{}".format(type(result.exit_code), result.exit_code, result.output)

        # add valid mclag member
        result = runner.invoke(config.config.commands["mclag"].commands["member"].commands["add"], [MCLAG_DOMAIN_ID, MCLAG_MEMBER_PO], obj=obj)
        assert result.exit_code == 0, "failed adding valid mclag member with code {}:{} Output:{}".format(type(result.exit_code), result.exit_code, result.output)

        # add mclag member again
        result = runner.invoke(config.config.commands["mclag"].commands["member"].commands["add"], [MCLAG_DOMAIN_ID, MCLAG_MEMBER_PO], obj=obj)
        print(result.exit_code)
        print(result.output)
        assert result.exit_code == 0, "testing of adding mclag member again failed" 

        # delete mclag domain
        result = runner.invoke(config.config.commands["mclag"].commands["del"], [MCLAG_DOMAIN_ID], obj=obj)
        print(result.exit_code)
        print(result.output)
        assert result.exit_code == 0, "testing of delete of mclag domain failed" 

        # add valid mclag domain
        result = runner.invoke(config.config.commands["mclag"].commands["add"], [MCLAG_DOMAIN_ID, MCLAG_SRC_IP, MCLAG_PEER_IP, MCLAG_PEER_LINK], obj=obj)
        assert result.exit_code == 0, "mclag creation failed with code {}:{} Output:{}".format(type(result.exit_code), result.exit_code, result.output)

        # add valid mclag member
        result = runner.invoke(config.config.commands["mclag"].commands["member"].commands["add"], [MCLAG_DOMAIN_ID, MCLAG_MEMBER_PO], obj=obj)
        assert result.exit_code == 0, "mclag member add with code {}:{} Output:{}".format(type(result.exit_code), result.exit_code, result.output)

        # del valid mclag member
        result = runner.invoke(config.config.commands["mclag"].commands["member"].commands["del"], [MCLAG_DOMAIN_ID, MCLAG_MEMBER_PO], obj=obj)
        assert result.exit_code == 0, "mclag member deletion failed with code {}:{} Output:{}".format(type(result.exit_code), result.exit_code, result.output)

        # del mclag member
        result = runner.invoke(config.config.commands["mclag"].commands["member"].commands["del"], [MCLAG_DOMAIN_ID, MCLAG_INVALID_MCLAG_MEMBER], obj=obj)
        print(result.exit_code)
        print(result.output)
        assert result.exit_code != 0, "testing of deleting valid mclag member failed" 

        result = runner.invoke(config.config.commands["mclag"].commands["member"].commands["del"], [MCLAG_DOMAIN_ID, MCLAG_INVALID_PORTCHANNEL1], obj=obj)
        assert result.exit_code != 0, "mclag invalid member del case failed with code {}:{} Output:{}".format(type(result.exit_code), result.exit_code, result.output)

        result = runner.invoke(config.config.commands["mclag"].commands["member"].commands["del"], [MCLAG_DOMAIN_ID, MCLAG_INVALID_PORTCHANNEL2], obj=obj)
        assert result.exit_code != 0, "mclag invalid member del case failed with code {}:{} Output:{}".format(type(result.exit_code), result.exit_code, result.output)

        result = runner.invoke(config.config.commands["mclag"].commands["member"].commands["del"], [MCLAG_DOMAIN_ID, MCLAG_INVALID_PORTCHANNEL3], obj=obj)

        result = runner.invoke(config.config.commands["mclag"].commands["member"].commands["del"], [MCLAG_DOMAIN_ID, MCLAG_INVALID_PORTCHANNEL4], obj=obj)
        assert result.exit_code != 0, "mclag invalid member del case failed with code {}:{} Output:{}".format(type(result.exit_code), result.exit_code, result.output)
        assert result.exit_code != 0, "mclag invalid member del case failed with code {}:{} Output:{}".format(type(result.exit_code), result.exit_code, result.output)



    def test_mclag_add_unique_ip(self):
        runner = CliRunner()
        db = Db()
        obj = {'db':db.cfgdb}

        # add valid mclag domain
        result = runner.invoke(config.config.commands["mclag"].commands["add"], [MCLAG_DOMAIN_ID, MCLAG_SRC_IP, MCLAG_PEER_IP, MCLAG_PEER_LINK], obj=obj)
        assert result.exit_code == 0, "mclag creation failed with code {}:{} Output:{}".format(type(result.exit_code), result.exit_code, result.output)

        # add mclag unique ip
        result = runner.invoke(config.config.commands["mclag"].commands["unique-ip"].commands["add"], [MCLAG_UNIQUE_IP_VLAN], obj=obj)
        print(result.exit_code)
        print(result.output)
        assert result.exit_code == 0, "testing of adding unique ip failed" 

        # add mclag unique ip for vlan interface which already has ip
        result = runner.invoke(config.config.commands["vlan"].commands["add"], ["111"], obj=db)
        assert result.exit_code == 0, "add vlan for unique ip failed {}:{} Output:{}".format(type(result.exit_code), result.exit_code, result.output)

        result = runner.invoke(config.config.commands["interface"].commands["ip"].commands["add"], ["Vlan111", "111.11.11.1/24"], obj=obj)        
        assert result.exit_code == 0, "ip config for unique ip vlan failed {}:{} Output:{}".format(type(result.exit_code), result.exit_code, result.output)

        result = runner.invoke(config.config.commands["mclag"].commands["unique-ip"].commands["add"], ["Vlan111"], obj=obj)
        assert result.exit_code != 0, "unique ip config for vlan with ip address case failed {}:{} Output:{}".format(type(result.exit_code), result.exit_code, result.output)

        # delete mclag unique ip
        result = runner.invoke(config.config.commands["mclag"].commands["unique-ip"].commands["del"], [MCLAG_UNIQUE_IP_VLAN], obj=obj)
        print(result.exit_code)
        print(result.output)
        assert result.exit_code == 0, "testing of delete of unique ip failed" 

    def test_mclag_not_present_domain(self):
        runner = CliRunner()
        db = Db()
        obj = {'db':db.cfgdb}

        # delete mclag domain
        result = runner.invoke(config.config.commands["mclag"].commands["del"], [MCLAG_DOMAIN_ID], obj=obj)
        assert result.exit_code == 0, "testing  non-existing domain deletion{}:{} Output:{}".format(type(result.exit_code), result.exit_code, result.output)

        # delete invalid mclag domain
        result = runner.invoke(config.config.commands["mclag"].commands["del"], [0], obj=obj)
        assert result.exit_code != 0, "mclag invalid domain delete test case with code {}:{} Output:{}".format(type(result.exit_code), result.exit_code, result.output)
        # delete invalid mclag domain
        result = runner.invoke(config.config.commands["mclag"].commands["del"], [5000], obj=obj)
        assert result.exit_code != 0, "mclag invalid domain delete test case with code {}:{} Output:{}".format(type(result.exit_code), result.exit_code, result.output)



    def test_add_unique_ip_for_nonexisting_domain(self):
        runner = CliRunner()
        db = Db()
        obj = {'db':db.cfgdb}

        # add unique_ip witout mclag domain
        result = runner.invoke(config.config.commands["mclag"].commands["unique-ip"].commands["add"], [MCLAG_UNIQUE_IP_VLAN], obj=obj)
        print(result.exit_code)
        print(result.output)
        assert result.exit_code != 0, "testing of adding uniqueip nonexisting mclag domain ailed"

        result =
        runner.invoke(config.config.commands["mclag"].commands["unique-ip"].commands["add"], [MCLAG_UNIQUE_IP_INTF_INVALID1], obj=obj)
        assert result.exit_code != 0, "mclag invalid unique ip test case with code {}:{} Output:{}".format(type(result.exit_code), result.exit_code, result.output)
        runner.invoke(config.config.commands["mclag"].commands["unique-ip"].commands["add"], [MCLAG_UNIQUE_IP_INTF_INVALID2], obj=obj)
        assert result.exit_code != 0, "mclag invalid unique ip test case with code {}:{} Output:{}".format(type(result.exit_code), result.exit_code, result.output)

    @classmethod
    def teardown_class(cls):
        os.environ['UTILITIES_UNIT_TESTING'] = "0"
        print("TEARDOWN")
