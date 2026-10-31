cmake_minimum_required(VERSION 3.20)
project(ziti-hook C)

find_package(ziti CONFIG REQUIRED)

add_executable(ziti-hook ziti-hook.c)
target_link_libraries(ziti-hook PRIVATE ziti::ziti)
target_compile_options(ziti-hook PRIVATE -Os -ffunction-sections -fdata-sections)
target_link_options(ziti-hook PRIVATE -static -Wl,--gc-sections -s)
