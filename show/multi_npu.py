
import subprocess
import json
import click

from sonic_device_util import get_num_npus, get_namespaces


BACKPLANE_INTERFACE_PREFIX = "Ethernet-BP"
DISPLAY_ALL = 'all'
DISPLAY_EXTERNAL = 'frontend'


def multi_npu_platform():
    """
    This function checks if the platform is multi npu/asic platform or not

    Returns:
        bool -- True, if platform has more than one NPU
    """
    if get_num_npus() > 1:
        return True
    else: 
        return False

def is_backplane_interface(intf_name):
    if intf_name.startswith(BACKPLANE_INTERFACE_PREFIX):
        return True
    else:
        return False

def skip_intf_display(intf, display_opt):
    if display_opt == DISPLAY_ALL:
        return False
    else:
        if is_backplane_interface(intf):
            return True

def get_frontend_namespaces():

    frontend_namespaces = []
    for ns in get_namespaces():
        cmd = 'sudo ip netns exec {} sonic-cfggen -d  --var-json "DEVICE_METADATA"'.format(ns)

        p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout = p.communicate()[0]
        if p.returncode == 0:
            device_metadata = json.loads(stdout)
            if device_metadata['localhost'].has_key('sub_role') and device_metadata['localhost']['sub_role'] == 'FrontEnd':
                frontend_namespaces.append(ns)
    return frontend_namespaces

def multi_npu_ns_choices():
    if not multi_npu_platform() :
        return []
    choices =  get_namespaces()
    return choices

def multi_npu_display_choices():
    if not multi_npu_platform():
        return [DISPLAY_ALL]
    else:
        return [DISPLAY_ALL, DISPLAY_EXTERNAL]

def multi_npu_display_default_option():
    if not multi_npu_platform():
        return DISPLAY_ALL
    else:
        return  DISPLAY_EXTERNAL

def multi_npu_process_options(display,namespace):
    ns_list = []
    if not multi_npu_platform():
        return [None]
    else:
        if namespace is None:
            if display ==  DISPLAY_ALL:
                ns_list += get_namespaces()
            else:
                ns_list += get_frontend_namespaces()
        else:
            ns_list.append(namespace)
    return ns_list

_multi_npu_options = [
    click.option('--display', '-d', 'display', default=multi_npu_display_default_option(), show_default=True, type=click.Choice([DISPLAY_ALL, DISPLAY_EXTERNAL]), help='Show internal interfaces'),
    click.option('--namespace', '-n', 'namespace', default=None, type=click.Choice(multi_npu_ns_choices()), show_default=True, help='Namespace name or all'),
    #click.option('--namespace', '-n', 'namespace',  callback=multi_npu_ns_callback, show_default=True, help='Namespace name or all'),
]

def multi_npu_options(func):
    for option in reversed(_multi_npu_options):
        func = option(func)
    return func
