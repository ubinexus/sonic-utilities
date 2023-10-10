"""
Module holding the correct values for show CLI command outputs for the hash_test.py
"""

show_hash_empty="""\
ECMP HASH    ECMP HASH ALGORITHM
-----------  ---------------------

LAG HASH    LAG HASH ALGORITHM
----------  --------------------
"""

show_hash_ecmp="""\
ECMP HASH          ECMP HASH ALGORITHM
-----------------  ---------------------
DST_MAC            CRC
SRC_MAC
ETHERTYPE
IP_PROTOCOL
DST_IP
SRC_IP
L4_DST_PORT
L4_SRC_PORT
INNER_DST_MAC
INNER_SRC_MAC
INNER_ETHERTYPE
INNER_IP_PROTOCOL
INNER_DST_IP
INNER_SRC_IP
INNER_L4_DST_PORT
INNER_L4_SRC_PORT

LAG HASH    LAG HASH ALGORITHM
----------  --------------------
N/A         N/A
"""

show_hash_lag="""\
ECMP HASH    ECMP HASH ALGORITHM
-----------  ---------------------
N/A          N/A

LAG HASH           LAG HASH ALGORITHM
-----------------  --------------------
DST_MAC            XOR
SRC_MAC
ETHERTYPE
IP_PROTOCOL
DST_IP
SRC_IP
L4_DST_PORT
L4_SRC_PORT
INNER_DST_MAC
INNER_SRC_MAC
INNER_ETHERTYPE
INNER_IP_PROTOCOL
INNER_DST_IP
INNER_SRC_IP
INNER_L4_DST_PORT
INNER_L4_SRC_PORT
"""

show_hash_ecmp_and_lag="""\
ECMP HASH          ECMP HASH ALGORITHM
-----------------  ---------------------
DST_MAC            CRC
SRC_MAC
ETHERTYPE
IP_PROTOCOL
DST_IP
SRC_IP
L4_DST_PORT
L4_SRC_PORT
INNER_DST_MAC
INNER_SRC_MAC
INNER_ETHERTYPE
INNER_IP_PROTOCOL
INNER_DST_IP
INNER_SRC_IP
INNER_L4_DST_PORT
INNER_L4_SRC_PORT

LAG HASH           LAG HASH ALGORITHM
-----------------  --------------------
DST_MAC            XOR
SRC_MAC
ETHERTYPE
IP_PROTOCOL
DST_IP
SRC_IP
L4_DST_PORT
L4_SRC_PORT
INNER_DST_MAC
INNER_SRC_MAC
INNER_ETHERTYPE
INNER_IP_PROTOCOL
INNER_DST_IP
INNER_SRC_IP
INNER_L4_DST_PORT
INNER_L4_SRC_PORT
"""

show_hash_capabilities_no="""\
ECMP HASH        ECMP HASH ALGORITHM
---------------  ---------------------
no capabilities  no capabilities

LAG HASH         LAG HASH ALGORITHM
---------------  --------------------
no capabilities  no capabilities
"""

show_hash_capabilities_na="""\
ECMP HASH    ECMP HASH ALGORITHM
-----------  ---------------------
N/A          N/A

LAG HASH    LAG HASH ALGORITHM
----------  --------------------
N/A         N/A
"""

show_hash_capabilities_empty="""\
ECMP HASH      ECMP HASH ALGORITHM
-------------  ---------------------
not supported  not supported

LAG HASH       LAG HASH ALGORITHM
-------------  --------------------
not supported  not supported
"""

show_hash_capabilities_ecmp="""\
ECMP HASH          ECMP HASH ALGORITHM
-----------------  ---------------------
IN_PORT            CRC
DST_MAC            XOR
SRC_MAC            RANDOM
ETHERTYPE          CRC_32LO
VLAN_ID            CRC_32HI
IP_PROTOCOL        CRC_CCITT
DST_IP             CRC_XOR
SRC_IP
L4_DST_PORT
L4_SRC_PORT
INNER_DST_MAC
INNER_SRC_MAC
INNER_ETHERTYPE
INNER_IP_PROTOCOL
INNER_DST_IP
INNER_SRC_IP
INNER_L4_DST_PORT
INNER_L4_SRC_PORT

LAG HASH       LAG HASH ALGORITHM
-------------  --------------------
not supported  not supported
"""

show_hash_capabilities_lag="""\
ECMP HASH      ECMP HASH ALGORITHM
-------------  ---------------------
not supported  not supported

LAG HASH           LAG HASH ALGORITHM
-----------------  --------------------
IN_PORT            CRC
DST_MAC            XOR
SRC_MAC            RANDOM
ETHERTYPE          CRC_32LO
VLAN_ID            CRC_32HI
IP_PROTOCOL        CRC_CCITT
DST_IP             CRC_XOR
SRC_IP
L4_DST_PORT
L4_SRC_PORT
INNER_DST_MAC
INNER_SRC_MAC
INNER_ETHERTYPE
INNER_IP_PROTOCOL
INNER_DST_IP
INNER_SRC_IP
INNER_L4_DST_PORT
INNER_L4_SRC_PORT
"""

show_hash_capabilities_ecmp_and_lag="""\
ECMP HASH          ECMP HASH ALGORITHM
-----------------  ---------------------
IN_PORT            CRC
DST_MAC            XOR
SRC_MAC            RANDOM
ETHERTYPE          CRC_32LO
VLAN_ID            CRC_32HI
IP_PROTOCOL        CRC_CCITT
DST_IP             CRC_XOR
SRC_IP
L4_DST_PORT
L4_SRC_PORT
INNER_DST_MAC
INNER_SRC_MAC
INNER_ETHERTYPE
INNER_IP_PROTOCOL
INNER_DST_IP
INNER_SRC_IP
INNER_L4_DST_PORT
INNER_L4_SRC_PORT

LAG HASH           LAG HASH ALGORITHM
-----------------  --------------------
IN_PORT            CRC
DST_MAC            XOR
SRC_MAC            RANDOM
ETHERTYPE          CRC_32LO
VLAN_ID            CRC_32HI
IP_PROTOCOL        CRC_CCITT
DST_IP             CRC_XOR
SRC_IP
L4_DST_PORT
L4_SRC_PORT
INNER_DST_MAC
INNER_SRC_MAC
INNER_ETHERTYPE
INNER_IP_PROTOCOL
INNER_DST_IP
INNER_SRC_IP
INNER_L4_DST_PORT
INNER_L4_SRC_PORT
"""
