#!/usr/bin/python3

import subprocess
import json
from scapy.all import *
import scapy.contrib.lacp
import os
import re
import sys
from threading import Thread
import time
import argparse

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
        ConditionalField(ByteField("actor_retry_count_type", 0x80), lambda pkt:pkt.version == 0xf1),
        ConditionalField(ByteField("actor_retry_count_length", 4), lambda pkt:pkt.version == 0xf1),
        ConditionalField(ByteField("actor_retry_count", 0), lambda pkt:pkt.version == 0xf1),
        ConditionalField(XStrFixedLenField("actor_retry_count_reserved", "", 1), lambda pkt:pkt.version == 0xf1),
        ConditionalField(ByteField("partner_retry_count_type", 0x81), lambda pkt:pkt.version == 0xf1),
        ConditionalField(ByteField("partner_retry_count_length", 4), lambda pkt:pkt.version == 0xf1),
        ConditionalField(ByteField("partner_retry_count", 0), lambda pkt:pkt.version == 0xf1),
        ConditionalField(XStrFixedLenField("partner_retry_count_reserved", "", 1), lambda pkt:pkt.version == 0xf1),
        ByteField("terminator_type", 0),
        ByteField("terminator_length", 0),
        ConditionalField(XStrFixedLenField("reserved", "", 42), lambda pkt:pkt.version == 0xf1),
        ConditionalField(XStrFixedLenField("reserved", "", 50), lambda pkt:pkt.version != 0xf1),
    ]

split_layers(scapy.contrib.lacp.SlowProtocol, scapy.contrib.lacp.LACP, subtype=1)
bind_layers(scapy.contrib.lacp.SlowProtocol, LACPRetryCount, subtype=1)

def getPortChannelConfig(portChannelName):
    process = subprocess.run(["teamdctl", portChannelName, "state", "dump"], capture_output=True)
    return json.loads(process.stdout)

def getLldpNeighbors():
    process = subprocess.run(["lldpctl", "-f", "json"], capture_output=True)
    return json.loads(process.stdout)

def craftLacpPacket(portChannelConfig, portName, isProbePacket=False, newVersion=True):
    portConfig = portChannelConfig["ports"][portName]
    actorConfig = portConfig["runner"]["actor_lacpdu_info"]
    partnerConfig = portConfig["runner"]["partner_lacpdu_info"]
    l2 = Ether(dst="01:80:c2:00:00:02", src=portConfig["ifinfo"]["dev_addr"], type=0x8809)
    l3 = scapy.contrib.lacp.SlowProtocol(subtype=0x01) 
    l4 = LACPRetryCount()
    if newVersion:
        l4.version = 0xf1
    else:
        l4.version = 0x1
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
    if newVersion:
        l4.actor_retry_count = 5 if not isProbePacket else 3
        l4.partner_retry_count = 3
    packet = l2 / l3 / l4
    return packet

def getPortChannels():
    configDb = DBConnector("CONFIG_DB", 0)
    portchannelTable = Table(configDb, "PORTCHANNEL")
    return list(portchannelTable.getKeys())

class LacpPacketListenThread(Thread):
    def __init__(self, port):
        Thread.__init__(self)
        self.port = port
        self.detectedNewVersion = False

    def lacpPacketCallback(self, pkt):
        if pkt["LACPRetryCount"].version == 0xf1:
            self.detectedNewVersion = True
        return self.detectedNewVersion

    def run(self):
        sniff(stop_filter=self.lacpPacketCallback, iface=self.port, filter="ether proto 0x8809", store=0, timeout=30)

def sendLacpPackets(packets):
    while True:
        for port, packet in packets:
            sendp(packet, iface=port)
        time.sleep(15)

def main(probeOnly=False):
    if os.geteuid() != 0:
        print("Root privileges required for this operation")
        sys.exit(1)
        return False
    portChannels = getPortChannels()
    if not portChannels:
        return True
    for portChannel in portChannels:
        config = getPortChannelConfig(portChannel)
        lldpInfo = getLldpNeighbors()
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
                break

            # Start sniffing thread
            lacpThread = LacpPacketListenThread(portName)
            lacpThread.start()

            # Generate and send probe packet
            probePacket = craftLacpPacket(config, portName, isProbePacket=True)
            sendp(probePacket, iface=portName)

            lacpThread.join()

            resetProbePacket = craftLacpPacket(config, portName, newVersion=False)
            time.sleep(2)
            sendp(resetProbePacket, iface=portName, count=2, inter=0.5)

            if lacpThread.detectedNewVersion:
                print("SUCCESS: Peer device {} is running version of SONiC with teamd retry count feature".format(peerName))
                break
            else:
                print("WARNING: Peer device {} is running version of SONiC without teamd retry count feature".format(peerName))
                break
    if not probeOnly:
        retryCountGetProcess = subprocess.run(["config", "portchannel", "retry-count", "get", portChannels[0]])
        if retryCountGetProcess.returncode == 0:
            # Currently running on SONiC version with teamd retry count feature
            for portChannel in portChannels:
                subprocess.run(["config", "portchannel", "retry-count", "set", portChannel, "5"])
        else:
            lacpPackets = []
            for portChannel in portChannels:
                config = getPortChannelConfig(portChannel)
                for portName in config["ports"].keys():
                    packet = craftLacpPacket(config, portName)
                    lacpPackets.append((portName, packet))
            sendLacpPackets(lacpPackets)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Teamd retry count changer.')
    parser.add_argument('--probe-only', action='store_true',
            help='Probe the peer devices only, to verify that they support the teamd retry count feature')
    args = parser.parse_args()
    main(args.probe_only)
