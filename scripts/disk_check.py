#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
What:
    There have been cases, where disk turns RO due to kernel bug.
    In RO state, system blocks new remote user login via TACACS.
    This utility is to check & make transient recovery as needed.

How:
    check for RW permission. If RO, create writable overlay using tmpfs.

    By default "/etc" & "/home" are checked and if in RO state, make them RW
    using overlay on top of tmpfs.

    Making /etc/ & /home as writable lets successful new remote user login.

    If in RO state or in RW state with the help of tmpfs overlay,
    syslog ERR messages are written, to help raise alerts.

    Monit may be used to invoke it periodically, to help scan & fix and
    report via syslog.

"""

import argparse
import os
import sys
import syslog
import subprocess

TEST_LOG_FN = None
UPPER_DIR = "/run/mount/upper"
WORK_DIR = "/run/mount/work"
MOUNTS_FILE = "/proc/mounts"

def log_err(m):
    print("Err: {}".format(m))
    syslog.syslog(syslog.LOG_ERR, m)
    if TEST_LOG_FN:
        TEST_LOG_FN(syslog.LOG_ERR, m)


def log_info(m):
    print("Info: {}".format(m))
    syslog.syslog(syslog.LOG_INFO, m)


def log_debug(m):
    print("debug: {}".format(m))
    syslog.syslog(syslog.LOG_DEBUG, m)


def test_rw(dirs): 
    for d in dirs:
        rw = os.access(d, os.W_OK)
        if not rw:
            log_err("{} dir is not RW".format(d))
            return False
        else:
            log_debug("{} dir is RW".format(d))
    return True


def run_cmd(cmd):
    proc = subprocess.run(cmd, shell=True, text=True, capture_output=True)
    ret = proc.returncode
    if ret:
        log_err("failed: ret={} cmd={}".format(ret, cmd))
    else:
        log_info("ret={} cmd: {}".format(ret, cmd))

    if proc.stdout:
        log_info("stdout: {}".format(str(proc.stdout)))
    if proc.stderr:
        log_info("stderr: {}".format(str(proc.stderr)))
    return ret


def get_dname(path_name):
    return path_name.replace('/', ' ').strip().split()[-1]


def do_mnt(dirs):
    if os.path.exists(UPPER_DIR):
        log_err("Already mounted")
        return 1

    for i in (UPPER_DIR, WORK_DIR):
        ret = run_cmd("mkdir {}".format(i))
        if ret:
            break

    for d in dirs:
        if not ret:
            ret = run_cmd("mount -t overlay overlay_{} -o lowerdir={},"
            "upperdir={},workdir={} {}".format(
                get_dname(d), d, UPPER_DIR, WORK_DIR, d))

    if ret:
        log_err("Failed to mount {} as RW".format(dirs))
    else:
        log_info("{} are mounted as RW".format(dirs))
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
    if not test_rw(dirs):
        if not skip_mount:
            ret = do_mnt(dirs)

    # Check if mounted
    if (not ret) and is_mounted(dirs):
        log_err("READ-ONLY: Mounted {} to make RW".format(dirs))

    return ret


def main():
    parser=argparse.ArgumentParser(
            description="check disk for RW and mount etc & home as RW")
    parser.add_argument('-s', "--skip-mount", action='store_true', default=False,
            help="Skip mounting /etc & /home as RW")
    parser.add_argument('-d', "--dirs", default="/etc,/home",
            help="dirs to mount")
    args = parser.parse_args()

    ret = do_check(args.skip_mount, args.dirs.split(","))
    return ret


if __name__ == "__main__":
    sys.exit(main())
