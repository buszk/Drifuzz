#!/bin/bash

set -x
set -e

BUILD_QEMU=0
BUILD_LINUX=1
REBUILD_QEMU=0
REBUILD_LINUX=0


# compile qemu
if [ "$BUILD_QEMU" = 1 ]; then
pushd $PWD
if [ ! -d qemu-build ] || [ "$REBUILD_QEMU" = 1 ]; then
rm -rf qemu-build
mkdir qemu-build
( cd qemu-build && ../qemu/configure --target-list=x86_64-softmmu --enable-debug --cc=gcc )
fi
make -C qemu-build -j4
popd
fi

# compile linux kernel
if [ "$BUILD_LINUX" = 1 ]; then
pushd $PWD
if [ ! -d linux-build ] || [ "$REBUILD_LINUX" = 1 ]; then
rm -rf linux-build
mkdir linux-build
(cd linux && make O=../linux-build allnoconfig)
cp .config linux-build
fi
make -C linux-build -j4
popd
fi


