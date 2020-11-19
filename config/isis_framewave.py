import click
import utilities_common.cli as clicommon

from swsssdk import ConfigDBConnector
from .utils import log


def _change_isis_interface_enabled(config_db, interface_id, enabled, verbose):
    """Enable or disable IS-IS configuration for a given interface
    """
    if verbose:
        verb = 'Enabling' if enabled == 'true' else 'Disabling'
        click.echo("{} IS-IS configuration for interface {}...".
                   format(verb, interface_id))

    config_db.mod_entry('isis_interface', interface_id, {'enabled': enabled})


#
# 'isis' group ('config isis ...')
#
@click.group(cls=clicommon.AbbreviationGroup)
def isis():
    """IS-IS-related configuration tasks
    """
    pass


#
# 'enable' subgroup ('config isis enable ...')
#
@isis.group(cls=clicommon.AbbreviationGroup)
def enable():
    """Enable IS-IS interface(s) configuration
    """
    pass


# 'all' subcommand
@enable.command()
@click.option('-v', '--verbose', is_flag=True, help="Enable verbose output")
def all(verbose):
    """Enable IS-IS configuration for all interfaces
    """
    log.log_info("'isis enable all' executing...")

    config_db = ConfigDBConnector()
    config_db.connect()
    isis_interfaces = config_db.get_keys('ISIS_INTERFACE')
    for interface_id in isis_interfaces:
        _change_isis_interface_enabled(config_db, interface_id, 'true', verbose)


# 'interface' subcommand
@enable.command()
@click.argument('interface_id', metavar='<interface_id>', required=True)
@click.option('-v', '--verbose', is_flag=True, help="Enable verbose output")
def interface(interface_id, verbose):
    """Enable IS-IS configuration for a specific interface
    """
    log.log_info("'isis enable interface {}' executing...".format(interface_id))

    config_db = ConfigDBConnector()
    config_db.connect()
    if config_db.get_entry('ISIS_INTERFACE', interface_id):
        _change_isis_interface_enabled(config_db, interface_id, 'true', verbose)
    else:
        click.get_current_context().fail("Could not locate IS-IS interface '{}'".
                                         format(interface_id))


@isis.group(cls=clicommon.AbbreviationGroup)
def disable():
    """Disable IS-IS interface(s) configuration
    """
    pass


# 'all' subcommand
@disable.command()
@click.option('-v', '--verbose', is_flag=True, help="Enable verbose output")
def all(verbose):
    """Disable IS-IS configuration for all interfaces
    """
    log.log_info("'isis disable all' executing...")

    config_db = ConfigDBConnector()
    config_db.connect()
    isis_interfaces = config_db.get_keys('ISIS_INTERFACE')
    for interface_id in isis_interfaces:
        _change_isis_interface_enabled(config_db, interface_id, 'false', verbose)


# 'interface' subcommand
@disable.command()
@click.argument('interface_id', metavar='<interface_id>', required=True)
@click.option('-v', '--verbose', is_flag=True, help="Enable verbose output")
def interface(interface_id, verbose):
    """Disable IS-IS configuration for a specific interface
    """
    log.log_info("'isis disable interface {}' executing...".format(interface_id))

    config_db = ConfigDBConnector()
    config_db.connect()
    if config_db.get_entry('ISIS_INTERFACE', interface_id):
        _change_isis_interface_enabled(config_db, interface_id, 'false', verbose)
    else:
        click.get_current_context().fail("Could not locate IS-IS interface '{}'".
                                         format(interface_id))
