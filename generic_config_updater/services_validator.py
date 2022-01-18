import os
from .gu_common import genericUpdaterLogging

logger = genericUpdaterLogging.get_logger(title="Service Validator")

print_to_console = False

PAUSE_AFTER_FAILED_RESTART = "7s"

def set_verbose(verbose=False):
    global print_to_console, logger

    print_to_console = verbose
    if verbose:
        logger.set_min_log_priority_debug()
    else:
        logger.set_min_log_priority_notice()


def _service_restart(svc_name):
    rc = os.system(f"systemctl restart {svc_name}")
    if rc != 0:
        # This failure is likely due to too many restarts
        # Which is the reflection of patch sorter not grouping
        # updates for keys effectively.
        # Once the patch sorter is tuned, the following
        # code would not be executed.
        #
        rc = os.system(f"systemctl reset-failed {svc_name}")
        logger.log(logger.LOG_PRIORITY_ERROR, 
                f"Service has been reset. rc={rc} Pause for {PAUSE_AFTER_FAILED_RESTART}",
                print_to_console)

        # Even with successful reset-failed, a pause is required, else the
        # immediate restart was found to fail in manual tests.
        # Hence add a pause.
        # This pause would help even if the earlier reset-failed fails.
        # Hence we ignore return code from reset-failed.
        #
        os.system(f"sleep {PAUSE_AFTER_FAILED_RESTART}")
        rc = os.system(f"systemctl restart {svc_name}")

    if rc == 0:
        logger.log(logger.LOG_PRIORITY_NOTICE,
                f"Restart succeeded for {svc_name}",
                print_to_console)
    else:
        logger.log(logger.LOG_PRIORITY_ERROR,
                f"Restart failed for {svc_name} rc={rc}",
                print_to_console)
    return rc == 0


def rsyslog_validator(old_config, upd_config, keys):
    return _service_restart("rsyslog-config")


def dhcp_validator(old_config, upd_config, keys):
    return _service_restart("dhcp_relay")


def vlan_validator(old_config, upd_config, keys):
    old_vlan = old_config.get("VLAN", {})
    upd_vlan = upd_config.get("VLAN", {})

    for key in set(old_vlan.keys()).union(set(upd_vlan.keys())):
        if (old_vlan.get(key, {}).get("dhcp_servers", []) != 
                upd_vlan.get(key, {}).get("dhcp_servers", [])):
            return _service_restart("dhcp_relay")
    # No update to DHCP servers.
    return True


def main_test():
    for(i=0; i<10; ++i):
        _service_restart("rsyslog-config")
