#!/usr/bin/python -u
# -*- coding: utf-8 -*-

__all__ = ['log_info', 'log_error', 'log_warning', 'log_debug',
        'do_exit', 'get_configdb_data', 
        'AbbreviationGroup', 'get_hostname']

import sys
import os
import syslog
import click
import inspect
from swsssdk import ConfigDBConnector

SYSLOG_IDENTIFIER = "config"

def get_hostname():
    return os.uname()[1]

def do_exit(msg):
    m = "FATAL failure: {}. Exiting...".format(msg)
    _log_msg(syslog.LOG_ERR, True, inspect.stack()[1][1], inspect.stack()[1][2], m)
    raise SystemExit(m)


def get_configdb_data(table, key):
    config_db = ConfigDBConnector()
    config_db.connect()
    data = config_db.get_table(table)
    return data[key] if key in data else None


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

