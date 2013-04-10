#!/usr/bin/env python
# -*- coding: utf-8 -*-


import burrdaemon
import time, sys, os, signal

class myapp(object):
    pidfile_path = '/tmp/tbd.pid'

    def run(self):
        print 'Run called'
        i = 0
        while True:
            i += 1
            print 'loop %d' %i
            time.sleep(5)
    


if __name__ == '__main__':
    instance = myapp()

    if (len(sys.argv) < 2):
        print "Use 'start' or 'stop' as argument'"
        sys.exit(1)

    pid = burrdaemon.readPidFile(instance.pidfile_path)

    if (sys.argv[1] == 'start'):
        if pid:
            print "Running as PID %d" % pid
            sys.exit(1)
        burrdaemon.run(instance.run, ident='tbd', pidFilePath=instance.pidfile_path)
        sys.exit(0)

    if (sys.argv[1] == 'stop'):
        if not pid:
            print "Not running"
            sys.exit(1)
        try:
            os.kill(pid, signal.SIGTERM)
            sys.exit(0)
        except OSError, exc:
            print "Failed to terminate %(pid)d: %(exc)s" % vars()
            sys.exit(1)

    print "Unknown command '%s'" % sys.argv[1]
    sys.exit(1)
