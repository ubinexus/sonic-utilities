#!/usr/sbin/env python

import sys
import click
import subprocess

def run_command(command, display_cmd=False, ignore_error=False):
    """Run bash command and print output to stdout
    """
    if display_cmd == True:
        click.echo(click.style("Running command: ", fg='cyan') + click.style(command, fg='green'))

    proc = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)
    (out, err) = proc.communicate()

    if len(out) > 0:
        click.echo(out)

    if proc.returncode != 0 and not ignore_error:
        sys.exit(proc.returncode)


class AbbreviationGroup(click.Group):
    """This subclass of click.Group supports abbreviated subgroup/subcommand names
    """

    def get_command(self, ctx, cmd_name):
        # Try to get builtin commands as normal
        rv = click.Group.get_command(self, ctx, cmd_name)
        if rv is not None:
            return rv

        # Allow automatic abbreviation of the command.  "status" for
        # instance will match "st".  We only allow that however if
        # there is only one command.
        # If there are multiple matches and the shortest one is the common prefix of all the matches, return
        # the shortest one
        matches = []
        shortest = None
        for x in self.list_commands(ctx):
            if x.lower().startswith(cmd_name.lower()):
                matches.append(x)
                if not shortest:
                    shortest = x
                elif len(shortest) > len(x):
                    shortest = x

        if not matches:
            return None
        elif len(matches) == 1:
            return click.Group.get_command(self, ctx, matches[0])
        else:
            for x in matches:
                if not x.startswith(shortest):
                    break
            else:
                return click.Group.get_command(self, ctx, shortest)

            ctx.fail('Too many matches: %s' % ', '.join(sorted(matches)))

