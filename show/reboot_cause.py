#! /usr/bin/python -u

import json
import os
import sys

import click

PREVIOUS_REBOOT_CAUSE_FILE = "/host/reboot-cause/previous-reboot-cause.json"
USER_ISSUED_REBOOT_CAUSE_REGEX ="User issued \'{}\' command [User: {}, Time: {}]"


#
# 'reboot-cause' group ("show reboot-cause")
#
def read_reboot_cause_file():
    result=""
    if os.path.exists(PREVIOUS_REBOOT_CAUSE_FILE):
        with open(PREVIOUS_REBOOT_CAUSE_FILE) as f:
            result = json.load(f)
    return result

@cli.group('reboot-cause', short_help='Show cause of most recent reboot', invoke_without_command=True)
@click.pass_context
def reboot_cause(ctx):
    if ctx.invoked_subcommand is None:
        last_reboot_cause = ""
        # Read the last previous reboot cause
        data = read_reboot_cause_file()
        if data['user']:
            last_reboot_cause = USER_ISSUED_REBOOT_CAUSE_REGEX.format(data['cause'], data['user'], data['time'])
        else:
            last_reboot_cause = "{}".format(data['cause'])

        click.echo(last_reboot_cause)

# 'history' subcommand ("show reboot-cause history")
@reboot_cause.command()
def history():
    """Show history of reboot-cause"""
    REBOOT_CAUSE_TABLE_NAME = "REBOOT_CAUSE"
    TABLE_NAME_SEPARATOR = '|'
    db = SonicV2Connector(host='127.0.0.1')
    db.connect(db.STATE_DB, False)   # Make one attempt only
    prefix = REBOOT_CAUSE_TABLE_NAME + TABLE_NAME_SEPARATOR
    _hash = '{}{}'.format(prefix, '*')
    table_keys = db.keys(db.STATE_DB, _hash)
    table_keys.sort(reverse=True)

    table = []
    for tk in table_keys:
        entry = db.get_all(db.STATE_DB, tk)
        r = []
        r.append(tk.replace(prefix,""))
        r.append(entry['cause'] if 'cause' in entry else "")
        r.append(entry['time'] if 'time' in entry else "")
        r.append(entry['user'] if 'user' in entry else "")
        r.append(entry['comment'] if 'comment' in entry else "")
        table.append(r)

    header = ['Name', 'Cause', 'Time', 'User', 'Comment']
    click.echo(tabulate(table, header))

