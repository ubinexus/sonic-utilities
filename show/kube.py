#!/usr/bin/python -u
# -*- coding: utf-8 -*-
    
from show.main import AliasedGroup, cli, run_command
import os
from swsssdk import ConfigDBConnector

KUBECTL_CMD = "kubectl --kubeconfig /etc/sonic/kube_admin.conf"
REDIS_KUBE_TABLE = 'KUBERNETES_MASTER'
REDIS_KUBE_KEY = 'SERVER'


def hostname():
    return os.uname()[1]

def _get_db_data(table, key):
    config_db = ConfigDBConnector()
    config_db.connect()
    data = config_db.get_table(table)
    return data[key] if key in data else None

def _print_entry(d, prefix):
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
@cli.group(cls=AliasedGroup)
def kubernetes():
    """Show details of the kubernetes nodes/pods/..."""
    pass

@kubernetes.command()
def nodes():
    """List all nodes in this kubernetes cluster"""
    run_command("{} get nodes".format(KUBECTL_CMD))

@kubernetes.command()
def pods():
    """List all pods in this kubernetes cluster"""
    run_command("{} get pods".format(KUBECTL_CMD))

@kubernetes.command()
def status():
    """Descibe this node"""
    run_command("{} describe node {}".format(KUBECTL_CMD, hostname()))

@kubernetes.command()
def server():
    """Show kube configuration"""
    db_data = _get_db_data(REDIS_KUBE_TABLE, REDIS_KUBE_KEY)
    if db_data:
        _print_entry(db_data, "{} {}".format(REDIS_KUBE_TABLE, REDIS_KUBE_KEY))
    else:
        print("Kubernetes server is not configured")

if __name__ == '__main__':
    kubernetes()
