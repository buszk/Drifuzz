#!/bin/bash

if [ $# != 1 ];then 
    echo "Usage: $0 <target>"
    exit 1
fi

target=$1
work=work/work-$target-conc
seed=seed/seed-random
np=$(nproc)
np=$(($np/2))
cnp=$(($np/8))

echo "$np Processes"
echo "target: $target"
echo "work directory: $work"
echo "seed directory: $seed"

if [ ! -f ~/Workspace/git/drifuzz-panda/work/$target/$target.qcow2 ]; then
    echo "Cannot run concolic script because concolic image for $target isn't setup"
    echo "Go to drifuzz-panda directory and run:"
    echo "  ./snapshot_helper.py $target"
    exit 1
fi

rm -rf $work/tmp_conc_*

# Run fuzzing
python3 fuzzer/drifuzz.py --Purge --concolic $cnp -D -p $np $seed $work $target 
