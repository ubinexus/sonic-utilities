#!/usr/bin/python3

import subprocess
import json
from scapy.all import *
import scapy.contrib.lacp
import os
import re
import sys

from swsscommon.swsscommon import DBConnector, Table

MIN_TAG_FOR_EACH_VERSION = {
        "20220531": 500
        }

class LACPRetryCount(Packet):
    name = "LACPRetryCount"
    fields_desc = [
        ByteField("version", 0xf1),
        ByteField("actor_type", 1),
        ByteField("actor_length", 20),
        ShortField("actor_system_priority", 0),
        MACField("actor_system", None),
        ShortField("actor_key", 0),
        ShortField("actor_port_priority", 0),
        ShortField("actor_port_number", 0),
        ByteField("actor_state", 0),
        XStrFixedLenField("actor_reserved", "", 3),
        ByteField("partner_type", 2),
        ByteField("partner_length", 20),
        ShortField("partner_system_priority", 0),
        MACField("partner_system", None),
        ShortField("partner_key", 0),
        ShortField("partner_port_priority", 0),
        ShortField("partner_port_number", 0),
        ByteField("partner_state", 0),
        XStrFixedLenField("partner_reserved", "", 3),
        ByteField("collector_type", 3),
        ByteField("collector_length", 16),
        ShortField("collector_max_delay", 0),
        XStrFixedLenField("collector_reserved", "", 12),
        ByteField("actor_retry_count_type", 0x80),
        ByteField("actor_retry_count_length", 4),
        ByteField("actor_retry_count", 0),
        XStrFixedLenField("actor_retry_count_reserved", "", 1),
        ByteField("partner_retry_count_type", 0x81),
        ByteField("partner_retry_count_length", 4),
        ByteField("partner_retry_count", 0),
        XStrFixedLenField("partner_retry_count_reserved", "", 1),
        ByteField("terminator_type", 0),
        ByteField("terminator_length", 0),
        XStrFixedLenField("reserved", "", 42),
    ]

bind_layers(scapy.contrib.lacp.SlowProtocol, LACPRetryCount, subtype=1)

def getPortChannelConfig(portChannelName):
    process = subprocess.run(["teamdctl", portChannelName, "state", "dump"], capture_output=True)
    return json.loads(process.stdout)

def getLldpNeighbors():
    process = subprocess.run(["lldpctl", "-f", "json"], capture_output=True)
    return json.loads(process.stdout)

def craftLacpPacket(portChannelConfig, portName):
    portConfig = portChannelConfig["ports"][portName]
    actorConfig = portConfig["runner"]["actor_lacpdu_info"]
    partnerConfig = portConfig["runner"]["partner_lacpdu_info"]
    l2 = Ether(dst="01:80:c2:00:00:02", src=portConfig["ifinfo"]["dev_addr"], type=0x8809)
    l3 = scapy.contrib.lacp.SlowProtocol(subtype=0x01) 
    l4 = LACPRetryCount()
    l4.actor_system_priority = actorConfig["system_priority"]
    l4.actor_system = actorConfig["system"]
    l4.actor_key = actorConfig["key"]
    l4.actor_port_priority = actorConfig["port_priority"]
    l4.actor_port_number = actorConfig["port"]
    l4.actor_state = actorConfig["state"]
    l4.partner_system_priority = partnerConfig["system_priority"]
    l4.partner_system = partnerConfig["system"]
    l4.partner_key = partnerConfig["key"]
    l4.partner_port_priority = partnerConfig["port_priority"]
    l4.partner_port_number = partnerConfig["port"]
    l4.partner_state = partnerConfig["state"]
    l4.actor_retry_count = 5
    l4.partner_retry_count = 3
    packet = l2 / l3 / l4
    return packet

def getPortChannels():
    configDb = DBConnector("CONFIG_DB", 0)
    portchannelTable = Table(configDb, "PORTCHANNEL")
    return list(portchannelTable.getKeys())

def main():
    if os.geteuid() != 0:
        print("Root privileges required for this operation")
        sys.exit(1)
        return
    portChannels = getPortChannels()
    for portChannel in portChannels:
        config = getPortChannelConfig(portChannel)
        lldpInfo = getLldpNeighbors()
        peerSupportsFeature = None
        for portName in config["ports"].keys():
            interfaceLldpInfo = [k for k in lldpInfo["lldp"]["interface"] if portName in k]
            if not interfaceLldpInfo:
                print("WARNING: No LLDP info available for {}; skipping".format(portName)) 
                continue
            interfaceLldpInfo = interfaceLldpInfo[0][portName]
            peerName = list(interfaceLldpInfo["chassis"].keys())[0]
            peerInfo = interfaceLldpInfo["chassis"][peerName]
            if "descr" not in peerInfo:
                print("WARNING: No peer description available via LLDP for {}; skipping".format(portName)) 
                continue
            if "SONiC" not in peerInfo["descr"]:
                print("WARNING: Peer device is not a SONiC device; skipping")
                peerSupportsFeature = False
                break
            sonicVersionMatch = re.search(r"SONiC Software Version: SONiC\.(.*?)(?: - |$)", peerInfo["descr"])
            if not sonicVersionMatch:
                print("WARNING: Unable to get SONiC version info for peer device; skipping")
                continue
            sonicVersion = sonicVersionMatch.group(1)
            if "teamd-retry-count" in sonicVersion:
                print("SUCCESS: Peer device {} is running version of SONiC ({}) with teamd retry count feature".format(peerName, sonicVersion))
                peerSupportsFeature = True
                break
            sonicVersionComponents = sonicVersion.split(".")
            if sonicVersionComponents[0] in MIN_TAG_FOR_EACH_VERSION and int(sonicVersionComponents[1]) >= MIN_TAG_FOR_EACH_VERSION[sonicVersionComponents[0]]:
                print("SUCCESS: Peer device {} is running version of SONiC ({}) with teamd retry count feature".format(peerName, sonicVersion))
                peerSupportsFeature = True
                break
            else:
                print("WARNING: Peer device {} is running version of SONiC ({}) without teamd retry count feature; skipping".format(peerName, sonicVersion))
                peerSupportsFeature = False
                break
        if peerSupportsFeature:
            retryCountChangeProcess = subprocess.run(["config", "portchannel", "retry-count", "set", portChannel, "5"])
            if retryCountChangeProcess.returncode != 0:
                for portName in config["ports"].keys():
                    packet = craftLacpPacket(config, portName)
                    sendp(packet, iface=portName)

if __name__ == "__main__":
    main()
