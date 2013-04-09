#!/usr/bin/env python
# -*- coding: utf-8 -*-


import signal, daemon, lockfile
import sys, os, os.path
import time

# Daemon config
config = {
    'images_dir': os.path.expanduser(os.path.join('~', 'timelapse_dumps')),
    'max_shots': 50, # How many shots max take before restarting the camera
    'max_time': 1200, # How many seconds max to keep the camera on without restarting
}


class capture(object):
    pass


class capture_service(object):
    running = False
    pass

    def initialize(self):
        pass

    def reload(self):
        pass

    def stop(self):
        self.running = False
        pass

    def start(self):
        self.initialize()
        self.running = True
        self.main()

    def main(self):
        while self.running:
            print "loop"
            time.sleep(5)
        pass

if __name__ == '__main__':
    # Initialize Daemon context
    context = daemon.DaemonContext(
        working_directory=config['images_dir'],
        umask=0o002,
        pidfile=lockfile.FileLock(os.path.join(config['images_dir'], 'capture_service.pid')),
    )

    s = capture_service()
    
    context.signal_map = {
        signal.SIGTERM: s.stop,
        signal.SIGHUP: s.reload,
        signal.SIGUSR1: s.reload,
    }

    if (len(sys.argv) < 2):
        print "Use 'start' or 'stop' as argument'"
        sys.exit(1)

    if (sys.argv[1] == 'start'):
        if context.is_open:
            print "Process is already running"
            sys.exit(1)
            
        # TODO: check if already running
        s.initialize()
        with context:
            s.start()
        sys.exit(0)

    if (sys.argv[1] == 'stop'):
        
        # TODO: check if running
        s.stop()
        

    print "Unknown command '%s'" % sys.argv[1]
    sys.exit(1)
