# sfputilbase.py
#
# Base class for creating platform-specific SFP transceiver interfaces for SONiC
#

try:
    import abc
    import binascii
    import os
    import re
    import bcmshell
    from sonic_eeprom import eeprom_dts
    from sff8472 import sff8472InterfaceId
    from sff8472 import sff8472Dom
    from sff8436 import sff8436InterfaceId
    from sff8436 import sff8436Dom
except ImportError as e:
    raise ImportError("%s - required module not found" % str(e))


class SfpUtilError(Exception):
    """Base class for exceptions in this module."""
    pass


class DeviceTreeError(SfpUtilError):
    """Exception raised when unable to find SFP device attributes in the device tree."""
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class SfpUtilBase(object):
    """ Abstract base class for SFP utility. This class
    provides base EEPROM read attributes and methods common
    to most platforms."""

    __metaclass__ = abc.ABCMeta

    IDENTITY_EEPROM_ADDR = 0x50
    DOM_EEPROM_ADDR = 0x51
    SFP_DEVICE_TYPE = "24c02"

    # List to specify filter for sfp_ports
    # Needed by platforms like dni-6448 which
    # have only a subset of ports that support sfp
    sfp_ports = []

    # List of logical port names available on a system
    """ ["swp1", "swp5", "swp6", "swp7", "swp8" ...] """
    logical = []

    # dicts for easier conversions between logical, physical and bcm ports
    logical_to_bcm = {}
    logical_to_physical = {}

    """
    phytab_mappings stores mapping between logical, physical and bcm ports
    from /var/lib/cumulus/phytab
    For a normal non-ganged port:
    "swp8": {"bcmport": "xe4", "physicalport": [8], "phyid": ["0xb"]}

    For a ganged 40G/4 port:
    "swp1": {"bcmport": "xe0", "physicalport": [1, 2, 3, 4], "phyid": ["0x4", "0x5", "0x6", "0x7"]}

    For ganged 4x10G port:
    "swp52s0": {"bcmport": "xe51", "physicalport": [52], "phyid": ["0x48"]},
    "swp52s1": {"bcmport": "xe52", "physicalport": [52], "phyid": ["0x49"]},
    "swp52s2": {"bcmport": "xe53", "physicalport": [52], "phyid": ["0x4a"]},
    "swp52s3": {"bcmport": "xe54", "physicalport": [52], "phyid": ["0x4b"]},
    """
    phytab_mappings = {}

    physical_to_logical = {}
    physical_to_phyaddrs = {}

    port_to_i2cbus_mapping = None

    @abc.abstractproperty
    def port_start(self):
        """ Starting index of physical port range """
        pass

    @abc.abstractproperty
    def port_end(self):
        """ Ending index of physical port range """
        pass

    @abc.abstractproperty
    def qsfp_ports(self):
        """ Ending index of physical port range """
        pass

    @abc.abstractproperty
    def port_to_eeprom_mapping(self):
        """ Dictionary where key = physical port index (integer),
            value = path to SFP EEPROM device file (string) """
        pass

    def __init__(self):
        pass

    def _get_bcm_port(self, port_num):
        bcm_port = None

        logical_port = self.physical_to_logical.get(port_num)
        if logical_port is not None and len(logical_port) > 0:
            bcm_port = self.logical_to_bcm.get(logical_port[0])

        if bcm_port is None:
            bcm_port = "xe%d" % (port_num - 1)

        return bcm_port

    def _get_port_i2c_adapter_id(self, port_num):
        if len(self.port_to_i2cbus_mapping) == 0:
            return -1

        return self.port_to_i2cbus_mapping.get(port_num, -1)

    # Adds new sfp device on i2c adapter/bus via i2c bus new_device
    # sysfs attribute
    def _add_new_sfp_device(self, sysfs_sfp_i2c_adapter_path, devaddr):
        try:
            sysfs_nd_path = "%s/new_device" % sysfs_sfp_i2c_adapter_path

            # Write device address to new_device file
            nd_file = open(sysfs_nd_path, "w")
            nd_str = "%s %s" % (self.SFP_DEVICE_TYPE, hex(devaddr))
            nd_file.write(nd_str)
            nd_file.close()

        except Exception, err:
            print "Error writing to new device file: %s" % str(err)
            return 1
        else:
            return 0

    # Deletes sfp device on i2c adapter/bus via i2c bus delete_device
    # sysfs attribute
    def _delete_sfp_device(self, sysfs_sfp_i2c_adapter_path, devaddr):
        try:
            sysfs_nd_path = "%s/delete_device" % sysfs_sfp_i2c_adapter_path
            print devaddr > sysfs_nd_path

            # Write device address to delete_device file
            nd_file = open(sysfs_nd_path, "w")
            nd_file.write(devaddr)
            nd_file.close()
        except Exception, err:
            print "Error writing to new device file: %s" % str(err)
            return 1
        else:
            return 0

    # Returns 1 if SFP EEPROM found. Returns 0 otherwise
    def _sfp_eeprom_present(self, sysfs_sfp_i2c_client_eeprompath, offset):
        """Tries to read the eeprom file to determine if the
        device/sfp is present or not. If sfp present, the read returns
        valid bytes. If not, read returns error 'Connection timed out"""

        if not os.path.exists(sysfs_sfp_i2c_client_eeprompath):
            return False
        else:
            try:
                sysfsfile = open(sysfs_sfp_i2c_client_eeprompath, "rb")
                sysfsfile.seek(offset)
                sysfsfile.read(1)
            except IOError:
                return False
            except:
                return False
            else:
                return True

    # Read eeprom
    def _read_eeprom_devid(self, port_num, devid, offset):
        sysfs_i2c_adapter_base_path = "/sys/class/i2c-adapter"
        eeprom_raw = []
        num_bytes = 256

        for i in range(0, num_bytes):
            eeprom_raw.append("0x00")

        if port_num in self.port_to_eeprom_mapping.keys():
            sysfs_sfp_i2c_client_eeprom_path = self.port_to_eeprom_mapping[port_num]
        else:
            sysfs_i2c_adapter_base_path = "/sys/class/i2c-adapter"

            i2c_adapter_id = self._get_port_i2c_adapter_id(port_num)
            if i2c_adapter_id is None:
                print "Error getting i2c bus num"
                return None

            # Get i2c virtual bus path for the sfp
            sysfs_sfp_i2c_adapter_path = "%s/i2c-%s" % (sysfs_i2c_adapter_base_path,
                                                        str(i2c_adapter_id))

            # If i2c bus for port does not exist
            if not os.path.exists(sysfs_sfp_i2c_adapter_path):
                print "Could not find i2c bus %s. Driver not loaded?" % sysfs_sfp_i2c_adapter_path
                return None

            sysfs_sfp_i2c_client_path = "%s/%s-00%s" % (sysfs_sfp_i2c_adapter_path,
                                                        str(i2c_adapter_id),
                                                        hex(devid)[-2:])

            # If sfp device is not present on bus, Add it
            if not os.path.exists(sysfs_sfp_i2c_client_path):
                ret = self._add_new_sfp_device(
                        sysfs_sfp_i2c_adapter_path, devid)
                if ret != 0:
                    print "Error adding sfp device"
                    return None

            sysfs_sfp_i2c_client_eeprom_path = "%s/eeprom" % sysfs_sfp_i2c_client_path

        if not self._sfp_eeprom_present(sysfs_sfp_i2c_client_eeprom_path, offset):
            return None

        try:
            sysfsfile_eeprom = open(sysfs_sfp_i2c_client_eeprom_path, "rb")
            sysfsfile_eeprom.seek(offset)
            raw = sysfsfile_eeprom.read(num_bytes)
        except IOError:
            print "Error: reading sysfs file %s" % sysfs_sfp_i2c_client_eeprom_path
            return None

        try:
            for n in range(0, num_bytes):
                eeprom_raw[n] = hex(ord(raw[n]))[2:].zfill(2)
        except:
            return None

        try:
            sysfsfile_eeprom.close()
        except:
            return 0

        return eeprom_raw

    def _is_valid_port(self, port_num):
        if port_num >= self.port_start and port_num <= self.port_end:
            return True

        return False

    def read_porttab_mappings(self, porttabfile):
        logical = []
        logical_to_bcm = {}
        logical_to_physical = {}
        physical_to_logical = {}
        last_fp_port_index = 0
        last_portname = ""
        first = 1
        port_pos_in_file = 0
        parse_fmt_port_config_ini = False

        try:
            f = open(porttabfile)
        except:
            raise

        parse_fmt_port_config_ini = (os.path.basename(porttabfile) == "port_config.ini")

        # Read the porttab file and generate dicts
        # with mapping for future reference.
        # XXX: move the porttab
        # parsing stuff to a separate module, or reuse
        # if something already exists
        for line in f:
            line.strip()
            if re.search("^#", line) is not None:
                continue

            # Parsing logic for 'port_config.ini' file
            if (parse_fmt_port_config_ini):
                # bcm_port is not explicitly listed in port_config.ini format
                # Currently we assume ports are listed in numerical order according to bcm_port
                # so we use the port's position in the file (zero-based) as bcm_port
                portname = line.split()[0]

                bcm_port = str(port_pos_in_file)

                if len(line.split()) == 4:
                    fp_port_index = int(line.split()[3])
                else:
                    fp_port_index = portname.split("Ethernet").pop()
                    fp_port_index = int(fp_port_index.split("s").pop(0))/4
            else:  # Parsing logic for older 'portmap.ini' file
                (portname, bcm_port) = line.split("=")[1].split(",")[:2]

                fp_port_index = portname.split("Ethernet").pop()
                fp_port_index = int(fp_port_index.split("s").pop(0))/4

            if ((len(self.sfp_ports) > 0) and (fp_port_index not in self.sfp_ports)):
                continue

            if first == 1:
                # Initialize last_[physical|logical]_port
                # to the first valid port
                last_fp_port_index = fp_port_index
                last_portname = portname
                first = 0

            logical.append(portname)

            logical_to_bcm[portname] = "xe" + bcm_port
            logical_to_physical[portname] = [fp_port_index]
            if physical_to_logical.get(fp_port_index) is None:
                physical_to_logical[fp_port_index] = [portname]
            else:
                physical_to_logical[fp_port_index].append(
                    portname)

            if (fp_port_index - last_fp_port_index) > 1:
                # last port was a gang port
                for p in range(last_fp_port_index+1, fp_port_index):
                    logical_to_physical[last_portname].append(p)
                    if physical_to_logical.get(p) is None:
                        physical_to_logical[p] = [last_portname]
                    else:
                        physical_to_logical[p].append(last_portname)

            last_fp_port_index = fp_port_index
            last_portname = portname

            port_pos_in_file += 1

        self.logical = logical
        self.logical_to_bcm = logical_to_bcm
        self.logical_to_physical = logical_to_physical
        self.physical_to_logical = physical_to_logical

        """
        print "logical: " +  self.logical
        print "logical to bcm: " + self.logical_to_bcm
        print "logical to physical: " + self.logical_to_physical
        print "physical to logical: " + self.physical_to_logical
        """

    def read_phytab_mappings(self, phytabfile):
        logical = []
        phytab_mappings = {}
        physical_to_logical = {}
        physical_to_phyaddrs = {}

        try:
            f = open(phytabfile)
        except:
            raise

        # Read the phytab file and generate dicts
        # with mapping for future reference.
        # XXX: move the phytabfile
        # parsing stuff to a separate module, or reuse
        # if something already exists
        for line in f:
            line = line.strip()
            line = re.sub(r"\s+", " ", line)
            if len(line) < 4:
                continue
            if re.search("^#", line) is not None:
                continue
            (phy_addr, logical_port, bcm_port, type) = line.split(" ", 3)

            if re.match("xe", bcm_port) is None:
                continue

            lport = re.findall("swp(\d+)s*(\d*)", logical_port)
            if lport is not None:
                lport_tuple = lport.pop()
                physical_port = int(lport_tuple[0])
            else:
                physical_port = logical_port.split("swp").pop()
                physical_port = int(physical_port.split("s").pop(0))

            # Some platforms have a list of physical sfp ports
            # defined. If such a list exists, check to see if this
            # port is blacklisted
            if ((len(self.sfp_ports) > 0) and (physical_port not in self.sfp_ports)):
                continue

            if logical_port not in logical:
                logical.append(logical_port)

            if phytab_mappings.get(logical_port) is None:
                phytab_mappings[logical_port] = {}
                phytab_mappings[logical_port]['physicalport'] = []
                phytab_mappings[logical_port]['phyid'] = []
                phytab_mappings[logical_port]['type'] = type

            # If the port is 40G/4 ganged, there will be multiple
            # physical ports corresponding to the logical port.
            # Generate the next physical port number in the series
            # and append it to the list
            tmp_physical_port_list = phytab_mappings[logical_port]['physicalport']
            if (type == "40G/4" and physical_port in tmp_physical_port_list):
                # Aha!...ganged port
                new_physical_port = tmp_physical_port_list[-1] + 1
            else:
                new_physical_port = physical_port

            if (new_physical_port not in phytab_mappings[logical_port]['physicalport']):
                phytab_mappings[logical_port]['physicalport'].append(new_physical_port)
            phytab_mappings[logical_port]['phyid'].append(phy_addr)
            phytab_mappings[logical_port]['bcmport'] = bcm_port

            # Store in physical_to_logical dict
            if physical_to_logical.get(new_physical_port) is None:
                physical_to_logical[new_physical_port] = []
            physical_to_logical[new_physical_port].append(logical_port)

            # Store in physical_to_phyaddrs dict
            if physical_to_phyaddrs.get(new_physical_port) is None:
                physical_to_phyaddrs[new_physical_port] = []
            physical_to_phyaddrs[new_physical_port].append(phy_addr)

        self.logical = logical
        self.phytab_mappings = phytab_mappings
        self.physical_to_logical = physical_to_logical
        self.physical_to_phyaddrs = physical_to_phyaddrs

        """
        pp = pprint.PrettyPrinter(indent=4)
        pp.pprint(self.phytab_mappings)

        print "logical: " +  self.logical
        print "logical to bcm: " +  self.logical_to_bcm
        print "phytab mappings: " + self.phytab_mappings
        print "physical to logical: " + self.physical_to_logical
        print "physical to phyaddrs: " + self.physical_to_phyaddrs
        """

    def get_physical_to_logical(self, port_num):
        """Returns list of logical ports for the given physical port"""

        return self.physical_to_logical[port_num]

    def get_logical_to_physical(self, logical_port):
        """Returns list of physical ports for the given logical port"""

        return self.logical_to_physical[logical_port]

    def is_logical_port(self, port):
        if port in self.logical:
            return 1
        else:
            return 0

    def is_logical_port_ganged_40_by_4(self, logical_port):
        physical_port_list = self.logical_to_physical[logical_port]
        if len(physical_port_list) > 1:
            return 1
        else:
            return 0

    def is_physical_port_ganged_40_by_4(self, port_num):
        logical_port = self.get_physical_to_logical(port_num)
        if logical_port is not None:
            return self.is_logical_port_ganged_40_by_4(logical_port[0])

        return 0

    def get_physical_port_phyid(self, physical_port):
        """Returns list of phyids for a physical port"""

        return self.physical_to_phyaddrs[physical_port]

    def get_40_by_4_gangport_phyid(self, logical_port):
        """ Return the first ports phyid. One use case for
            this is to address the gang port in single mode """

        phyid_list = self.phytab_mappings[logical_port]['phyid']
        if phyid_list is not None:
            return phyid_list[0]

    def is_valid_sfputil_port(self, port):
        if port.startswith(""):
            if self.is_logical_port(port):
                return 1
            else:
                return 0
        else:
            return 0

    def read_port_mappings(self):
        if self.port_to_eeprom_mapping is None or self.port_to_i2cbus_mapping is None:
            self.read_port_to_eeprom_mapping()
            self.read_port_to_i2cbus_mapping()

    def read_port_to_eeprom_mapping(self):
        eeprom_dev = "/sys/class/eeprom_dev"
        self.port_to_eeprom_mapping = {}
        for eeprom_path in [os.path.join(eeprom_dev, x) for x in os.listdir(eeprom_dev)]:
            eeprom_label = open(os.path.join(eeprom_path, "label"), "r").read().strip()
            if eeprom_label.startswith("port"):
                port = int(eeprom_label[4:])
                self.port_to_eeprom_mapping[port] = os.path.join(eeprom_path, "device", "eeprom")

    def read_port_to_i2cbus_mapping(self):
        if self.port_to_i2cbus_mapping is not None and len(self.port_to_i2cbus_mapping) > 0:
            return

        self.eep_dict = eeprom_dts.get_dev_attr_from_dtb(['sfp'])
        if len(self.eep_dict) == 0:
            return

        # XXX: there should be a cleaner way to do this.
        i2cbus_list = []
        self.port_to_i2cbus_mapping = {}
        s = self.port_start
        for sfp_sysfs_path, attrs in sorted(self.eep_dict.iteritems()):
            i2cbus = attrs.get("dev-id")
            if i2cbus is None:
                raise DeviceTreeError("No 'dev-id' attribute found in attr: %s" % repr(attrs))
            if i2cbus in i2cbus_list:
                continue
            i2cbus_list.append(i2cbus)
            self.port_to_i2cbus_mapping[s] = i2cbus
            s += 1
            if s > self.port_end:
                break

    def get_eeprom_raw(self, port_num):
        # Read interface id EEPROM at addr 0x50
        return self._read_eeprom_devid(port_num, self.IDENTITY_EEPROM_ADDR, 0)

    def get_eeprom_dom_raw(self, port_num):
        if port_num in self.qsfp_ports:
            # QSFP DOM EEPROM is also at addr 0x50 and thus also stored in eeprom_ifraw
            return None
        else:
            # Read dom eeprom at addr 0x51
            return self._read_eeprom_devid(port_num, self.DOM_EEPROM_ADDR, 0)

    def get_eeprom_dict(self, port_num):
        """Returns dictionary of interface and dom data.
        format: {<port_num> : {'interface': {'version' : '1.0', 'data' : {...}},
                               'dom' : {'version' : '1.0', 'data' : {...}}}}
        """

        sfp_data = {}

        eeprom_ifraw = self.get_eeprom_raw(port_num)
        eeprom_domraw = self.get_eeprom_dom_raw(port_num)

        if eeprom_ifraw is None:
            return None

        if port_num in self.qsfp_ports:
            sfpi_obj = sff8436InterfaceId(eeprom_ifraw)
            if sfpi_obj is not None:
                sfp_data['interface'] = sfpi_obj.get_data_pretty()
            # For Qsfp's the dom data is part of eeprom_if_raw
            # The first 128 bytes

            sfpd_obj = sff8436Dom(eeprom_ifraw)
            if sfpd_obj is not None:
                sfp_data['dom'] = sfpd_obj.get_data_pretty()
            return sfp_data

        sfpi_obj = sff8472InterfaceId(eeprom_ifraw)
        if sfpi_obj is not None:
            sfp_data['interface'] = sfpi_obj.get_data_pretty()
            cal_type = sfpi_obj.get_calibration_type()

        if eeprom_domraw is not None:
            sfpd_obj = sff8472Dom(eeprom_domraw, cal_type)
            if sfpd_obj is not None:
                sfp_data['dom'] = sfpd_obj.get_data_pretty()

        return sfp_data

    @abc.abstractmethod
    def get_presence(self, port_num):
        """
        :param port_num: Integer, index of physical port
        :returns: Boolean, True if tranceiver is present, False if not
        """
        return

    @abc.abstractmethod
    def get_low_power_mode(self, port_num):
        """
        :param port_num: Integer, index of physical port
        :returns: Boolean, True if low-power mode enabled, False if disabled
        """
        return

    @abc.abstractmethod
    def set_low_power_mode(self, port_num, lpmode):
        """
        :param port_num: Integer, index of physical port
        :param lpmode: Boolean, True to enable low-power mode, False to disable it
        :returns: Boolean, True if low-power mode set successfully, False if not
        """
        return

    @abc.abstractmethod
    def reset(self, port_num):
        """
        :param port_num: Integer, index of physical port
        :returns: Boolean, True if reset successful, False if not
        """
        return


class SfpUtilBcmMdio(SfpUtilBase):
    """Provides SFP+/QSFP EEPROM access via BCM MDIO methods"""

    __metaclass__ = abc.ABCMeta

    IDENTITY_EEPROM_ADDR = 0xa000
    DOM_EEPROM_ADDR = 0xa200

    # Register Offsets and Constants
    EEPROM_ADDR = 0x8007
    TWOWIRE_CONTROL_REG = 0x8000
    TWOWIRE_CONTROL_ENABLE_MASK = 0x8000
    TWOWIRE_CONTROL_READ_CMD_MASK = 0x0002
    TWOWIRE_CONTROL_CMD_STATUS_MASK = 0xc
    TWOWIRE_CONTROL_CMD_STATUS_IDLE = 0x0
    TWOWIRE_CONTROL_CMD_STATUS_SUCCESS = 0x4
    TWOWIRE_CONTROL_CMD_STATUS_BUSY = 0x8
    TWOWIRE_CONTROL_CMD_STATUS_FAILED = 0xc

    TWOWIRE_INTERNAL_ADDR_REG = 0x8004
    TWOWIRE_INTERNAL_ADDR_REGVAL = EEPROM_ADDR

    TWOWIRE_TRANSFER_SIZE_REG = 0x8002

    TWOWIRE_TRANSFER_SLAVEID_ADDR_REG = 0x8005

    # bcmcmd handle
    bcm = None

    # With BCM MDIO, we do not use port_to_eeprom_mapping
    @property
    def port_to_eeprom_mapping(self):
        return None

    def __init__(self):
        try:
            self.bcm = bcmshell.bcmshell()
        except:
            raise RuntimeError("unable to obtain exclusive access to hardware")

        SfpUtilBase.__init__(self)

    def _read_eeprom_devid(self, port_num, devid, offset):
        if port_num in self.qsfp_ports:
            # Get QSFP page 0 and page 1 eeprom
            # XXX: Need to have a way to select page 2,3,4 for dom eeprom
            eeprom_raw_1 = self._read_eeprom_devid_page_size(port_num, devid, 0, 128, offset)
            eeprom_raw_2 = self._read_eeprom_devid_page_size(port_num, devid, 1, 128, offset)
            if eeprom_raw_1 is None or eeprom_raw_2 is None:
                return None
            return eeprom_raw_1 + eeprom_raw_2
        else:
            # Read 256 bytes of data from specified devid
            return self._read_eeprom_devid_page_size(port_num, devid, 0, 256, offset)

    def _read_eeprom_devid_page_size(self, port_num, devid, page, size, offset):
        """
        Read data from specified devid using the bcmshell's 'phy' command..

        Use port_num to identify which EEPROM to read.
        """

        TWOWIRE_TRANSFER_SLAVEID_ADDR = 0x0001 | devid | page << 8

        eeprom_raw = None
        num_bytes = size
        phy_addr = None
        bcm_port = None

        ganged_40_by_4 = self.is_physical_port_ganged_40_by_4(port_num)
        if ganged_40_by_4 == 1:
            # In 40G/4 gang mode, the port is by default configured in
            # single mode. To read the individual sfp details, the port
            # needs to be in quad mode. Set the port mode to quad mode
            # for the duration of this function. Switch it back to
            # original state after we are done
            logical_port = self.get_physical_to_logical(port_num)
            gang_phyid = self.get_40_by_4_gangport_phyid(logical_port[0])

            # Set the gang port to quad mode
            chip_mode_reg = 0xc805
            chip_mode_mask = 0x1

            # bcmcmd phy raw c45 <phyid> <device> <mode_reg_addr> <mode_mask>
            # Ex: bcmcmd phy raw c45 0x4 1 0xc805 0x0070
            gang_chip_mode_orig = self._phy_reg_get(gang_phyid, None, chip_mode_reg)
            quad_mode_mask = gang_chip_mode_orig & ~(chip_mode_mask)
            self._phy_reg_set(gang_phyid, None, chip_mode_reg, quad_mode_mask)

            phy_addr = self.get_physical_port_phyid(port_num)[0]

        if phy_addr is None:
            bcm_port = self._get_bcm_port(port_num)

        # Enable 2 wire master
        regval = self._phy_reg_get(phy_addr, bcm_port, self.TWOWIRE_CONTROL_REG)
        regval = regval | self.TWOWIRE_CONTROL_ENABLE_MASK
        self._phy_reg_set(phy_addr, bcm_port, self.TWOWIRE_CONTROL_REG, regval)

        # Set 2wire internal addr reg
        self._phy_reg_set(phy_addr, bcm_port,
                          self.TWOWIRE_INTERNAL_ADDR_REG,
                          self.TWOWIRE_INTERNAL_ADDR_REGVAL)

        # Set transfer count
        self._phy_reg_set(phy_addr, bcm_port,
                          self.TWOWIRE_TRANSFER_SIZE_REG, size)

        # Set eeprom dev id
        self._phy_reg_set(phy_addr, bcm_port,
                          self.TWOWIRE_TRANSFER_SLAVEID_ADDR_REG,
                          TWOWIRE_TRANSFER_SLAVEID_ADDR)

        # Initiate read
        regval = self._phy_reg_get(phy_addr, bcm_port, self.TWOWIRE_CONTROL_REG)
        regval = regval | self.TWOWIRE_CONTROL_READ_CMD_MASK
        self._phy_reg_set(phy_addr, bcm_port, self.TWOWIRE_CONTROL_REG, regval)

        # Read command status
        regval = self._phy_reg_get(phy_addr, bcm_port, self.TWOWIRE_CONTROL_REG)
        cmd_status = regval & self.TWOWIRE_CONTROL_CMD_STATUS_MASK

        # poll while command busy
        poll_count = 0
        while cmd_status == self.TWOWIRE_CONTROL_CMD_STATUS_BUSY:
            regval = self._phy_reg_get(phy_addr, bcm_port, self.TWOWIRE_CONTROL_REG)
            cmd_status = regval & self.TWOWIRE_CONTROL_CMD_STATUS_MASK
            poll_count += 1
            if poll_count > 500:
                raise RuntimeError("Timeout waiting for two-wire transaction completion")

        if cmd_status == self.TWOWIRE_CONTROL_CMD_STATUS_SUCCESS:
            # Initialize return buffer
            eeprom_raw = []
            for i in range(0, num_bytes):
                eeprom_raw.append("0x00")

            # Read into return buffer
            for i in range(0, num_bytes):
                addr = self.EEPROM_ADDR + i
                out = self._phy_reg_get(phy_addr, bcm_port, addr)
                eeprom_raw[i] = hex(out)[2:].zfill(2)

        if ganged_40_by_4 == 1:
            # Restore original ganging mode
            self._phy_reg_set(gang_phyid, bcm_port,
                              chip_mode_reg, gang_chip_mode_orig)

        return eeprom_raw

    def _phy_reg_get(self, phy_addr, bcm_port, regaddr):
        if phy_addr is not None:
            cmd = "phy raw c45 %s 1 0x%x" % (phy_addr, regaddr)
        else:
            cmd = "phy %s 0x%x 1" % (bcm_port, regaddr)

        try:
            out = self.bcm.run(cmd)
        except:
            raise RuntimeError("Error getting access to hardware - bcm cmd '%s' failed" % cmd)

        return int(out.split().pop(), 16)

    def _phy_reg_set(self, phy_addr, bcm_port, regaddr, regval):
        if phy_addr is not None:
            cmd = "phy raw c45 %s 1 0x%x 0x%x" % (phy_addr, regaddr, regval)
        else:
            cmd = "phy %s 0x%x 1 0x%x" % (bcm_port, regaddr, regval)

        try:
            return self.bcm.run(cmd)
        except:
            raise RuntimeError("Error getting access to hardware - bcm cmd '%s' failed" % cmd)
