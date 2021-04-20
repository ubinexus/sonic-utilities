bgp_v4_neighbors = \
"""
BGP neighbor is 10.0.0.57, remote AS 64600, local AS 65100, external link
 Description: ARISTA01T1
 Member of peer-group PEER_V4 for session parameters
  BGP version 4, remote router ID 100.1.0.29, local router ID 10.1.0.32
  BGP state = Established, up for 00:00:39
  Last read 00:00:00, Last write 00:00:00
  Hold time is 10, keepalive interval is 3 seconds
  Configured hold time is 10, keepalive interval is 3 seconds
  Neighbor capabilities:
    4 Byte AS: advertised and received
    AddPath:
      IPv4 Unicast: RX advertised IPv4 Unicast and received
    Route refresh: advertised and received(new)
    Address Family IPv4 Unicast: advertised and received
    Hostname Capability: advertised (name: vlab-01,domain name: n/a) not received
    Graceful Restart Capability: advertised and received
      Remote Restart timer is 300 seconds
      Address families by peer:
        none
  Graceful restart information:
    End-of-RIB send: IPv4 Unicast
    End-of-RIB received: IPv4 Unicast
    Local GR Mode: Restart*
    Remote GR Mode: Helper
    R bit: False
    Timers:
      Configured Restart Time(sec): 240
      Received Restart Time(sec): 300
    IPv4 Unicast:
      F bit: False
      End-of-RIB sent: Yes
      End-of-RIB sent after update: No
      End-of-RIB received: Yes
      Timers:
        Configured Stale Path Time(sec): 360
        Configured Selection Deferral Time(sec): 360
  Message statistics:
    Inq depth is 0
    Outq depth is 0
                         Sent       Rcvd
    Opens:                  2          1
    Notifications:          2          2
    Updates:             3203       3202
    Keepalives:            14         15
    Route Refresh:          0          0
    Capability:             0          0
    Total:               3221       3220
  Minimum time between advertisement runs is 0 seconds

 For address family: IPv4 Unicast
  PEER_V4 peer-group member
  Update group 1, subgroup 1
  Packet Queue length 0
  Inbound soft reconfiguration allowed
  Community attribute sent to this neighbor(all)
  Inbound path policy configured
  Outbound path policy configured
  Route map for incoming advertisements is *FROM_BGP_PEER_V4
  Route map for outgoing advertisements is *TO_BGP_PEER_V4
  6400 accepted prefixes

  Connections established 1; dropped 0
  Last reset 00:01:01,  No AFI/SAFI activated for peer
Local host: 10.0.0.56, Local port: 179
Foreign host: 10.0.0.57, Foreign port: 44731
Nexthop: 10.0.0.56
Nexthop global: fc00::71
Nexthop local: fe80::5054:ff:fea9:41c2
BGP connection: shared network
BGP Connect Retry Timer in Seconds: 10
Estimated round trip time: 20 ms
Read thread: on  Write thread: on  FD used: 28
"""

bgp_v4_neighbor_invalid = \
"""Usage: neighbors [OPTIONS] [IPADDRESS] [[routes|advertised-routes|received-
                 routes]]
Try 'neighbors --help' for help.

Error:  Bgp neighbor 20.1.1.1 not configured

"""

bgp_v4_neighbor_invalid_address = \
"""Error: invalid_address is not valid ipv4 address"""

bgp_v4_neighbor_adv_routes = \
"""
BGP table version is 6405, local router ID is 10.1.0.32, vrf id 0
Default local pref 100, local AS 65100
Status codes:  s suppressed, d damped, h history, * valid, > best, = multipath,
               i internal, r RIB-failure, S Stale, R Removed
Nexthop codes: @NNN nexthop's vrf id, < announce-nh-self
Origin codes:  i - IGP, e - EGP, ? - incomplete

   Network          Next Hop            Metric LocPrf Weight Path
*> 0.0.0.0/0        0.0.0.0                                0 64600 65534 6666 6667 i
*> 10.1.0.32/32     0.0.0.0                  0         32768 i
*> 100.1.0.29/32    0.0.0.0                                0 64600 i
*> 100.1.0.30/32    0.0.0.0                                0 64600 i
*> 100.1.0.31/32    0.0.0.0                                0 64600 i
*> 100.1.0.32/32    0.0.0.0                                0 64600 i
*> 192.168.0.0/21   0.0.0.0                  0         32768 i
*> 192.168.8.0/25   0.0.0.0                                0 64600 65501 i
*> 192.168.8.128/25 0.0.0.0                                0 64600 65501 i
*> 192.168.16.0/25  0.0.0.0                                0 64600 65502 i
*> 192.168.16.128/25
                    0.0.0.0                                0 64600 65502 i
*> 192.168.24.0/25  0.0.0.0                                0 64600 65503 i
*> 192.168.24.128/25
                    0.0.0.0                                0 64600 65503 i
*> 192.168.32.0/25  0.0.0.0                                0 64600 65504 i
*> 192.168.32.128/25
                    0.0.0.0                                0 64600 65504 i
*> 192.168.40.0/25  0.0.0.0                                0 64600 65505 i
*> 192.168.40.128/25
                    0.0.0.0                                0 64600 65505 i
*> 192.168.48.0/25  0.0.0.0                                0 64600 65506 i
*> 192.168.48.128/25
                    0.0.0.0                                0 64600 65506 i
*> 192.168.56.0/25  0.0.0.0                                0 64600 65507 i
*> 192.168.56.128/25
                    0.0.0.0                                0 64600 65507 i
"""

bgp_v4_neighbor_recv_routes = \
"""
BGP table version is 6405, local router ID is 10.1.0.32, vrf id 0
Default local pref 100, local AS 65100
Status codes:  s suppressed, d damped, h history, * valid, > best, = multipath,
               i internal, r RIB-failure, S Stale, R Removed
Nexthop codes: @NNN nexthop's vrf id, < announce-nh-self
Origin codes:  i - IGP, e - EGP, ? - incomplete

   Network          Next Hop            Metric LocPrf Weight Path
*> 0.0.0.0/0        10.0.0.57                              0 64600 65534 6666 6667 i
*> 100.1.0.29/32    10.0.0.57                              0 64600 i
*> 192.168.8.0/25   10.0.0.57                              0 64600 65501 i
*> 192.168.8.128/25 10.0.0.57                              0 64600 65501 i
*> 192.168.16.0/25  10.0.0.57                              0 64600 65502 i
*> 192.168.16.128/25
                    10.0.0.57                              0 64600 65502 i
*> 192.168.24.0/25  10.0.0.57                              0 64600 65503 i
*> 192.168.24.128/25
                    10.0.0.57                              0 64600 65503 i
*> 192.168.32.0/25  10.0.0.57                              0 64600 65504 i
*> 192.168.32.128/25
                    10.0.0.57                              0 64600 65504 i
*> 192.168.40.0/25  10.0.0.57                              0 64600 65505 i
*> 192.168.40.128/25
                    10.0.0.57                              0 64600 65505 i
*> 192.168.48.0/25  10.0.0.57                              0 64600 65506 i
*> 192.168.48.128/25
                    10.0.0.57                              0 64600 65506 i
*> 192.168.56.0/25  10.0.0.57                              0 64600 65507 i
*> 192.168.56.128/25
                    10.0.0.57                              0 64600 65507 i 
"""

bgp_v6_neighbors = \
"""
BGP neighbor is fc00::72, remote AS 64600, local AS 65100, external link
 Description: ARISTA01T1
 Member of peer-group PEER_V6 for session parameters
  BGP version 4, remote router ID 100.1.0.29, local router ID 10.1.0.32
  BGP state = Established, up for 01:06:23
  Last read 00:00:02, Last write 00:00:00
  Hold time is 10, keepalive interval is 3 seconds
  Configured hold time is 10, keepalive interval is 3 seconds
  Neighbor capabilities:
    4 Byte AS: advertised and received
    AddPath:
      IPv6 Unicast: RX advertised IPv6 Unicast and received
    Route refresh: advertised and received(new)
    Address Family IPv6 Unicast: advertised and received
    Hostname Capability: advertised (name: vlab-01,domain name: n/a) not received
    Graceful Restart Capability: advertised and received
      Remote Restart timer is 300 seconds
      Address families by peer:
        none
  Graceful restart information:
    End-of-RIB send: IPv6 Unicast
    End-of-RIB received: IPv6 Unicast
    Local GR Mode: Restart*
    Remote GR Mode: Helper
    R bit: False
    Timers:
      Configured Restart Time(sec): 240
      Received Restart Time(sec): 300
    IPv6 Unicast:
      F bit: False
      End-of-RIB sent: Yes
      End-of-RIB sent after update: No
      End-of-RIB received: Yes
      Timers:
        Configured Stale Path Time(sec): 360
        Configured Selection Deferral Time(sec): 360
  Message statistics:
    Inq depth is 0
    Outq depth is 0
                         Sent       Rcvd
    Opens:                  1          1
    Notifications:          0          0
    Updates:             3206       3202
    Keepalives:          1328       1329
    Route Refresh:          0          0
    Capability:             0          0
    Total:               4535       4532
  Minimum time between advertisement runs is 0 seconds

 For address family: IPv6 Unicast
  PEER_V6 peer-group member
  Update group 2, subgroup 2
  Packet Queue length 0
  Inbound soft reconfiguration allowed
  Community attribute sent to this neighbor(all)
  Inbound path policy configured
  Outbound path policy configured
  Route map for incoming advertisements is *FROM_BGP_PEER_V6
  Route map for outgoing advertisements is *TO_BGP_PEER_V6
  6400 accepted prefixes

  Connections established 1; dropped 0
  Last reset 01:06:46,  Waiting for peer OPEN
Local host: fc00::71, Local port: 59726
Foreign host: fc00::72, Foreign port: 179
Nexthop: 10.0.0.56
Nexthop global: fc00::71
Nexthop local: fe80::5054:ff:fea9:41c2
BGP connection: shared network
BGP Connect Retry Timer in Seconds: 10
Estimated round trip time: 4 ms
Read thread: on  Write thread: on  FD used: 30
"""

bgp_v6_neighbor_adv_routes = \
"""
BGP table version is 6407, local router ID is 10.1.0.32, vrf id 0
Default local pref 100, local AS 65100
Status codes:  s suppressed, d damped, h history, * valid, > best, = multipath,
               i internal, r RIB-failure, S Stale, R Removed
Nexthop codes: @NNN nexthop's vrf id, < announce-nh-self
Origin codes:  i - IGP, e - EGP, ? - incomplete

   Network          Next Hop            Metric LocPrf Weight Path
*> ::/0             ::                                     0 64600 65534 6666 6667 i
*> 2064:100::1d/128 ::                                     0 64600 i
*> 2064:100::1e/128 ::                                     0 64600 i
*> 2064:100::1f/128 ::                                     0 64600 i
*> 2064:100::20/128 ::                                     0 64600 i
*> 20c0:a808::/64   ::                                     0 64600 65501 i
*> 20c0:a808:0:80::/64
                    ::                                     0 64600 65501 i
*> 20c0:a810::/64   ::                                     0 64600 65502 i
*> 20c0:a810:0:80::/64
                    ::                                     0 64600 65502 i
*> 20c0:a818::/64   ::                                     0 64600 65503 i
*> 20c0:a818:0:80::/64
                    ::                                     0 64600 65503 i
*> 20c0:a820::/64   ::                                     0 64600 65504 i
*> 20c0:a820:0:80::/64
                    ::                                     0 64600 65504 i
*> 20c0:a828::/64   ::                                     0 64600 65505 i
*> 20c0:a828:0:80::/64
                    ::                                     0 64600 65505 i
*> 20c0:a830::/64   ::                                     0 64600 65506 i
*> 20c0:a830:0:80::/64
                    ::                                     0 64600 65506 i
*> 20c0:a838::/64   ::                                     0 64600 65507 i
*> 20c0:a838:0:80::/64
                    ::                                     0 64600 65507 i
*> 20c0:a840::/64   ::                                     0 64600 65508 i
*> 20c0:a840:0:80::/64
                    ::                                     0 64600 65508 i
*> 20c0:a848::/64   ::                                     0 64600 65509 i
*> 20c0:a848:0:80::/64
                    ::                                     0 64600 65509 i
*> 20c0:a850::/64   ::                                     0 64600 65510 i
*> 20c0:a850:0:80::/64
                    ::                                     0 64600 65510 i
*> 20c0:a858::/64   ::                                     0 64600 65511 i
*> 20c0:a858:0:80::/64
                    ::                                     0 64600 65511 i
*> 20c0:a860::/64   ::                                     0 64600 65512 i
*> 20c0:a860:0:80::/64
                    ::                                     0 64600 65512 i
*> 20c0:a868::/64   ::                                     0 64600 65513 i
*> 20c0:a868:0:80::/64
                    ::                                     0 64600 65513 i
"""

bgp_v6_neighbor_recv_routes = \
"""
BGP table version is 6407, local router ID is 10.1.0.32, vrf id 0
Default local pref 100, local AS 65100
Status codes:  s suppressed, d damped, h history, * valid, > best, = multipath,
               i internal, r RIB-failure, S Stale, R Removed
Nexthop codes: @NNN nexthop's vrf id, < announce-nh-self
Origin codes:  i - IGP, e - EGP, ? - incomplete

   Network          Next Hop            Metric LocPrf Weight Path
*> ::/0             fc00::72                               0 64600 65534 6666 6667 i
*> 2064:100::1d/128 fc00::72                               0 64600 i
*> 20c0:a808::/64   fc00::72                               0 64600 65501 i
*> 20c0:a808:0:80::/64
                    fc00::72                               0 64600 65501 i
*> 20c0:a810::/64   fc00::72                               0 64600 65502 i
*> 20c0:a810:0:80::/64
                    fc00::72                               0 64600 65502 i
*> 20c0:a818::/64   fc00::72                               0 64600 65503 i
*> 20c0:a818:0:80::/64
                    fc00::72                               0 64600 65503 i
*> 20c0:a820::/64   fc00::72                               0 64600 65504 i
*> 20c0:a820:0:80::/64
                    fc00::72                               0 64600 65504 i
*> 20c0:a828::/64   fc00::72                               0 64600 65505 i
*> 20c0:a828:0:80::/64
                    fc00::72                               0 64600 65505 i
*> 20c0:a830::/64   fc00::72                               0 64600 65506 i
*> 20c0:a830:0:80::/64
                    fc00::72                               0 64600 65506 i
*> 20c0:a838::/64   fc00::72                               0 64600 65507 i
*> 20c0:a838:0:80::/64
                    fc00::72                               0 64600 65507 i
*> 20c0:a840::/64   fc00::72                               0 64600 65508 i
*> 20c0:a840:0:80::/64
                    fc00::72                               0 64600 65508 i
*> 20c0:a848::/64   fc00::72                               0 64600 65509 i
*> 20c0:a848:0:80::/64
                    fc00::72                               0 64600 65509 i
*> 20c0:a850::/64   fc00::72                               0 64600 65510 i
*> 20c0:a850:0:80::/64
                    fc00::72                               0 64600 65510 i
*> 20c0:a858::/64   fc00::72                               0 64600 65511 i
*> 20c0:a858:0:80::/64
                    fc00::72                               0 64600 65511 i
*> 20c0:a860::/64   fc00::72                               0 64600 65512 i
*> 20c0:a860:0:80::/64
                    fc00::72                               0 64600 65512 i
*> 20c0:a868::/64   fc00::72                               0 64600 65513 i
*> 20c0:a868:0:80::/64
                    fc00::72                               0 64600 65513 i
"""

bgp_v6_neighbor_invalid  = \
"""Error:  Bgp neighbor aa00::72 not configured"""

bgp_v6_neighbor_invalid_address = \
"""Error: 20.1.1.1 is not valid ipv6 address"""
