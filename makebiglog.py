#!/usr/bin/env python

# will overwrite current 'biglog'
# grabs individual files from exp/log and writes to scripts/logs

import os

INFOLDER='./logs/'
OUTFILE='./logs/biglog.csv'

subj=1
session=1
fnew = open(OUTFILE,'w')

for logname in os.listdir(INFOLDER):

    if ('.csv' in logname) and ('biglog' not in logname):
        logname = './logs/' + logname
        f = open(logname, 'r')
        cond=0
        rep=1
        onerep=1
        fiverep=1

        # delete everything through practice trials
        for line in range(14):
            f.readline()

        for line in f:
            if 'Start' in line:
                if 'calibration' in line:
                    cond=10
                    rep=line.split(':')[0].split('calibration ')[1]
                if '1.0 minutes' in line:
                    cond=1
                    rep=onerep
                    onerep=onerep+1
                if '5.0 minutes' in line:
                    cond=5
                    rep=fiverep
                    fiverep=fiverep+1
            if '#' not in line:
                newline=str(subj) + ',' + str(session) + ',' + str(cond) + ',' + str(rep) + ',' + str(onerep+fiverep-1) + ',' + line
                fnew.write(newline)
        
        f.close() 
        if session < 3:
            session += 1
        else:
            subj=subj+1
            session=1

fnew.close()
