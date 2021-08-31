#!/usr/bin/env python3

import os, sys
import json, jsonschema
import argparse
import syslog
import subprocess
import traceback
from db_integrity_schemas import CONFIG_DB_SCHEMA, COUNTERS_DB_SCHEMA

CONFIG_DB_JSON = "/etc/sonic/config_db.json"
COUNTER_DB_JSON = "/tmp/counters_db.json"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config_db_file', type=str,
        default=CONFIG_DB_JSON, help='Absolute location of config_db.json file')

    args = parser.parse_args()
    config_db_file = args.config_db_file
    config_db_data = dict()

    dump_counters_db_cmd = "redis-dump -d 2 > {}".format(COUNTER_DB_JSON)
    p = subprocess.Popen(dump_counters_db_cmd, shell=True, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (_, err) = p.communicate()
    rc = p.wait()
    if rc != 0:
        print("Failed to dump counters db. Return code: {} with err: {}".format(rc, err))

    # Read config_db.json and check if it is a valid JSON file
    try:
        with open(config_db_file) as fp:
            config_db_data = json.load(fp)
        with open(COUNTER_DB_JSON) as fp:
            counters_db_data = json.load(fp)
    except ValueError as err:
        syslog.syslog(syslog.LOG_DEBUG, "Config DB json file is not a valid json file. " +\
            "Error: {}".format(str(err)))
        return 1

    # What: Validate if critical tables and entries are present in DB.
    # Why: This is needed to avoid rebooting with a bad DB; which can
    #   potentially trigger failures in the reboot recovery path.
    # How: Validate DB against a schema which defines required tables.
    try:
        jsonschema.validate(instance=config_db_data, schema=CONFIG_DB_SCHEMA)
        jsonschema.validate(instance=counters_db_data, schema=COUNTERS_DB_SCHEMA)
    except jsonschema.exceptions.ValidationError as err:
        syslog.syslog(syslog.LOG_ERR, "Database is missing tables/entries needed for reboot procedure. " +\
            "Config db integrity check failed with:\n{}".format(str(err.message)))
        return 1
    syslog.syslog(syslog.LOG_DEBUG, "Database integrity checks passed.")
    return 0


if __name__ == '__main__':
    res = 0
    try:
        res = main()
    except KeyboardInterrupt:
        syslog.syslog(syslog.LOG_NOTICE, "SIGINT received. Quitting")
        res = 1
    except Exception as e:
        syslog.syslog(syslog.LOG_ERR, "Got an exception %s: Traceback: %s" % (str(e), traceback.format_exc()))
        res = 2
    finally:
        syslog.closelog()
    try:
        sys.exit(res)
    except SystemExit:
        os._exit(res)
