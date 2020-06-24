#!/usr/bin/python -u
# -*- coding: utf-8 -*-

import argparse
from kube import *


def main():
    if os.geteuid():
        usage(parser, "Run as root user")

    parser=argparse.ArgumentParser(description="To join kubernetes master")
    parser.add_argument("-c", "--command", help="command to run; join / reset")
    parser.add_argument("-a", "--async", help="Join asynchronously", default=False)
    parser.add_argument("-f", "--force", help="Force the Join", default=False)

    args = parser.parse_args()

    if args.command == "join":
        kube_join(args.async, args.force)
    elif args.command == "reset":
        kube_reset()
    else:
        log_msg("Unknown command {}. Understand only 'join' and 'reset'".format(args.command))
        parser.print_help()

    return 0


if __name__ == "__main__":
    main()
