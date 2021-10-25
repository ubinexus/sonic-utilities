import click
import utilities_common.cli as clicommon

from time import sleep
from .utils import log

#
# 'macsec' group ('config macsec ...')
#
@click.group(cls=clicommon.AbbreviationGroup, name='macsec')
def macsec():
    """MACsec-related configuration tasks"""
    pass

@macsec.group(cls=clicommon.AbbreviationGroup, name='port')
def macsec_port():
    pass

@macsec_port.command('add')
@click.argument('port', metavar='<port_name>', required=True)
@click.argument('profile', metavar='<profile_name>', required=True)
@clicommon.pass_db
def add_port(db, port, profile):
    """
    Add MACsec port
    """
    ctx = click.get_current_context()

    if clicommon.get_interface_naming_mode() == "alias":
        alias = port
        iface_alias_converter = clicommon.InterfaceAliasConverter(db)
        port = iface_alias_converter.alias_to_name(alias)
        if port is None:
            ctx.fail("cannot find port name for alias {}".format(alias))

    profile_entry = db.cfgdb.get_entry('MACSEC_PROFILE', profile)
    if len(profile_entry) == 0:
        ctx.fail("{} doesn't exist".format(profile))

    db.cfgdb.set_entry("PORT", port, {'macsec': profile})

@macsec_port.command('del')
@click.argument('port', metavar='<port_name>', required=True)
@clicommon.pass_db
def del_port(db, port):
    """
    Delete MACsec port
    """
    ctx = click.get_current_context()

    if clicommon.get_interface_naming_mode() == "alias":
        alias = port
        iface_alias_converter = clicommon.InterfaceAliasConverter(db)
        port = iface_alias_converter.alias_to_name(alias)
        if port is None:
            ctx.fail("cannot find port name for alias {}".format(alias))

    db.cfgdb.set_entry("PORT", port, {'macsec': ""})

@macsec.group(cls=clicommon.AbbreviationGroup, name='profile')
def macsec_profile():
    pass

@macsec_profile.command('add')
@click.argument('profile', metavar='<profile_name>', required=True)
@clicommon.pass_db
def add_profile(db,profile):
    """
    Add MACsec profile
    """
    ctx = click.get_current_context()

    if not len(profile_entry) == 0:
        ctx.fail("{} already exists".format(profile))

    db.cfgdb.set_entry("MACSEC_PROFILE", profile, {'NULL': 'NULL'})

@macsec_profile.command('del')
@click.argument('profile', metavar='<profile_name>', required=True)
@clicommon.pass_db
def del_profile(db, profile):
    """
    Delete MACsec profile
    """
    ctx = click.get_current_context()

    profile_entry = db.cfgdb.get_entry('MACSEC_PROFILE', profile)
    if len(profile_entry) == 0:
        ctx.fail("{} doesn't exist".format(profile))

    db.cfgdb.set_entry("MACSEC_PROFILE", profile, None)

