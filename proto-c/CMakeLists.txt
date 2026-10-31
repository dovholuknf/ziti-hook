cmake_minimum_required(VERSION 3.21)
project(ziti-hook C CXX)

set(ZITI_SDK_VERSION "1.20.1" CACHE STRING "ziti-sdk-c tag or branch")
set(ZITI_SDK_DIR "" CACHE FILEPATH "developer option: use a local ziti-sdk-c checkout")

include(FetchContent)
if (ZITI_SDK_DIR)
    add_subdirectory(${ZITI_SDK_DIR} ziti-sdk)
else ()
    FetchContent_Declare(ziti-sdk-c
            GIT_REPOSITORY https://github.com/openziti/ziti-sdk-c.git
            GIT_TAG ${ZITI_SDK_VERSION})
    set(ZITI_BUILD_TESTS off)
    set(ZITI_BUILD_PROGRAMS off)
    set(BUILD_TESTING off)
    set(BUILD_EXAMPLES off)
    FetchContent_MakeAvailable(ziti-sdk-c)
endif ()

add_executable(ziti-hook ziti-hook.c)
target_link_libraries(ziti-hook PRIVATE ziti)
target_compile_options(ziti-hook PRIVATE -Os -ffunction-sections -fdata-sections)
target_link_options(ziti-hook PRIVATE -static -Wl,--gc-sections -s)
