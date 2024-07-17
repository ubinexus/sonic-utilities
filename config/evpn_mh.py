import click
import utilities_common.cli as clicommon


#
# 'evpn-mh' group ('config evpn-mh ...')
#
@click.group(name="evpn-mh")
def evpn_mh():
    """Multihoming EVPN-related configuration tasks"""
    pass


#
# 'startup-delay' subgroup ('config interface startup-delay ...')
#
@evpn_mh.group()
@click.pass_context
def startup_delay(ctx):
    """Configure startup delay"""
    pass


@startup_delay.command('add')
@click.argument('startup-delay', metavar='<startup_delay>', required=True, type=click.IntRange(min=0, max=3600))
@clicommon.pass_db
def add_startup_delay(db, startup_delay):
    """Add startup delay"""
    ctx = click.get_current_context()

    evpn_eth = db.cfgdb.get_entry("EVPN_MH_GLOBAL", "default")
    if evpn_eth.get("startup_delay") is not None:
        ctx.fail("Startup delay is already added!")

    db.cfgdb.mod_entry("EVPN_MH_GLOBAL", "default", {"startup_delay": startup_delay})


@startup_delay.command('set')
@click.argument('startup-delay', metavar='<startup_delay>', required=True, type=click.IntRange(min=0, max=3600))
@clicommon.pass_db
def set_startup_delay(db, startup_delay):
    """Set startup delay"""
    ctx = click.get_current_context()

    evpn_eth = db.cfgdb.get_entry("EVPN_MH_GLOBAL", "default")
    if evpn_eth.get("startup_delay") is None:
        ctx.fail("Startup delay should be added first!")

    db.cfgdb.mod_entry("EVPN_MH_GLOBAL", "default", {"startup_delay": startup_delay})


@startup_delay.command('del')
@click.argument('startup-delay', metavar='<startup_delay>', required=True, type=click.IntRange(min=0, max=3600))
@clicommon.pass_db
def del_startup_delay(db, startup_delay):
    """Delete startup delay"""
    ctx = click.get_current_context()

    evpn_eth = db.cfgdb.get_entry("EVPN_MH_GLOBAL", "default")
    db_startup_delay = evpn_eth.get("startup_delay")
    if db_startup_delay is None:
        ctx.fail("Startup delay is not configured!")
    if db_startup_delay != str(startup_delay):
        ctx.fail("Unable to delete startup delay. Configured value is {}".format(db_startup_delay))

    del evpn_eth["startup_delay"]
    db.cfgdb.set_entry("EVPN_MH_GLOBAL", "default", evpn_eth)


#
# 'mac-holdtime' subgroup ('config interface mac-holdtime ...')
#
@evpn_mh.group()
@click.pass_context
def mac_holdtime(ctx):
    """Configure MAC holdtime"""
    pass


@mac_holdtime.command('add')
@click.argument('mac-holdtime', metavar='<mac_holdtime>', required=True, type=click.IntRange(min=0, max=86400))
@clicommon.pass_db
def add_mac_holdtime(db, mac_holdtime):
    """Add MAC holdtime"""
    ctx = click.get_current_context()

    evpn_eth = db.cfgdb.get_entry("EVPN_MH_GLOBAL", "default")
    if evpn_eth.get("mac_holdtime") is not None:
        ctx.fail("MAC holdtime is already added!")

    db.cfgdb.mod_entry("EVPN_MH_GLOBAL", "default", {"mac_holdtime": mac_holdtime})


@mac_holdtime.command('set')
@click.argument('mac-holdtime', metavar='<mac_holdtime>', required=True, type=click.IntRange(min=0, max=86400))
@clicommon.pass_db
def set_mac_holdtime(db, mac_holdtime):
    """Set MAC holdtime"""
    ctx = click.get_current_context()

    evpn_eth = db.cfgdb.get_entry("EVPN_MH_GLOBAL", "default")
    if evpn_eth.get("mac_holdtime") is None:
        ctx.fail("MAC holdtime should be added first!")

    db.cfgdb.mod_entry("EVPN_MH_GLOBAL", "default", {"mac_holdtime": mac_holdtime})


@mac_holdtime.command('del')
@click.argument('mac-holdtime', metavar='<mac_holdtime>', required=True, type=click.IntRange(min=0, max=86400))
@clicommon.pass_db
def del_mac_holdtime(db, mac_holdtime):
    """Delete MAC holdtime"""
    ctx = click.get_current_context()

    evpn_eth = db.cfgdb.get_entry("EVPN_MH_GLOBAL", "default")
    db_mac_holdtime = evpn_eth.get("mac_holdtime")
    if db_mac_holdtime is None:
        ctx.fail("MAC holdtime is not configured!")
    if db_mac_holdtime != str(mac_holdtime):
        ctx.fail("Unable to delete MAC holdtime. Configured value is {}".format(db_mac_holdtime))

    del evpn_eth["mac_holdtime"]
    db.cfgdb.set_entry("EVPN_MH_GLOBAL", "default", evpn_eth)


#
# 'neigh-holdtime' subgroup ('config interface neigh-holdtime ...')
#
@evpn_mh.group()
@click.pass_context
def neigh_holdtime(ctx):
    """Configure neighbor entry holdtime"""
    pass


@neigh_holdtime.command('add')
@click.argument('neigh-holdtime', metavar='<neigh_holdtime>', required=True, type=click.IntRange(min=0, max=86400))
@clicommon.pass_db
def add_neigh_holdtime(db, neigh_holdtime):
    """Add neighbor entry holdtime"""
    ctx = click.get_current_context()

    evpn_eth = db.cfgdb.get_entry("EVPN_MH_GLOBAL", "default")
    if evpn_eth.get("neigh_holdtime") is not None:
        ctx.fail("Neighbor entry holdtime is already added!")

    db.cfgdb.mod_entry("EVPN_MH_GLOBAL", "default", {"neigh_holdtime": neigh_holdtime})


@neigh_holdtime.command('set')
@click.argument('neigh-holdtime', metavar='<neigh_holdtime>', required=True, type=click.IntRange(min=0, max=86400))
@clicommon.pass_db
def set_neigh_holdtime(db, neigh_holdtime):
    """Set neighbor entry holdtime"""
    ctx = click.get_current_context()

    evpn_eth = db.cfgdb.get_entry("EVPN_MH_GLOBAL", "default")
    if evpn_eth.get("neigh_holdtime") is None:
        ctx.fail("Neighbor entry holdtime should be added first!")

    db.cfgdb.mod_entry("EVPN_MH_GLOBAL", "default", {"neigh_holdtime": neigh_holdtime})


@neigh_holdtime.command('del')
@click.argument('neigh-holdtime', metavar='<neigh_holdtime>', required=True, type=click.IntRange(min=0, max=86400))
@clicommon.pass_db
def del_neigh_holdtime(db, neigh_holdtime):
    """Delete neighbor entry holdtime"""
    ctx = click.get_current_context()

    evpn_eth = db.cfgdb.get_entry("EVPN_MH_GLOBAL", "default")
    db_neigh_holdtime = evpn_eth.get("neigh_holdtime")
    if db_neigh_holdtime is None:
        ctx.fail("Neighbor entry holdtime is not configured!")
    if db_neigh_holdtime != str(neigh_holdtime):
        ctx.fail("Unable to delete neighbor entry holdtime. Configured value is {}".format(db_neigh_holdtime))

    del evpn_eth["neigh_holdtime"]
    db.cfgdb.set_entry("EVPN_MH_GLOBAL", "default", evpn_eth)
