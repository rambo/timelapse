#!/usr/bin/env python
# -*- coding: utf-8 -*-


import signal, daemon, lockfile
import sys, os, os.path, syslog
import time

syslog.openlog(logoption=syslog.LOG_PID)

def main():
    i = 0
    print 'main called'
    while True:
        i += 1
        print 'loop %d\n' % i
        with open('test_daemon_out.txt', 'w') as f:
            f.write('loop %d\n' % i)
        time.sleep(5)

class streamproxy:
    def open(self):
        pass
    
    def close(self):
        pass
    
    def write(self, msg):
        pass
    
    def read(self):
        return 0x0    

class stdout(streamproxy):
    def write(self, msg):
         syslog.syslog(msg)

class stderr(streamproxy):
    def write(self, msg):
         syslog.syslog(syslog.LOG_ERR, msg)
    
so = stdout()
so.write('stdout proxy test')

se = stderr()
se.write('stderr proxy test')

context = daemon.DaemonContext(
# This won't work the callbacks need to look like file objects so a wrapper is needed
#    stdout=syslog.syslog,
#    stderr=lambda msg: syslog.syslog(syslog.LOG_ERR, msg)
    stdout=so,
    stderr=se
)
with context:
    main()


