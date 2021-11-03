#!/bin/bash

target=$1
work=work/work-reproduce

if [ $# == 1 ]; then
input=~/Workspace/git/drifuzz-concolic/work/$target/out/0
else
input=$2
fi

rm -rf $work
mkdir -p $work
cp ~/Workspace/git/drifuzz-concolic/work/$target/$target.sav $work/globalmodule.json

python3 fuzzer/reproduce.py --Purge --reproduce $input seed/seed-random $work $target
stty sane
