#!/usr/bin/python -u
# -*- coding: utf-8 -*-

import click
import netaddr

from swsssdk import ConfigDBConnector
from utilities_common.db import Db
import utilities_common.cli as clicommon

from .utils import log

# DB Field names
KUBE_SERVER_TABLE_NAME = "KUBERNETES_MASTER"
KUBE_SERVER_TABLE_KEY = "SERVER"
KUBE_SERVER_IP = "ip"
KUBE_SERVER_PORT = "port"
KUBE_SERVER_DISABLE = "disable"
KUBE_SERVER_INSECURE = "insecure"

KUBE_STATE_SERVER_CONNECTED = "connected"
KUBE_STATE_SERVER_REACHABLE = "server_reachability"
KUBE_STATE_SERVER_IP = "server_ip"
KUBE_STATE_SERVER_TS = "last_update_ts"

KUBE_LABEL_TABLE = "KUBE_LABELS"
KUBE_LABEL_SET_KEY = "SET"
KUBE_LABEL_UNSET_KEY = "UNSET"


def _update_kube_server(field, val):
    config_db = ConfigDBConnector()
    config_db.connect()
    db_data = Db().get_data(KUBE_SERVER_TABLE_NAME, KUBE_SERVER_TABLE_KEY)
    def_data = {
        KUBE_SERVER_IP: "",
        KUBE_SERVER_PORT: "6443",
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


def _label_node(name, val=""):
    state_db = ConfigDBConnector()
    state_db.db_connect("STATE_DB", wait_for_init=False, retry_on=True)
    ct_labels = state_db.get_entry(KUBE_LABEL_TABLE, KUBE_LABEL_SET_KEY)
    unset_labels = state_db.get_entry(KUBE_LABEL_TABLE, KUBE_LABEL_UNSET_KEY)
    if val:
        if name not in ct_labels:
            state_db.mod_entry(KUBE_LABEL_TABLE, KUBE_LABEL_SET_KEY,
                    {name: val})
        elif (ct_labels[name] != val):
            click.echo("Label value can't change.")
            raise click.Abort()
        if name in unset_labels:
            del unset_labels[name]
            state_db.set_entry(KUBE_LABEL_TABLE, KUBE_LABEL_UNSET_KEY,
                    unset_labels)
    else:
        if name in ct_labels:
            del ct_labels[name]
            state_db.set_entry(KUBE_LABEL_TABLE, KUBE_LABEL_SET_KEY, ct_labels)
        if name not in unset_labels:
            state_db.mod_entry(KUBE_LABEL_TABLE, KUBE_LABEL_UNSET_KEY,
                    {name: "" })


@click.group(cls=clicommon.AbbreviationGroup)
def kubernetes():
    """kubernetes command line"""
    pass


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
    if vip and not netaddr.IPAddress(vip):
        click.echo('Invalid IP address %s' % vip)
        return
    _update_kube_server(KUBE_SERVER_IP, vip)


# cmd kubernetes server Port
@server.command()
@click.argument('port')
def port(p):
    """Specify a kubernetes Service port"""
    val = int(p)
    if (val <= 0) or (val >= (64 << 10)):
        click.echo('Invalid port value %s' % p)
        return
    _update_kube_server(KUBE_SERVER_PORT, p)


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
    _label_node(key, val)


# cmd kubernetes label drop <key>
@label.command()
@click.argument('key', required=True)
def drop(key):
    """Drop a label from this node"""
    if not key:
        click.echo('Require key to drop')
        return
    _label_node(key)
