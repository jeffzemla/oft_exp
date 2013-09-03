#!/usr/bin/env python

import sys
import subprocess

if len(sys.argv) == 2:
    if sys.argv[1] == "1":
        subprocess.call(['./exp_without_time_limit.py'])
    elif sys.argv[1] == "2":
        subprocess.call(['./exp_with_time_limit.py'])
    else:
        print "invalid selection"
else:
    print "./exp.py <#>"
    print "1 - exp_without_time_limits.py"
    print "2 - exp_with_time_limits.py"
