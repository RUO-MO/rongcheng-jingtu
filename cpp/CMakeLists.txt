cmake_minimum_required(VERSION 3.10)
project(cpp_module)

set(CMAKE_EXPORT_COMPILE_COMMANDS ON)
set(CMAKE_CXX_STANDARD 17)

message(STATUS "========================================")
message(STATUS "配置 蓉城净途 C++ 模块")
message(STATUS "========================================")

# 包含目录
include_directories(include)

# 实际存在的源文件（根据检查结果调整）
set(COMMON_SOURCES
    src/TSP.cpp
    # src/Utils.cpp  # 空文件，暂时移除
    # src/Interpolation.cpp  # 不存在，暂时移除
)

# 检查源文件
foreach(src ${COMMON_SOURCES})
    if(NOT EXISTS "${CMAKE_SOURCE_DIR}/${src}")
        message(FATAL_ERROR "源文件不存在: ${src}")
    endif()
endforeach()

# bindings.cpp 在根目录
set(BINDINGS_FILE "bindings.cpp")
if(NOT EXISTS "${CMAKE_SOURCE_DIR}/${BINDINGS_FILE}")
    message(FATAL_ERROR "bindings.cpp 必须在项目根目录！")
endif()

message(STATUS "源文件: ${COMMON_SOURCES}")
message(STATUS "绑定文件: ${BINDINGS_FILE}")

# Python3 配置
find_package(Python3 COMPONENTS Interpreter Development REQUIRED)
message(STATUS "Python3: ${Python3_EXECUTABLE}")

# pybind11：优先使用环境变量 pybind11_DIR，否则由 CMake 自动查找
if(DEFINED ENV{pybind11_DIR})
    set(pybind11_DIR "$ENV{pybind11_DIR}")
endif()
find_package(pybind11 CONFIG REQUIRED)
message(STATUS "pybind11: ${pybind11_VERSION}")

# 创建 Python 模块
pybind11_add_module(_core ${BINDINGS_FILE} ${COMMON_SOURCES})

# 输出目录
set(OUTPUT_DIR "${CMAKE_SOURCE_DIR}/../python")
file(MAKE_DIRECTORY ${OUTPUT_DIR})

set_target_properties(_core PROPERTIES
    LIBRARY_OUTPUT_DIRECTORY "${OUTPUT_DIR}"
    RUNTIME_OUTPUT_DIRECTORY "${OUTPUT_DIR}"
    LIBRARY_OUTPUT_DIRECTORY_DEBUG "${OUTPUT_DIR}"
    RUNTIME_OUTPUT_DIRECTORY_DEBUG "${OUTPUT_DIR}"
    LIBRARY_OUTPUT_DIRECTORY_RELEASE "${OUTPUT_DIR}"
    RUNTIME_OUTPUT_DIRECTORY_RELEASE "${OUTPUT_DIR}"
)

message(STATUS "输出目录: ${OUTPUT_DIR}")
message(STATUS "========================================")
message(STATUS "配置完成！")
message(STATUS "========================================")