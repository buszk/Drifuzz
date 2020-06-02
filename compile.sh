#!/bin/bash

#set -x
set -e

BUILD_QEMU=0
BUILD_LINUX=0
BUILD_MODULE=0
BUILD_IMAGE=0
REBUILD_QEMU=0
REBUILD_LINUX=0
TARGET=

while :; do
    case $1 in
        --build)
            BUILD_QEMU=1
            BUILD_LINUX=1
        ;;
        --build-qemu)
            BUILD_QEMU=1
        ;;
        --build-linux)
            BUILD_LINUX=1
        ;;
        --build-module)
            BUILD_MODULE=1
        ;;
        --build-image)
            sudo pwd
            BUILD_IMAGE=1
        ;;
        --rebuild)
            REBUILD_QEMU=1
            REBUILD_LINUX=1
        ;;
        --rebuild-qemu)
            REBUILD_QEMU=1
        ;;
        --rebuild-linux)
            REBUILD_LINUX=1
        ;;
        --target)
            shift
            TARGET=$1
        ;;
        *)
        break
    esac
    shift
done


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

# compile modular linux kernel
if [ "$BUILD_LINUX" = 1 ]; then
pushd $PWD
if [ ! -d linux-module-build ]; then
rm -rf linux-module-build
mkdir linux-module-build
(cd linux && make O=../linux-module-build allnoconfig)
cp .config.mod linux-module-build
fi
make -C linux-module-build -j4
popd
fi

# compile linux modules
if [ "$BUILD_MODULE" = 1 ]; then
pushd $PWD
make -C linux-module-build -j4 modules
popd
fi

# build image
if [ "$BUILD_IMAGE" = 1 ]; then
pushd $PWD
sudo make INSTALL_MOD_PATH=$PWD/image/chroot -C linux-module-build -j4 modules_install
if [ "$TARGET" != "" ]; then
(cd image && make clean && make driver-$TARGET && ./build-image.sh)
else
(cd image && make clean && ./build-image.sh)
fi
popd
fi

