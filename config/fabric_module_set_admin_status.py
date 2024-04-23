#!/usr/bin/env python3
#
# Copyright (c) 2024, Nokia
# All rights reserved.

import re
import subprocess
import time
from swsscommon.swsscommon import SonicV2Connector
from sonic_py_common.logger import Logger
from platform_ndk import nokia_common

sfm_hw_slot_mapping = {
    0: 15,
    1: 16,
    2: 17,
    3: 18,
    4: 19,
    5: 20,
    6: 21,
    7: 22
}

# Name: fabric_module_set_admin_status.py, version: 1.0
# Syntax: fabric_module_set_admin_status <module_name> <up/down>
def fabric_module_set_admin_status(module, state):
    logger = Logger("fabric_module_set_admin_status.py")
    logger.set_min_log_priority_info()
   
    if not module.startswith("FABRIC-CARD"):
        logger.log_warning("Failed to set {} state. Admin state can only be set on Fabric module.".format(module))
        return

    if (state != "up" and state != "down"):
        logger.log_warning("Failed to set {}. Admin state can only be set to up or down.".format(state))
        return

    num = int(re.search(r"(\d+)$", module).group())
    chassisdb = SonicV2Connector(host="127.0.0.1")
    chassisdb.connect("CHASSIS_STATE_DB")

    if state == "down":
        services_list = chassisdb.keys("CHASSIS_STATE_DB", "CHASSIS_FABRIC_ASIC_TABLE*")
        asic_list = []
        for service in services_list:
            name = chassisdb.get("CHASSIS_STATE_DB",service,"name")
            if name == module:
                asic_id = int(re.search(r"(\d+)$", service).group())
                asic_list.append(asic_id)

        logger.log_info("Shutting down chassis module {}".format(module))    

        for asic in asic_list:
            logger.log_info("Stopping swss@{} and syncd@{} ...".format(asic, asic))
            process = subprocess.Popen(['sudo', 'systemctl', 'stop', 'swss@{}.service'.format(asic)],
                                        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = process.communicate()
            outstr = stdout.decode('ascii')
        # wait for service is down
        time.sleep(2)

        logger.log_info("Power off {} module ...".format(module))
        hw_slot = sfm_hw_slot_mapping[num]
        nokia_common._power_onoff_SFM(hw_slot,False)
        logger.log_info("Chassis module {} shutdown completed".format(module))
    else:
        logger.log_info("Starting up chassis module {}".format(module))
        hw_slot = sfm_hw_slot_mapping[num]
        nokia_common._power_onoff_SFM(hw_slot,True)
        # wait SFM HW init done.
        time.sleep(15)

        services_list = chassisdb.keys("CHASSIS_STATE_DB", "CHASSIS_FABRIC_ASIC_TABLE*")
        asic_list = []
        for service in services_list:
            name = chassisdb.get("CHASSIS_STATE_DB",service,"name")
            if name == module:
                asic_id = int(re.search(r"(\d+)$", service).group())
                asic_list.append(asic_id)

        for asic in asic_list:
            logger.log_info("Start swss@{} and syncd@{} ...".format(asic, asic))
            # Process state
            process = subprocess.Popen(['sudo', 'systemctl', 'start', 'swss@{}.service'.format(asic)],
                                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = process.communicate()
            outstr = stdout.decode('ascii')
        logger.log_info("Chassis module {} startup completed".format(module))
    return