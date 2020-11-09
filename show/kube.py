#!/usr/bin/python -u
# -*- coding: utf-8 -*-

import os
import click

from utilities_common.cli import AbbreviationGroup, pass_db, run_command
from sonic_py_common import device_info
from swsssdk import ConfigDBConnector

KUBE_ADMIN_CONF = "/etc/sonic/kube_admin.conf"
KUBECTL_CMD = "kubectl --kubeconfig /etc/sonic/kube_admin.conf {}"
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


def run_kube_command(cmd):
    if os.path.exists(KUBE_ADMIN_CONF):
        run_command(KUBECTL_CMD.format(cmd))
    else:
        print("System not connected to cluster yet")


#
# kubernetes group ("show kubernetes ...")
#
@click.group()
def kubernetes():
    pass


@kubernetes.command()
def nodes():
    """List all nodes in this kubernetes cluster"""
    run_kube_command("get nodes")


@kubernetes.command()
def pods():
    """List all pods in this kubernetes cluster"""
    run_kube_command("get pods  --field-selector spec.nodeName={}".format(device_info.get_hostname()))


@kubernetes.command()
def status():
    """Descibe this node"""
    run_kube_command("describe node {}".format(device_info.get_hostname()))


@kubernetes.command()
@pass_db
def server(db):
    """Show kube configuration"""
    kube_fvs = db.cfgdb.get_entry(REDIS_KUBE_TABLE, REDIS_KUBE_KEY)
    state_db = ConfigDBConnector()
    state_db.db_connect("STATE_DB", wait_for_init=False, retry_on=True)
    state_data = state_db.get_table(REDIS_KUBE_TABLE)
    if kube_fvs:
        print("Kubernetes server config:")
        _print_entry(kube_fvs, "{} {}".format(
            REDIS_KUBE_TABLE, REDIS_KUBE_KEY))
    else:
        print("Kubernetes server is not configured")

    if REDIS_KUBE_KEY in state_data:
        print("\nKubernetes server state:")
        _print_entry(state_data[REDIS_KUBE_KEY], "{} {}".format(
                        REDIS_KUBE_TABLE, REDIS_KUBE_KEY))
    else:
        print("Kubernetes server has no status info")


@kubernetes.command()
def labels():
    state_db = ConfigDBConnector()
    state_db.db_connect("STATE_DB", wait_for_init=False, retry_on=True)
    ct_labels = state_db.get_entry(KUBE_LABEL_TABLE, KUBE_LABEL_SET_KEY)
    unset_labels = state_db.get_entry(KUBE_LABEL_TABLE, KUBE_LABEL_UNSET_KEY)
    print("SET labels:")
    _print_entry(ct_labels)
    print("\nUNSET labels:")
    _print_entry(unset_labels)

