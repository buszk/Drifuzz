#!/bin/bash

if [ $# != 1 ];then
    echo "Usage: $0 <target>"
    exit 1
fi

target=$1
work=work/work-$target-model
seed=seed-$target

echo "target: $target"
echo "work directory: $work"
echo "seed directory: $seed"

# Prepare work directory with globalmodule.json
rm -rf $work
mkdir -p $work
cp ../drifuzz-concolic/work/$target/$target.sav $work/globalmodule.json

# Prepare seed directory with initial seed
rm -rf $seed
mkdir -p $seed
cp ../drifuzz-concolic/work/$target/out/0 $seed

# Run fuzzing
python3 fuzzer/drifuzz.py --gdb -D -p 1 $seed $work $target
stty sane
