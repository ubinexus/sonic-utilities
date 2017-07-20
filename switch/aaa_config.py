#!/usr/bin/env python -u
# -*- coding: utf-8 -*-

import os
import json
import yaml
import commands

# FILE
PAM_CONFIG_DIR = "/etc/pam.d/"
PAM_AUTH_FILE = PAM_CONFIG_DIR + "common-auth-sonic"
SSHD_CONFIG_FILE = "/etc/ssh/sshd_config"
NSS_TACPLUS_CONF = "/etc/tacplus_nss.conf"
AAA_CONF_FILE = "/etc/sonic/aaa.json"
NSS_CONF = "/etc/nsswitch.conf"

# AAA
AAA_TACPLUS = "tacacs+"
AAA_LOCAL = "local"
AAA_ENABLE = "enable"
AAA_AUTH_PROTOCOL = "authentication_protocol"
AAA_AUZ_PROTOCOL = "authorization_protocol"
AAA_AUTH_FAILTHROUGH = "authentication_failthrough"
AAA_AUZ_FAILTHROUGH = "authorization_failthrough"
AAA_AUTH_FALLBACK = "authentication_fallback"
AAA_AUZ_FALLBACK = "authorization_fallback"
AAA_AUTHENTICATION = "authentication"

AAA_TACPLUS_GLOBAL = "tacplus_global"
AAA_TACPLUS_SERVER_LIST = "tacplus_server_list"
AAA_DEBUG = "debug"

# TACACS+
TACPLUS_SERVER_TCP_PORT_DEFAULT = "49"
TACPLUS_SERVER_PASSKEY_DEFAULT = ""
TACPLUS_SERVER_TIMEOUT_DEFAULT = "5"
TACPLUS_SERVER_PRI_DEFAULT = "1"
TACPLUS_SERVER_SRC_IP_DEFAULT = ""
TACPLUS_SERVER_AUTH_TYPE_DEFAULT = "pap"

TACPLUS_TIMEOUT = 'timeout'
TACPLUS_AUTH_TYPE = 'auth_type'
TACPLUS_PASSKEY = 'passkey'
TACPLUS_SRC_IP = "src_ip"
TACPLUS_ADDRESS = 'address'
TACPLUS_TCP_PORT = 'tcp_port'
TACPLUS_PRI = 'priority'
TACPLUS_PAP = "pap"
TACPLUS_CHAP = "chap"
TACPLUS_MSCHAP = "mschap"

# PAM
PAM_TACACS_MODULE = "pam_tacplus.so"
PAM_LOCAL_MODULE = "pam_unix.so"


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


class TacacsPlusServer(object):
    def __init__(self,
                 address,
                 tcp_port=TACPLUS_SERVER_TCP_PORT_DEFAULT,
                 passkey=TACPLUS_SERVER_PASSKEY_DEFAULT,
                 timeout=TACPLUS_SERVER_TIMEOUT_DEFAULT,
                 auth_type=TACPLUS_SERVER_AUTH_TYPE_DEFAULT,
                 priority=TACPLUS_SERVER_PRI_DEFAULT):
        self.address = address
        self.tcp_port = tcp_port
        self.passkey = passkey
        self.timeout = timeout
        self.auth_type = auth_type
        self.priority = priority
        self.pam_module = PAM_TACACS_MODULE

    def get_pam_auth(self, debug, src_ip=''):
        pam_auth = self.pam_module
        if debug:
            pam_auth += " debug"
        pam_auth += " server=" + self.address + ":" + self.tcp_port \
                    + " secret=" + self.passkey + " login=" + self.auth_type \
                    + " timeout=" + self.timeout

        if src_ip is not '':
            pam_auth += " source_ip=" + src_ip
        pam_auth += " try_first_pass\n"

        return pam_auth

    def get_nss_conf(self):
        conf = "server=" + self.address + ":" + self.tcp_port + ",secret=" + self.passkey \
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


def tacplus_server2dict(server):
    return {
        TACPLUS_ADDRESS: server.address,
        TACPLUS_TCP_PORT: server.tcp_port,
        TACPLUS_PASSKEY: server.passkey,
        TACPLUS_TIMEOUT: server.timeout,
        TACPLUS_AUTH_TYPE: server.auth_type,
        TACPLUS_PRI: server.priority
    }


def dict2tacplus_server(dic):
    return TacacsPlusServer(dic[TACPLUS_ADDRESS],
                            dic[TACPLUS_TCP_PORT] if TACPLUS_TCP_PORT in dic else TACPLUS_SERVER_TCP_PORT_DEFAULT,
                            dic[TACPLUS_PASSKEY] if TACPLUS_PASSKEY in dic else TACPLUS_SERVER_PASSKEY_DEFAULT,
                            dic[TACPLUS_TIMEOUT] if TACPLUS_TIMEOUT in dic else TACPLUS_SERVER_TIMEOUT_DEFAULT,
                            dic[TACPLUS_AUTH_TYPE] if TACPLUS_AUTH_TYPE in dic else TACPLUS_SERVER_AUTH_TYPE_DEFAULT,
                            dic[TACPLUS_PRI] if TACPLUS_PRI in dic else TACPLUS_SERVER_PRI_DEFAULT)


class TacacsPlusGlobal(object):
    def __init__(self,
                 timeout=TACPLUS_SERVER_TIMEOUT_DEFAULT,
                 passkey=TACPLUS_SERVER_SRC_IP_DEFAULT,
                 auth_type=TACPLUS_SERVER_AUTH_TYPE_DEFAULT,
                 src_ip=TACPLUS_SERVER_SRC_IP_DEFAULT):
        self.timeout = timeout
        self.passkey = passkey
        self.auth_type = auth_type
        self.src_ip = src_ip

    def get_dict(self):
        return {
            TACPLUS_TIMEOUT: self.timeout,
            TACPLUS_PASSKEY: self.passkey,
            TACPLUS_AUTH_TYPE: self.auth_type,
            TACPLUS_SRC_IP: self.src_ip
        }


class AaaCfg(object):
    def __init__(self):
        self.enable = True
        self.auth_protocol = [AAA_LOCAL]
        self.auth_fallback = True
        self.auth_failthrough = True
        self.auz_protocol = [AAA_LOCAL]
        self.auz_fallback = True
        self.auz_failthrough = True
        self.tacplus_global = TacacsPlusGlobal()
        self.tacplus_server_list = []
        self.debug = False
        self.load()

    # Load conf from AAA_CONF_FILE directly
    def load(self):
        if not os.path.exists(AAA_CONF_FILE):
            return

        with open(AAA_CONF_FILE, 'r') as f:
            conf = yaml.safe_load(f)
        if conf is not None:
            if AAA_ENABLE in conf:
                self.enable = conf[AAA_ENABLE]
            if AAA_AUTH_PROTOCOL in conf:
                self.auth_protocol = conf[AAA_AUTH_PROTOCOL]
            if AAA_AUTH_FALLBACK in conf:
                self.auth_fallback = conf[AAA_AUTH_FALLBACK]
            if AAA_AUTH_FAILTHROUGH in conf:
                self.auth_failthrough = conf[AAA_AUTH_FAILTHROUGH]

            if AAA_AUZ_PROTOCOL in conf:
                self.auz_protocol = conf[AAA_AUZ_PROTOCOL]
            if AAA_AUZ_FALLBACK in conf:
                self.auz_fallback = conf[AAA_AUZ_FALLBACK]
            if AAA_AUZ_FAILTHROUGH in conf:
                self.auz_failthrough = conf[AAA_AUZ_FAILTHROUGH]
            if AAA_DEBUG in conf:
                self.debug = conf[AAA_DEBUG]

            if AAA_TACPLUS_GLOBAL in conf:
                tacplus_global = conf[AAA_TACPLUS_GLOBAL]
                if TACPLUS_TIMEOUT in tacplus_global:
                    self.tacplus_global.timeout = tacplus_global[TACPLUS_TIMEOUT]
                if TACPLUS_PASSKEY in tacplus_global:
                    self.tacplus_global.passkey = tacplus_global[TACPLUS_PASSKEY]
                if TACPLUS_AUTH_TYPE in tacplus_global:
                    self.tacplus_global.auth_type = tacplus_global[TACPLUS_AUTH_TYPE]
                if TACPLUS_SRC_IP in tacplus_global:
                    self.tacplus_global.src_ip = tacplus_global[TACPLUS_SRC_IP]

            if AAA_TACPLUS_SERVER_LIST in conf:
                server_list = conf[AAA_TACPLUS_SERVER_LIST]
                for server in server_list:
                    if TACPLUS_ADDRESS in server:
                        self.tacplus_server_list.append(dict2tacplus_server(server))
                self.tacplus_server_list = sorted(self.tacplus_server_list, key=lambda server: server.priority)

    # Save conf as json file
    def save(self):
        server_list = []
        for server in self.tacplus_server_list:
            server_list.append(tacplus_server2dict(server))

        tacplus_global_dict = self.tacplus_global.get_dict()

        conf_dict = {
            AAA_ENABLE: self.enable,
            AAA_DEBUG: self.debug,
            AAA_AUTH_PROTOCOL: self.auth_protocol,
            AAA_AUTH_FAILTHROUGH: self.auth_failthrough,
            AAA_AUTH_FALLBACK: self.auth_fallback,
            AAA_AUZ_PROTOCOL: self.auz_protocol,
            AAA_AUZ_FAILTHROUGH: self.auz_failthrough,
            AAA_AUZ_FALLBACK: self.auz_fallback,
            AAA_TACPLUS_GLOBAL: tacplus_global_dict,
            AAA_TACPLUS_SERVER_LIST: server_list
        }
        conf = json.dumps(conf_dict, indent=4)
        with open(AAA_CONF_FILE, "w") as f:
            f.write(conf)

    def enable_tacplus(self):
        if AAA_TACPLUS in self.auth_protocol:
            # Create remote user if TACACS+ enable
            output = commands.getoutput("grep 'remote_user' /etc/passwd")
            if output == '':
                cmd = 'useradd -G docker "remote_user" -g 999 ' + \
                      '-c "remote user" -d /home/remote_user -m -s /bin/rbash'
                os.system(cmd)
                cmd = 'useradd -G sudo,docker "remote_user_su" -g 1000 ' + \
                      '-c "remote sudo user" -d /home/remote_user_su -m -s /bin/bash'
                os.system(cmd)

            # Add tacplus in nsswitch.conf if TACACS+ enable
            if os.path.isfile(NSS_CONF):
                os.system("sed -i -e '/tacplus/b' -e '/^passwd/s/compat/& tacplus/' /etc/nsswitch.conf")
        else:
            if os.path.isfile(NSS_CONF):
                os.system("sed -i -e '/^passwd/s/ tacplus//' /etc/nsswitch.conf")

    def modify_pam_auth_file(self):
        if self.auth_failthrough:
            pam_control = "[success=done new_authtok_reqd=done default=ignore]"
        else:
            pam_control = "[success=done new_authtok_reqd=done default=ignore auth_err=die]"

        module_list = []
        auth_file_body = ""

        # Set local and tacacs+ pam priority
        # ['local'] or ['local','tacacs+'] or ['tacacs+', 'local'] or ['tacacs+']
        if self.auth_protocol == [AAA_LOCAL]:
            module_list = [Local()]
        elif self.auth_protocol == [AAA_LOCAL, AAA_TACPLUS]:
            module_list = [Local()] + self.tacplus_server_list
        elif self.auth_protocol == [AAA_TACPLUS] or self.auth_protocol == [AAA_TACPLUS, AAA_LOCAL]:
            # Don't accept only TACACS+ authentication
            # Make sure root will always authentication on local, not TACACS+
            module_list = self.tacplus_server_list + [Local()]
            auth_file_body += "auth\t[success=%d new_authtok_reqd=done default=ignore]\t" % (len(module_list)-1)
            auth_file_body += "pam_succeed_if.so user = root debug\n"

        if len(module_list):
            for module in module_list[:-1]:
                line = module.get_pam_auth(self.debug, self.tacplus_global.src_ip)
                if line is not "":
                    auth_file_body += "auth\t" + pam_control + "\t" + line

            module = module_list[-1]
            line = module.get_pam_auth(self.debug, self.tacplus_global.src_ip)
            auth_file_body += "auth\t[success=1 default=ignore]\t" + line

        with open(PAM_AUTH_FILE, "w") as f:
            f.write(AUTH_FILE_HEADER + auth_file_body + AUTH_FILE_FOOTER)

        self.enable_tacplus()

        # Modify common-auth include file in /etc/pam.d/type and sshd
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

        if self.tacplus_global.src_ip is not '':
            contents += "src_ip=" + self.tacplus_global.src_ip + "\n"
        for server in self.tacplus_server_list:
            contents += server.get_nss_conf()

        with open(NSS_TACPLUS_CONF, "w") as f:
            f.write(contents)


def set_debug(debug):
    cfg = AaaCfg()
    if debug is not cfg.debug:
        cfg.debug = debug
        cfg.modify_pam_auth_file()
        cfg.modify_nss_conf()
        cfg.save()


def set_auth_failthrough(enable):
    cfg = AaaCfg()
    if enable is not cfg.auth_failthrough:
        cfg.auth_failthrough = enable
        cfg.modify_pam_auth_file()
        cfg.save()


def set_tacplus_src_ip(src_ip):
    cfg = AaaCfg()
    if src_ip is not cfg.tacplus_global.src_ip:
        cfg.tacplus_global.src_ip = src_ip
        cfg.modify_pam_auth_file()
        cfg.modify_nss_conf()
        cfg.save()


def add_tacplus_server(address, tcp_port, passkey, timeout, auth_type, pri):
    cfg = AaaCfg()
    address_list = [server.address for server in cfg.tacplus_server_list]
    # If address exists in server_list, update it
    if address in address_list:
        idx = address_list.index(address)
        server = cfg.tacplus_server_list[idx]
        server.tcp_port = tcp_port
        server.passkey = passkey
        server.timeout = timeout
        server.auth_type = auth_type
        server.priority = pri
    else:
        server = TacacsPlusServer(address, tcp_port, passkey, timeout, auth_type, pri)
        cfg.tacplus_server_list.append(server)

    cfg.tacplus_server_list = sorted(cfg.tacplus_server_list, key=lambda server: server.priority)
    cfg.modify_pam_auth_file()
    cfg.modify_nss_conf()
    cfg.save()


def del_tacplus_server(address):
    cfg = AaaCfg()
    for server in cfg.tacplus_server_list:
        if address == server.address:
            cfg.tacplus_server_list.remove(server)
            cfg.modify_pam_auth_file()
            cfg.modify_nss_conf()
            cfg.save()


# set authentication protocol of tacacs+, local
def set_auth_protocol(auth_protocol):
    protocol = []
    for i in auth_protocol:
        protocol.append(i)

    cfg = AaaCfg()
    if protocol is not cfg.auth_protocol:
        cfg.auth_protocol = protocol
        cfg.modify_pam_auth_file()
        cfg.modify_nss_conf()
        cfg.save()


def show_conf():
    cfg = AaaCfg()
    print 'AAA Configuration:\n'

    def bool2enable(flag):
        if flag:
            return 'enable'
        else:
            return 'disable'

    print 'AAA ' + bool2enable(cfg.enable)
    protocols = ''
    for proto in cfg.auth_protocol:
        protocols += proto + ' '
    print 'AAA authentication protocol ' + protocols
    print 'AAA authentication fallback ' + bool2enable(cfg.auth_fallback)
    print 'AAA authentication failthrough ' + bool2enable(cfg.auth_failthrough)

    protocols = ''
    for proto in cfg.auz_protocol:
        protocols += proto + ' '
    print 'AAA authorization protocol ' + protocols
    print 'AAA authorization fallback ' + bool2enable(cfg.auth_fallback)
    print 'AAA authorization failthrough ' + bool2enable(cfg.auth_failthrough)

    print '\nTACACS+ global authentication type ' + cfg.tacplus_global.auth_type
    print 'TACACS+ global timeout ' + cfg.tacplus_global.timeout
    if cfg.tacplus_global.src_ip is not '':
        print 'TACACS+ global source ip address ' + cfg.tacplus_global.src_ip
    if cfg.tacplus_global.passkey is not '':
        print 'TACACS+ global passkey ' + cfg.tacplus_global.passkey

    for server in cfg.tacplus_server_list:
        print '\nTACACS+ server ' + server.address
        print '               tcp_port ' + server.tcp_port
        print '               passkey ' + server.passkey
        print '               timeout ' + server.timeout
        print '               authentication type ' + server.auth_type
        print '               priority %d' % server.priority


def load_aaa_cfg():
    cfg = AaaCfg()
    cfg.modify_pam_auth_file()
    cfg.modify_nss_conf()
    cfg.save()

if __name__ == "__main__":
    load_aaa_cfg()
