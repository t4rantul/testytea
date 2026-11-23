cmake_minimum_required(VERSION 3.24)
project(Basalt VERSION 0.1.0 LANGUAGES CXX)

if(POLICY CMP0135)
    cmake_policy(SET CMP0135 NEW)
endif()

option(BASALT_BUILD_TESTS "Build Basalt unit tests" ON)
option(BASALT_ENABLE_SANITIZERS "Enable address and undefined-behavior sanitizers where supported" OFF)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

include(FetchContent)
set(GLM_BUILD_TESTS OFF CACHE BOOL "" FORCE)
set(GLM_BUILD_LIBRARY OFF CACHE BOOL "" FORCE)
set(DOCTEST_WITH_TESTS OFF CACHE BOOL "" FORCE)
set(DOCTEST_NO_INSTALL ON CACHE BOOL "" FORCE)
set(DOCTEST_WITH_MAIN_IN_STATIC_LIB OFF CACHE BOOL "" FORCE)

FetchContent_Declare(
    glm
    GIT_REPOSITORY https://github.com/g-truc/glm.git
    GIT_TAG 1.0.3
    GIT_SHALLOW TRUE
)
FetchContent_Declare(
    doctest
    GIT_REPOSITORY https://github.com/doctest/doctest.git
    GIT_TAG v2.5.3
    GIT_SHALLOW TRUE
)
FetchContent_MakeAvailable(glm doctest)

add_library(BasaltCore STATIC
    src/Basalt/Core/Scene.cpp
)
add_library(Basalt::Core ALIAS BasaltCore)
target_include_directories(BasaltCore PUBLIC
    $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
    $<INSTALL_INTERFACE:include>
)
target_link_libraries(BasaltCore PUBLIC glm::glm)
target_compile_features(BasaltCore PUBLIC cxx_std_20)

function(basalt_enable_warnings target)
    if(MSVC)
        target_compile_options(${target} PRIVATE /W4 /WX /permissive-)
    else()
        target_compile_options(${target} PRIVATE -Wall -Wextra -Wpedantic -Werror)
    endif()
endfunction()
basalt_enable_warnings(BasaltCore)

if(BASALT_ENABLE_SANITIZERS AND NOT MSVC)
    target_compile_options(BasaltCore PRIVATE -fsanitize=address,undefined -fno-omit-frame-pointer)
    target_link_options(BasaltCore PRIVATE -fsanitize=address,undefined)
endif()

if(BASALT_BUILD_TESTS)
    include(CTest)
    enable_testing()
    add_executable(BasaltCoreTests
        tests/Basalt/Core/SceneTests.cpp
    )
    target_link_libraries(BasaltCoreTests PRIVATE Basalt::Core doctest::doctest)
    basalt_enable_warnings(BasaltCoreTests)
    if(BASALT_ENABLE_SANITIZERS AND NOT MSVC)
        target_compile_options(BasaltCoreTests PRIVATE -fsanitize=address,undefined -fno-omit-frame-pointer)
        target_link_options(BasaltCoreTests PRIVATE -fsanitize=address,undefined)
    endif()
    add_test(NAME BasaltCoreTests COMMAND BasaltCoreTests)
endif()
