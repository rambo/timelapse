#!/usr/bin/env python
# -*- coding: utf-8 -*-


import daemon.runner
import sys, os, os.path, syslog
import time


class myapp(object):
    pidfile_path = '/tmp/td.pid'
    stdout_path = '/tmp/td.out'
    stderr_path = '/tmp/td.err'
    stdin_path = '/tmp/td.in'
    pidfile_timeout = None
    
    def run(self):
        print 'Run called'
        i = 0
        while True:
            i += 1
            print 'loop %d' %i
            time.sleep(5)



if __name__ == '__main__':
    instance = myapp()
    runner = daemon.runner.DaemonRunner(instance)
    runner.parse_args()
