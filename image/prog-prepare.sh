#!/bin/bash

modprobe -v -n $1 |sed \$d > load_dep_module.sh
bash load_dep_module.sh
