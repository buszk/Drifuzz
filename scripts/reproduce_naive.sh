#!/bin/bash

FLAT=0
N=1
while :; do
    case $1 in
        --flat)
            FLAT=1
            shift
        ;;
        --n)
            N=$2
            shift
            shift
        ;;
        *)
            break
    esac
done

if [ $# -lt 3 ]; then
    echo "$0 <target> <work> <input>"
    exit 1
fi
target=$1
work=$2
input=$3

if [ "$FLAT" -eq 1 ]; then
    python3 fuzzer/reproduce.py --reproduce $input seed/seed-random $work $target
    stty sane
    scripts/flat_seed.py
    mv rw.log rw.log.1
fi
for i in `seq $N`; do
    python3 fuzzer/reproduce.py --naive --reproduce flat.inp seed/seed-random $work $target
    stty sane
    mv rw.log rw.log.2
done