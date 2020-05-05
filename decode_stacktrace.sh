#!/bin/bash
file=$1

# Preprocessing
sed -ie 's///g' $file

# handle to linux script
./linux/scripts/decode_stacktrace.sh linux-module-build/vmlinux image/chroot/lib/modules/5.6.0/ linux-module-build/ < $file
