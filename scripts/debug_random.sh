#!/bin/bash

if [ $# != 1 ];then 
    echo "Usage: $0 <target>"
    exit 1
fi

target=$1
work=work-$target-random
seed=seed/seed-random

echo "target: $target"
echo "work directory: $work"
echo "seed directory: $seed"

# Prepare work directory with globalmodule.json
rm -rf $work
mkdir -p $work

# Run fuzzing
python3 fuzzer/drifuzz.py --verbose -D -p 1 $seed $work $target 
