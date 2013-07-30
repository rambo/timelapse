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
    
    #print td
    #print files
    
    
    
