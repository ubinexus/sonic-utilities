import json
import os
import sys
import redis

import click
from tabulate import tabulate
from swsscommon.swsscommon import SonicV2Connector
import utilities_common.cli as clicommon


PREVIOUS_REBOOT_CAUSE_FILE_PATH = "/host/reboot-cause/previous-reboot-cause.json"
STATE_DB=6
CHASSIS_STATE_DB=13

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
def fetch_data_from_db(module_name, fetch_history=False, use_chassis_db=False):
    if use_chassis_db:
        redis_host = 'redis_chassis.server'
        redis_port = 6380
        redis_idx = CHASSIS_STATE_DB
    else:
        redis_host = '127.0.0.1'
        redis_port = 6379
        redis_idx = STATE_DB
    prefix='REBOOT_CAUSE|'
    try:
        rdb = redis.Redis(host = redis_host, port = redis_port, decode_responses=True, db=redis_idx)
        table_keys = rdb.keys(prefix+'*')
    except redis.exceptions.RedisError as e:
        return []
    except Exception as e:
        return []

    if not table_keys is None:
        table_keys.sort(reverse=True)

    table = []
    d = []
    for tk in table_keys:
        r = []
        append = False
        entry = rdb.hgetall(tk)

        if not module_name is None:
            if 'device' in entry:
                if module_name != entry['device'] and module_name != "all":
                    continue
                if entry['device'] in d and history == False:
                    append = False
                    continue
                elif not entry['device'] in d or entry['device'] in d and history == True:
                    append = True
                    if not entry['device'] in d:
                        d.append(entry['device'])
            r.append(entry['device'] if 'device' in entry else "SWITCH")
        suffix=""
        if append and "DPU" in entry['device']:
            suffix='|' + entry['device']
        r.append(tk.replace(prefix, "").replace(suffix, ""))
        r.append(entry['cause'] if 'cause' in entry else "")
        r.append(entry['time'] if 'time' in entry else "")
        r.append(entry['user'] if 'user' in entry else "")
        if append == True and fetch_history == False:
            table.append(r)
        elif fetch_history == True:
            r.append(entry['comment'] if 'comment' in entry else "")
            if module_name is None or module_name == 'all' or module_name.startswith('SWITCH') or 'device' in entry and module_name == entry['device']:
                table.append(r)

    return table


# Wrapper-function to fetch reboot cause data from database
def fetch_reboot_cause_from_db(module_name):
    table = []
    r = []

    # Read the previous reboot cause
    if module_name == "all" or module_name == "SWITCH":
        reboot_cause_dict = read_reboot_cause_file()
        reboot_gen_time = reboot_cause_dict.get("gen_time", "N/A")
        reboot_cause = reboot_cause_dict.get("cause", "Unknown")
        reboot_time = reboot_cause_dict.get("time", "N/A")
        reboot_user = reboot_cause_dict.get("user", "N/A")

        r.append("SWITCH")
        r.append(reboot_gen_time if reboot_gen_time else "")
        r.append(reboot_cause if reboot_cause else "")
        r.append(reboot_time if reboot_time else "")
        r.append(reboot_user if reboot_user else "")
        table.append(r)

        if module_name == "SWITCH":
            return table

    table += fetch_data_from_db(module_name, fetch_history=False, use_chassis_db=True)
    return table

# Function to fetch reboot cause history data from database
def fetch_reboot_cause_history_from_db(module_name):
    if module_name == "all":
        # Combine data from both Redis containers for "all" modules
        data_switch = fetch_data_from_db(module_name, fetch_history=True, use_chassis_db=False)
        data_dpu = fetch_data_from_db(module_name, fetch_history=True, use_chassis_db=True)
        return data_switch + data_dpu
    elif module_name is None or module_name == "SWITCH":
        return fetch_data_from_db(module_name, fetch_history=True, use_chassis_db=False)
    else:
        return fetch_data_from_db(module_name, fetch_history=True, use_chassis_db=True)

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
    header = ['Device', 'Name', 'Cause', 'Time', 'User']
    click.echo(tabulate(reboot_cause_data, header, numalign="left"))

# 'history' command within 'reboot-cause'
@reboot_cause.command()
@click.argument('module_name', required=False)
def history(module_name):
    """Show history of reboot-cause"""
    reboot_cause_history = fetch_reboot_cause_history_from_db(module_name)
    if not module_name is None :
        header = ['Device', 'Name', 'Cause', 'Time', 'User', 'Comment']
        click.echo(tabulate(reboot_cause_history, header, numalign="left"))
    else:
        header = ['Name', 'Cause', 'Time', 'User', 'Comment']
        click.echo(tabulate(reboot_cause_history, header, numalign="left"))

