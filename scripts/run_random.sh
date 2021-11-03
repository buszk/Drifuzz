#!/bin/bash

if [ $# != 1 ];then
    echo "Usage: $0 <target>"
    exit 1
fi

target=$1
work=work/work-$target-random
seed=seed/seed-random
np=$(nproc)
np=$(($np/2))

echo "$np Processes"
echo "target: $target"
echo "work directory: $work"
echo "seed directory: $seed"

# Run fuzzing
python3 fuzzer/drifuzz.py --Purge -D -p $np $seed $work $target
stty sane
