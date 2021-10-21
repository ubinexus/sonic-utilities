#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
What:
    There have been cases, where disk turns Read-only due to kernel bug.
    In Read-only state, system blocks new remote user login via TACACS.
    This utility is to check & make transient recovery as needed.

How:
    check for Read-Write permission. If Read-only, create writable overlay using tmpfs.

    By default "/etc" & "/home" are checked and if in Read-only state, make them Read-Write
    using overlay on top of tmpfs.

    Making /etc & /home as writable lets successful new remote user login.

    If in Read-only state or in Read-Write state with the help of tmpfs overlay,
    syslog ERR messages are written, to help raise alerts.

    Monit may be used to invoke it periodically, to help scan & fix and
    report via syslog.

Tidbit:
    If you would like to test this script, you could simulate a RO disk
    with the following command. Reboot will revert the effect.
        sudo bash -c "echo u > /proc/sysrq-trigger"

"""

import argparse
import os
import sys
import syslog
import time
import subprocess

UPPER_DIR = "/run/mount/upper"
WORK_DIR = "/run/mount/work"
MOUNTS_FILE = "/proc/mounts"

chk_log_level = syslog.LOG_ERR

def _log_msg(lvl, pfx, msg):
    if lvl <= chk_log_level:
        print("{}: {}".format(pfx, msg))
        syslog.syslog(lvl, msg)

def log_err(m):
    _log_msg(syslog.LOG_ERR, "Err", m)


def log_info(m):
    _log_msg(syslog.LOG_INFO, "Info",  m)


def log_debug(m):
    _log_msg(syslog.LOG_DEBUG, "Debug", m)


def test_writable(dirs): 
    for d in dirs:
        rw = os.access(d, os.W_OK)
        if not rw:
            log_err("{} is not read-write".format(d))
            return False
        else:
            log_debug("{} is Read-Write".format(d))
    return True


def run_cmd(cmd):
    proc = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE)
    ret = proc.returncode
    if ret:
        log_err("failed: ret={} cmd={}".format(ret, cmd))
    else:
        log_info("ret={} cmd: {}".format(ret, cmd))

    if proc.stdout:
        log_info("stdout: {}".format(proc.stdout.decode("utf-8")))
    if proc.stderr:
        log_info("stderr: {}".format(proc.stderr.decode("utf-8")))
    return ret


def get_dname(path_name):
    return os.path.basename(os.path.normpath(path_name))


def do_mkdir(d):
    try:
        os.mkdir(d)
        return 0
    except OSError as error:
        log_err(f"Failed to create {d}")
        return -1


def do_mnt(dirs):
    ret = 0

    if os.path.exists(UPPER_DIR):
        log_err("Already mounted")
        return 1

    for i in (UPPER_DIR, WORK_DIR):
        ret = do_mkdir(i)
        if ret:
            return ret

    # disable ssh during mounting of /etc & /home
    # If a ssh login happen during this remount, it could end up creating
    # the user account incorrectly, which could block this user forever,
    # until reboot.
    #
    log_info("Stopping ssh")
    os.system("systemctl stop ssh")

    # Pause 5 seconds, to let any current login failure to complete.
    #
    time.sleep(5)

    try:
        for d in dirs:
            d_name = get_dname(d)
            d_upper = os.path.join(UPPER_DIR, d_name)
            d_work = os.path.join(WORK_DIR, d_name)
            ret = do_mkdir(d_upper)
            if not ret:
                ret = do_mkdir(d_work)

            if not ret:
                ret = run_cmd("mount -t overlay overlay_{} -o lowerdir={},"
                        "upperdir={},workdir={} {}".format(
                            d_name, d, d_upper, d_work, d))
            if ret:
                break
    finally:
        os.system("systemctl start ssh")
        log_info("ssh started")

    if ret:
        log_err("Failed to mount {} as Read-Write".format(dirs))
    else:
        log_info("{} are mounted as Read-Write".format(dirs))
    return ret


def is_mounted(dirs):
    if not os.path.exists(UPPER_DIR):
        return False

    onames = set()
    for d in dirs:
        onames.add("overlay_{}".format(get_dname(d)))

    with open(MOUNTS_FILE, "r") as s:
        for ln in s.readlines():
            n = ln.strip().split()[0]
            if n in onames:
                log_debug("Mount exists for {}".format(n))
                return True
    return False


def do_check(skip_mount, dirs):
    ret = 0
    if not test_writable(dirs):
        if not skip_mount:
            ret = do_mnt(dirs)

        # ensure, ssh is started.
        # If in case, process crashed after stop
        # Start is no-op, if already running.
        #
        os.system("systemctl start ssh")

    # Check if mounted
    if (not ret) and is_mounted(dirs):
        log_err("READ-ONLY: Mounted {} to make Read-Write".format(dirs))

    return ret


def main():
    global chk_log_level

    parser=argparse.ArgumentParser(
            description="check disk for Read-Write and mount etc & home as Read-Write")
    parser.add_argument('-s', "--skip-mount", action='store_true', default=False,
            help="Skip mounting /etc & /home as Read-Write")
    parser.add_argument('-d', "--dirs", default="/etc,/home",
            help="dirs to mount")
    parser.add_argument('-l', "--loglvl", default=syslog.LOG_ERR, type=int,
            help="log level")
    args = parser.parse_args()

    chk_log_level = args.loglvl
    ret = do_check(args.skip_mount, args.dirs.split(","))
    return ret


if __name__ == "__main__":
    sys.exit(main())
