#!/usr/bin/env python3

"""
This is to verify if Database has critical tables present before warmboot can proceed.
If warmboot is allowed with missing critical tables, it can lead to issues in going
down path or during the recovery path. This test detects such issues before proceeding.
The verification procedure here uses JSON schemas to verify the DB entities.

In future, to verify new tables or their content, just the schema modification
in db_integrity_schema is needed. No modification may be needed to this generic script.
"""

import os, sys
import json, jsonschema
import syslog
import subprocess
import traceback
from db_integrity_schemas import DB_ID_MAP, DB_SCHEMA


def main():
    if not DB_SCHEMA:
        return 0

    for db_name, schema in DB_SCHEMA.items():
        db_id = DB_ID_MAP.get(db_name)
        db_dump_file = "/tmp/{}.json".format(db_name)
        dump_db_cmd = "redis-dump -d {} > {}".format(db_id, db_dump_file)
        p = subprocess.Popen(dump_db_cmd, shell=True, text=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        (_, err) = p.communicate()
        rc = p.wait()
        if rc != 0:
            print("Failed to dump db {}. Return code: {} with err: {}".format(db_name, rc, err))

        try:
            with open(db_dump_file) as fp:
                db_dump_data = json.load(fp)
        except ValueError as err:
            syslog.syslog(syslog.LOG_DEBUG, "DB json file is not a valid json file. " +\
                "Error: {}".format(str(err)))
            return 1

        # What: Validate if critical tables and entries are present in DB.
        # Why: This is needed to avoid warmbooting with a bad DB; which can
        #   potentially trigger failures in the reboot recovery path.
        # How: Validate DB against a schema which defines required tables.
        try:
            jsonschema.validate(instance=db_dump_data, schema=schema)
        except jsonschema.exceptions.ValidationError as err:
            syslog.syslog(syslog.LOG_ERR, "Database is missing tables/entries needed for reboot procedure. " +\
                "DB integrity check failed with:\n{}".format(str(err.message)))
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
