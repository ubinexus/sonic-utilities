show_run_bgp_sasic = \
"""
Building configuration...

Current configuration:
!
frr version 8.2.2
frr defaults traditional
hostname str2-7050cx3-acs-02
log syslog informational
log facility local4
agentx
no service integrated-vtysh-config
!
password zebra
enable password zebra
!
router bgp 65100
 bgp router-id 10.1.0.32
 bgp log-neighbor-changes
 no bgp ebgp-requires-policy
 no bgp default ipv4-unicast
 bgp graceful-restart restart-time 240
 bgp graceful-restart select-defer-time 45
 bgp graceful-restart
 bgp graceful-restart preserve-fw-state
 bgp bestpath as-path multipath-relax
 neighbor BGPSLBPassive peer-group
 neighbor BGPSLBPassive remote-as 65432
 neighbor BGPSLBPassive passive
 neighbor BGPSLBPassive ebgp-multihop 255
 neighbor BGPSLBPassive update-source 10.1.0.32
 neighbor BGPVac peer-group
 neighbor BGPVac remote-as 65432
 neighbor BGPVac passive
 neighbor BGPVac ebgp-multihop 255
 neighbor BGPVac update-source 10.1.0.32
 neighbor PEER_V4 peer-group
 neighbor PEER_V6 peer-group
 neighbor 10.0.0.57 remote-as 64600
 neighbor 10.0.0.57 peer-group PEER_V4
 neighbor 10.0.0.57 description ARISTA01T1
 neighbor 10.0.0.57 timers 3 10
 neighbor 10.0.0.57 timers connect 10
 neighbor 10.0.0.59 remote-as 64600
 neighbor 10.0.0.59 peer-group PEER_V4
 neighbor 10.0.0.59 description ARISTA02T1
 neighbor 10.0.0.59 timers 3 10
 neighbor 10.0.0.59 timers connect 10
 neighbor 10.0.0.61 remote-as 64600
 neighbor 10.0.0.61 peer-group PEER_V4
 neighbor 10.0.0.61 description ARISTA03T1
 neighbor 10.0.0.61 timers 3 10
 neighbor 10.0.0.61 timers connect 10
 neighbor 10.0.0.63 remote-as 64600
 neighbor 10.0.0.63 peer-group PEER_V4
 neighbor 10.0.0.63 description ARISTA04T1
 neighbor 10.0.0.63 timers 3 10
 neighbor 10.0.0.63 timers connect 10
 neighbor fc00::72 remote-as 64600
 neighbor fc00::72 peer-group PEER_V6
 neighbor fc00::72 description ARISTA01T1
 neighbor fc00::72 timers 3 10
 neighbor fc00::72 timers connect 10
 neighbor fc00::76 remote-as 64600
 neighbor fc00::76 peer-group PEER_V6
 neighbor fc00::76 description ARISTA02T1
 neighbor fc00::76 timers 3 10
 neighbor fc00::76 timers connect 10
 neighbor fc00::7a remote-as 64600
 neighbor fc00::7a peer-group PEER_V6
 neighbor fc00::7a description ARISTA03T1
 neighbor fc00::7a timers 3 10
 neighbor fc00::7a timers connect 10
 neighbor fc00::7e remote-as 64600
 neighbor fc00::7e peer-group PEER_V6
 neighbor fc00::7e description ARISTA04T1
 neighbor fc00::7e timers 3 10
 neighbor fc00::7e timers connect 10
 bgp listen range 10.255.0.0/25 peer-group BGPSLBPassive
 bgp listen range 192.168.0.0/21 peer-group BGPVac
 !
 address-family ipv4 unicast
  network 10.1.0.32/32
  network 192.168.0.0/21
  neighbor BGPSLBPassive activate
  neighbor BGPSLBPassive soft-reconfiguration inbound
  neighbor BGPSLBPassive route-map FROM_BGP_SPEAKER in
  neighbor BGPSLBPassive route-map TO_BGP_SPEAKER out
  neighbor BGPVac activate
  neighbor BGPVac soft-reconfiguration inbound
  neighbor BGPVac route-map FROM_BGP_SPEAKER in
  neighbor BGPVac route-map TO_BGP_SPEAKER out
  neighbor PEER_V4 soft-reconfiguration inbound
  neighbor PEER_V4 allowas-in 1
  neighbor PEER_V4 route-map FROM_BGP_PEER_V4 in
  neighbor PEER_V4 route-map TO_BGP_PEER_V4 out
  neighbor 10.0.0.57 activate
  neighbor 10.0.0.59 activate
  neighbor 10.0.0.61 activate
  neighbor 10.0.0.63 activate
  maximum-paths 64
 exit-address-family
 !
 address-family ipv6 unicast
  network fc00:1::/64
  network fc02:1000::/64
  neighbor BGPSLBPassive activate
  neighbor BGPVac activate
  neighbor PEER_V6 soft-reconfiguration inbound
  neighbor PEER_V6 allowas-in 1
  neighbor PEER_V6 route-map FROM_BGP_PEER_V6 in
  neighbor PEER_V6 route-map TO_BGP_PEER_V6 out
  neighbor fc00::72 activate
  neighbor fc00::76 activate
  neighbor fc00::7a activate
  neighbor fc00::7e activate
  maximum-paths 64
 exit-address-family
exit
!
ip prefix-list PL_LoopbackV4 seq 5 permit 10.1.0.32/32
ip prefix-list LOCAL_VLAN_IPV4_PREFIX seq 5 permit 192.168.0.0/21
!
ipv6 prefix-list PL_LoopbackV6 seq 5 permit fc00:1::/64
ipv6 prefix-list LOCAL_VLAN_IPV6_PREFIX seq 10 permit fc02:1000::/64
!
bgp community-list standard allow_list_default_community seq 5 permit no-export
bgp community-list standard allow_list_default_community seq 10 permit 5060:12345
!
route-map ALLOW_LIST_DEPLOYMENT_ID_0_V4 permit 65535
 set community 5060:12345 additive
exit
!
route-map ALLOW_LIST_DEPLOYMENT_ID_0_V6 permit 65535
 set community 5060:12345 additive
exit
!
route-map FROM_BGP_PEER_V4 permit 10
 call ALLOW_LIST_DEPLOYMENT_ID_0_V4
 on-match next
exit
!
route-map FROM_BGP_PEER_V4 permit 11
 match community allow_list_default_community
exit
!
route-map FROM_BGP_PEER_V4 permit 100
exit
!
route-map FROM_BGP_PEER_V6 permit 1
 on-match next
 set ipv6 next-hop prefer-global
exit
!
route-map FROM_BGP_PEER_V6 permit 10
 call ALLOW_LIST_DEPLOYMENT_ID_0_V6
 on-match next
exit
!
route-map FROM_BGP_PEER_V6 permit 11
 match community allow_list_default_community
exit
!
route-map FROM_BGP_PEER_V6 permit 100
exit
!
route-map TO_BGP_PEER_V4 permit 100
exit
!
route-map TO_BGP_PEER_V6 permit 100
exit
!
route-map FROM_BGP_SPEAKER permit 10
exit
!
route-map TO_BGP_SPEAKER deny 1
exit
!
route-map RM_SET_SRC permit 10
exit
!
route-map RM_SET_SRC6 permit 10
exit
!
end
"""


show_run_bgp_invalid_sasic_with_namespace = \
"""
-n/--namespace is not available for single asic
"""


show_run_bgp_masic_asic0 = \
"""
------------Showing running config bgp on asic0------------
Building configuration...

Current configuration:
!
frr version 7.2.1-sonic
frr defaults traditional
hostname svcstr-n3164-acs-1
log syslog informational
log facility local4
no service integrated-vtysh-config
!
enable password zebra
password zebra
!
router bgp 65100
 bgp router-id 10.1.0.32
 bgp log-neighbor-changes
 no bgp default ipv4-unicast
 bgp graceful-restart restart-time 240
 bgp graceful-restart
 bgp graceful-restart preserve-fw-state
 bgp bestpath as-path multipath-relax
 neighbor INTERNAL_PEER_V4 peer-group
 neighbor INTERNAL_PEER_V6 peer-group
 neighbor TIER2_V4 peer-group
 neighbor TIER2_V6 peer-group
 neighbor 10.1.0.0 remote-as 65100
 neighbor 10.1.0.0 peer-group INTERNAL_PEER_V4
 neighbor 10.1.0.0 description ASIC4
 neighbor 10.1.0.0 timers 3 10
 neighbor 10.1.0.0 timers connect 10
 neighbor 10.1.0.2 remote-as 65100
 neighbor 10.1.0.2 peer-group INTERNAL_PEER_V4
 neighbor 10.1.0.2 description ASIC5
 neighbor 10.1.0.2 timers 3 10
 neighbor 10.1.0.2 timers connect 10
 neighbor 2603:10e2:400:1::1 remote-as 65100
 neighbor 2603:10e2:400:1::1 peer-group INTERNAL_PEER_V6
 neighbor 2603:10e2:400:1::1 description ASIC4
 neighbor 2603:10e2:400:1::1 timers 3 10
 neighbor 2603:10e2:400:1::1 timers connect 10
 neighbor 2603:10e2:400:1::5 remote-as 65100
 neighbor 2603:10e2:400:1::5 peer-group INTERNAL_PEER_V6
 neighbor 2603:10e2:400:1::5 description ASIC5
 neighbor 2603:10e2:400:1::5 timers 3 10
 neighbor 2603:10e2:400:1::5 timers connect 10
 neighbor 10.0.0.1 remote-as 65200
 neighbor 10.0.0.1 peer-group TIER2_V4
 neighbor 10.0.0.1 description ARISTA01T2
 neighbor 10.0.0.5 remote-as 65200
 neighbor 10.0.0.5 peer-group TIER2_V4
 neighbor 10.0.0.5 description ARISTA03T2
 neighbor fc00::2 remote-as 65200
 neighbor fc00::2 peer-group TIER2_V6
 neighbor fc00::2 description ARISTA01T2
 neighbor fc00::6 remote-as 65200
 neighbor fc00::6 peer-group TIER2_V6
 neighbor fc00::6 description ARISTA03T2
 !
 address-family ipv4 unicast
  network 8.0.0.0/32 route-map HIDE_INTERNAL
  network 10.1.0.32/32
  redistribute connected route-map HIDE_INTERNAL
  neighbor INTERNAL_PEER_V4 soft-reconfiguration inbound
  neighbor INTERNAL_PEER_V4 route-map FROM_BGP_INTERNAL_PEER_V4 in
  neighbor INTERNAL_PEER_V4 route-map TO_BGP_INTERNAL_PEER_V4 out
  neighbor TIER2_V4 activate
  neighbor TIER2_V4 soft-reconfiguration inbound
  neighbor TIER2_V4 maximum-prefix 12000 90 warning-only
  neighbor TIER2_V4 route-map FROM_TIER2_V4 in
  neighbor TIER2_V4 route-map TO_TIER2_V4 out
  neighbor 10.1.0.0 activate
  neighbor 10.1.0.0 allowas-in 1
  neighbor 10.1.0.2 activate
  neighbor 10.1.0.2 allowas-in 1
  maximum-paths 64
 exit-address-family
 !
 address-family ipv6 unicast
  network 2603:10e2:400::/128 route-map HIDE_INTERNAL
  network fc00:1::/64
  redistribute connected route-map HIDE_INTERNAL
  neighbor INTERNAL_PEER_V6 soft-reconfiguration inbound
  neighbor INTERNAL_PEER_V6 route-map FROM_BGP_INTERNAL_PEER_V6 in
  neighbor INTERNAL_PEER_V6 route-map TO_BGP_INTERNAL_PEER_V6 out
  neighbor TIER2_V6 activate
  neighbor TIER2_V6 soft-reconfiguration inbound
  neighbor TIER2_V6 maximum-prefix 8000 90 warning-only
  neighbor TIER2_V6 route-map FROM_TIER2_V6 in
  neighbor TIER2_V6 route-map TO_TIER2_V6 out
  neighbor 2603:10e2:400:1::1 activate
  neighbor 2603:10e2:400:1::1 allowas-in 1
  neighbor 2603:10e2:400:1::5 activate
  neighbor 2603:10e2:400:1::5 allowas-in 1
  maximum-paths 64
 exit-address-family
!
ip prefix-list PL_LoopbackV4 seq 5 permit 10.1.0.32/32
!
ipv6 prefix-list PL_LoopbackV6 seq 5 permit fc00:1::/64
!
bgp community-list standard UPSTREAM_PREFIX permit 8075:54000
!
route-map FROM_BGP_INTERNAL_PEER_V4 permit 100
!
route-map FROM_BGP_INTERNAL_PEER_V6 permit 1
 on-match next
 set ipv6 next-hop prefer-global 
!
route-map FROM_BGP_INTERNAL_PEER_V6 permit 100
!
route-map FROM_TIER2_V4 permit 100
 set community 8075:54000 additive
!
route-map FROM_TIER2_V6 permit 100
 on-match next
 set ipv6 next-hop prefer-global 
!
route-map FROM_TIER2_V6 permit 200
 set community 8075:54000 additive
!
route-map HIDE_INTERNAL permit 10
 on-match next
 set community no-export
!
route-map HIDE_INTERNAL permit 20
 set community 8075:9306 additive
!
route-map RM_SET_SRC permit 10
!
route-map RM_SET_SRC6 permit 10
!
route-map TO_BGP_INTERNAL_PEER_V4 permit 100
!
route-map TO_BGP_INTERNAL_PEER_V6 permit 100
!
route-map TO_TIER2_V4 deny 100
 match community UPSTREAM_PREFIX
!
route-map TO_TIER2_V4 permit 10000
!
route-map TO_TIER2_V6 deny 100
 match community UPSTREAM_PREFIX
!
route-map TO_TIER2_V6 permit 10000
!
line vty
!
end
"""

show_run_bgp_masic_asic1 = \
"""
------------Showing running config bgp on asic1------------
Building configuration...

Current configuration:
!
frr version 7.2.1-sonic
frr defaults traditional
hostname svcstr-n3164-acs-1
log syslog informational
log facility local4
no service integrated-vtysh-config
!
enable password zebra
password zebra
!
router bgp 65100
 bgp router-id 10.1.0.32
 bgp log-neighbor-changes
 no bgp default ipv4-unicast
 bgp graceful-restart restart-time 240
 bgp graceful-restart
 bgp graceful-restart preserve-fw-state
 bgp bestpath as-path multipath-relax
 neighbor INTERNAL_PEER_V4 peer-group
 neighbor INTERNAL_PEER_V6 peer-group
 neighbor TIER2_V4 peer-group
 neighbor TIER2_V6 peer-group
 neighbor 10.1.0.4 remote-as 65100
 neighbor 10.1.0.4 peer-group INTERNAL_PEER_V4
 neighbor 10.1.0.4 description ASIC4
 neighbor 10.1.0.4 timers 3 10
 neighbor 10.1.0.4 timers connect 10
 neighbor 10.1.0.6 remote-as 65100
 neighbor 10.1.0.6 peer-group INTERNAL_PEER_V4
 neighbor 10.1.0.6 description ASIC5
 neighbor 10.1.0.6 timers 3 10
 neighbor 10.1.0.6 timers connect 10
 neighbor 2603:10e2:400:1::9 remote-as 65100
 neighbor 2603:10e2:400:1::9 peer-group INTERNAL_PEER_V6
 neighbor 2603:10e2:400:1::9 description ASIC4
 neighbor 2603:10e2:400:1::9 timers 3 10
 neighbor 2603:10e2:400:1::9 timers connect 10
 neighbor 2603:10e2:400:1::d remote-as 65100
 neighbor 2603:10e2:400:1::d peer-group INTERNAL_PEER_V6
 neighbor 2603:10e2:400:1::d description ASIC5
 neighbor 2603:10e2:400:1::d timers 3 10
 neighbor 2603:10e2:400:1::d timers connect 10
 neighbor 10.0.0.9 remote-as 65200
 neighbor 10.0.0.9 peer-group TIER2_V4
 neighbor 10.0.0.9 description ARISTA05T2
 neighbor 10.0.0.13 remote-as 65200
 neighbor 10.0.0.13 peer-group TIER2_V4
 neighbor 10.0.0.13 description ARISTA07T2
 neighbor fc00::a remote-as 65200
 neighbor fc00::a peer-group TIER2_V6
 neighbor fc00::a description ARISTA05T2
 neighbor fc00::e remote-as 65200
 neighbor fc00::e peer-group TIER2_V6
 neighbor fc00::e description ARISTA07T2
 !
 address-family ipv4 unicast
  network 8.0.0.1/32 route-map HIDE_INTERNAL
  network 10.1.0.32/32
  redistribute connected route-map HIDE_INTERNAL
  neighbor INTERNAL_PEER_V4 soft-reconfiguration inbound
  neighbor INTERNAL_PEER_V4 route-map FROM_BGP_INTERNAL_PEER_V4 in
  neighbor INTERNAL_PEER_V4 route-map TO_BGP_INTERNAL_PEER_V4 out
  neighbor TIER2_V4 activate
  neighbor TIER2_V4 soft-reconfiguration inbound
  neighbor TIER2_V4 maximum-prefix 12000 90 warning-only
  neighbor TIER2_V4 route-map FROM_TIER2_V4 in
  neighbor TIER2_V4 route-map TO_TIER2_V4 out
  neighbor 10.1.0.4 activate
  neighbor 10.1.0.4 allowas-in 1
  neighbor 10.1.0.6 activate
  neighbor 10.1.0.6 allowas-in 1
  maximum-paths 64
 exit-address-family
 !
 address-family ipv6 unicast
  network 2603:10e2:400::1/128 route-map HIDE_INTERNAL
  network fc00:1::/64
  redistribute connected route-map HIDE_INTERNAL
  neighbor INTERNAL_PEER_V6 soft-reconfiguration inbound
  neighbor INTERNAL_PEER_V6 route-map FROM_BGP_INTERNAL_PEER_V6 in
  neighbor INTERNAL_PEER_V6 route-map TO_BGP_INTERNAL_PEER_V6 out
  neighbor TIER2_V6 activate
  neighbor TIER2_V6 soft-reconfiguration inbound
  neighbor TIER2_V6 maximum-prefix 8000 90 warning-only
  neighbor TIER2_V6 route-map FROM_TIER2_V6 in
  neighbor TIER2_V6 route-map TO_TIER2_V6 out
  neighbor 2603:10e2:400:1::9 activate
  neighbor 2603:10e2:400:1::9 allowas-in 1
  neighbor 2603:10e2:400:1::d activate
  neighbor 2603:10e2:400:1::d allowas-in 1
  maximum-paths 64
 exit-address-family
!
ip prefix-list PL_LoopbackV4 seq 5 permit 10.1.0.32/32
!
ipv6 prefix-list PL_LoopbackV6 seq 5 permit fc00:1::/64
!
bgp community-list standard UPSTREAM_PREFIX permit 8075:54000
!
route-map FROM_BGP_INTERNAL_PEER_V4 permit 100
!
route-map FROM_BGP_INTERNAL_PEER_V6 permit 1
 on-match next
 set ipv6 next-hop prefer-global 
!
route-map FROM_BGP_INTERNAL_PEER_V6 permit 100
!
route-map FROM_TIER2_V4 permit 100
 set community 8075:54000 additive
!
route-map FROM_TIER2_V6 permit 100
 on-match next
 set ipv6 next-hop prefer-global 
!
route-map FROM_TIER2_V6 permit 200
 set community 8075:54000 additive
!
route-map HIDE_INTERNAL permit 10
 on-match next
 set community no-export
!
route-map HIDE_INTERNAL permit 20
 set community 8075:9306 additive
!
route-map RM_SET_SRC permit 10
!
route-map RM_SET_SRC6 permit 10
!
route-map TO_BGP_INTERNAL_PEER_V4 permit 100
!
route-map TO_BGP_INTERNAL_PEER_V6 permit 100
!
route-map TO_TIER2_V4 deny 100
 match community UPSTREAM_PREFIX
!
route-map TO_TIER2_V4 permit 10000
!
route-map TO_TIER2_V6 deny 100
 match community UPSTREAM_PREFIX
!
route-map TO_TIER2_V6 permit 10000
!
line vty
!
end
"""

show_run_bgp_invalid_masic_no_namespace = \
"""
Error: -n/--namespace option required. provide namespace from list ['asic0', 'asic1', 'asic2', 'asic3', 'asic4', 'asic5'], or give '-n all'
"""

show_run_bgp_invalid_masic_wrong_namespace = \
"""
Error: -n/--namespace option required. provide namespace from list ['asic0', 'asic1', 'asic2', 'asic3', 'asic4', 'asic5'], or give '-n all'
"""
