#!/bin/bash

panda-build/x86_64-softmmu/panda-system-x86_64 \
    -hda image/buster.img \
    -kernel linux-module-build/arch/x86_64/boot/bzImage \
    -append "console=ttyS0 nokaslr root=/dev/sda earlyprintk=serial net.ifnames=0 modprobe.blacklist=e1000,$1" \
    -snapshot \
    -enable-kvm \
    -k dev \
    -m 1G \
    -nographic \
    -machine kernel-irqchip=off \
    -net user \
    -net nic,model=$1 \
    # -device drifuzz
