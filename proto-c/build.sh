#!/bin/sh
# Builds the static C ziti-hook binary on Alpine against the prebuilt ziti-sdk-c-deps bundle.
# Usage: build.sh <dir holding CMakeLists.txt and ziti-hook.c> <output dir>
set -eu
src="$1"
out="$2"

apk add --no-cache build-base cmake ninja-is-really-ninja
cmake -S "$src" -B /build -G Ninja -DCMAKE_BUILD_TYPE=MinSizeRel
cmake --build /build
mkdir -p "$out"
cp /build/ziti-hook "$out/"