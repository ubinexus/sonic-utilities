import click
import utilities_common.cli as clicommon

from sonic_py_common import logger
from utilities_common.bgp import (
    CFG_BGP_DEVICE_GLOBAL,
    BGP_DEVICE_GLOBAL_KEY,
    SYSLOG_IDENTIFIER,
    to_str,
)


log = logger.Logger(SYSLOG_IDENTIFIER)
log.set_min_log_priority_info()


#
# BGP DB interface ----------------------------------------------------------------------------------------------------
#


def update_entry_validated(db, table, key, data, create_if_not_exists=False):
    """ Update entry in table and validate configuration.
    If attribute value in data is None, the attribute is deleted.

    Args:
        db (swsscommon.ConfigDBConnector): Config DB connector object.
        table (str): Table name to add new entry to.
        key (Union[str, Tuple]): Key name in the table.
        data (Dict): Entry data.
        create_if_not_exists (bool):
            In case entry does not exists already a new entry
            is not created if this flag is set to False and
            creates a new entry if flag is set to True.
    Raises:
        Exception: when cfg does not satisfy YANG schema.
    """

    cfg = db.get_config()
    cfg.setdefault(table, {})

    if not data:
        raise click.ClickException(f"No field/values to update {key}")

    if create_if_not_exists:
        cfg[table].setdefault(key, {})

    if key not in cfg[table]:
        raise click.ClickException(f"{key} does not exist")

    entry_changed = False
    for attr, value in data.items():
        if value == cfg[table][key].get(attr):
            continue
        entry_changed = True
        if value is None:
            cfg[table][key].pop(attr, None)
        else:
            cfg[table][key][attr] = value

    if not entry_changed:
        return

    db.set_entry(table, key, cfg[table][key])


#
# BGP handlers --------------------------------------------------------------------------------------------------------
#


def tsa_handler(ctx, db, state):
    """ Handle config updates for Traffic-Shift-Away (TSA) feature """

    table = CFG_BGP_DEVICE_GLOBAL
    key = BGP_DEVICE_GLOBAL_KEY
    data = {
        "tsa_enabled": state,
    }

    try:
        update_entry_validated(db.cfgdb, table, key, data, create_if_not_exists=True)
        log.log_notice("Configured TSA state: {}".format(to_str(state)))
    except Exception as e:
        log.log_error("Failed to configure TSA state: {}".format(str(e)))
        ctx.fail(str(e))


def wcmp_handler(ctx, db, state):
    """ Handle config updates for Weighted-Cost Multi-Path (W-ECMP) feature """

    table = CFG_BGP_DEVICE_GLOBAL
    key = BGP_DEVICE_GLOBAL_KEY
    data = {
        "wcmp_enabled": state,
    }

    try:
        update_entry_validated(db.cfgdb, table, key, data, create_if_not_exists=True)
        log.log_notice("Configured W-ECMP state: {}".format(to_str(state)))
    except Exception as e:
        log.log_error("Failed to configure W-ECMP state: {}".format(str(e)))
        ctx.fail(str(e))

def bandwidth_handler(ctx, db, state):
    
    table = CFG_BGP_DEVICE_GLOBAL
    key = BGP_DEVICE_GLOBAL_KEY
    data = {
        "bestpath_bandwidth": state,
    }

    try:
        update_entry_validated(db.cfgdb, table, key, data, create_if_not_exists=True)
        log.log_notice("Configured bestpath for bandwidth state: {}".format(to_str(state)))
    except Exception as e:
        log.log_error("Failed to configure bestpath for bandwidth state: {}".format(str(e)))
        ctx.fail(str(e))


#
# BGP device-global ---------------------------------------------------------------------------------------------------
#


@click.group(
    name="device-global",
    cls=clicommon.AliasedGroup
)
def DEVICE_GLOBAL():
    """ Configure BGP device global state """

    pass


#
# BGP device-global tsa -----------------------------------------------------------------------------------------------
#


@DEVICE_GLOBAL.group(
    name="tsa",
    cls=clicommon.AliasedGroup
)
def DEVICE_GLOBAL_TSA():
    """ Configure Traffic-Shift-Away (TSA) feature """

    pass


@DEVICE_GLOBAL_TSA.command(
    name="enabled"
)
@clicommon.pass_db
@click.pass_context
def DEVICE_GLOBAL_TSA_ENABLED(ctx, db):
    """ Enable Traffic-Shift-Away (TSA) feature """

    tsa_handler(ctx, db, "true")


@DEVICE_GLOBAL_TSA.command(
    name="disabled"
)
@clicommon.pass_db
@click.pass_context
def DEVICE_GLOBAL_TSA_DISABLED(ctx, db):
    """ Disable Traffic-Shift-Away (TSA) feature """

    tsa_handler(ctx, db, "false")


#
# BGP device-global w-ecmp --------------------------------------------------------------------------------------------
#


class CustomAliasedGroup(click.Group):
    def parse_args(self, ctx, args):
        if args and args[0].isdigit():
            ctx.protected_args = [args.pop(0)]
        super().parse_args(ctx, args)

    def format_help(self, ctx, formatter):
        super().format_help(ctx, formatter)
        formatter.write_text("\nYou can also directly input a weight value between 1 and 25600.\n")

@DEVICE_GLOBAL.group(
    name="w-ecmp",
    cls=CustomAliasedGroup
)
@clicommon.pass_db
@click.pass_context
@click.argument("weight", required=False)
def DEVICE_GLOBAL_WCMP(ctx, db, weight):
    """Configure Weighted-Cost Multi-Path (W-ECMP) feature"""
    if weight:
        try:
            weight = int(weight)
        except ValueError:
            raise click.BadParameter('Weight must be an integer.')

        if not (1 <= weight <= 25600):
            raise click.BadParameter('Weight must be between 1 and 25600.')

        wcmp_handler(ctx, db, str(weight))
    elif not ctx.invoked_subcommand:
        click.echo(ctx.get_help())
        ctx.exit()


@DEVICE_GLOBAL_WCMP.command(
    name="cumulative"
)
@clicommon.pass_db
@click.pass_context
def DEVICE_GLOBAL_WCMP_CUMULATIVE(ctx, db):
    """Cumulative bandwidth of all multipaths"""
    wcmp_handler(ctx, db, "cumulative")


@DEVICE_GLOBAL_WCMP.command(
    name="num-multipaths"
)
@clicommon.pass_db
@click.pass_context
def DEVICE_GLOBAL_WCMP_NUM_MULTIPATHS(ctx, db):
    """Bandwidth based on number of multipaths"""
    wcmp_handler(ctx, db, "num_multipaths")


@DEVICE_GLOBAL_WCMP.command(
    name="disabled"
)
@clicommon.pass_db
@click.pass_context
def DEVICE_GLOBAL_WCMP_DISABLED(ctx, db):
    """Disable Weighted-Cost Multi-Path (W-ECMP) feature"""
    wcmp_handler(ctx, db, "false")
    
#
# BGP device-global bandwidth --------------------------------------------------------------------------------------------
#

@DEVICE_GLOBAL.group(
    name="bandwidth",
    cls=clicommon.AliasedGroup
)
def DEVICE_GLOBAL_BANDWIDTH():
    """ Configure bestpath for bandwidth feature """

    pass

@DEVICE_GLOBAL_BANDWIDTH.command(
    name="ignore"
)
@clicommon.pass_db
@click.pass_context
def DEVICE_GLOBAL_BANDWIDTH_IGNORE(ctx, db):
    """ Ignore link bandwidth (i.e., do regular ECMP, not weighted) """

    bandwidth_handler(ctx, db, "ignore")
    
@DEVICE_GLOBAL_BANDWIDTH.command(
    name="active"
)
@clicommon.pass_db
@click.pass_context
def DEVICE_GLOBAL_BANDWIDTH_ACTIVE(ctx, db):
    """ Allow for normal behavior without bestpath for bandwidth """

    bandwidth_handler(ctx, db, "active")
    
@DEVICE_GLOBAL_BANDWIDTH.command(
    name="skip_missing"
)
@clicommon.pass_db
@click.pass_context
def DEVICE_GLOBAL_BANDWIDTH_SKIP_MISSING(ctx, db):
    """ Ignore paths without link bandwidth for W-ECMP (if other paths have it) """

    bandwidth_handler(ctx, db, "skip_missing")
    
@DEVICE_GLOBAL_BANDWIDTH.command(
    name="default_weight_for_missing"
)
@clicommon.pass_db
@click.pass_context
def DEVICE_GLOBAL_BANDWIDTH_DEFAULT_WEIGHT(ctx, db):
    """ Assign a low default weight (value 1) to paths not having link bandwidth """

    bandwidth_handler(ctx, db, "default_weight_for_missing")

