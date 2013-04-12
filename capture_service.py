#!/usr/bin/env python
# -*- coding: utf-8 -*-

import burrdaemon
import sys, os, signal, os.path, subprocess
import time, datetime


# Daemon config
config = {
    'images_dir': os.path.expanduser(os.path.join('~', 'timelapse_dumps')),
    'max_shots': 50, # How many shots max take before restarting the camera
    'max_time': datetime.timedelta(seconds=1200), # How many seconds max to keep the camera on without restarting
    'shot_interval': datetime.timedelta(seconds=30),
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

class timelapse_service(object):
    pidfile_path = os.path.join(config['images_dir'], 'timelapse_service.pid')
    running = False
    api = capture_api()
    shot_count_service = 0
    shot_count_camera = 0
    start_time = None
    camera_init_time = None
    last_photo_time = None
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

    def restart_camera(self):
        self.shutdown_camera()
        return self.init_camera()

    def shutdown_camera(self):
        api.try3('quit')
        camera_init_time = None

    def init_camera(self):
        self.camera_init_time = None
        if not api.try3('start'):
            return False
# Other default settings ?
#        api.try3('zoom', 0)
#        api.try3('metering', 'spot')
#        api.try3('focuspoint', 'center')

        # Set the init time and return
        self.shot_count_camera = 0
        self.camera_init_time = datetime.datetime.now()
        return True

    def take_photo(self):
        if not self.photo_dir:
            self.photo_dir = config['images_dir']
        try3_args = ('capture', os.path.join(self.photo_dir, datetime.datetime.now().strftime('%Y%m%d_%H%M%S.jpg')))
        if not api.try3(*try3_args):
            if self.restart_camera():
                # Try once more after restarting camera
                if not api.try3(*try3_args):
                    return False
            else:
                return False
        self.shot_count_service += 1
        self.shot_count_camera += 1
        self.last_photo_time = datetime.datetime.now()
        return True

    def iterate(self):
        now = datetime.datetime.now()
        if (   not self.last_photo_time
            or self.last_photo_time + config['shot_interval'] < now):
            self.take_photo()
        
        if (   self.shot_count_camera > config['max_shots']
            or self.camera_init_time + config['max_time'] < now):
            if not self.restart_camera():
                # If camera does not come back up we're screwed
                self.stop()

        # yield cpu to other things that might want it                
        time.sleep(0.5)


if __name__ == '__main__':
    instance = timelapse_service()
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
