#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys,os
import datetime

def usage():
    print "\nUsage:\n    %s yyyymmdd_hhmm yyyymmdd_hhmm \n" % os.path.basename(sys.argv[0])


if __name__ == '__main__':
    args = sys.argv[1:]
    if len(args) < 2:
        usage()
        sys.exit(1)
    dt1 = datetime.datetime(year=int(args[0][0:4]),month=int(args[0][4:6]),day=int(args[0][6:8]),hour=int(args[0][9:11]),minute=int(args[0][11:13]))
    dt2 = datetime.datetime(year=int(args[1][0:4]),month=int(args[1][4:6]),day=int(args[1][6:8]),hour=int(args[1][9:11]),minute=int(args[1][11:13]))
    td = dt2 - dt1
    days = td.days
    hours = td.seconds/3600
    minutes = (td.seconds-hours*3600)/60
    print "%d,%d,%d" % (days, hours, minutes)
    
