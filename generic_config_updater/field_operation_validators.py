import os
import re
import json
import subprocess
from sonic_py_common import device_info
from .gu_common import GenericConfigUpdaterError

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
GCU_TABLE_MOD_CONF_FILE = f"{SCRIPT_DIR}/gcu_table_modification_validators.conf.json"

def get_asic_name():
    asic = "unknown"
    command = ["sudo", "lspci"]
    hwsku = device_info.get_hwsku()
    proc = subprocess.Popen(command, universal_newlines=True, stdout=subprocess.PIPE)
    proc.communicate()
    output = proc.stdout.readlines()
 
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


def rdma_config_update_validator(path, operation):
    version_info = device_info.get_sonic_version_info()
    build_version = version_info.get('build_version')
    asic = get_asic_name()
    path = path.lower()

    # For paths like /BUFFER_PROFILE/pg_lossless_50000_300m_profile/xoff, remove pg_lossless_50000_300m from the path so that we can clearly determine which fields are modifiable
    cleaned_path = "/".join([part for part in path.split("/") if not any(char.isdigit() for char in part)])
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

    if os.path.exists(GCU_TABLE_MOD_CONF_FILE):
        with open(GCU_TABLE_MOD_CONF_FILE, "r") as s:
            gcu_field_operation_conf = json.load(s)
    else:
        raise GenericConfigUpdaterError("GCU table modification validators config file not found")

    match = re.search(r'\/([^\/]+)(\/|$)', cleaned_path) # This matches the table name in the path, eg if path if /PFC_WD/GLOBAL, the match would be PFC_WD
    if match is not None:
        table = match.group(1)
        index = cleaned_path.index(table) + len(table)
        field = cleaned_path[index:].lstrip('/')
    else:
        raise GenericConfigUpdaterError("Invalid jsonpatch path: {}".format(path))
    
    tables = gcu_field_operation_conf["tables"]
    scenarios = tables[table]["validator_data"]["rdma_config_update_validator"]
    scenario = None
    for key in scenarios.keys():
        if field in scenarios[key]["fields"]:
            scenario = scenarios[key]
            break
    
    if scenario is None:
        return False

    if operation not in scenario["operations"]:
        return False

    if platform in scenario["platforms"]:
        if version < scenario["platforms"][platform]:
            return False
    else:
        return False

    return True
