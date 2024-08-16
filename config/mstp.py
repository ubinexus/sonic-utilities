import click
import utilities_common.cli as clicommon

#
# This group has MSTP commands and subgroups
#
@click.group(cls=clicommon.AliasedGroup)
@click.pass_context
def spanning_tree(ctx):
    '''Manage MSTP (Multiple Spanning Tree Protocol) settings'''
    pass

@spanning_tree.group('global', cls=clicommon.AliasedGroup, invoke_without_command=True)
@click.pass_context
def mstp_global(ctx):
    if ctx.invoked_subcommand is None:
        click.echo('Please specify a command.')

@mstp_global.command('enable')
@click.pass_context
def enable_mstp(ctx):
    command = 'sudo mstpctl enable'
    clicommon.run_command(command)

@mstp_global.command('disable')
@click.pass_context
def disable_mstp(ctx):
    command = 'sudo mstpctl disable'
    clicommon.run_command(command)

@mstp_global.command('max_hops')
@click.argument('max_hops_value', metavar='<max_hops_value>', type=int, required=True)
@click.pass_context
def set_max_hops(ctx, max_hops_value):
    command = f'sudo mstpctl max_hops {max_hops_value}'
    clicommon.run_command(command)

@mstp_global.command('hello')
@click.argument('hello_value', metavar='<hello_value>', type=int, required=True)
@click.pass_context
def set_hello_interval(ctx, hello_value):
    command = f'sudo mstpctl hello {hello_value}'
    clicommon.run_command(command)

@mstp_global.command('max_age')
@click.argument('max_age_value', metavar='<max_age_value>', type=int, required=True)
@click.pass_context
def set_max_age(ctx, max_age_value):
    command = f'sudo mstpctl max_age {max_age_value}'
    clicommon.run_command(command)

@spanning_tree.group('region', cls=clicommon.AliasedGroup, invoke_without_command=True)
@click.pass_context
def mstp_region(ctx):
    if ctx.invoked_subcommand is None:
        click.echo('Please specify a command.')

@mstp_region.command('name')
@click.argument('region_name', metavar='<region_name>', required=True)
@click.pass_context
def set_region_name(ctx, region_name):
    command = f'sudo mstpctl region-name {region_name}'
    clicommon.run_command(command)

@mstp_region.command('revision')
@click.argument('revision_number', metavar='<revision_number>', type=int, required=True)
@click.pass_context
def set_revision_number(ctx, revision_number):
    command = f'sudo mstpctl revision {revision_number}'
    clicommon.run_command(command)

@spanning_tree.group('instance', cls=clicommon.AliasedGroup, invoke_without_command=True)
@click.pass_context
def mstp_instance(ctx):
    if ctx.invoked_subcommand is None:
        click.echo('Please specify a command.')

@mstp_instance.command('priority')
@click.argument('instance_id', metavar='<instance_id>', required=True)
@click.argument('priority_value', metavar='<priority_value>', type=int, required=True)
@click.pass_context
def set_instance_priority(ctx, instance_id, priority_value):
    command = f'sudo mstpctl instance {instance_id} priority {priority_value}'
    clicommon.run_command(command)

@mstp_instance.command('vlan')
@click.argument('instance_id', metavar='<instance_id>', required=True)
@click.argument('operation', metavar='<operation>', type=click.Choice(['add', 'del']), required=True)
@click.argument('vlan_id', metavar='<vlan_id>', type=int, required=True)
@click.pass_context
def vlan_mapping(ctx, instance_id, operation, vlan_id):
    command = f'sudo mstpctl instance {instance_id} vlan {operation} {vlan_id}'
    clicommon.run_command(command)

@spanning_tree.group('interface', cls=clicommon.AliasedGroup, invoke_without_command=True)
@click.pass_context
def mstp_interface(ctx):
    if ctx.invoked_subcommand is None:
        click.echo('Please specify a command.')

@mstp_interface.command('priority')
@click.argument('ifname', metavar='<ifname>', required=True)
@click.argument('priority_value', metavar='<priority_value>', type=int, required=True)
@click.pass_context
def set_interface_priority(ctx, ifname, priority_value):
    command = f'sudo mstpctl interface {ifname} priority {priority_value}'
    clicommon.run_command(command)

@mstp_interface.command('cost')
@click.argument('ifname', metavar='<ifname>', required=True)
@click.argument('cost_value', metavar='<cost_value>', type=int, required=True)
@click.pass_context
def set_interface_cost(ctx, ifname, cost_value):
    command = f'sudo mstpctl interface {ifname} cost {cost_value}'
    clicommon.run_command(command)

@mstp_interface.command('enable')
@click.argument('ifname', metavar='<ifname>', required=True)
@click.pass_context
def enable_interface(ctx, ifname):
    command = f'sudo mstpctl interface {ifname} enable'
    clicommon.run_command(command)

@mstp_interface.command('disable')
@click.argument('ifname', metavar='<ifname>', required=True)
@click.pass_context
def disable_interface(ctx, ifname):
    command = f'sudo mstpctl interface {ifname} disable'
    clicommon.run_command(command)

@mstp_interface.command('edgeport')
@click.argument('ifname', metavar='<ifname>', required=True)
@click.argument('state', metavar='<state>', type=click.Choice(['enable', 'disable']), required=True)
@click.pass_context
def set_edgeport(ctx, ifname, state):
    command = f'sudo mstpctl interface {ifname} edgeport {state}'
    clicommon.run_command(command)

@mstp_interface.command('guard')
@click.argument('ifname', metavar='<ifname>', required=True)
@click.argument('guard_type', metavar='<guard_type>', type=click.Choice(['root', 'bpdu']), required=True)
@click.argument('state', metavar='<state>', type=click.Choice(['enable', 'disable']), required=True)
@click.pass_context
def set_guard(ctx, ifname, guard_type, state):
    command = f'sudo mstpctl interface {ifname} guard {guard_type} {state}'
    clicommon.run_command(command)
