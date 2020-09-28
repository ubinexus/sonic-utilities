#!/usr/bin/python -u
# -*- coding: utf-8 -*-

import fcntl
import os
import shutil
import tempfile
import inspect
import datetime

import click
import netaddr
import requests
import urllib3
import yaml
from urlparse import urlparse

from sonic_py_common import device_info
from swsssdk import ConfigDBConnector
from utilities_common.db import Db
import utilities_common.cli as clicommon

from .utils import log

KUBE_ADMIN_CONF = "/etc/sonic/kube_admin.conf"
KUBELET_YAML = "/var/lib/kubelet/config.yaml"
KUBELET_SERVICE = "/etc/systemd/system/multi-user.target.wants/kubelet.service"

SERVER_ADMIN_URL = "https://{}/admin.conf"
KUBEADM_JOIN_CMD = "kubeadm join --discovery-file {} --node-name {}"

LOCK_FILE = "/var/lock/kube_join.lock"

# DB Field names
KUBE_SERVER_TABLE_NAME = "KUBERNETES_MASTER"
KUBE_SERVER_TABLE_KEY = "SERVER"
KUBE_SERVER_IP = "ip"
KUBE_SERVER_DISABLE = "disable"
KUBE_SERVER_INSECURE = "insecure"

KUBE_STATE_SERVER_CONNECTED = "connected"
KUBE_STATE_SERVER_REACHABLE = "server_reachability"
KUBE_STATE_SERVER_IP = "server_ip"
KUBE_STATE_SERVER_TS = "last_update_ts"


def _do_exit(msg):
    m = "FATAL failure: {}. Exiting...".format(msg)
    log.log_error("{}: {}: {}".format(inspect.stack()[1][1], inspect.stack()[1][2], m))
    raise SystemExit(m)


def _update_kube_server(field, val):
    config_db = ConfigDBConnector()
    config_db.connect()
    db_data = Db().get_data(KUBE_SERVER_TABLE_NAME, KUBE_SERVER_TABLE_KEY)
    def_data = {
        KUBE_SERVER_IP: "",
        KUBE_SERVER_INSECURE: "False",
        KUBE_SERVER_DISABLE: "False"
    }
    for f in def_data:
        if db_data and f in db_data:
            if f == field and db_data[f] != val:
                config_db.mod_entry(KUBE_SERVER_TABLE_NAME, KUBE_SERVER_TABLE_KEY, {field: val})
                log.log_info("modify kubernetes server entry {}={}".format(field,val))
        else:
            # Missing field. Set to default or given value
            v = val if f == field else def_data[f]
            config_db.mod_entry(KUBE_SERVER_TABLE_NAME, KUBE_SERVER_TABLE_KEY, {f: v})
            log.log_info("set kubernetes server entry {}={}".format(f,v))


def _get_state_db():
    state_db = ConfigDBConnector()
    state_db.db_connect("STATE_DB", wait_for_init=False, retry_on=True)
    return state_db


def _get_kube_server_state(state_db):
    def_data = {
            KUBE_STATE_SERVER_CONNECTED: "false",
            KUBE_STATE_SERVER_REACHABLE: "false",
            KUBE_STATE_SERVER_IP: "",
            KUBE_STATE_SERVER_TS: ""
            }

    tbl = state_db.get_table(KUBE_SERVER_TABLE_NAME)
    data = dict(def_data)
    if KUBE_SERVER_TABLE_KEY in tbl:
        data.update(tbl[KUBE_SERVER_TABLE_KEY])
    return data


def _update_kube_server_state(state_db, connected, server_ip=""):
    data = {
            KUBE_STATE_SERVER_CONNECTED: "true" if connected else "false",
            KUBE_STATE_SERVER_REACHABLE: "true" if connected else "false",
            KUBE_STATE_SERVER_TS: str(datetime.datetime.now())
            }
    if connected:
        data[KUBE_STATE_SERVER_IP] = server_ip

    state_db.mod_entry(KUBE_SERVER_TABLE_NAME, KUBE_SERVER_TABLE_KEY, data)


def _take_lock():
    lock_fd = None
    try:
        lock_fd = open(LOCK_FILE, "w")
        fcntl.lockf(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        log.log_info("Lock taken {}".format(LOCK_FILE))
    except IOError as e:
        lock_fd = None
        log.log_error("Lock {} failed: {}".format(LOCK_FILE, str(e)))
    return lock_fd


def _download_file(server, insecure):
    fname = ""
    if insecure:
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    try:
        r = requests.get(SERVER_ADMIN_URL.format(server), verify=not insecure)
    except requests.RequestException as err:
        _do_exit("Download failed: {}".format(str(err)))

    if r.status_code == 200:
        (h, fname) = tempfile.mkstemp(suffix="_kube_join")
        os.write(h, r.text)
        os.close(h)
    else:
        _do_exit("Failed to download {}".format(
            SERVER_ADMIN_URL.format(server)))

    # Ensure the admin.conf has given VIP as server-IP.
    update_file = "{}.upd".format(fname)
    cmd = 'sed "s/server:.*:6443/server: https:\/\/{}:6443/" {} > {}'.format(
            server, fname, update_file)
    clicommon.run_command(cmd)

    shutil.copyfile(update_file, KUBE_ADMIN_CONF)

    clicommon.run_command("rm -f {} {}".format(fname, update_file))
    clicommon.run_command("rm -f {} {}".format(fname, fname))


def is_connected(server=""):
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

    hwsku = device_info.get_hwsku()
    version_info = device_info.get_sonic_version_info()

    labels.append(("sonic_version", version_info['build_version']))
    labels.append(("hwsku", hwsku))
    lh = Db().get_data('DEVICE_METADATA', 'localhost')
    labels.append(("deployment_type", lh['type'] if lh and 'type' in lh else "Unknown"))
    labels.append(("enable_pods", "True"))

    return labels


def _label_node(label):
    if label[1]:
        cmd = "/usr/bin/kube_label -n {} -v {}".format(label[0], label[1])
    else:
        cmd = "/usr/bin/kube_label -n {}".format(label[0])
    clicommon.run_command(cmd, ignore_error=True)


def _troubleshoot_tips():
    msg = """
if join fails, check the following

a.  Ensure both master & node run same or compatible k8s versions

b.  Check if this node already exists in master
    Use 'sudo kubectl --kubeconfig=/etc/kubernetes/admin.conf get nodes' to list nodes at master.

    If yes, delete it, as the node is attempting a new join.
    'kubectl --kubeconfig=/etc/kubernetes/admin.conf drain <node name> --ignore-daemonsets'
    'kubectl --kubeconfig=/etc/kubernetes/admin.conf delete node <node name>'

c.  In Master check if all system pods are running good.
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

    log.log_error("Refer file {} for troubleshooting tips".format(fname))


def _do_join(state_db, server):
    try:
        clicommon.run_command("systemctl enable kubelet")

        clicommon.run_command("modprobe br_netfilter")

        clicommon.run_command(KUBEADM_JOIN_CMD.format(
            KUBE_ADMIN_CONF, device_info.get_hostname()), ignore_error=True)

        if is_connected(server):
            labels = _get_labels()
            for label in labels:
                _label_node(label)

            _update_kube_server_state(state_db, True, server)

    except requests.exceptions.RequestException as e:
        _do_exit("Download failed: {}".format(str(e)))

    except OSError as e:
        _do_exit("Download failed: {}".format(str(e)))

    _troubleshoot_tips()


def _do_reset(state_db, purge_conf):
    # Remove a key label and drain/delete self from cluster
    # If not, the next join would fail
    #
    if os.path.exists(KUBE_ADMIN_CONF):
        _label_node(("enable_pods", None))
        clicommon.run_command(
                "kubectl --kubeconfig {} --request-timeout 20s drain {} --ignore-daemonsets".format(
                    KUBE_ADMIN_CONF, device_info.get_hostname()),
                ignore_error=True)
        clicommon.run_command(
                "kubectl --kubeconfig {} --request-timeout 20s delete node {}".format(
                    KUBE_ADMIN_CONF, device_info.get_hostname()),
                ignore_error=True)

    clicommon.run_command("kubeadm reset -f", ignore_error=True)
    clicommon.run_command("rm -rf /etc/cni/net.d")
    if purge_conf:
        clicommon.run_command("rm -f {}".format(KUBE_ADMIN_CONF))
    clicommon.run_command("systemctl stop kubelet")
    clicommon.run_command("systemctl disable kubelet")

    connected =  _get_kube_server_state(state_db)[KUBE_STATE_SERVER_CONNECTED]
    if connected.lower() != "false":
        _update_kube_server_state(state_db, False)


def kube_reset(force=False):
    lock_fd = _take_lock()
    if not lock_fd:
        log.log_error("Lock {} is active; Bail out".format(LOCK_FILE))
        return

    if not force:
        if not is_connected():
            # Already *not* connected. No-Op
            connected = _get_kube_server_state(state_db)[KUBE_STATE_SERVER_CONNECTED]
            if connected.lower() != "false":
                _update_kube_server_state(state_db, False)
            return

    _do_reset(_get_state_db(), True)


def kube_join(force=False):
    lock_fd = _take_lock()
    if not lock_fd:
        log.log_error("Lock {} is active; Bail out".format(LOCK_FILE))
        return

    db_data = {
            KUBE_SERVER_IP: "",
            KUBE_SERVER_DISABLE: "false"
            }
    db_data.update(Db().get_data(KUBE_SERVER_TABLE_NAME, KUBE_SERVER_TABLE_KEY))

    if (not db_data[KUBE_SERVER_IP]):
        log.log_error("Kubernetes server is not configured")

    if db_data[KUBE_SERVER_DISABLE].lower() != "false":
        log.log_error("kube join skipped as kubernetes server is marked disabled")
        return

    state_db = _get_state_db()

    if not force:
        if is_connected(db_data[KUBE_SERVER_IP]):
            # Already connected. No-Op
            connected = _get_kube_server_state(state_db)[KUBE_STATE_SERVER_CONNECTED]
            if connected.lower() != "true":
                _update_kube_server_state(state_db, True, db_data[KUBE_SERVER_IP])
            return

    _download_file(db_data[KUBE_SERVER_IP], db_data[KUBE_SERVER_INSECURE])

    # Ensure we start in clean slate
    _do_reset(state_db, False)
    _do_join(state_db, db_data[KUBE_SERVER_IP])


@click.group(cls=clicommon.AbbreviationGroup)
def kubernetes():
    """kubernetes command line"""
    pass


# cmd kubernetes join [-f/--force]
@kubernetes.command()
@click.option('-f', '--force', help='Force a join', is_flag=True)
def join(force):
    kube_join(force=force)


# cmd kubernetes reset
@kubernetes.command()
@click.option('-f', '--force', help='Force a reset', is_flag=True)
def reset(force):
    kube_reset(force=force)


# cmd kubernetes server
@kubernetes.group()
def server():
    """ Server configuration """
    pass


# cmd kubernetes server IP
@server.command()
@click.argument('vip')
def ip(vip):
    """Specify a kubernetes cluster VIP"""
    if not netaddr.IPAddress(vip):
        click.echo('Invalid IP address %s' % vip)
        return
    _update_kube_server(KUBE_SERVER_IP, vip)


# cmd kubernetes server insecure
@server.command()
@click.argument('option', type=click.Choice(["on", "off"]))
def insecure(option):
    """Specify a kubernetes cluster VIP access as insecure or not"""
    _update_kube_server('insecure', option == "on")


# cmd kubernetes server disable
@server.command()
@click.argument('option', type=click.Choice(["on", "off"]))
def disable(option):
    """Specify a kubernetes cluster VIP access is disabled or not"""
    _update_kube_server('disable', option == "on")


# cmd kubernetes label
@kubernetes.group()
def label():
    """ label configuration """
    pass


# cmd kubernetes label add <key> <val>
@label.command()
@click.argument('key', required=True)
@click.argument('val', required=True)
def add(key, val):
    """Add a label to this node"""
    if not key or not val:
        click.echo('Require key & val')
        return
    _label_node((key, val))


# cmd kubernetes label drop <key>
@label.command()
@click.argument('key', required=True)
def drop(key):
    """Drop a label from this node"""
    if not key:
        click.echo('Require key to drop')
        return
    _label_node((key, None))
