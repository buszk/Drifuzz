#!/bin/bash
np=$(nproc)
np=$(($np/2))
for i in `seq 0 $(($np-1))`; do
    grep -rn " $i]" debug.log|tail -n 1
done
