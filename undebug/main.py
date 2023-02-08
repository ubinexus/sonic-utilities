import click
import subprocess
from shlex import join

def run_command(command, pager=False):
    command_str = join(command)
    click.echo(click.style("Command: ", fg='cyan') + click.style(command_str, fg='green'))
    p = subprocess.Popen(command, text=True, stdout=subprocess.PIPE)
    output = p.stdout.read()
    if pager:
        click.echo_via_pager(output)
    else:
        click.echo(output)


CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help', '-?'])
#
# 'cli' group (root group) ###
#

@click.group(cls=click.Group, context_settings=CONTEXT_SETTINGS, invoke_without_command=True)
def cli():
    """SONiC command line - 'debug' command"""
    pass


vtysh_cmd = ["sudo", "vtysh", "-c"]
bgp_cmd = "no debug bgp "
zebra_cmd = "no debug zebra "
p = subprocess.check_output(vtysh_cmd + ['show version'], text=True)
if 'FRRouting' in p:
    #
    # 'bgp' group for FRR ###
    #
    @cli.group()
    def bgp():
        """debug bgp group """
        pass

    @bgp.command('allow-martians')
    def allow_martians():
        """BGP allow martian next hops"""
        command = vtysh_cmd + [bgp_cmd + "allow-martians"]
        run_command(command)

    @bgp.command()
    @click.argument('additional', type=click.Choice(['segment']), required=False)
    def as4(additional):
        """BGP AS4 actions"""
        command = vtysh_cmd + ["no debug bgp as4"]
        if additional is not None:
            command = vtysh_cmd + [bgp_cmd + "as4 segment"]
        run_command(command)

    @bgp.command()
    @click.argument('prefix', required=True)
    def bestpath(prefix):
        """BGP bestpath"""
        command = vtysh_cmd + [bgp_cmd + "bestpath %s" % prefix]
        run_command(command)

    @bgp.command()
    @click.argument('prefix_or_iface', required=False)
    def keepalives(prefix_or_iface):
        """BGP Neighbor Keepalives"""
        command = vtysh_cmd + [bgp_cmd + "keepalives"]
        if prefix_or_iface is not None:
            command = vtysh_cmd + [bgp_cmd + "keepalives " + prefix_or_iface]
        run_command(command)

    @bgp.command('neighbor-events')
    @click.argument('prefix_or_iface', required=False)
    def neighbor_events(prefix_or_iface):
        """BGP Neighbor Events"""
        command = vtysh_cmd + [bgp_cmd + "neighbor-events"]
        if prefix_or_iface is not None:
            command = vtysh_cmd + [bgp_cmd + "neighbor-events " + prefix_or_iface]
        run_command(command)

    @bgp.command()
    def nht():
        """BGP nexthop tracking events"""
        command = vtysh_cmd + [bgp_cmd + "nht"]
        run_command(command)

    @bgp.command()
    @click.argument('additional', type=click.Choice(['error']), required=False)
    def pbr(additional):
        """BGP policy based routing"""
        command = vtysh_cmd + [bgp_cmd + "pbr"]
        if additional is not None:
            command = vtysh_cmd + [bgp_cmd + "pbr error"]
        run_command(command)

    @bgp.command('update-groups')
    def update_groups():
        """BGP update-groups"""
        command = vtysh_cmd + [bgp_cmd + "update-groups"]
        run_command(command)

    @bgp.command()
    @click.argument('direction', type=click.Choice(['in', 'out', 'prefix']), required=False)
    @click.argument('prefix', required=False)
    def updates(direction, prefix):
        """BGP updates"""
        bgp_ud_cmd = "no debug bgp updates"
        if direction is not None:
            bgp_ud_cmd += ' ' + direction
        if prefix is not None:
            bgp_ud_cmd += ' ' + prefix
        command = vtysh_cmd + [bgp_ud_cmd]
        run_command(command)

    @bgp.command()
    @click.argument('prefix', required=False)
    def zebra(prefix):
        """BGP Zebra messages"""
        bgp_zb_cmd = "no debug bgp zebra"
        if prefix is not None:
            bgp_zb_cmd += ' ' + prefix
        command = vtysh_cmd + [bgp_zb_cmd]
        run_command(command)

    #
    # 'zebra' group for FRR ###
    #
    @cli.group()
    def zebra():
        """debug zebra group"""
        pass

    @zebra.command()
    @click.argument('detailed', type=click.Choice(['detailed']), required=False)
    def dplane(detailed):
        """Debug zebra dataplane events"""
        zebra_dplane_cmd = "no debug zebra dplane"
        if detailed is not None:
            zebra_dplane_cmd += ' ' + "detailed"
        command = vtysh_cmd + [zebra_dplane_cmd]
        run_command(command)

    @zebra.command()
    def events():
        """Debug option set for zebra events"""
        command = vtysh_cmd + ["events"]
        run_command(command)

    @zebra.command()
    def fpm():
        """Debug zebra FPM events"""
        command = vtysh_cmd + [zebra_cmd + "fpm"]
        run_command(command)

    @zebra.command()
    def kernel():
        """Debug option set for zebra between kernel interface"""
        command = vtysh_cmd + [zebra_cmd + "kernel"]
        run_command(command)

    @zebra.command()
    def nht():
        """Debug option set for zebra next hop tracking"""
        command = vtysh_cmd + [zebra_cmd + "nht"]
        run_command(command)

    @zebra.command()
    def packet():
        """Debug option set for zebra packet"""
        command = vtysh_cmd + [zebra_cmd + "packet"]
        run_command(command)

    @zebra.command()
    @click.argument('detailed', type=click.Choice(['detailed']), required=False)
    def rib(detailed):
        """Debug RIB events"""
        command = vtysh_cmd + [zebra_cmd + "rib"]
        if detailed is not None:
            command = vtysh_cmd + [zebra_cmd + "rib detailed"]
        run_command(command)

    @zebra.command()
    def vxlan():
        """Debug option set for zebra VxLAN (EVPN)"""
        command = vtysh_cmd + [zebra_cmd + "vxlan"]
        run_command(command)

else:
    #
    # 'bgp' group for quagga ###
    #
    @cli.group(invoke_without_command=True)
    @click.pass_context
    def bgp(ctx):
        """debug bgp off"""
        if ctx.invoked_subcommand is None:
            command = vtysh_cmd + [bgp_cmd]
            run_command(command)

    @bgp.command()
    def events():
        """debug bgp events off"""
        command = vtysh_cmd + [bgp_cmd + "events"]
        run_command(command)

    @bgp.command()
    def updates():
        """debug bgp updates off"""
        command = vtysh_cmd + [bgp_cmd + "updates"]
        run_command(command)

    @bgp.command()
    def as4():
        """debug bgp as4 actions off"""
        command = vtysh_cmd + [bgp_cmd + "as4"]
        run_command(command)

    @bgp.command()
    def filters():
        """debug bgp filters off"""
        command = vtysh_cmd + [bgp_cmd + "filters"]
        run_command(command)

    @bgp.command()
    def fsm():
        """debug bgp finite state machine off"""
        command = vtysh_cmd + [bgp_cmd + "fsm"]
        run_command(command)

    @bgp.command()
    def keepalives():
        """debug bgp keepalives off"""
        command = vtysh_cmd + [bgp_cmd + "keepalives"]
        run_command(command)

    @bgp.command()
    def zebra():
        """debug bgp zebra messages off"""
        command = vtysh_cmd + [bgp_cmd + "zebra"]
        run_command(command)

    #
    # 'zebra' group for quagga ###
    #
    @cli.group()
    def zebra():
        """debug zebra group"""
        pass

    @zebra.command()
    def events():
        """debug option set for zebra events"""
        command = vtysh_cmd + [zebra_cmd + "events"]
        run_command(command)

    @zebra.command()
    def fpm():
        """debug zebra FPM events"""
        command = vtysh_cmd + [zebra_cmd + "fpm"]
        run_command(command)

    @zebra.command()
    def kernel():
        """debug option set for zebra between kernel interface"""
        command = vtysh_cmd + [zebra_cmd + "kernel"]
        run_command(command)

    @zebra.command()
    def packet():
        """debug option set for zebra packet"""
        command = vtysh_cmd + [zebra_cmd + "packet"]
        run_command(command)

    @zebra.command()
    def rib():
        """debug RIB events"""
        command = vtysh_cmd + [zebra_cmd + "rib"]
        run_command(command)


if __name__ == '__main__':
    cli()
