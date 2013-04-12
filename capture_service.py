#!/usr/bin/env python
# -*- coding: utf-8 -*-

import burrdaemon
import sys, os, signal, os.path, subprocess
import time, datetime


# Daemon config
config = {
    'images_dir': os.path.expanduser(os.path.join('~', 'timelapse_dumps')),
    'max_shots': 50, # How many shots max take before restarting the camera
    'max_time': 1200, # How many seconds max to keep the camera on without restarting
}


class capture_api(object):
    """For now just uses the cli client, the socket api would be more expressive though..."""
    capture_cmd = 'capture'

    def try3(self, *args):
        d = 3
        while d:
            d -= 1
            if self.execute(*args):
                return True
        # TODO: raise exception instead ??
        return False

    def execute(self, *args):
        try:
            retcode = subprocess.call(self.capture_cmd, *args)
            if retcode < 0:
                print >>sys.stderr, "Child was terminated by signal", -retcode
                return False
            if retcode > 0:
                print >>sys.stderr, "Child returned", retcode
                return False
            return True
        except OSError as e:
            print >>sys.stderr, "Execution failed:", e
            return False

class capture_service(object):
    pidfile_path = os.path.join(config['images_dir'], 'capture_service.pid')
    running = False
    api = capture_api()
    shot_count = 0
    start_time = None
    camere_init_time = None
    photo_dir = None

    def cleanup(self, *agrs, **kwargs):
        try:
            self.shutdown_camera()
            # Other cleanup routines ?
        except Exception as e:
            print >>sys.stderr, "Exception at cleanup:", e
            # Ignore error so other cleanup routines can take place
            pass

    def run(self):
        # Make sure we clean up
        import atexit
        atexit.register(self.cleanup)
        # Initializations
        self.photo_dir = os.path.joint(config['images_dir'], datetime.datetime.now().strftime('%Y%m%d_%H%M'))
        if not self.init_camera():
            print >>sys.stderr, "Camera init failed"
            return
        
        self.running = True
        while self.running:
             self.iterate()

    def stop(self, *args, **kwargs):
        self.running = False

    def shutdown_camera(self):
        api.try3('quit')
        camere_init_time = None
        

    def init_camera(self):
        self.camere_init_time = None
        if not api.try3('start'):
            return False
# Other default settings ?
#        api.try3('zoom', 0)
#        api.try3('metering', 'spot')
#        api.try3('focuspoint', 'center')

        self.camere_init_time = datetime.datetime.now()
        return True

    def take_photo(self):
        if not self.photo_dir:
            self.photo_dir = config['images_dir']
        return api.try3('capture', os.path.join(self.photo_dir, datetime.datetime.now().strftime('%Y%m%d_%H%M%S.jpg')))

    def iterate(self):
        pass


if __name__ == '__main__':
    instance = myapp()
    signal.signal(signal.SIGUSR1, instance.stop)

    if (len(sys.argv) < 2):
        print "Use 'start' or 'stop' as argument'"
        sys.exit(1)

    pid = burrdaemon.readPidFile(instance.pidfile_path)

    if (sys.argv[1] == 'start'):
        if pid:
            print "Running as PID %d" % pid
            sys.exit(1)
        burrdaemon.run(instance.run, dir='/tmp', ident='tbd', pidFilePath=instance.pidfile_path)
        sys.exit(0)

    if (sys.argv[1] == 'stop'):
        if not pid:
            print "Not running"
            sys.exit(1)
        try:
            os.kill(pid, signal.SIGUSR1)
            #os.kill(pid, signal.SIGTERM)
            sys.exit(0)
        except OSError, exc:
            print "Failed to terminate %(pid)d: %(exc)s" % vars()
            sys.exit(1)

    print "Unknown command '%s'" % sys.argv[1]
    sys.exit(1)
