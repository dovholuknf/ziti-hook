# Static musl build of the C ziti-hook client, shipped as a one-binary FROM scratch image.
# Unverified: written without a Docker daemon. Expect to fix the vcpkg-on-Alpine steps on the first CI run.
FROM alpine:3.22 AS build
RUN apk add --no-cache build-base cmake ninja git curl zip unzip tar pkgconf linux-headers perl bash
ENV VCPKG_FORCE_SYSTEM_BINARIES=1 VCPKG_ROOT=/opt/vcpkg
RUN git clone --depth 1 https://github.com/microsoft/vcpkg ${VCPKG_ROOT} && ${VCPKG_ROOT}/bootstrap-vcpkg.sh -disableMetrics

ARG ZITI_SDK_C_REF=main
RUN git clone --depth 1 --branch ${ZITI_SDK_C_REF} https://github.com/openziti/ziti-sdk-c /src/ziti-sdk-c
RUN cmake -S /src/ziti-sdk-c -B /build/sdk -G Ninja -DCMAKE_BUILD_TYPE=MinSizeRel \
        -DCMAKE_TOOLCHAIN_FILE=${VCPKG_ROOT}/scripts/buildsystems/vcpkg.cmake \
        -DVCPKG_TARGET_TRIPLET=x64-linux -DBUILD_SHARED_LIBS=OFF -DBUILD_TESTING=OFF -DBUILD_EXAMPLES=OFF \
        -DCMAKE_INSTALL_PREFIX=/opt/ziti \
    && cmake --build /build/sdk && cmake --install /build/sdk

COPY CMakeLists.txt ziti-hook.c /src/hook/
RUN cmake -S /src/hook -B /build/hook -G Ninja -DCMAKE_BUILD_TYPE=MinSizeRel \
        -DCMAKE_TOOLCHAIN_FILE=${VCPKG_ROOT}/scripts/buildsystems/vcpkg.cmake \
        -DVCPKG_TARGET_TRIPLET=x64-linux -DCMAKE_PREFIX_PATH=/opt/ziti \
    && cmake --build /build/hook && mkdir /out && cp /build/hook/ziti-hook /out/

FROM scratch
COPY --from=build /out/ziti-hook /ziti-hook
ENTRYPOINT ["/ziti-hook"]
