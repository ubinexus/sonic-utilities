#!/usr/bin/env python3
#
# reboot_helper.py
#
# Utility helper for reboot within SONiC

import sonic_platform
from sonic_py_common import logger
from utilities_common.chassis import is_smartswitch, get_dpu_list

SYSLOG_IDENTIFIER = "reboot_helper"

EXIT_FAIL = -1
EXIT_SUCCESS = 0

# Global logger instance
log = logger.Logger(SYSLOG_IDENTIFIER)

# Global variable for platform chassis
platform_chassis = None


def load_platform_chassis():
    """
    Load the platform chassis using the SONiC platform API.

    This function attempts to instantiate the platform chassis object.
    If successful, it sets the global variable `platform_chassis` to the instantiated object.

    Returns:
        bool: True if the platform chassis is successfully loaded, False otherwise.
    """
    global platform_chassis

    # Load new platform API class
    try:
        platform_chassis = sonic_platform.platform.Platform().get_chassis()
        if platform_chassis is None:
            log.log_error("Platform chassis is not loaded")
            return False
        return True
    except Exception as e:
        log.log_error("Failed to instantiate Chassis: {}".format(str(e)))
        return False


def load_and_verify(module_name):
    """
    Load the platform chassis and verify the required parameters.

    Args:
        module_name (str): The name of the module to verify.

    Returns:
        bool: True if platform chassis is successfully loaded and required parameters are verified, False otherwise.
    """
    # Load the platform chassis if not already loaded
    if not load_platform_chassis():
        return False

    if not is_smartswitch():
        log.log_error("Platform is not a smartswitch")
        return False

    dpu_list = get_dpu_list()
    if module_name.lower() not in dpu_list:
        log.log_error("Module {} not found".format(module_name))
        return False

    return True


def reboot_dpu(module_name, reboot_type):
    """
    Reboot the specified module by invoking the platform API.

    Args:
        module_name (str): The name of the module to reboot.
        reboot_type (str): The type of reboot requested for the module.

    Returns:
        bool: True if the reboot command was successfully sent, False otherwise.
    """
    if not load_and_verify(module_name):
        return False

    # Attempt to reboot the module
    if not hasattr(platform_chassis, 'reboot'):
        log.log_error("Reboot method not found in platform chassis")
        return False

    log.log_info("Rebooting module {} with reboot_type {}...".format(module_name, reboot_type))
    try:
        status = platform_chassis.reboot(module_name, reboot_type)
        if not status:
            log.log_error("Reboot status for module {}: {}".format(module_name, status))
            return False
        return True
    except Exception as e:
        log.log_error("Unexpected error occurred while rebooting module {}: {}".format(module_name, e))
        return False


def pci_detach_module(module_name):
    """
    Detach the specified module by invoking the platform API.

    Args:
        module_name (str): The name of the module to detach.

    Returns:
        bool: True if the detach command was successfully sent, False otherwise.
    """
    if not load_and_verify(module_name):
        return False

    # Attempt to detach the module
    if not hasattr(platform_chassis, 'pci_detach'):
        log.log_error("PCI detach method not found in platform chassis")
        return False

    log.log_info("Detaching module {}...".format(module_name))
    try:
        status = platform_chassis.pci_detach(module_name)
        if not status:
            log.log_error("PCI detach status for module {}: {}".format(module_name, status))
            return False
        return True
    except Exception as e:
        log.log_error("Unexpected error occurred while detaching module {}: {}".format(module_name, e))
        return False


def pci_reattach_module(module_name):
    """
    Rescan the specified module by invoking the platform API.

    Args:
        module_name (str): The name of the module to rescan.

    Returns:
        bool: True if the rescan command was successfully sent, False otherwise.
    """
    if not load_and_verify(module_name):
        return False

    # Attempt to detach the module
    if not hasattr(platform_chassis, 'pci_reattach'):
        log.log_error("PCI reattach method not found in platform chassis")
        return False

    log.log_info("Rescaning module {}...".format(module_name))
    try:
        status = platform_chassis.pci_reattach(module_name)
        if not status:
            log.log_error("PCI detach status for module {}: {}".format(module_name, status))
            return False
        return True
    except Exception as e:
        log.log_error("Unexpected error occurred while detaching module {}: {}".format(module_name, e))
        return False
