#!/bin/bash

if [ $# -lt 3 ]; then
    echo "$0 <target> <work> <input>"
    exit 1
fi
target=$1
work=$2
input=$3

python3 fuzzer/reproduce.py --reproduce $input seed/seed-random $work $target
stty sane
