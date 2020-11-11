#!/usr/bin/python -u
# -*- coding: utf-8 -*-

import os
import click

from utilities_common.cli import pass_db, run_command
from sonic_py_common import device_info
from swsssdk import ConfigDBConnector

REDIS_KUBE_TABLE = 'KUBERNETES_MASTER'
REDIS_KUBE_KEY = 'SERVER'

KUBE_LABEL_TABLE = "KUBE_LABELS"
KUBE_LABEL_SET_KEY = "SET"
KUBE_LABEL_UNSET_KEY = "UNSET"


def _print_entry(d, prefix=""):
    if prefix:
        prefix += " "

    if isinstance(d, dict):
        for k in d:
            _print_entry(d[k], prefix + k)
    else:
        print(prefix + str(d))


#
# kubernetes group ("show kubernetes ...")
#
@click.group()
def kubernetes():
    pass


# cmd kubernetes server
@kubernetes.group()
def server():
    """ Server configuration """
    pass


@server.command()
@pass_db
def config(db):
    """Show kube configuration"""
    kube_fvs = db.cfgdb.get_entry(REDIS_KUBE_TABLE, REDIS_KUBE_KEY)
    if kube_fvs:
        _print_entry(kube_fvs, "{} {}".format(
            REDIS_KUBE_TABLE, REDIS_KUBE_KEY))
    else:
        print("Kubernetes server is not configured")


@server.command()
@pass_db
def status(db):
    """Show kube configuration"""
    kube_fvs = db.db.get_all(db.db.STATE_DB,
            "{}|{}".format(REDIS_KUBE_TABLE, REDIS_KUBE_KEY))
    if kube_fvs:
        _print_entry(kube_fvs, "{} {}".format(
            REDIS_KUBE_TABLE, REDIS_KUBE_KEY))
    else:
        print("Kubernetes server has no status info")


@kubernetes.command()
@pass_db
def labels(db):
    ct_labels = db.db.get_all(db.db.STATE_DB,
            "{}|{}".format(KUBE_LABEL_TABLE, KUBE_LABEL_SET_KEY))
    unset_labels = db.db.get_all(db.db.STATE_DB,
            "{}|{}".format(KUBE_LABEL_TABLE, KUBE_LABEL_UNSET_KEY))
    print("SET labels:")
    _print_entry(ct_labels)
    print("\nUNSET labels:")
    _print_entry(unset_labels)

