import click
from debug.main import *


###############################################################################
#
# 'undebug bgp' cli stanza
#
###############################################################################


@cli.group(cls=AliasedGroup, default_if_no_args=False)
def bgp():
    """undebug bgp events """
    pass

@bgp.command()
def as4():
    """undebug bgp AS4 actions """
    command = 'sudo vtysh -c "no debug bgp as4"'
    run_command(command)

@bgp.command()
def bestpath():
    """undebug bgp bestpath """
    command = 'sudo vtysh -c "no debug bgp bestpath"'
    run_command(command)

@bgp.command()
def keepalives():
    """undebug bgp keepalives """
    command = 'sudo vtysh -c "no debug bgp keepalives"'
    run_command(command)

@bgp.command()
def neighborEvents():
    """undebug bgp neighbor events """
    command = 'sudo vtysh -c "no debug bgp neighbor-events"'
    run_command(command)

@bgp.command()
def nht():
    """undebug bgp nexthop tracking events """
    command = 'sudo vtysh -c "no debug bgp nht"'
    run_command(command)

@bgp.command()
def updateGroups():
    """undebug bgp update-group events """
    command = 'sudo vtysh -c "no debug bgp update-groups"'
    run_command(command)

@bgp.command()
def updates():
    """undebug bgp updates """
    command = 'sudo vtysh -c "no debug bgp updates"'
    run_command(command)

@bgp.command()
def zebra():
    """undebug bgp zebra messages """
    command = 'sudo vtysh -c "no debug bgp zebra"'
    run_command(command)


###############################################################################
#
# 'undebug zebra' cli stanza
#
###############################################################################


@cli.group(cls=AliasedGroup, default_if_no_args=False)
def zebra():
    """undebug zebra events """
    pass

@zebra.command()
def events():
    """undebug zebra events """
    command = 'sudo vtysh -c "no debug zebra events"'
    run_command(command)

@zebra.command()
def fpm():
    """undebug zebra fpm events """
    command = 'sudo vtysh -c "no debug zebra fpm"'
    run_command(command)

@zebra.command()
def kernel():
    """undebug zebra's kernel-interface events """
    command = 'sudo vtysh -c "no debug zebra kernel"'
    run_command(command)

@zebra.command()
def mpls():
    """undebug zebra MPLS events """
    command = 'sudo vtysh -c "no debug zebra mpls"'
    run_command(command)

@zebra.command()
def nht():
    """undebug zebra next-hop-tracking events """
    command = 'sudo vtysh -c "no debug zebra nht"'
    run_command(command)

@zebra.command()
def packet():
    """undebug zebra packets """
    command = 'sudo vtysh -c "no debug zebra packet"'
    run_command(command)

@zebra.command()
def pseudowires():
    """undebug zebra pseudowire events """
    command = 'sudo vtysh -c "no debug zebra pseudowires"'
    run_command(command)

@zebra.command()
def rib():
    """undebug zebra RIB events """
    command = 'sudo vtysh -c "no debug zebra rib"'
    run_command(command)
