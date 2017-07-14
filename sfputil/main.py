#!/usr/sbin/env python

try:
    import sys
    import os
    import subprocess
    import click
    import imp
    import syslog
    import types
    import traceback
except ImportError, e:
    raise ImportError (str(e) + "- required module not found")

VERSION = '1.0'


SONIC_CFGGEN_PATH = '/usr/local/bin/sonic-cfggen'
MINIGRAPH_PATH = '/etc/sonic/minigraph.xml'
HWSKU_KEY = 'minigraph_hwsku'
PLATFORM_KEY = 'platform'

PLATFORM_ROOT = '/usr/share/sonic/device'

csfputil = None
porttabfile = None
phytabfile = '/var/lib/cumulus/phytab'
indent = '\t'


#
# Helper functions
#

def log_init():
    syslog.openlog('sfputil')

def log_info(logmsg):
    syslog.syslog(syslog.LOG_INFO, logmsg)

def inc_indent():
    global indent
    indent += '\t'

def dec_indent():
    global indent
    indent = indent[:-1]

def print_sfp_status(port, port_sfp_status):
    if port_sfp_status == 1:
        print '%s: ' %port + 'SFP detected'
    else:
        print '%s: ' %port + 'SFP not detected'


# Returns,
#   port_num if physical
#   logical_port:port_num if logical port and is a ganged port
#   logical_port if logical and not ganged
#
def get_port_name(logical_port, physical_port, ganged):
    port_name = None

    if logical_port == physical_port:
        return logical_port
    elif ganged == 1:
        return logical_port + ":%d (ganged)" % physical_port
    else:
        return logical_port

def conv_port_to_physical_port_list(port):
    if port.startswith('Ethernet'):
        if csfputil.is_logical_port(port):
            return csfputil.get_logical_to_physical(port)
        else:
            print "Error: Invalid port '%s'" % port
            return None
    else:
        return [int(port)]

def print_valid_values_for_port_cmdoption():
    print "Valid values for port: " + str(csfputil.logical)
    print

#============ Functions to get and print sfp data ======================


# Get sfp port object
def get_port_sfp_data(sfp_obj, port_num):
    sfp_port_data = {}

    if sfp_obj == None:
        print "Error getting sfp data for port %d" % port_num
        sfp_port_data[port_num] = None
    else:
        sfp_port_data[port_num] = sfp_obj.get_sfp_data(port_num)

    return sfp_port_data


# Returns sfp data for all ports
def get_port_sfp_data_all(sfp_obj_all):
    """{1: {'interface': {'version': '1.0', 'data': {}},
        'dom': {'version' : '1.0', 'data' : {}}},
       {2: {'interface': {'version': '1.0', 'data': {}},
        'dom': {'version' : '1.0', 'data' : {}}}}}"""

    port_sfp_data_all = {}
    port_start = csfputil.port_start
    port_end = csfputil.port_end

    for p in range(port_start, port_end + 1):
        port_sfp_data_all.update(get_port_sfp_data(sfp_obj_all.get(p), p))

    return port_sfp_data_all


# recursively pretty print dictionary 
def print_dict_pretty(indict):
    for elem, elem_val in sorted(indict.iteritems()):
        if type(elem_val) == types.DictType:
            print indent, elem, ':'
            inc_indent()
            print_dict_pretty(elem_val)
            dec_indent()
        else:
            print indent, elem, ':', elem_val

# Print pretty sfp port data
def print_port_sfp_data_pretty(port_sfp_data, port, dump_dom):
    ganged = 0
    i = 1

    port_list = conv_port_to_physical_port_list(port)
    if len(port_list) > 1:
        ganged = 1

    for p in port_list:
        port_name = get_port_name(port, i, ganged)
        sfp_data = port_sfp_data.get(p)
        if sfp_data != None:
            sfp_idata = sfp_data.get('interface')
            idata = sfp_idata.get('data')
            print_sfp_status(port_name, 1)
            print_dict_pretty(idata)
            if dump_dom == 1:
                sfp_ddata = sfp_data.get('dom')
                if sfp_ddata != None:
                    ddata = sfp_ddata.get('data')
                    print_dict_pretty(ddata)
        else:
            print_sfp_status(port_name, 0)
        print
        i += 1

# Print pretty all sfp port data
def print_port_sfp_data_pretty_all(port_sfp_data, dump_dom):
    for p in csfputil.logical:
        print_port_sfp_data_pretty(port_sfp_data, p, dump_dom)


# Recursively print dict elems into comma separated list
def print_dict_commaseparated(indict, elem_blacklist, elemprefix, first):
    iter = 0
    for elem, elem_val in sorted(indict.iteritems()):
        if elem in elem_blacklist:
            continue
        if type(elem_val) == types.DictType:
            if iter != 0:
                print ',',
            print_dict_commaseparated(elem_val, elem_blacklist, elem, first)
        else:
            elemname = elemprefix + elem
            if first == 1:
                prbuf = elemname + ':' + str(elem_val)
                first = 0
            else:
                prbuf = ',' + elemname + ':' + str(elem_val)
            sys.stdout.write(prbuf)
        iter = iter + 1


# Pretty print oneline all sfp data
def print_port_sfp_data_pretty_oneline(port_sfp_data,
                       ifdata_blacklist,
                       domdata_blacklist,
                       port, dump_dom):
    ganged = 0
    i = 1

    port_list = conv_port_to_physical_port_list(port)
    if len(port_list) > 1:
        ganged = 1

    for p in port_list:
        port_name = get_port_name(port, i, ganged)
        sfp_data = port_sfp_data.get(p)
        if sfp_data != None:
            sfp_idata = sfp_data.get('interface')
            idata = sfp_idata.get('data')
            print 'port:' + port_name + ',',
            print_dict_commaseparated(idata, ifdata_blacklist, '', 1)
            if dump_dom == 1:
                sfp_ddata = sfp_data.get('dom')
                if sfp_ddata != None:
                    ddata = sfp_ddata.get('data')
                    if ddata != None:
                        print_dict_commaseparated(ddata, domdata_blacklist, '', 1)
            print
        #Only print detected sfp ports for oneline
        #else:
            #print_sfp_status(port_name, 0)
        i += 1


def print_port_sfp_data_pretty_oneline_all(port_sfp_data,
                       ifdata_blacklist,
                       domdata_blacklist,
                       dump_dom):
    for p in csfputil.logical:
        print_port_sfp_data_pretty_oneline(port_sfp_data,
                           ifdata_blacklist,
                           domdata_blacklist,
                           p, dump_dom)

def get_port_sfp_object(port_num):
    sfp_obj = {}
    sfp_obj[port_num] = csfputil(int(port_num))

    return sfp_obj

# Return sfp objects for all ports
def get_port_sfp_object_all():
    port_sfp_object_all = {}
    port_start = csfputil.port_start
    port_end = csfputil.port_end

    for p in range(port_start, port_end + 1):
        port_sfp_object_all.update(get_port_sfp_object(p))

    return port_sfp_object_all

def print_raw_bytes(bytes):
    hexstr = ''

    for e in range(1, len(bytes)+1):
        print bytes[e-1],
        hexstr += bytes[e-1]
        if e > 0 and (e % 8) == 0:
            print ' ',
        if e > 0 and (e % 16) == 0:
            # XXX: Does not print some characters
            # right, comment it to fix it later
            #print binascii.unhexlify(hexstr),
            hexstr = ''
            print

def print_port_sfp_data_raw(sfp_obj_all, port):
    ganged = 0
    i = 1

    physical_port_list = conv_port_to_physical_port_list(port)
    if len(physical_port_list) > 1:
        ganged = 1

    for p in physical_port_list:
        port_name = get_port_name(port, i, ganged)
        sfp_obj = sfp_obj_all.get(p)
        if sfp_obj == None:
            print ('Error: Unexpected error: sfp object for '
                'port %d' %p + 'not found')
            return
        eeprom_if_raw = sfp_obj.get_interface_eeprom_bytes()
        if eeprom_if_raw == None:
            print_sfp_status(port_name, 0)
        else:
            print_sfp_status(port_name, 1)
            print_raw_bytes(eeprom_if_raw)
        print
        i += 1

def print_port_sfp_data_raw_all(sfp_obj_all):
    for p in csfputil.logical:
        print_port_sfp_data_raw(sfp_obj_all, p)

#=========== Functions to load platform specific classes ====================

# Returns platform and HW SKU
def get_platform_and_hwsku():
    try:
        proc = subprocess.Popen([SONIC_CFGGEN_PATH, '-v', PLATFORM_KEY],
                                stdout=subprocess.PIPE,
                                shell=False,
                                stderr=subprocess.STDOUT)
        stdout = proc.communicate()[0]
        proc.wait()
        platform = stdout.rstrip('\n')

        proc = subprocess.Popen([SONIC_CFGGEN_PATH, '-m', MINIGRAPH_PATH, '-v', HWSKU_KEY],
                                stdout=subprocess.PIPE,
                                shell=False,
                                stderr=subprocess.STDOUT)
        stdout = proc.communicate()[0]
        proc.wait()
        hwsku = stdout.rstrip('\n')
    except OSError, e:
        raise OSError("Cannot detect platform")

    return (platform, hwsku)


# Loads platform specific sfputil module from source
def load_platform_sfputil():
    global csfputil
    global porttabfile
    module_name = 'sfputil'

    # Get platform and hwsku
    (platform, hwsku) = get_platform_and_hwsku()

    # Load platform module from source
    platform_path = '/'.join([PLATFORM_ROOT, platform])
    hwsku_path = '/'.join([platform_path, hwsku])

    # First check for the presence of the new 'port_config.ini' file
    porttabfile = '/'.join([hwsku_path, 'port_config.ini'])
    if not os.path.isfile(porttabfile):
        # port_config.ini doesn't exist. Try loading the older 'portmap.ini' file
        porttabfile = '/'.join([hwsku_path, 'portmap.ini'])

    try:
        module_full_name = module_name
        module_file = '/'.join([platform_path, 'plugins', module_full_name + '.py'])
        module = imp.load_source(module_name, module_file)
    except IOError, e:
        print 'Error loading platform module ' + module_name + str(e)
        return None

    try:
        csfputil = getattr(module, 'sfputil')
    except AttributeError, e:
        print 'Error finding sfputil class: ' + str(e)
        return -1

    return 0


# This is our main entrypoint - the main 'sfputil' command
@click.group()
def cli():
    """sfputil - Command line utility for managing SFP transceivers"""
    if os.geteuid() != 0:
        exit("Root privileges are required for this operation")

    # Init log
    log_init()



# 'show' subgroup
@cli.group()
def show():
    """Display status of SFP transceivers"""
    pass

# 'details' subcommand
@show.command()
@click.option('-p', '--port', metavar='<port_name>', help="Display SFP details for port <port_name> only")
@click.option('-d', '--dom', 'dump_dom', is_flag=True, help="Also display Digital Optical Monitoring (DOM) data")
@click.option('-o', '--oneline', is_flag=True, help="Condense output for each port to a single line")
@click.option('--raw', is_flag=True, help="Output raw, unformatted data")
def details(port, dump_dom, oneline, raw):
    """Display detailed status of SFP transceivers"""
    port_sfp_data = {}
    pretty = True
    sfp_objects = {}
    port_list = []

    all_ports = True if port is None else False

    # Load platform sfputil class
    err = load_platform_sfputil()
    if err != 0:
        exit(1)

    try:
        csfputil.read_porttab_mappings(porttabfile)
    except Exception, e:
        print 'Error reading port info (%s)' % str(e)
        exit(1)

    if all_ports == False:
        if csfputil.is_valid_sfputil_port(port) == 0:
            print 'Error: invalid port'
            print
            print_valid_values_for_port_cmdoption()
            exit(1)

        port_list = conv_port_to_physical_port_list(port)
        if port_list == None:
            exit(0)

    # Get all sfp objects
    if all_ports == True:
        sfp_objects = get_port_sfp_object_all()
    else:
        for p in port_list:
            sfp_objects.update(get_port_sfp_object(p))

    if raw == True:
        # Print raw and return
        if all_ports == True:
            print_port_sfp_data_raw_all(sfp_objects)
        else:
            print_port_sfp_data_raw(sfp_objects, port)
        exit(0)

    if all_ports == True:
        port_sfp_data = get_port_sfp_data_all(sfp_objects)
    else:
        for p in port_list:
            port_sfp_data.update(get_port_sfp_data(sfp_objects.get(p), p))

    # Print all sfp data
    if oneline == True:
        ifdata_out_blacklist = ['EncodingCodes',
                    'ExtIdentOfTypeOfTransceiver',
                    'NominalSignallingRate(UnitsOf100Mbd)']
        domdata_out_blacklist = ['AwThresholds', 'StatusControl']

        if all_ports == True:
            print_port_sfp_data_pretty_oneline_all(port_sfp_data,
                            ifdata_out_blacklist,
                            domdata_out_blacklist,
                            dump_dom)
        else:
            print_port_sfp_data_pretty_oneline(port_sfp_data,
                            ifdata_out_blacklist,
                            domdata_out_blacklist,
                            port, dump_dom)
    elif pretty == True:
        if all_ports == True:
            print_port_sfp_data_pretty_all(port_sfp_data, dump_dom)
        else:
            print_port_sfp_data_pretty(port_sfp_data, port, dump_dom)

# 'presence' subcommand
@show.command()
@click.argument('port_name', metavar='<port_name>', required=False)
def presence(port_name):
    """Display presence of SFP transceiver(s)"""
    if port_name is not None:
        # TODO
        pass
    else:
        # TODO
        pass

# 'reset' subcommand
@cli.command()
@click.argument('port_name', metavar='<port_name>')
def reset(port_name):
    """Reset SFP transceiver"""
    # TODO
    pass

# 'version' subcommand
@cli.command()
def version():
    """Display version info"""
    click.echo("sfputil version {0}".format(VERSION))


if __name__ == '__main__':
    cli()
