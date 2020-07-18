#!/usr/bin/python -u
# -*- coding: utf-8 -*-

import click
import os
import sys
import urllib3
import tempfile
import requests
import fcntl
import sonic_device_util
import yaml
import netaddr
import inspect
import shutil
from urlparse import urlparse
from swsssdk import ConfigDBConnector
from utilities_common.common import *

KUBE_ADMIN_CONF = "/etc/sonic/kube_admin.conf"
KUBELET_YAML = "/var/lib/kubelet/config.yaml"
KUBELET_SERVICE = "/etc/systemd/system/multi-user.target.wants/kubelet.service"

SERVER_ADMIN_URL = "https://{}/admin.conf"
KUBEADM_JOIN_CMD = "kubeadm join --discovery-file {} --node-name {}"

LOCK_FILE = "/var/lock/kube_join.lock"


def _update_kube_server(field, val):
    config_db = ConfigDBConnector()
    config_db.connect()
    table = "KUBERNETES_MASTER"
    key = "SERVER"
    db_data = get_configdb_data(table, key)
    def_data = {
        "IP": "",
        "insecure": "False",
        "disable": "False"
    }
    for f in def_data:
        if db_data and f in db_data:
            if f == field and db_data[f] != val:
                config_db.mod_entry(table, key, {field: val})
        else:
            # Missing field. Set to default or given value
            v = val if f == field else def_data[f]
            config_db.mod_entry(table, key, {f: v})


def _take_lock():
    lock_fd = None
    try:
        lock_fd = open(LOCK_FILE, "w")
        fcntl.lockf(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        log_info("Lock taken {}".format(LOCK_FILE), True)
    except IOError as e:
        lock_fd = None
        log_err("Lock {} failed: {}".format(LOCK_FILE, str(e)), True)
    return lock_fd


def _download_file(server, insecure):
    fname = ""
    if insecure:
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    r = requests.get(SERVER_ADMIN_URL.format(server), verify=not insecure)
    if r.status_code == 200:
        (h, fname) = tempfile.mkstemp(suffix="_kube_join")
        os.write(h, r.text)
        os.close(h)
    else:
        do_exit("Failed to download {}".format(
            SERVER_ADMIN_URL.format(server)))

    # Ensure the admin.conf has given VIP as server-IP.
    update_file = "{}.upd".format(fname)
    cmd = 'sed "s/server:.*:6443/server: https:\/\/{}:6443/" {} > {}'.format(
            server, fname, update_file)
    run_command(cmd)

    shutil.copyfile(update_file, KUBE_ADMIN_CONF)

    run_command("rm -f {} {}".format(fname, update_file))


def _is_connected(server=""):
    if (os.path.exists(KUBE_ADMIN_CONF) and
            os.path.exists(KUBELET_YAML) and
            os.path.exists(KUBELET_SERVICE)):

        with open(KUBE_ADMIN_CONF, 'r') as s:
            d = yaml.load(s)
            d = d['clusters'] if 'clusters' in d else []
            d = d[0] if len(d) > 0 else {}
            d = d['cluster'] if 'cluster' in d else {}
            d = d['server'] if 'server' in d else ""
            if d:
                o = urlparse(d)
                if o.hostname:
                    return not server or server == o.hostname
    return False


def _get_labels():
    labels = []

    labels.append("sonic_version={}".format(
        sonic_device_util.get_sonic_version_info()['build_version']))
    labels.append("hwsku={}".format(sonic_device_util.get_hwsku()))
    lh = get_configdb_data('DEVICE_METADATA', 'localhost')
    labels.append("deployment_type={}".format(
        lh['type'] if lh and 'type' in lh else "Unknown"))
    labels.append("enable_pods=True")

    return labels


def _label_node(label):
    cmd = "kubectl --kubeconfig {} label nodes {} {}".format(
            KUBE_ADMIN_CONF, get_hostname(), label)
    run_command(cmd, ignore_error=True)


def _troubleshoot_tips():
    msg = """
if join fails, check the following

a)  Ensure both master & node run same or compatible k8s versions

b)  Check if this node already exists in master
    Use 'sudo kubectl --kubeconfig=/etc/kubernetes/admin.conf get nodes' to list nodes at master.

    If yes, delete it, as the node is attempting a new join.
    'kubectl --kubeconfig=/etc/kubernetes/admin.conf drain <node name> --ignore-daemonsets'
    'kubectl --kubeconfig=/etc/kubernetes/admin.conf delete node <node name>'

c)  In Master check if all system pods are running good.
    'kubectl get pods --namespace kube-system'

    If any not running properly, say READY column has 0/1, decribe pod for more detail.
    'kubectl --namespace kube-system describe pod <pod name>'

    For additional details, look into pod's logs.
    @ node: /var/log/pods/<podname>/...
    @ master: 'kubectl logs -n kube-system <pod name>'
    """

    (h, fname) = tempfile.mkstemp(suffix="kube_hints_")
    os.write(h, msg)
    os.close(h)

    log_err("Refer file {} for troubleshooting tips".format(fname), True)


def _do_join(server, insecure):
    try:
        _download_file(server, insecure)

        run_command("systemctl enable kubelet")

        run_command(KUBEADM_JOIN_CMD.format(
            KUBE_ADMIN_CONF, get_hostname()), ignore_error=True)

        if _is_connected(server):
            labels = _get_labels()
            for label in labels:
                _label_node(label)

    except requests.exceptions.RequestException as e:
        do_exit("Download failed: {}".format(str(e)))

    except OSError as e:
        do_exit("Download failed: {}".format(str(e)))

    _troubleshoot_tips()


def kube_reset():
    lock_fd = _take_lock()
    if not lock_fd:
        log_err("Lock {} is active; Bail out".format(LOCK_FILE), True)
        return

    # Remove a key label and drain/delete self from cluster
    # If not, the next join would fail
    #
    if os.path.exists(KUBE_ADMIN_CONF):
        _label_node("enable_pods-")
        run_command(
                "kubectl --kubeconfig {} --request-timeout 20s drain {} --ignore-daemonsets".format(
                    KUBE_ADMIN_CONF, get_hostname()),
                ignore_error=True)
        run_command(
                "kubectl --kubeconfig {} --request-timeout 20s delete node {}".format(
                    KUBE_ADMIN_CONF, get_hostname()),
                ignore_error=True)

    run_command("kubeadm reset -f", ignore_error=True)
    run_command("rm -rf /etc/cni/net.d")
    run_command("rm -f {}".format(KUBE_ADMIN_CONF))
    run_command("systemctl stop kubelet")
    run_command("systemctl disable kubelet")


def kube_join(force=False):
    lock_fd = _take_lock()
    if not lock_fd:
        log_err("Lock {} is active; Bail out".format(LOCK_FILE), True)
        return

    db_data = get_configdb_data('KUBERNETES_MASTER', 'SERVER')
    if not db_data or 'IP' not in db_data or not db_data['IP']:
        log_err("Kubernetes server is not configured", True)

    if db_data['disable'].lower() != "false":
        log_err("kube join skipped as kubernetes server is marked disabled", True)
        return

    if not force:
        if _is_connected(db_data['IP']):
            # Already connected. No-Op
            return

    kube_reset()
    _do_join(db_data['IP'], db_data['insecure'])


@click.group(cls=AbbreviationGroup)
def kubernetes():
    """kubernetes command line"""
    pass


# cmd kubernetes join [-f/--force]
@click.command()
@click.option('-f', '--force', help='Force a join', is_flag=True)
def join(force):
    kube_join(force=force)

kubernetes.add_command(join)


# cmd kubernetes reset
@click.command()
def reset():
    kube_reset()

kubernetes.add_command(reset)


# cmd kubernetes server
@click.group()
def server():
    """ Server configuration """
    pass

kubernetes.add_command(server)


# cmd kubernetes server IP
@click.command()
@click.argument('vip')
def ip(vip):
    """Specify a kubernetes cluster VIP"""
    if not netaddr.IPAddress(vip):
        click.echo('Invalid IP address %s' % vip)
        return
    _update_kube_server('IP', vip)

server.add_command(ip)


# cmd kubernetes server insecure
@click.command()
@click.argument('option', type=click.Choice(["on", "off"]))
def insecure(option):
    """Specify a kubernetes cluster VIP access as insecure or not"""
    _update_kube_server('insecure', option == "on")

server.add_command(insecure)


# cmd kubernetes server disable
@click.command()
@click.argument('option', type=click.Choice(["on", "off"]))
def disable(option):
    """Specify a kubernetes cluster VIP access is disabled or not"""
    _update_kube_server('disable', option == "on")

server.add_command(disable)


# cmd kubernetes label
@click.group()
def label():
    """ label configuration """
    pass

kubernetes.add_command(label)


# cmd kubernetes label add <key> <val>
@click.command()
@click.argument('key', required=True)
@click.argument('val', required=True)
def add(key, val):
    """Add a label to this node"""
    if not key or not val:
        click.echo('Require key & val')
        return
    _label_node("{}={}".format(key, val))

label.add_command(add)


# cmd kubernetes label drop <key>
@click.command()
@click.argument('key', required=True)
def drop(key):
    """Drop a label from this node"""
    if not key:
        click.echo('Require key to drop')
        return
    _label_node("{}-".format(key))

label.add_command(drop)


