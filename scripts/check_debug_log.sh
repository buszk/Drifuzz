#!/bin/bash

for i in `seq 0 19`; do
    grep -rn " $i]" debug.log|tail -n 1
done
