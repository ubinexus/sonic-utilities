import sys
import syslog
from unittest.mock import patch
import pytest

sys.path.append("scripts")
import disk_check

disk_check.MOUNTS_FILE = "/tmp/proc_mounts"

test_data = {
    "0": {
        "args": ["", "-d", "/tmp"],
        "err": ""
    },
    "1": {
        "args": ["", "-d", "/tmpx", "-s"],
        "err": "/tmpx dir is not RW"
    },
    "2": {
        "args": ["", "-d", "/tmpx"],
        "mounts": "overlay_tmpx blahblah",
        "err": "/tmpx dir is not RW",
        "cmds": ['mkdir /run/mount/upper', 'mkdir /run/mount/work',
            'mount -t overlay overlay_tmpx -o lowerdir=/tmpx,upperdir=/run/mount/upper,workdir=/run/mount/work /tmpx']
    },
    "3": {
        "args": ["", "-d", "/tmpx"],
        "cmds": ['mkdir /run/mount/upper'],
        "proc": [ {"ret": -1, "stdout": "blah", "stderr": "blah blah"} ],
        "expect_ret": -1
    },
    "4": {
        "args": ["", "-d", "/tmpx"],
        "upperdir": "/tmp",
        "err": "/tmpx dir is not RW|Already mounted",
        "expect_ret": 1
    },
    "5": {
        "args": ["", "-d", "/tmp"],
        "upperdir": "/tmp",
        "mounts": "overlay_tmp blahblah",
        "err": "READ-ONLY: Mounted ['/tmp'] to make RW"
    },
    "6": {
        "args": ["", "-d", "/tmp"],
        "upperdir": "/tmp"
    }
}

err_data = ""
cmds = []
current_tc = None

def mount_file(d):
    with open(disk_check.MOUNTS_FILE, "w") as s:
        s.write(d)


def report_err_msg(lvl, m):
    global err_data
    if lvl == syslog.LOG_ERR:
        if err_data:
            err_data += "|"
        err_data += m

disk_check.TEST_LOG_FN = report_err_msg

class proc:
    returncode = 0
    stdout = None
    stderr = None

    def __init__(self, proc_upd = None):
        if proc_upd:
            self.returncode = proc_upd.get("ret", 0)
            self.stdout = proc_upd.get("stdout", None)
            self.stderr = proc_upd.get("stderr", None)


def mock_subproc_run(cmd, shell, text, capture_output):
    global cmds

    upd = (current_tc["proc"][len(cmds)]
            if len(current_tc.get("proc", [])) > len(cmds) else None)
    cmds.append(cmd)
    
    return proc(upd)


def init_tc(tc):
    global err_data, cmds, current_tc

    err_data = ""
    cmds = []
    mount_file(tc.get("mounts", ""))
    current_tc = tc


def swap_upper(tc):
    tmp_u = tc["upperdir"]
    tc["upperdir"] = disk_check.UPPER_DIR
    disk_check.UPPER_DIR = tmp_u


class TestDiskCheck(object):
    def setup(self):
        pass


    @patch("disk_check.subprocess.run")
    def test_readonly(self, mock_proc):
        global err_data, cmds

        mock_proc.side_effect = mock_subproc_run
        for i, tc in test_data.items():
            print("-----------Start tc {}---------".format(i))
            init_tc(tc)

            with patch('sys.argv', tc["args"]):
                if "upperdir" in tc:
                    swap_upper(tc)

                ret = disk_check.main()

                if "upperdir" in tc:
                    # restore
                    swap_upper(tc)

            print("ret = {}".format(ret))
            print("err_data={}".format(err_data))
            print("cmds: {}".format(cmds))

            assert ret == tc.get("expect_ret", 0)
            if  "err" in tc:
                assert err_data == tc["err"]
            assert cmds == tc.get("cmds", [])
            print("-----------End tc {}-----------".format(i))
