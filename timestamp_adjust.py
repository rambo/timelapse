#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys,os
import datetime

def usage():
    print "\nUsage:\n    %s days,hours,minutes file1 [file2] [filen]\n" % os.path.basename(sys.argv[0])


if __name__ == '__main__':
    args = sys.argv[1:]
    if len(args) < 2:
        usage()
        sys.exit(1)
    adays, ahours, aminutes = args[0].split(',')
    files = args[1:]
    td = datetime.timedelta(days=int(adays), hours=int(ahours), minutes=int(aminutes))
    
    for fname in files:
        fname_b = os.path.basename(fname)
        file_time = datetime.datetime(year=int(fname_b[0:4]),month=int(fname_b[4:6]),day=int(fname_b[6:8]),hour=int(fname_b[9:11]),minute=int(fname_b[11:13]),second=int(fname_b[13:15]))
        new_time = file_time+td
        #print "DEBUG: adjusted %s to %s" % (file_time, new_time)
        newname_b = "%s%s" % (new_time.strftime('%Y%m%d_%H%M%S'), fname_b[15:])
        newname = fname.replace(fname_b, newname_b)
        print "Renaming %s -> %s" % (fname, newname)
        os.rename(fname, newname)
