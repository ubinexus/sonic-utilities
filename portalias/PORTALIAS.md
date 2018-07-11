#Portalias
Most of the hardware vendors port naming scheme vary with respective to the sonic default interface naming scheme. This feature helps the user to get the show, config command outputs in hardware vendor naming scheme. This documents targets on the design schema of show commands output in  vendor interface names.

show commands depends  SONiC utilites
---------------------------------------------
Below mentioned show commands print results by using SONiC utitlites as input. For the portalias feature we need to print the results with alias name interfaces for all the below mentioned commands.

```
show portchannel-----------------------teamshow -w
show interface transceiver eeprom-----sfputil show eeprom -w
show interface transceiver presence----sfputil show presence -w
show interface transceiver lpmode-----sfputil show lpmode -w
show lldp table--------------------------lldpshow -w
show queue counters-------------------queuestat -w
show mac--------------------------------fdbshow -w
show vlan config------------------------in-built code 
show acl---------------------------------acl-loader -w
show pfc counters----------------------pfcstat -w
show counters--------------------------portstat -w
```
To achieve this introduced a switch -w to print the results in alias interface name.

    parser.add_argument('-w', '--alias', action='store_true', help='Show the queue counters for alias interfaces')
    args = parser.parse_args()


#####Example: show queue counters 
- In this command each interface has 9+9=18 counters. So, by introducing -w alias switch in queuestat we fetch the alias interface from APPL_DB database. In this approach we fetch the equivalent alias interface names from database. So, the results are quick and execution time is mere equivalent to the default interface results.

    The same approach is propogated to all possible other commands for quick results.

admin@sonic:~$ queuestat -w

~
        Port    TxQ    Counter/pkts    Counter/bytes    Drop/pkts    Drop/bytes
--------------  -----  --------------  ---------------  -----------  ------------
hundredGigE1/2    UC0               0                0            0             0
hundredGigE1/2    UC1               0                0            0             0
hundredGigE1/2    UC2               0                0            0             0
hundredGigE1/2    UC3               0                0            0             0
hundredGigE1/2    UC4               0                0            0             0
hundredGigE1/2    UC5               0                0            0             0
hundredGigE1/2    UC6               0                0            0             0
hundredGigE1/2    UC7               0                0            0             0
hundredGigE1/2    UC8               0                0            0             0
hundredGigE1/2    UC9               0                0            0             0
hundredGigE1/2    MC0               0                0            0             0
hundredGigE1/2    MC1               0                0            0             0
hundredGigE1/2    MC2               0                0            0             0
hundredGigE1/2    MC3               0                0            0             0
hundredGigE1/2    MC4               0                0            0             0
hundredGigE1/2    MC5               0                0            0             0
hundredGigE1/2    MC6               0                0            0             0
hundredGigE1/2    MC7               0                0            0             0
hundredGigE1/2    MC8               0                0            0             0
hundredGigE1/2    MC9               0                0            0             0
~

Timing issues:
--------------
 For some commands the interface name list is too big. Extracting alias name for each interface via sonic-cffgen utility or parsing affects the execution time badly. So, this switch method is introduced to keep the timing within limits.

show commands depends LINUX utilites.
----------------------------------------

- Below mentioned show commands print the results by depending on the Linux commands. Unlike above here we left very less option to print the results in alias interface names. So, we need to design a framework to do parse all possible command outputs with alias interface names.

```
show summary------------------- ifconfig
show arp------------------------- arp
show ip route-------------------- vtysh -c "show ip route"
show ipv6 route------------------ vtysh -c "show ipv6 route"
show lldp neigh------------------ lldpctl in docker
show vlan brief------------------- brctl show
```
