#!/usr/bin/env python
# -*- coding: utf-8 -*-

import burrdaemon
import sys, os, signal, os.path, subprocess
import time, datetime
import syslog

# http://stackoverflow.com/questions/600268/mkdir-p-functionality-in-python
import os, errno
def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc: # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else: raise

# Daemon config
config = {
    'images_dir': os.path.expanduser(os.path.join('~', 'timelapse_dumps')),
    'max_shots': 50, # How many shots max take before restarting the camera
    'max_time': datetime.timedelta(seconds=1200), # How many seconds max to keep the camera on without restarting
    'shot_interval': datetime.timedelta(seconds=30),
}

def touch(fname, times=None):
    with file(fname, 'a'):
        os.utime(fname, times)

class capture_api(object):
    """For now just uses the cli client, the socket api would be more expressive though..."""
    capture_cmd = '/usr/local/bin/capture'

    def try3(self, *args):
        d = 3
        while d:
            d -= 1
            if self.execute(*args):
                return True
            time.sleep(1)
        return False

    def execute(self, *args):
        try:
            call_list = (self.capture_cmd, ' ' .join(args))
            retcode = subprocess.call(call_list)
            if retcode < 0:
                print >>sys.stderr, "Command %s was terminated by signal %d" % (repr(call_list), retcode)
                return False
            if retcode > 0:
                print >>sys.stderr, "Command %s returned %d" % (repr(call_list), retcode)
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
            # Write a simple status file
            if self.photo_dir:
                with file(os.path.join(self.photo_dir, 'done.txt'), 'a') as f:
                    f.write('Started: %s\n' % self.start_time.strftime('%Y%m%d_%H%M%S'))
                    f.write('Completed: %s\n' % datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
                    f.write('Photo count: %d\n' % self.shot_count_service)
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
        self.start_time = datetime.datetime.now()
        self.photo_dir = os.path.join(config['images_dir'], self.start_time.strftime('%Y%m%d_%H%M'))
        self.latest_path = os.path.join(config['images_dir'], 'latest.jpg')
        mkdir_p(self.photo_dir)
        if not self.restart_camera(): # Use restart just in case another process has left capture into weird state
            print >>sys.stderr, "Camera init failed"
            return
        
        self.running = True
        while self.running:
             self.iterate()

    def stop(self, *args, **kwargs):
        self.running = False

    def restart_camera(self):
        self.shutdown_camera()
        # Give the camera time to shut down properly
        time.sleep(10)
        return self.init_camera()

    def shutdown_camera(self):
        self.api.try3('quit')
        camera_init_time = None

    def init_camera(self):
        self.camera_init_time = None
        if not self.api.try3('start'):
            return False
# Other default settings ?
#        self.api.try3('zoom', 0)
#        self.api.try3('metering', 'spot')
#        self.api.try3('focuspoint', 'center')

        # Set the init time and return
        self.shot_count_camera = 0
        self.camera_init_time = datetime.datetime.now()
        return True

    def take_photo(self):
        if not self.photo_dir:
            self.photo_dir = config['images_dir']
        photo_path = os.path.join(self.photo_dir, datetime.datetime.now().strftime('%Y%m%d_%H%M%S.jpg'))
        try3_args = ('capture', photo_path)
        if not self.api.try3(*try3_args):
            if self.restart_camera():
                # Try once more after restarting camera
                if not self.api.try3(*try3_args):
                    return False
            else:
                return False
        print "Saved to %s" % photo_path
        # Remove old symlink (if possible)
        try:
            os.unlink(self.latest_path)
        except Exception,e:
            pass
        # Create new symlink (if possible, if not just ignore the error)
        try:
            os.symlink(photo_path, self.latest_path)
        except Exception,e:
            pass
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
            or not self.camera_init_time
            or self.camera_init_time + config['max_time'] < now):
            if not self.restart_camera():
                # If camera does not come back up we're screwed
                self.stop()

        # yield cpu to other things that might want it                
        time.sleep(0.5)


if __name__ == '__main__':
    instance = timelapse_service()

    if (len(sys.argv) < 2):
        print "Use 'start', 'stop' or 'status' as argument"
        sys.exit(1)

    silent = False
    try:
        if sys.argv[2] == 'silent':
            silent = True
    except Exception as e:
        pass
    

    #syslog.syslog('Called with %s' % sys.argv[1])
    #print 'Called with %s' % sys.argv[1]
    pid = burrdaemon.readPidFile(instance.pidfile_path)

    if (sys.argv[1] == 'status'):
        if pid:
            if not silent:
                msg = "Running as PID %d" % pid
                print msg
            sys.exit(0)
        else:
            if not silent:
                msg =  "Not running"
                print msg
            sys.exit(1)

    if (sys.argv[1] == 'start'):
        # If previous run is being stopped wait for it to complete
        if (   pid
            and os.path.exists(instance.pidfile_path+'.stopping')):
            if not silent:
                msg = "PID %d is being stopped, waiting" % pid
                print msg
                syslog.syslog(msg)
            wait_for_done = datetime.timedelta(seconds=30)
            wait_started = datetime.datetime.now()
            while pid:
                pid = burrdaemon.readPidFile(instance.pidfile_path)
                now = datetime.datetime.now()
                if wait_started + wait_for_done < now:
                    if not silent:
                        msg = "Grew tired of waiting"
                        print msg
                        syslog.syslog(msg)
                    break
                time.sleep(0.1)

        if pid:
            if not silent:
                msg = "Running as PID %d" % pid
                print msg
                syslog.syslog(msg)
            sys.exit(1)
        signal.signal(signal.SIGUSR1, instance.stop)
        burrdaemon.run(instance.run, dir=os.path.dirname(instance.pidfile_path), ident='timelapse_service', pidFilePath=instance.pidfile_path)
        sys.exit(0)

    def stop_cleanup():
        try:
            os.unlink(instance.pidfile_path+'.stopping')
        except OSError as e:
            print >>sys.stderr, "cleanup failed:", e
            return False
        

    wait_for_exit = datetime.timedelta(seconds=10)
    if (sys.argv[1] == 'stop'):
        if not pid:
            if not silent:
                msg =  "Not running"
                print msg
                syslog.syslog(msg)
            sys.exit(1)
        try:
            import atexit
            atexit.register(stop_cleanup)
            touch(instance.pidfile_path+'.stopping')
            os.kill(pid, signal.SIGUSR1)
            wait_started = datetime.datetime.now()
            while True:
                if not burrdaemon.readPidFile(instance.pidfile_path):
                    # Process exited ok
                    sys.exit(0)
                now = datetime.datetime.now()
                if wait_started + wait_for_exit < now:
                    break
                time.sleep(0.1)
                
            if not silent:
                msg =  "SIGUSR1 did not stop the child, trying SIGTERM"
                print msg
                syslog.syslog(msg)
            os.kill(pid, signal.SIGTERM)
            wait_started = datetime.datetime.now()
            while True:
                if not burrdaemon.readPidFile(instance.pidfile_path):
                    # Process exited ok
                    sys.exit(0)
                now = datetime.datetime.now()
                if wait_started + wait_for_exit < now:
                    break
                time.sleep(0.1)

            if not silent:
                msg =  "SIGTERM did not stop the child, trying SIGKILL"
                print msg
                syslog.syslog(msg)
            os.kill(pid, signal.SIGKILL)
            wait_started = datetime.datetime.now()
            while True:
                if not burrdaemon.readPidFile(instance.pidfile_path):
                    # Process exited ok
                    sys.exit(0)
                now = datetime.datetime.now()
                if wait_started + wait_for_exit < now:
                    break
                time.sleep(0.1)
                
            if not silent:
                msg =  "SIGKILL did not work, giving up. PID is %s" % pid
                print msg
                syslog.syslog(msg)
            sys.exit(1)
        except OSError, exc:
            msg = "Failed to terminate %(pid)d: %(exc)s" % vars()
            print msg
            syslog.syslog(msg)
            sys.exit(1)

    print "Unknown command '%s'" % sys.argv[1]
    sys.exit(1)
