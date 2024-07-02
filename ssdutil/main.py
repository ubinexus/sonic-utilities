#!/usr/bin/env python3
#
# main.py
#
# Command-line utility to check SSD health and parameters
#

try:
    import os
    import sys
    import argparse
    import json
    import psutil
    from blkinfo import BlkDiskInfo

    from sonic_py_common import device_info, logger
except ImportError as e:
    raise ImportError("%s - required module not found" % str(e))

DEFAULT_DEVICE="/dev/sda"
SYSLOG_IDENTIFIER = "ssdutil"
DISK_TYPE_SSD = "sata"

# Global logger instance
log = logger.Logger(SYSLOG_IDENTIFIER)

def get_default_disk():
    """Check default disk"""
    default_device = DEFAULT_DEVICE
    host_mnt = '/host'
    host_partition = None
    partitions = psutil.disk_partitions()

    for parts in partitions:
        if parts.mountpoint == "/host":
            host_partition = parts
            break

    disk_major = os.major(os.stat(host_partition.device).st_rdev)
    filters = {
       'maj:min': '{}:0'.format(disk_major)
    }

    myblkd = BlkDiskInfo()
    my_filtered_disks = myblkd.get_disks(filters)
    json_output = eval(my_filtered_disks)[0]
    blkdev = json_output['name']
    disk_type = json_output['tran']
    default_device = os.path.join("/dev/", blkdev)

    return default_device, disk_type

def import_ssd_api(diskdev):
    """
    Loads platform specific or generic ssd_util module from source
    Raises an ImportError exception if none of above available

    Returns:
        Instance of the class with SSD API implementation (vendor or generic)
    """

    # try to load platform specific module
    try:
        platform_path, _ = device_info.get_paths_to_platform_and_hwsku_dirs()
        platform_plugins_path = os.path.join(platform_path, "plugins")
        sys.path.append(os.path.abspath(platform_plugins_path))
        from ssd_util import SsdUtil
    except ImportError as e:
        log.log_warning("Platform specific SsdUtil module not found. Falling down to the generic implementation")
        try:
            from sonic_platform_base.sonic_ssd.ssd_generic import SsdUtil
        except ImportError as e:
            try:
                from sonic_platform_base.sonic_storage.ssd import SsdUtil
            except ImportError as e:
                log.log_error("Failed to import default SsdUtil. Error: {}".format(str(e)), True)
                raise e

    return SsdUtil(diskdev)

def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

# ==================== Entry point ====================
def ssdutil():
    if os.geteuid() != 0:
        print("Root privileges are required for this operation")
        sys.exit(1)

    parser = argparse.ArgumentParser()
    (default_device , disk_type) = get_default_disk()
    parser.add_argument("-d", "--device", help="Device name to show health info", default=default_device)
    parser.add_argument("-v", "--verbose", action="store_true", default=False, help="Show verbose output (some additional parameters)")
    parser.add_argument("-e", "--vendor", action="store_true", default=False, help="Show vendor output (extended output if provided by platform vendor)")
    args = parser.parse_args()

    if DISK_TYPE_SSD not in disk_type:
        print("Disk type is not SSD")

    ssd = import_ssd_api(args.device)

    print("Device Model : {}".format(ssd.get_model()))
    if args.verbose:
        print("Firmware     : {}".format(ssd.get_firmware()))
        print("Serial       : {}".format(ssd.get_serial()))
    print("Health       : {}{}".format(ssd.get_health(),      "%" if is_number(ssd.get_health()) else ""))
    print("Temperature  : {}{}".format(ssd.get_temperature(), "C" if is_number(ssd.get_temperature()) else ""))
    if args.vendor:
        print(ssd.get_vendor_output())

if __name__ == '__main__':
    ssdutil()
