import os
import json
from sonic_py_common import device_info

def get_chassis_local_interfaces():
    lst = []
    platform = device_info.get_platform()
    chassisdb_conf=os.path.join('/usr/share/sonic/device/', platform, "chassisdb.conf")
    if os.path.exists(chassisdb_conf):
        lines=[]
        with open(chassisdb_conf, 'r') as f:
            lines = f.readlines()
        for line in lines:
            line = line.strip()
            if "chassis_internal_intfs" in line:
                data = line.split("=")
                lst = data[1].split(",")
                return lst
    return lst


def is_smartswitch():
    return hasattr(device_info, 'is_smartswitch') and device_info.is_smartswitch()


# utility to get dpu module name list
def get_all_dpus():
    dpu_list = []

    if not is_smartswitch():
        return dpu_list

    # Load platform.json
    platform_info = device_info.get_platform_info()
    platform = platform_info['platform']
    platform_file = os.path.join("/usr/share/sonic/device", platform, "platform.json")
    try:
        with open(platform_file, 'r') as platform_json:
            config_data = json.load(platform_json)

            # Extract DPUs dictionary
            dpus = config_data.get("DPUS", {})

            # Convert DPU names to uppercase and append to the list
            dpu_list = [dpu.upper() for dpu in dpus.keys()]

    except FileNotFoundError:
        print("Error: platform.json not found")
    except json.JSONDecodeError:
        print("Error: Failed to parse platform.json")

    return dpu_list


# utility to get dpu module name list and all
def get_all_dpu_options():
    dpu_list = get_all_dpus()

    # Add 'all' and 'SWITCH' to the list
    dpu_list += ['all']

    return dpu_list


# utility to get dpu module name list and "all, SWITCH"
def get_all_options():
    dpu_list = get_all_dpus()

    # Add 'all' and 'SWITCH' to the list
    dpu_list += ['all', 'SWITCH']

    return dpu_list
