#!/bin/bash
qemu-build/x86_64-softmmu/qemu-system-x86_64 \
    -kernel linux-build/arch/x86_64/boot/bzImage \
    -initrd initramfs.cpio.gz \
    -m 1G \
    -device drifuzz\
    -net nic,model=alx \
    -nographic \
    -append "console=ttyS0 nokaslr" \
    -enable-kvm
