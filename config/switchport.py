import click
from .utils import log
import utilities_common.cli as clicommon

# since default vlan id is 1
default_vid = 1

#
# 'switchport' mode ('config switchport ...')
#


@click.group(cls=clicommon.AbbreviationGroup, name='switchport')
def switchport():
    """Switchport mode configuration tasks"""
    pass


@switchport.add_command("mode")
@click.argument("type", metavar="<mode_type>", Required=True, type=click.Choice(["access", "trunk", "routed"]))
@click.argument("port", metavar="port", required=True)
@clicommon.pass_db
def access_mode(db, type, port):
    """switchport mode help commands\nmode_type can either be:\n\t access for untagged mode\n\t trunk for tagged mode \n\t routed for non vlan mode"""

    ctx = click.get_current_context()

    log.log_info(
        "'switchport mode {} {}' executing...".format(type, port))

    vlan = 'Vlan{}'.format(default_vid)

    # checking if port name with alias exists
    if clicommon.get_interface_naming_mode() == "alias":
        alias = port
        iface_alias_converter = clicommon.InterfaceAliasConverter(db)
        port = iface_alias_converter.alias_to_name(port)
        if port is None:
            ctx.fail("cannot find port name for alias {}".format(alias))

    # mode type is either access or trunk
    if type != "routed":

        # checking if default Vlan has been created or not
        if not clicommon.check_if_vlanid_exist(db.cfgdb, vlan):

            db.cfgdb.set_entry('VLAN', vlan, {'vlanid': default_vid})

            log.log_info(
                "'vlan add {}' in switchport mode executing...".format(default_vid))

        # tagging_mode will be untagged if access and tagged if trunk
        if clicommon.is_port_mirror_dst_port(db.cfgdb, port):
            ctx.fail("{} is configured as mirror destination port".format(port))

        if clicommon.is_port_vlan_member(db.cfgdb, port, vlan):
            ctx.fail("{} is already a member of {}".format(port, vlan))

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

        # checking if it exists in default Vlan1
        if clicommon.port_vlan_member_exist(db, vlan, port):

            existing_port_vlan_status = clicommon.get_existing_port_vlan_status(
                db, vlan, port)
            existing_status = "access" if existing_port_vlan_status == "untagged" else "trunk"

            if (type == existing_status):
                ctx.fail("{} is already in {} mode!".format(port, type))

            elif (type != existing_status):

                if (type == "trunk" and existing_status == "access"):
                    db.cfgdb.mod_entry('VLAN_MEMBER', (vlan, port), {
                        'tagging_mode': "tagged"})

                elif (type == "access" and existing_status == "trunk"):
                    db.cfgdb.mod_entry('VLAN_MEMBER', (vlan, port), {
                        'tagging_mode': "untagged"})

                # switched the mode of already defined switchport
                click.echo("{} switched from {} to {} mode".format(
                    port, existing_status, type))

        # if it not exists already set entry
        else:
            db.cfgdb.set_entry('VLAN_MEMBER', (vlan, port), {
                               'tagging_mode': "untagged" if type == "access" else "tagged"})

            click.echo("{} switched to {} mode. Added to default {}".format(
                port, type, vlan))

    # if mode type is routed
    else:

        if clicommon.check_if_vlanid_exist(db.cfgdb, vlan) == False:
            ctx.fail("{} is already in routed mode".format(port))

        if not clicommon.is_port_vlan_member(db.cfgdb, port, vlan):
            ctx.fail("{} is already in routed mode".format(port))

        db.cfgdb.set_entry('VLAN_MEMBER', (vlan, port), None)

        click.echo("{} is in {} mode. Removed from default {}".format(
            port, type, vlan))
