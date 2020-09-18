#!/bin/bash

#set -x
set -e

BUILD_PANDA=0
BUILD_QEMU=0
BUILD_LINUX=0
BUILD_MODULE=0
BUILD_IMAGE=0
REBUILD_PANDA=0
REBUILD_QEMU=0
REBUILD_LINUX=0
TARGET=
NP=4

while :; do
    case $1 in
        --build)
            BUILD_PANDA=1
            BUILD_QEMU=1
            BUILD_LINUX=1
        ;;
        --build-panda)
            BUILD_PANDA=1
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
            sudo pwd #Ask for sudo perm early
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
        -j)
            shift
            NP=$1
        ;;
        *)
        break
    esac
    shift
done

# compile panda
if [ "$BUILD_PANDA" = 1 ]; then
if [ -z "$LLVM_INSTALL" ] || [ ! -d "$LLVM_INSTALL" ]; then
echo "Please specify LLVM install directory; skipping without"
else
pushd $PWD
if [ ! -d panda-build ] || [ "$REBUILD_PANDA" = 1 ]; then
rm -rf panda-build
mkdir panda-build
( cd panda-build &&
../panda/configure \
    --target-list=x86_64-softmmu \
    --cc=gcc --cxx=g++ \
    --enable-llvm --with-llvm="$LLVM_INSTALL" \
    --extra-cxxflags=-Wno-error=class-memaccess \
    --disable-werror \
    --python=python3
)
fi
make -C panda-build -j$NP
popd
fi
fi

# compile qemu
if [ "$BUILD_QEMU" = 1 ]; then
pushd $PWD
if [ ! -d qemu-build ] || [ "$REBUILD_QEMU" = 1 ]; then
rm -rf qemu-build
mkdir qemu-build
( cd qemu-build && ../qemu/configure --target-list=x86_64-softmmu --enable-debug --cc=gcc )
fi
make -C qemu-build -j$NP
popd
fi

# compile modular linux kernel
if [ "$BUILD_LINUX" = 1 ]; then
pushd $PWD
if [ ! -d linux-module-build ]; then
rm -rf linux-module-build
mkdir linux-module-build
(cd linux && make O=../linux-module-build allnoconfig)
cp .config linux-module-build
fi
make -C linux-module-build -j$NP
popd
fi

# compile linux modules
if [ "$BUILD_MODULE" = 1 ]; then
pushd $PWD
make -C linux-module-build -j$NP modules
popd
fi

# build image
if [ "$BUILD_IMAGE" = 1 ]; then
if ! [ -d image/chroot ]; then
(cd image && ./build-image.sh)
fi
pushd $PWD
sudo make INSTALL_MOD_PATH=$PWD/image/chroot -C linux-module-build -j4 modules_install
if [ "$TARGET" != "" ]; then
(cd image && make clean && make driver-$TARGET && ./build-image.sh)
else
(cd image && make clean && ./build-image.sh)
fi
popd
fi

