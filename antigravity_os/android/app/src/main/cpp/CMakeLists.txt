cmake_minimum_required(VERSION 3.22.1)
project(agos C)

# The stage-0 interpreter lives at antigravity_os/src/bada.c and is included
# verbatim by agos_jni.c -- one source of truth for desktop and Android.
get_filename_component(AGOS_ROOT "${CMAKE_CURRENT_SOURCE_DIR}/../../../../.." ABSOLUTE)

add_library(agos SHARED agos_jni.c)
target_include_directories(agos PRIVATE "${AGOS_ROOT}/src")
target_link_libraries(agos m)
