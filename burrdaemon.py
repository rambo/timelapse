#!/usr/bin/python
# -*- Mode: Python; py-indent-offset: 4 -*-
#
# Copyright (C) 2000,2001,2006,2007  Ray Burr
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
# 

"""
Run as a background process detached from the console.

This was developed under Linux, and it seems to also work under
FreeBSD.

:authors: Ray Burr
:license: MIT License
:contact: http://www.nightmare.com/~ryb/
"""

__version__ = "20070612"

import errno
import fcntl
import os
import sys
import syslog
import signal


# Hook directly into sys.exitfunc instead of using atexit.register to make
# sure that cleanup is done as the last thing (or as close as possible) when
# the interpreter is shutting down.  We'd like the PID file to be deleted just
# before the process exits.  This is to avoid a situation where the process
# gets stuck during shutdown after the PID file was deleted (for example, the
# threading atexit handler waits for a thread that hasn't exited).
import atexit # Import atexit so that it sets sys.exitfunc with its handler.
def _exitfunc(old_exitfunc=sys.exitfunc):
    old_exitfunc()
    cleanup()
sys.exitfunc = _exitfunc

_pidFilePath = None

_syslogFacilityMap = {
    "auth":   syslog.LOG_AUTH,
    "cron":   syslog.LOG_CRON,
    "daemon": syslog.LOG_DAEMON,
    "kern":   syslog.LOG_KERN,
    "lpr":    syslog.LOG_LPR,
    "mail":   syslog.LOG_MAIL,
    "news":   syslog.LOG_NEWS,
    "user":   syslog.LOG_USER,
    "uucp":   syslog.LOG_UUCP,
    "local0": syslog.LOG_LOCAL0,
    "local1": syslog.LOG_LOCAL1,
    "local2": syslog.LOG_LOCAL2,
    "local3": syslog.LOG_LOCAL3,
    "local4": syslog.LOG_LOCAL4,
    "local5": syslog.LOG_LOCAL5,
    "local6": syslog.LOG_LOCAL6,
    "local7": syslog.LOG_LOCAL7,
}

_syslogPriorityMap = {
    "emerg":  syslog.LOG_EMERG,
    "alert":  syslog.LOG_ALERT,
    "crit":   syslog.LOG_CRIT,
    "err":    syslog.LOG_ERR,
    "warning": syslog.LOG_WARNING,
    "notice": syslog.LOG_NOTICE,
    "info":   syslog.LOG_INFO,
    "debug":  syslog.LOG_DEBUG,
}

def _checkPidFile(pidfile):
    str = pidfile.readline(100)
    if str == "":
        return None
    try:
        n = int(str)
    except ValueError:
        return None
    try:
        os.kill(n, 0)
    except os.error, (code, message):
        if code != errno.ESRCH:
            raise
        return None
    return n

def readPidFile(path):
    try:
        pidfile = open(path, "r")
    except IOError:
        return None
    try:
        result = _checkPidFile(pidfile)
    finally:
        pidfile.close()
    return result

def lockPidFile(path):
    global _pidFilePath
    file = open(path, "a+", 0)
    try:
        # The lockf function is not well documented in the Python
        # Library Reference.  Calling it with these arguments results
        # in a F_SETLKW fcntl call with l_type set to F_WRLCK.  It
        # does not call the lockf() of the C library.
        fcntl.lockf(file.fileno(), fcntl.LOCK_EX)
        file.seek(0)
        pid = _checkPidFile(file)
        if pid is not None:
            return pid
        file.truncate(0)
        file.write("%d\n" % os.getpid())
        _pidFilePath = path
    finally:
        file.close()
    return None

def cleanup():
    global _pidFilePath
    try:
        if _pidFilePath:
            os.unlink(_pidFilePath)
            _pidFilePath = None
    except os.error:
        pass

class LoggerFile:
    """
    A class for a writable file-like object that calls a function for
    every line of text.  It is intended for replacing stdout/stderr
    and calling a logging function.  A callable object should be
    provided for logFn.
    """
    def __init__(self, logFn, name=None):
        self._logFn = logFn
        self.name = name
        self._line = ""
        self.softspace = 0

    def __repr__(self):
        if self.name:
            return "<LoggerFile %r>" % name
        else:
            return "<LoggerFile at %#x>" % _intToUnsignedLong(id(self))

    def write(self, s):
        while s:
            i = s.find("\n")
            if i < 0:
                self._line += s
                break
            self._line += s[:i]
            if self._line:
                self._logFn(self._line)
                self._line = ""
            s = s[i+1:]

    def writelines(self, lines):
        for line in lines:
            self.write(line)

    def flush(self):
        if self._line:
            self._logFn(self._line)
            self._line = ""

def detach(
        dir=None, ident=None, facility=None, logFn=None,
        syslogPriority=None):
    """
    Continue running in a new background process while exiting the
    current process.  Optionally redirect sys.stdout and sys.stderr to
    syslog.
    """
    if os.fork():
        # The parent process exits.
        os._exit(0)

    os.setsid()

    # Close stdin, stdout, stderr, and reopen pointing to /dev/null.
    # This assumes these are the first three file descriptors as is
    # usually the case.  Bad things could happen if these were altered
    # before this point.
    for fd in range(0, 3):
        try: os.close(fd)
        except: pass
    os.open("/dev/null", os.O_RDONLY)
    os.open("/dev/null", os.O_WRONLY)
    os.open("/dev/null", os.O_WRONLY)

    if ident:
        if facility is None:
            facility = syslog.LOG_USER
        if type(facility) is type(""):
            facility = _syslogFacilityMap[facility]

        if syslogPriority is None:
            syslogPriority = syslog.LOG_INFO
        if type(syslogPriority) is type(""):
            syslogPriority = _syslogPriorityMap[syslogPriority]

        syslog.openlog(ident, syslog.LOG_PID, facility)

        def logFn(text):
            syslog.syslog(syslogPriority, text)

    if logFn:
        sys.stdout = LoggerFile(logFn, "<stdout>")
        sys.stderr = LoggerFile(logFn, "<stderr>")

    if dir:
        os.chdir(dir)

def run(
        target, args=(), kwargs={},
        dir=None, ident=None, facility=None, logFn=None,
        noDetach=False, quiet=False, pidFilePath=None,
        trapKeyboardInterrupt=True, syslogPriority=None):
    """
    Call the target object running as a daemon process.
    """

    if dir is not None:
        os.chdir(dir)

    if (logFn is None) and (ident is None):
        try:
            ident = os.path.basename(sys.argv[0])
        except:
            pass

    err = sys.stderr

    if pidFilePath is not None:
        pid = readPidFile(pidFilePath)
        if pid is not None:
            print >>err, "Already running as PID %d" % pid
            sys.exit(1)

    if not noDetach:
        # Run as a background process.
        detach(dir, ident, facility, logFn, syslogPriority)
        # sys.stderr may have been changed.
        err = sys.stderr

    if pidFilePath is not None:
        pid = lockPidFile(pidFilePath)
        if pid is not None:
            # Somebody else locked.  Another instance must have been
            # started at almost the same time.
            print >>err, "Already running as PID %d" % pid
            sys.exit(1)

    try:
        if not quiet:
            print >>err, "Starting"
        # Set the SIGTERM signal to be handled the same way SIGINT
        # usually is so that the process exits more gracefully
        # (finally clauses are executed, etc.) when killed through
        # the kill system call.
        signal.signal(signal.SIGTERM, signal.default_int_handler)
        try:
            apply(target, args, kwargs)
        except KeyboardInterrupt:
            if not trapKeyboardInterrupt:
                raise
            if not quiet:
                print >>err, "Received a SIGTERM or SIGINT signal"
    finally:
        if not quiet:
            print >>err, "Exiting"
        # sys.exitfunc will call cleanup()

def _intToUnsignedLong(x):
    """
    Reinterpret negative int values as unsigned.  Depending on the OS and
    maybe the Python version, the id() builtin may sometimes return an
    object's address a negative integer.  This can be used to ensure the
    address is always positive.

    >>> '%#x' % id(object())
    '-0x481eabc8'
    >>> '%#x' % _intToUnsignedLong(id(object()))
    '0xb7e15438'
    """
    if x < 0:
        x += (sys.maxint + 1) << 1
    return x

def _test():

    import time

    def _thing():
        print "sleeping"
        time.sleep(10)

    # Run the above function in the background.  Output goes to the
    # system debug log which is usually somewhere like /var/log/debug.
    run(_thing,
        dir="/",
        ident="daemon-test",
        pidFilePath="/tmp/test.pid",
        syslogPriority="debug")

if __name__ == "__main__":
    _test()
