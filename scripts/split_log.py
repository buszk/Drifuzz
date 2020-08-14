#!/usr/bin/env python3
import sys
print(sys.argv[1])
with open(sys.argv[1], 'r') as f:
    buf = ''
    #line = f.readline()
    cnt = 0
    #print(line)
    #while line:
    for line in f:
        if 'exec_init' in line:
            buf = ''
        if 'exec_exit' in line:
            print(buf)
            with open('rw-%d.log' % cnt, 'w') as lf:
                lf.write(buf)
            cnt += 1

        buf += line
        #line = f.readline()

