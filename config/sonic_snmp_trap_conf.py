#!/usr/bin/python

'''
Motivation: Backend API implementation for manipulation of the SNMP configuration file.

Functionalities:
               Add trap recipient host(s) config entries
               modifiy/delete a trap recipient host entry
'''

import os
import sys
import click
import json
import subprocess
import fileinput
import netaddr
import syslog
import logging
import logging.handlers
from swsssdk import ConfigDBConnector

SNMP_SERVER_LOCAL_IP="127.100.100.1"


def snmptrap_modify_cfg(ver, hostaddr, port, use_mgmt_vrf):
    """
    Function to set snmp-server configuration for the destination to
    send the notifications to.
    """
    syslog.syslog(syslog.LOG_DEBUG, "SNMP " + \
     "mod_cfg() : received : " + \
     " snmp version - %s"%(ver) + \
     " host address - port %s %s"%(hostaddr, port))
    try :
        # use_mgmt_vrf is valid only when vrf is enabled . 
        # If VRF enabled, delete old NAT rule based on old serverip/port and add new NAT rule
        if use_mgmt_vrf:
            #vrf is enabled. Get the local_port based on version number. For v1 serverIP, local port 62101 is used
            # for v2 serverIP, local port 62102 is used. For v3, 62103 is used.
            local_port = "6210{0}".format(ver)
            # Get the previously configured serverip and delete the corresponding iptables rule before adding the new rule.
            TrapVar = "v{0}TrapDest".format(ver)
            config_db = ConfigDBConnector()
            config_db.connect()
            snmp_config=config_db.get_entry('SNMP_TRAP_CONFIG',TrapVar)
            if snmp_config:
                old_server_ip = snmp_config['DestIp']
                old_server_port = snmp_config['DestPort']
                cmd = "ip netns exec mgmt iptables -t nat -D PREROUTING -i if1 -p udp -d {0} --dport {1} -j DNAT --to-destination {2}:{3}".format(SNMP_SERVER_LOCAL_IP, local_port, old_server_ip, old_server_port)
                syslog.syslog(syslog.LOG_DEBUG, "Deleting iptables rule for old SNMPv{0} Trap Destination Config. Rule={1}".format(ver,cmd))
                os.system(cmd)

        cmd="systemctl restart snmp"
        os.system (cmd)
        
    except :
        syslog.syslog(syslog.LOG_ERR, "Exception in modifying the snmp trap destination")
        return 1
    return 0

