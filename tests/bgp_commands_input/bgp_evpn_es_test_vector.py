bgp_evpn_es_output = """
Type: L local, R remote, N non-DF
ESI                            Type    ES Interface    status    Peers
-----------------------------  ------  --------------  --------  ------------
03:00:11:22:33:44:55:00:00:03  LR      PortChannel0    up        10.127.127.2
"""

bgp_evpn_es_detail_output = """
ESI: 03:00:11:22:33:44:55:00:00:03
 Type: Local,Remote
 Interface: PortChannel0
 State: up
 DF status: is DF
 DF preference: 32767
 Nexthop group: 536870913
 VTEPs:
     10.127.127.2 df_alg: preference df_pref: 32767 nh: 268435458
     10.127.127.3 df_alg: preference df_pref: 32767 nh: 268435458
"""

bgp_evpn_es_evi_output = """
Flags: L local, R remote, I inconsistent
VTEP-Flags: E EAD-per-ES, V EAD-per-EVI
  VNI  ESI                            Flags    VTEPs
-----  -----------------------------  -------  ---------------
 1000  03:00:11:22:33:44:55:00:00:03  LR       10.127.127.2(V)
"""

bgp_evpn_es_evi_2vtep_output = """
Flags: L local, R remote, I inconsistent
VTEP-Flags: E EAD-per-ES, V EAD-per-EVI
VNI    ESI                            Flags    VTEPs
-----  -----------------------------  -------  -----------
1000   00:11:22:33:44:55:66:77:88:99  R        1.1.1.1(VE)
                                               2.2.2.2(VE)
"""

bgp_evpn_route_output = """
BGP table version is 3, local router ID is 10.127.127.1
Status codes: s suppressed, d damped, h history, * valid, > best, i - internal
Origin codes: i - IGP, e - EGP, ? - incomplete
EVPN type-1 prefix: [1]:[EthTag]:[ESI]:[IPlen]:[VTEP-IP]:[Frag-id]
EVPN type-2 prefix: [2]:[EthTag]:[MAClen]:[MAC]:[IPlen]:[IP]
EVPN type-3 prefix: [3]:[EthTag]:[IPlen]:[OrigIP]
EVPN type-4 prefix: [4]:[ESI]:[IPlen]:[OrigIP]
EVPN type-5 prefix: [5]:[EthTag]:[IPlen]:[IP]

   Network          Next Hop            Metric LocPrf Weight Path
                    Extended Community
Route Distinguisher: 10.127.127.1:2
 *> [1]:[0]:[03:00:11:22:33:44:55:00:00:03]:[128]:[::]:[0]
                    10.127.127.1                       32768 i
                    ET:8 RT:65100:1000
 *> [2]:[0]:[48]:[0c:5d:d9:3b:00:00]
                    10.127.127.1                       32768 i
                    ET:8 RT:65100:1000
 *> [3]:[0]:[32]:[10.127.127.1]
                    10.127.127.1                       32768 i
                    ET:8 RT:65100:1000
Route Distinguisher: 10.127.127.2:2
 *>i[1]:[0]:[03:00:11:22:33:44:55:00:00:03]:[32]:[0.0.0.0]:[0]
                    10.127.127.2                  100      0 i
                    RT:65100:1000 ET:8
 *>i[2]:[0]:[48]:[0c:8f:8b:e6:00:00]
                    10.127.127.2                  100      0 i
                    RT:65100:1000 ET:8
 *>i[3]:[0]:[32]:[10.127.127.2]
                    10.127.127.2                  100      0 i
                    RT:65100:1000 ET:8
Route Distinguisher: 10.127.127.3:2
 *>i[2]:[0]:[48]:[0c:1d:5c:21:00:01]
                    10.127.127.3                  100      0 i
                    RT:65100:1000 ET:8
 *>i[2]:[0]:[48]:[0c:1d:5c:21:00:01]:[128]:[fe80::e1d:5cff:fe21:1]
                    10.127.127.3                  100      0 i
                    RT:65100:1000 ET:8
 *>i[3]:[0]:[32]:[10.127.127.3]
                    10.127.127.3                  100      0 i
                    RT:65100:1000 ET:8

Displayed 9 prefixes (9 paths)
"""


def mock_show_bgp_evpn_route_single_asic(request):
    if request.param == 'show_bgp_evpn_route':
        return bgp_evpn_route_output
    else:
        return ""


testData = {
    'bgp_evpn_es': {
        'name': 'es',
        'args': [],
        'rc': 0,
        'rc_output': bgp_evpn_es_output
    },
    'bgp_evpn_es_detail': {
        'name': 'es',
        'args': ['--detail'],
        'rc': 0,
        'rc_output': bgp_evpn_es_detail_output
    },
    'bgp_evpn_es_evi': {
        'name': 'es-evi',
        'args': [],
        'rc': 0,
        'rc_output': bgp_evpn_es_evi_output
    },
    'bgp_evpn_es_evi_2vtep': {
        'name': 'es-evi',
        'args': [],
        'rc': 0,
        'rc_output': bgp_evpn_es_evi_2vtep_output
    },
    'bgp_evpn_route': {
        'name': 'route',
        'args': [],
        'rc': 0,
        'rc_output': '\nNamespace: default\n' + bgp_evpn_route_output + '\n'
    },
}
