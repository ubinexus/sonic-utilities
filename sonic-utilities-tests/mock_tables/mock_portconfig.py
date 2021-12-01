import os
import portconfig

def mock_get_port_config(hwsku=None, platform=None, port_config_file=None, asic=None):
    test_dir = os.path.dirname(os.path.realpath(__file__))
    if asic:
        portconfig_file = "port_config" + asic + ".ini"
        return portconfig.parse_port_config_file(os.path.join(test_dir, portconfig_file))
    else:
        return portconfig.parse_port_config_file(os.path.join(test_dir, 'port_config.ini'))

portconfig.get_port_config = mock_get_port_config
