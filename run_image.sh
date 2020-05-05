#!/bin/bash
#gdb -ex "handle SIGUSR1 noprint" \
#    -ex "r" \
#    --args \
qemu-build/x86_64-softmmu/qemu-system-x86_64 \
    -kernel linux-module-build/arch/x86_64/boot/bzImage \
    -hda image/buster.img \
    -append "console=ttyS0 nokaslr root=/dev/sda earlyprintk=serial" \
    -m 1G \
    -snapshot \
    -device drifuzz\
    -net user\
    -net nic,model=alx\
    -nographic \
    -machine kernel-irqchip=off \
    -enable-kvm \
    -object memory-backend-file,size=1M,share,mem-path=/dev/shm/ivshmem,id=hostmem \
    -device ivshmem-plain,memdev=hostmem \
    #-gdb tcp::1234 \
    #-S

exit
    -net user,hostfwd=tcp::7788-:22\

    -hda $IMAGE/stretch.img \

    -initrd image/initramfs.cpio.gz \
    -append "console=ttyS0 nokaslr root=/dev/ram0" \

    -hda $IMAGE/stretch.img \
    -append "console=ttyS0 nokaslr root=/dev/sda earlyprintk=serial" \

    -initrd initramfs.cpio.gz \
    -append "console=ttyS0 nokaslr" \

    -hda image/buster.img \
    -append "console=ttyS0 nokaslr root=/dev/sda earlyprintk=serial" \
