from sonic_py_common import device_info

def rdma_config_update_validator():
    version_info = device_info.get_sonic_version_info()
    build_version = version_info.get('build_version')
    asic_type = version_info.get('asic_type')

    if (asic_type != 'mellanox' and asic_type != 'broadcom' and asic_type != 'cisco-8000'):
        return False

    if len(build_version) >= 6:
        if build_version[:6].isdigit():
            branch_int = int(build_version[:6])
        else:
            return False
        if asic_type == 'cisco-8000':
            return branch_int >= 202012
        else:
            return branch_int >= 201811
    else:
        return False
