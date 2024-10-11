#!/usr/bin/env python
#########################################################
# Copyright 2021-2022 Cisco Systems, Inc.
# All rights reserved.
#
# CLI Extensions for show command
#########################################################

try:
    from sonic_py_common import device_info
    import utilities_common.cli as clicommon
except ImportError as e:
    raise ImportError("%s - required module not found".format(str(e)))

try:
    from sonic_platform.cli import PLATFORM_CLIS
except ImportError:
    PLATFORM_CLIS = []

try:
    from sonic_platform.cli import VENDOR_CLIS
except ImportError:
    VENDOR_CLIS = {}


def register(cli):
    version_info = device_info.get_sonic_version_info()
    if version_info and version_info.get("asic_type") == "cisco-8000":
        if PLATFORM_CLIS and not VENDOR_CLIS.get("platform"):
            VENDOR_CLIS["platform"] = PLATFORM_CLIS
        for command, subcommands in VENDOR_CLIS.items():
            for subcommand in subcommands:
                cli.commands[command].add_command(subcommand)
