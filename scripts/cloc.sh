#!/bin/bash

echo "Linux kernel comm driver and instrumentation"
cloc linux/drivers/drifuzz linux/kernel/instr.c linux/include/linux/drifuzz.h |grep -A1 SUM

echo "kAFL modification"
cloc --fullpath --match-d='/(fuzzer)/' --git --diff 285a6e40e4d513278047c418a99d05064f715e89 HEAD |grep -A5 SUM

echo "Other"
cloc compile.sh image/ scripts --fullpath --not-match-d=image/chroot |grep -A1 SUM

echo "PANDA change"
cd panda
cloc --git --diff 264550a 3234d7a --fullpath --not-match-d=drifuzz/hw |grep -A5 SUM
cd ..

echo "Concolic scripts"
cloc ../drifuzz-concolic |grep SUM -A1
