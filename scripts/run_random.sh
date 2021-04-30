#!/bin/bash

if [ $# != 1 ];then 
    echo "Usage: $0 <target>"
    exit 1
fi

target=$1
work=work/work-$target-random
seed=seed/seed-random

echo "target: $target"
echo "work directory: $work"
echo "seed directory: $seed"

# Run fuzzing
python3 fuzzer/drifuzz.py --Purge -D -p 8 $seed $work $target 
