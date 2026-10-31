# Static musl build of the C ziti-hook client, shipped as a one-binary FROM scratch image.
FROM alpine:3.22 AS build
COPY CMakeLists.txt vcpkg.json ziti-hook.c build.sh /src/hook/
RUN sh /src/hook/build.sh /src/hook /out

FROM scratch
COPY --from=build /out/ziti-hook /ziti-hook
ENTRYPOINT ["/ziti-hook"]
