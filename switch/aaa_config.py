#!/usr/bin/env python -u
# -*- coding: utf-8 -*-

import os
import json
import yaml

# FILE
PAM_CONFIG_DIR = "/etc/pam.d/"
PAM_AUTH_FILE = PAM_CONFIG_DIR + "common-auth-sonic"
SSHD_CONFIG_FILE = "/etc/ssh/sshd_config"
NSS_TACACAS_CONF = "/etc/tacplus_nss.conf"
AAA_CONF_FILE = "/etc/sonic/aaa.json"

# AAA
AAA_TACACS = "tacacs"
AAA_LOCAL = "local"
AAA_NONE = "none"
AAA_FAIL_THROUGH = "fail_through"
AAA_SRC_IP = "src_ip"
AAA_AUTHENTICATION = "authentication"
AAA_LOGIN_SETTING = "login"
AAA_TACACS_SERVER_LIST = "tacacs_server_list"
AAA_DEBUG = "debug"

# TACACS+
TACACS_SERVER_TCP_PORT_DEFAULT = "49"
TACACS_SERVER_SECRET_DEFAULT = "test123"
TACACS_SERVER_TIMEOUT_DEFAULT = "5"
TACACS_SERVER_PRI_DEFAULT = "1"
TACACS_PAP = "pap"
TACACS_CHAP = "chap"

# PAM
PAM_TACACS_MODULE = "pam_tacplus.so"
PAM_LOCAL_MODULE = "pam_unix.so"

# SSHD
SSH_PUBKEY_AUTH = "PubkeyAuthentication"
SSH_PASSWD_AUTH = "PasswordAuthentication"

AUTH_FILE_HEADER = "# THIS IS AN AUTO-GENERATED FILE\n" \
                   "#\n" \
                   "# /etc/pam.d/common-auth- authentication settings common to all services\n" \
                   "# This file is included from other service-specific PAM config files,\n" \
                   "# and should contain a list of the authentication modules that define\n" \
                   "# the central authentication scheme for use on the system\n" \
                   "# (e.g., /etc/shadow, LDAP, Kerberos, etc.). The default is to use the\n" \
                   "# traditional Unix authentication mechanisms.\n" \
                   "#\n" \
                   "# here are the per-package modules (the \"Primary\" block)\n"

AUTH_FILE_FOOTER = "#\n" \
                   "# here's the fallback if no module succeeds\n" \
                   "auth    requisite                       pam_deny.so\n" \
                   "# prime the stack with a positive return value if there isn't one already;\n" \
                   "# this avoids us returning an error just because nothing sets a success code\n" \
                   "# since the modules above will each just jump around\n" \
                   "auth    required                        pam_permit.so\n" \
                   "# and here are more per-package modules (the \"Additional\" block)\n"


class TacacsServer(object):
    def __init__(self,
                 host,
                 tcp_port=TACACS_SERVER_TCP_PORT_DEFAULT,
                 secret=TACACS_SERVER_SECRET_DEFAULT,
                 timeout=TACACS_SERVER_TIMEOUT_DEFAULT,
                 login=TACACS_PAP,
                 pri=TACACS_SERVER_PRI_DEFAULT):
        self.host = host
        self.tcp_port = tcp_port
        self.secret = secret
        self.timeout = timeout
        self.login = login
        self.pri = pri
        self.pam_module = PAM_TACACS_MODULE

    def get_pam_auth(self, debug, src_ip=''):
        pam_auth = self.pam_module
        if debug:
            pam_auth += " debug"
        pam_auth += " server=" + self.host + ":" + self.tcp_port \
                    + " secret=" + self.secret + " login=" + self.login \
                    + " timeout=" + self.timeout

        if src_ip is not '':
            pam_auth += " source_ip=" + src_ip
        pam_auth += " try_first_pass\n"

        return pam_auth

    def get_nss_conf(self):
        conf = "server=" + self.host + ":" + self.tcp_port + ",secret=" + self.secret \
               + ",timeout=" + self.timeout + "\n"
        return conf


class Local(object):
    def __init__(self):
        self.pam_module = PAM_LOCAL_MODULE

    def get_pam_auth(self, debug, src_ip=None):
        pam_auth = self.pam_module
        if debug:
            pam_auth += " debug"

        pam_auth += " nullok try_first_pass\n"
        return pam_auth


def tacacs_server2dict(server):
    return {
        'host': server.host,
        'tcp_port': server.tcp_port,
        'secret': server.secret,
        'timeout': server.timeout,
        'login': server.login,
        'priority': server.pri
    }


def dict2tacacs_server(dic):
    return TacacsServer(dic['host'],
                        dic['tcp_port'] if 'tcp_port' in dic else TACACS_SERVER_TCP_PORT_DEFAULT,
                        dic['secret'] if 'secret' in dic else TACACS_SERVER_SECRET_DEFAULT,
                        dic['timeout'] if 'timeout' in dic else TACACS_SERVER_TIMEOUT_DEFAULT,
                        dic['login'] if 'login' in dic else TACACS_PAP,
                        dic['priority'] if 'priority' in dic else TACACS_SERVER_PRI_DEFAULT)


class AaaCfg(object):
    def __init__(self):
        # Set debug default True before feature ok
        self.debug = True
        self.fail_through = False
        self.src_ip = ''
        self.server_list = []
        self.auth_login_policy = {'pam_priority': [AAA_LOCAL]}
        self.load()

    # Load conf from AAA_CONF_FILE directly
    def load(self):
        if not os.path.exists(AAA_CONF_FILE):
            return

        with open(AAA_CONF_FILE, 'r') as f:
            conf = yaml.safe_load(f)
        if conf is not None:
            if AAA_FAIL_THROUGH in conf:
                self.fail_through = conf[AAA_FAIL_THROUGH]
            if AAA_DEBUG in conf:
                self.debug = conf[AAA_DEBUG]

            if AAA_SRC_IP in conf:
                self.src_ip = conf[AAA_SRC_IP]

            if AAA_TACACS_SERVER_LIST in conf:
                server_list = conf[AAA_TACACS_SERVER_LIST]
                for server in server_list:
                    if 'host' in server:
                        self.server_list.append(dict2tacacs_server(server))

                self.server_list = sorted(self.server_list, key=lambda server: server.pri)

            if AAA_AUTHENTICATION in conf:
                auth = conf[AAA_AUTHENTICATION]
                if AAA_LOGIN_SETTING in auth:
                    auth_login = auth[AAA_LOGIN_SETTING]
                    if 'pam_priority' in auth_login:
                        self.auth_login_policy['pam_priority'] = auth_login['pam_priority']

    # Save conf as json file
    def save(self):
        server_list = []
        for server in self.server_list:
            server_list.append(tacacs_server2dict(server))

        conf_dict = {
            AAA_DEBUG: self.debug,
            AAA_FAIL_THROUGH: self.fail_through,
            AAA_SRC_IP: self.src_ip,
            AAA_TACACS_SERVER_LIST: server_list,
            AAA_AUTHENTICATION: {
                AAA_LOGIN_SETTING: self.auth_login_policy
            }
        }
        conf = json.dumps(conf_dict, indent=4)
        with open(AAA_CONF_FILE, "w") as f:
            f.write(conf)

    def modify_pam_auth_file(self):
        if self.fail_through:
            pam_control = "[success=done new_authtok_reqd=done default=ignore]"
        else:
            pam_control = "[success=done new_authtok_reqd=done default=ignore auth_err=die]"

        module_list = []
        auth_file_body = ""

        # Set local and tacacs+ pam priority
        # pam_priority is ['local'] or ['local','tacacs'] or ['tacacs', 'local'] or ['tacacs']
        pam_priority = self.auth_login_policy['pam_priority']
        if pam_priority == [AAA_LOCAL]:
            module_list = [Local()]
        elif pam_priority == [AAA_LOCAL, AAA_TACACS]:
            module_list = [Local()] + self.server_list
        elif pam_priority == [AAA_TACACS] or pam_priority == [AAA_TACACS, AAA_LOCAL]:
            # Don't accept only TACACS+ authentication
            # Make sure root will always authentication on local, not TACACS+
            module_list = self.server_list + [Local()]
            auth_file_body += "auth\t[success=%d new_authtok_reqd=done default=ignore]\t" % (len(module_list)-1)
            auth_file_body += "pam_succeed_if.so user = root debug\n"

        if len(module_list):
            for module in module_list[:-1]:
                line = module.get_pam_auth(self.debug, self.src_ip)
                if line is not "":
                    auth_file_body += "auth\t" + pam_control + "\t" + line

            module = module_list[-1]
            line = module.get_pam_auth(self.debug, self.src_ip)
            auth_file_body += "auth\t[success=1 default=ignore]\t" + line

        with open(PAM_AUTH_FILE, "w") as f:
            f.write(AUTH_FILE_HEADER + auth_file_body + AUTH_FILE_FOOTER)

        # Modify common-auth include file in /etc/pam.d/login and sshd
        if os.path.isfile(PAM_AUTH_FILE):
            os.system("sed -i -e '/^@include/s/common-auth$/common-auth-sonic/' /etc/pam.d/sshd")
            os.system("sed -i -e '/^@include/s/common-auth$/common-auth-sonic/' /etc/pam.d/login")
        else:
            os.system("sed -i -e '/^@include/s/common-auth-sonic$/common-auth/' /etc/pam.d/sshd")
            os.system("sed -i -e '/^@include/s/common-auth-sonic$/common-auth/' /etc/pam.d/login")

    # Set tacacs+ server in nss-tacplus conf
    def modify_nss_conf(self):
        if self.debug:
            contents = "debug\n"
        else:
            contents = ""

        if self.src_ip is not '':
            contents += "src_ip=" + self.src_ip + "\n"
        for server in self.server_list:
            contents += server.get_nss_conf()

        with open(NSS_TACACAS_CONF, "w") as f:
            f.write(contents)


def set_debug(debug):
    cfg = AaaCfg()
    if debug is not cfg.debug:
        cfg.debug = debug
        cfg.modify_pam_auth_file()
        cfg.modify_nss_conf()
        cfg.save()


def set_fail_through(enable):
    cfg = AaaCfg()
    if enable is not cfg.fail_through:
        cfg.fail_through = enable
        cfg.modify_pam_auth_file()
        cfg.save()


def set_src_ip(src_ip):
    cfg = AaaCfg()
    if src_ip is not cfg.src_ip:
        cfg.src_ip = src_ip
        cfg.modify_pam_auth_file()
        cfg.modify_nss_conf()
        cfg.save()


def add_server(host, tcp_port, secret, timeout, login, pri):
    cfg = AaaCfg()
    host_list = [server.host for server in cfg.server_list]
    # If host exists in server_list, update it
    if host in host_list:
        idx = host_list.index(host)
        server = cfg.server_list[idx]
        server.tcp_port = tcp_port
        server.secret = secret
        server.timeout = timeout
        server.login = login
        server.pri = pri
    else:
        server = TacacsServer(host, tcp_port, secret, timeout, login, pri)
        cfg.server_list.append(server)

    cfg.server_list = sorted(cfg.server_list, key=lambda server: server.pri)
    cfg.modify_pam_auth_file()
    cfg.modify_nss_conf()
    cfg.save()


def del_server(host):
    cfg = AaaCfg()
    for server in cfg.server_list:
        if host == server.host:
            cfg.server_list.remove(server)
            cfg.modify_pam_auth_file()
            cfg.modify_nss_conf()
            cfg.save()


# set pam priority of tacacs, local
def set_auth_login(pam_priority):
    pri = []
    for pam in pam_priority:
        pri.append(pam)

    cfg = AaaCfg()
    if pri is not cfg.auth_login_policy['pam_priority']:
        cfg.auth_login_policy['pam_priority'] = pri
        cfg.modify_pam_auth_file()
        cfg.save()


def show_conf():
    with open(AAA_CONF_FILE, 'r') as f:
        conf = yaml.safe_load(f)
    print "AAA Configuration:"
    print json.dumps(conf, indent=4)


def load_aaa_cfg():
    cfg = AaaCfg()
    cfg.modify_pam_auth_file()
    cfg.modify_nss_conf()

if __name__ == "__main__":
    load_aaa_cfg()

