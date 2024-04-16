import json
import os
import sys

import click
from tabulate import tabulate
import textwrap
from swsscommon.swsscommon import SonicV2Connector
import utilities_common.cli as clicommon


PREVIOUS_REBOOT_CAUSE_FILE_PATH = "/host/reboot-cause/previous-reboot-cause.json"


def read_reboot_cause_file():
    reboot_cause_dict = {}

    if os.path.exists(PREVIOUS_REBOOT_CAUSE_FILE_PATH):
        with open(PREVIOUS_REBOOT_CAUSE_FILE_PATH) as prev_reboot_cause_file:
            try:
                reboot_cause_dict = json.load(prev_reboot_cause_file)
            except json.JSONDecodeError as err:
                click.echo("Failed to load JSON file '{}'!".format(PREVIOUS_REBOOT_CAUSE_FILE_PATH), err=True)

    return reboot_cause_dict

# Function to fetch reboot cause data from database
def fetch_reboot_cause_from_db(module_name):
    table = []
    r = []
    wrapper = textwrap.TextWrapper(width=30)

    # Read the previous reboot cause
    if module_name == "all" or module_name == "SWITCH":
        reboot_cause_dict = read_reboot_cause_file()
        reboot_cause = reboot_cause_dict.get("cause", "Unknown")
        reboot_user = reboot_cause_dict.get("user", "N/A")
        reboot_time = reboot_cause_dict.get("time", "N/A")

        r.append("SWITCH")
        r.append(reboot_cause if reboot_cause else "")
        r.append(reboot_time if reboot_time else "")
        r.append(reboot_user if reboot_user else "")
        table.append(r)

        if module_name == "SWITCH":
            return table

    REBOOT_CAUSE_TABLE_NAME = "REBOOT_CAUSE"
    TABLE_NAME_SEPARATOR = '|'
    db = SonicV2Connector(host='127.0.0.1')
    db.connect(db.STATE_DB, False)   # Make one attempt only
    prefix = REBOOT_CAUSE_TABLE_NAME + TABLE_NAME_SEPARATOR
    _hash = '{}{}'.format(prefix, '*')
    table_keys = db.keys(db.STATE_DB, _hash)
    if table_keys is not None:
        table_keys.sort(reverse=True)

    d = []
    append = False
    for tk in table_keys:
        r = []
        entry = db.get_all(db.STATE_DB, tk)
        if 'device' in entry:
            if module_name != entry['device'] and module_name != "all":
                continue
            if entry['device'] in d:
                append = False
                continue
            else:
                append = True
                d.append(entry['device'])
            if not module_name is None:
                r.append(entry['device'] if 'device' in entry else "")
            if 'cause' in entry:
                wrp_cause = wrapper.fill(entry['cause'])
            r.append(wrp_cause if 'cause' in entry else "")
            r.append(entry['time'] if 'time' in entry else "")
            r.append(entry['user'] if 'user' in entry else "")
            if append == True:
                table.append(r)

    return table

# Function to fetch reboot cause history data from database
def fetch_reboot_cause_history_from_db(module_name):
    REBOOT_CAUSE_TABLE_NAME = "REBOOT_CAUSE"
    TABLE_NAME_SEPARATOR = '|'
    db = SonicV2Connector(host='127.0.0.1')
    db.connect(db.STATE_DB, False)   # Make one attempt only
    prefix = REBOOT_CAUSE_TABLE_NAME + TABLE_NAME_SEPARATOR
    _hash = '{}{}'.format(prefix, '*')
    table_keys = db.keys(db.STATE_DB, _hash)
    wrapper = textwrap.TextWrapper(width=30)

    if table_keys is not None:
        table_keys.sort(reverse=True)

        table = []
        device_present = False
        for tk in table_keys:
            entry = db.get_all(db.STATE_DB, tk)
            if 'device' in entry:
                device_present = True
            r = []
            if not module_name is None and device_present: 
                r.append(entry['device'] if 'device' in entry else "SWITCH")
            r.append(tk.replace(prefix, ""))
            if 'cause' in entry:
                wrp_cause = wrapper.fill(entry['cause'])
            r.append(wrp_cause if 'cause' in entry else "")
            r.append(entry['time'] if 'time' in entry else "")
            r.append(entry['user'] if 'user' in entry else "")
            if 'comment' in entry:
                wrp_comment = wrapper.fill(entry['comment'])
            r.append(wrp_comment if 'comment' in entry else "")
            if module_name == 'all' or module_name == entry['device']:
                table.append(r)

    return table

#
# 'reboot-cause' group ("show reboot-cause")
#
@click.group(cls=clicommon.AliasedGroup, invoke_without_command=True)
@click.pass_context
def reboot_cause(ctx):
    """Show cause of most recent reboot"""
    if ctx.invoked_subcommand is None:
        reboot_cause_str = ""

        # Read the previous reboot cause
        reboot_cause_dict = read_reboot_cause_file()

        reboot_cause = reboot_cause_dict.get("cause", "Unknown")
        reboot_user = reboot_cause_dict.get("user", "N/A")
        reboot_time = reboot_cause_dict.get("time", "N/A")

        if reboot_user != "N/A":
            reboot_cause_str = "User issued '{}' command".format(reboot_cause)
        else:
            reboot_cause_str = reboot_cause

        if reboot_user != "N/A" or reboot_time != "N/A":
            reboot_cause_str += " ["

            if reboot_user != "N/A":
                reboot_cause_str += "User: {}".format(reboot_user)
                if reboot_time != "N/A":
                    reboot_cause_str += ", "

            if reboot_time != "N/A":
                reboot_cause_str += "Time: {}".format(reboot_time)

            reboot_cause_str += "]"

        click.echo(reboot_cause_str)

# 'all' command within 'reboot-cause'
@reboot_cause.command()
def all():
    """Show cause of most recent reboot"""
    reboot_cause_data = fetch_reboot_cause_from_db("all")
    if not reboot_cause_data:
        click.echo("Reboot-cause history is not yet available in StateDB")
    else:
        header = ['Device', 'Name', 'Cause', 'Time', 'User']
        click.echo(tabulate(reboot_cause_data, header, numalign="left"))

# 'history' command within 'reboot-cause'
@reboot_cause.command()
@click.argument('module_name', required=False)
def history(module_name):
    """Show history of reboot-cause"""
    reboot_cause_history = fetch_reboot_cause_history_from_db(module_name)
    if not reboot_cause_history:
        click.echo("Reboot-cause history is not yet available in StateDB")
    else:
        if not module_name is None :
            header = ['Device', 'Name', 'Cause', 'Time', 'User', 'Comment']
            click.echo(tabulate(reboot_cause_history, header, numalign="left"))
        else:
            header = ['Name', 'Cause', 'Time', 'User', 'Comment']
            click.echo(tabulate(reboot_cause_history, header, numalign="left"))

