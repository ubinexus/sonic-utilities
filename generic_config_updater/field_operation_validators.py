from sonic_py_common import device_info

def rdma_config_update_validator():
    version_info = device_info.get_sonic_version_info()
    build_version = version_info.get('build_version')
    asic_type = version_info.get('asic_type')

    if (asic_type != 'mellanox' and asic_type != 'broadcom' and asic_type != 'cisco-8000'):
        return False

    version_substrings = build_version.split('.')
    branch_int = None

    for substring in version_substrings:
        if substring.isdigit() and (substring.startswith("202") or substring.startswith("201")):
            branch_int = int(substring)
            break

    if branch_int is None:
        return False

    if asic_type == 'cisco-8000':
        return branch_int >= 202012
    else:
        return branch_int >= 201811
