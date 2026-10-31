cmake_minimum_required(VERSION 3.21)
project(ziti-hook C)

set(ZITI_DEPS_URL "https://github.com/dovholuknf/ziti-sdk-c-deps/releases/download/sdk-1.20.1-1/ziti-deps-1.20.1-x64-musl.zip"
        CACHE STRING "prebuilt static musl libziti and dependencies")

include(FetchContent)
FetchContent_Declare(ziti-deps URL ${ZITI_DEPS_URL} DOWNLOAD_EXTRACT_TIMESTAMP TRUE)
FetchContent_MakeAvailable(ziti-deps)
list(APPEND CMAKE_PREFIX_PATH ${ziti-deps_SOURCE_DIR})
find_package(ziti-deps CONFIG REQUIRED)

add_executable(ziti-hook ziti-hook.c)
target_link_libraries(ziti-hook PRIVATE ziti-deps::ziti)
target_compile_options(ziti-hook PRIVATE -Os -ffunction-sections -fdata-sections)
target_link_options(ziti-hook PRIVATE -static -Wl,--gc-sections -s)
