#!/usr/bin/env python
# -*- coding: utf-8 -*-


import signal, daemon, lockfile
import sys, os, os.path, syslog
import time


def main():
    while True:
        print "foo"
        time.sleep(5)


context = daemon.DaemonContext(
    stdout=syslog.syslog,
    stderr=lambda msg: syslog.syslog(syslog.LOG_ERR, msg)
)
with context:
    main()