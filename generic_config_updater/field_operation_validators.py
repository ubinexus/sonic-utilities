import re
import subprocess
from sonic_py_common import device_info

def get_asic_name():
    asic = "unknown"
    command = ["sudo", "lspci"]
    hwsku = device_info.get_hwsku()

    proc = subprocess.Popen(command, universal_newlines=True, stdout=subprocess.PIPE)
    output = proc.stdout.readlines()
    proc.communicate()

    if proc.returncode == 0:
        if "Broadcom Limited Device b960" in output or "Broadcom Limited Broadcom BCM56960" in output:
            asic = "th"
        elif "Broadcom Limited Device b971" in output:
            asic = "th2"
        elif "Broadcom Limited Device b850" in output or "Broadcom Limited Broadcom BCM56850" in output:
            asic = "td2"
        elif "Broadcom Limited Device b870" in output or "Broadcom Inc. and subsidiaries Device b870" in output:
            asic = "td3"

    if device_info.get_sonic_version_info()['asic_type'] == 'cisco-8000':
        asic = "cisco-8000"
    elif asic == "unknown":
        spc1_hwskus = [ 'ACS-MSN2700', 'ACS-MSN2740', 'ACS-MSN2100', 'ACS-MSN2410', 'ACS-MSN2010', 'Mellanox-SN2700', 'Mellanox-SN2700-D48C8' ]
        if hwsku.lower() in [spc1_hwsku.lower() for spc1_hwsku in spc1_hwskus]:
            asic = "spc1"

    return asic


def rdma_config_update_validator(field):
    version_info = device_info.get_sonic_version_info()
    build_version = version_info.get('build_version')
    asic = get_asic_name()
    field = field.lower()

    if asic == "unknown":
        return False

    version_substrings = build_version.split('.')
    branch_version = None

    for substring in version_substrings:
        if substring.isdigit() and re.match(r'^\d{8}$', substring):
            branch_version = substring
            break

    if branch_version is None:
        return False

    # PFCWD enable/disable scenario
    if "pfc_wd" in field:
        if asic == 'cisco-8000':
            return branch_version >= "20201200"
        else:
            return branch_version >= "20181100"

    # Shared/headroom pool size scenario
    elif "buffer_pool" in field:
        if asic in ['cisco-8000', 'td2']:
            return False
        if asic == 'spc1':
            return branch_version >= "20191100"
        if asic in ['th', 'th2', 'td3']:
            return branch_version >= "20221100"

    # Dynamic threshold tuning scenario
    elif "buffer_profile" in field and "dynamic_th" in field:
        if asic == 'cisco-8000':
            return False
        if asic in ['spc1', 'td2', 'th', 'th2']:
            return branch_version >= "20181100"
        elif asic == 'td3':
            return branch_version >= "20201200"

    # ECN tuning scenario
    elif "wred_profile" in field:
        if asic == 'cisco-8000':
            return False
        elif asic in ['spc1', 'td2', 'th', 'th2']:
            return branch_version >= "20181100"
        elif asic == 'td3':
            return branch_version >= "20201200"

    # PG headroom modification scenario
    elif "buffer_profile" in field and "xoff" in field:
        if asic in ['cisco-8000', 'td2']:
            return False
        elif asic == 'spc1':
            return branch_version >= "20191100"
        elif asic in ['th', 'th2', 'td3']:
            return branch_version >= "20221100"

    return False

