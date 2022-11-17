import click
from .utils import log
import utilities_common.cli as clicommon

#
# 'switchport' mode ('config switchport ...')
#


@click.group(cls=clicommon.AbbreviationGroup, name='switchport')
def switchport():
    """Switchport mode configuration tasks"""
    pass


@switchport.command("mode")
@click.argument("type", metavar="<mode_type>", required=True, type=click.Choice(["access", "trunk", "routed", "hybrid"]))
@click.argument("port", metavar="port", required=True)
@clicommon.pass_db
def switchport_mode(db, type, port):
    """switchport mode help commands\nmode_type can either be:\n\t -> access \n\t -> trunk \n\t -> routed"""

    ctx = click.get_current_context()

    log.log_info("'switchport mode {} {}' executing...".format(type, port))
    mode_exists_status = True

    # checking if port name with alias exists
    if clicommon.get_interface_naming_mode() == "alias":
        alias = port
        iface_alias_converter = clicommon.InterfaceAliasConverter(db)
        port = iface_alias_converter.alias_to_name(port)
        if port is None:
            ctx.fail("cannot find port name for alias {}".format(alias))

    if clicommon.is_port_mirror_dst_port(db.cfgdb, port):
            ctx.fail("{} is configured as mirror destination port".format(port))


    if clicommon.is_valid_port(db.cfgdb, port):
        is_port = True
    elif clicommon.is_valid_portchannel(db.cfgdb, port):
        is_port = False
    else:
        ctx.fail("{} does not exist".format(port))

    if (is_port and clicommon.is_port_router_interface(db.cfgdb, port)) or \
            (not is_port and clicommon.is_pc_router_interface(db.cfgdb, port)):
        ctx.fail("{} is a router interface!".format(port))

    portchannel_member_table = db.cfgdb.get_table('PORTCHANNEL_MEMBER')

    if (is_port and clicommon.interface_is_in_portchannel(portchannel_member_table, port)):
        ctx.fail("{} is part of portchannel!".format(port))

    port_table_data = db.cfgdb.get_table('PORT')
    port_data = port_table_data[port]

    # mode type is either access or trunk
    if type != "routed":

        if "mode" in port_data:
            existing_mode = port_data["mode"]
        else:
            existing_mode = "routed"
            mode_exists_status = False

        if existing_mode == "routed":
            if mode_exists_status:
                db.cfgdb.mod_entry("PORT", port, {"mode": "{}".format(type)})
            if not mode_exists_status:
                port_data["mode"] = type
                db.cfgdb.set_entry("PORT", port, port_data)
        
        if existing_mode == type:
            ctx.fail("{} is already in the {} mode".format(port,type))
        else: 
            if existing_mode == "access" and (type == "trunk" or type == "hybrid"):
                pass
            elif existing_mode == "trunk":
                if type == "access":
                    if clicommon.interface_is_tagged_member(db.cfgdb,port):
                        ctx.fail("{} is in {} mode and have tagged member|s.\nRemove tagged member|s from {} to switch to {} mode".format(port,existing_mode,port,type))

            elif existing_mode == "hybrid":
                if type == "access":
                    if clicommon.interface_is_tagged_member(db.cfgdb,port):
                        ctx.fail("{} has tagged member|s. \nRemove them to change mode to {}".format(port,type))

                    if clicommon.interface_has_multiple_untagged_member(db.cfgdb,port):
                        ctx.fail("{} has more than one untagged member. \nRemove them to change mode to {}".format(port,type))
                        
                elif type == "trunk":
                    if clicommon.interface_has_multiple_untagged_member(db.cfgdb,port):
                        ctx.fail("{} has more than one untagged member|s. \nRemove them to change mode to {}".format(port,type))


            db.cfgdb.mod_entry("PORT", port, {"mode": "{}".format(type)})

        click.echo("{} switched from {} to {} mode".format(port, existing_mode, type))

    # if mode type is routed
    else:

        if clicommon.interface_is_tagged_member(db.cfgdb,port):
            ctx.fail("{} has tagged member|s. \nRemove them to change mode to {}".format(port,type))

        if clicommon.interface_is_untagged_member(db.cfgdb,port):
            ctx.fail("{} has untagged member. \nRemove them to change mode to {}".format(port,type))

        if "mode" in port_data:
            existing_mode = port_data["mode"]
        else:
            existing_mode = "routed"
            mode_exists_status = False
        
        if not mode_exists_status:
            port_data["mode"] = type
            db.cfgdb.set_entry("PORT", port, {"mode": "{}".format(type)})
            click.echo("{} switched to {} mode".format(port, type))
        
        if mode_exists_status and existing_mode == type:
            ctx.fail("{} is already in {} mode".format(port,type))
        
        else:
            db.cfgdb.mod_entry("PORT", port, {"mode": "{}".format(type)})
            click.echo("{} switched from {} to {} mode".format(port,existing_mode,type))

@switchport.group(cls=clicommon.AbbreviationGroup, name='hybrid')
def switchport_hybrid():
    pass

@switchport_hybrid.command("PVID")
@click.argument("pvid", metavar="pvid", required=True, type=int)
@click.argument("port", metavar="port", required=True)
@clicommon.pass_db
def switchport_mode(db, pvid, port):
    """switchport hybrid pvid sets the PVID for the hybrid interface"""

    ctx = click.get_current_context()

    log.log_info("'switchport mode {} {}' executing...".format(type, port))

    if clicommon.get_interface_naming_mode() == "alias":  # TODO: MISSING CONSTRAINT IN YANG MODEL
        alias = port
        iface_alias_converter = clicommon.InterfaceAliasConverter(db)
        port = iface_alias_converter.alias_to_name(alias)
        if port is None:
            ctx.fail("cannot find port name for alias {}".format(alias))

    # TODO: MISSING CONSTRAINT IN YANG MODEL
    if clicommon.is_port_mirror_dst_port(db.cfgdb, port):
        ctx.fail("{} is configured as mirror destination port".format(port))

    if clicommon.is_valid_port(db.cfgdb, port):
        is_port = True
    elif clicommon.is_valid_portchannel(db.cfgdb, port):
        is_port = False
    else:
        ctx.fail("{} does not exist".format(port))

    if (is_port and clicommon.is_port_router_interface(db.cfgdb, port)) or \
            (not is_port and clicommon.is_pc_router_interface(db.cfgdb, port)):  # TODO: MISSING CONSTRAINT IN YANG MODEL
        ctx.fail("{} is a router interface!".format(port))

    portchannel_member_table = db.cfgdb.get_table('PORTCHANNEL_MEMBER')

    # TODO: MISSING CONSTRAINT IN YANG MODEL
    if (is_port and clicommon.interface_is_in_portchannel(portchannel_member_table, port)):
        ctx.fail("{} is part of portchannel!".format(port))
    
    port_table_data = db.cfgdb.get_table('PORT')
    port_data = port_table_data[port]
    
    if "mode" not in port_data:
        ctx.fail("{} is in routed mode!\nUse switchport mode command to change port mode".format(port))
    else:
        if port_data["mode"] != "hybrid":
            ctx.fail("{} is not in hybrid mode!\nUse switchport mode command to change port mode to hybrid to set PVID".format(port))

    port_data["pvid"] = pvid
    db.cfgdb.set_entry("PORT", port, port_data)


    


