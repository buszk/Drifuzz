#!/bin/bash
if [ $# -lt 2 ]; then
    echo "$0 <target> <setting>"
    exit 1
fi
target=$1
setting=$2
work=work/work-$target-$setting
for f in $work/corpus/*; do
    echo "File: $f"
    ./reproduce.sh $target $work $f
done
stty sane
