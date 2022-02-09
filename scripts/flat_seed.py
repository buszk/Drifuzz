#!/usr/bin/env python3

import argparse
from ast import parse
from email.policy import default

parser = argparse.ArgumentParser()

parser.add_argument("--rwlog", default='rw.log')
parser.add_argument('--out', default='flat.inp')
args = parser.parse_args()

def get_size(s):
    s = s.replace('[', ' ')
    s = s.replace(']', '')
    return int(s.split(' ')[2])

def parse_log(f):
    ret = bytearray()
    with open(f) as lf:
        for line in lf:
            if 'read' in line:
                sps = line.split(' ')
                assert len(sps) == 6
                size = get_size(sps[3])
                data = sps[5]
                if data[-1] == '\n':
                    data = data[:-1]
                assert len(data) <= 2*size
                data = data.rjust(2*size, '0')
                ret += bytearray(reversed(bytearray.fromhex(data)))
            elif 'dma_buf' in line:
                sps = line.split(' ')
                assert len(sps) == 5
                data = sps[4]
                if data[-1] == '\n':
                    data = data[:-1]
                ret += bytearray.fromhex(data)
    return ret

ba = parse_log(args.rwlog)
with open(args.out, 'wb') as f:
    f.write(ba)
