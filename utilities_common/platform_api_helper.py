import click

platform_chassis = None
platform_sfp_base = None
platform_sfputil_loaded = False

RJ45_PORT_TYPE = 'RJ45'

def is_rj45_port(port_name, state_db=None):
    global platform_chassis
    global platform_sfp_base
    global platform_sfputil_loaded

    if state_db:
        sfp_info_dict = state_db.get_all(state_db.STATE_DB, 'TRANSCEIVER_INFO|{}'.format(port_name))
        if sfp_info_dict and sfp_info_dict['type'] == RJ45_PORT_TYPE:
            return True

    if not platform_chassis:
        import sonic_platform
        platform_chassis = sonic_platform.platform.Platform().get_chassis()
    if not platform_sfp_base:
        import sonic_platform_base
        platform_sfp_base = sonic_platform_base.sfp_base.SfpBase

    if platform_chassis and platform_sfp_base:
        from utilities_common import platform_sfputil_helper
        if not platform_sfputil_loaded:
            platform_sfputil_helper.load_platform_sfputil()
            platform_sfputil_helper.platform_sfputil_read_porttab_mappings()
            platform_sfputil_loaded = True

        physical_port = platform_sfputil_helper.logical_port_name_to_physical_port_list(port_name)[0]
        try:
            port_type = platform_chassis.get_port_or_cage_type(physical_port)
        except NotImplementedError as e:
            port_type = None

        return port_type == platform_sfp_base.SFP_PORT_TYPE_BIT_RJ45

    return False
