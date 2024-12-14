import os
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


def is_dpu():
    return hasattr(device_info, 'is_dpu') and device_info.is_dpu()


def get_num_dpus():
    if hasattr(device_info, 'get_num_dpus'):
        return device_info.get_num_dpus()
    return 0


def get_dpu_list():
    if hasattr(device_info, 'get_dpu_list'):
        return device_info.get_dpu_list()
    return []
