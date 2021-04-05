#!/bin/bash

target=$1
work=work-reproduce

if [ $# == 1 ]; then
input=~/Workspace/git/drifuzz-panda/work/$target/out/0
else
input=$2
fi

rm -rf $work
mkdir -p $work
cp ~/Workspace/git/drifuzz-panda/work/$target/$target.sav $work/globalmodule.json

python3 fuzzer/reproduce.py --Purge --reproduce $input seed $work $target
