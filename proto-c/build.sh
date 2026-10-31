#!/bin/sh
# Builds the static C ziti-hook binary on Alpine. Run by the Dockerfile, or by hand in any Alpine shell.
# Usage: build.sh <dir holding CMakeLists.txt, vcpkg.json and ziti-hook.c> <output dir>
set -eu
src="$1"
out="$2"

apk add --no-cache build-base cmake ninja-is-really-ninja autoconf autoconf-archive automake libtool git curl zip unzip tar \
    pkgconf linux-headers perl bash python3
export VCPKG_FORCE_SYSTEM_BINARIES=1 VCPKG_ROOT=/opt/vcpkg
[ -d "$VCPKG_ROOT" ] || git clone https://github.com/microsoft/vcpkg "$VCPKG_ROOT"
[ -x "$VCPKG_ROOT/vcpkg" ] || "$VCPKG_ROOT/bootstrap-vcpkg.sh" -disableMetrics

cmake -S "$src" -B /build -G Ninja -DCMAKE_BUILD_TYPE=MinSizeRel \
    -DCMAKE_TOOLCHAIN_FILE="$VCPKG_ROOT/scripts/buildsystems/vcpkg.cmake" -DVCPKG_TARGET_TRIPLET=x64-linux
cmake --build /build
mkdir -p "$out"
cp /build/ziti-hook "$out/"