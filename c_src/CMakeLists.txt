cmake_minimum_required(VERSION 3.18)

project(pylibtooling CXX)

if (NOT LLVM_SOURCE_DIR)
  message(FATAL_ERROR "LLVM_SOURCE_DIR not set")
endif ()

add_subdirectory(${LLVM_SOURCE_DIR}/llvm ${CMAKE_CURRENT_BINARY_DIR}/llvm EXCLUDE_FROM_ALL)
include_directories(${LLVM_SOURCE_DIR}/clang/include)
include_directories(${CMAKE_CURRENT_BINARY_DIR}/llvm/tools/clang/include)
include_directories(${LLVM_SOURCE_DIR}/llvm/include)
include_directories(${CMAKE_CURRENT_BINARY_DIR}/llvm/include)

find_package(pybind11 REQUIRED CONFIG)
pybind11_add_module(_C binding.cc)
add_library(dummy SHARED dummy.cc)

llvm_map_components_to_libnames(llvm_libs support)
set(DEPS_LIBS
    ${llvm_libs}
    clangAST
    clangBasic
    clangDriver
    clangFrontend
    clangRewriteFrontend
    clangSerialization
    clangStaticAnalyzerFrontend
    clangTooling
    clangToolingSyntax
    clangDependencyScanning
    clangTransformer
    clangToolingASTDiff
    clangAST
    clangASTMatchers
    clangFormat
    clangLex
    clangRewrite
    clangToolingCore
    clangToolingInclusions
    clangToolingInclusionsStdlib
    clangToolingRefactoring
    clangAnalysis
    clangARCMigrate
    clangCodeGen
    clangDynamicASTMatchers
    clangEdit
    clangFrontendTool
    clangIndex
    clangParse
    clangSema
    clangStaticAnalyzerCheckers
    clangStaticAnalyzerCore
)
target_link_libraries(_C PRIVATE ${DEPS_LIBS})
target_link_libraries(dummy PRIVATE ${DEPS_LIBS})
if (NOT EXTENSION_OUTPUT_DIR)
  set(EXTENSION_OUTPUT_DIR ${CMAKE_CURRENT_BINARY_DIR})
endif ()
set_target_properties(_C
    PROPERTIES
    LIBRARY_OUTPUT_DIRECTORY "${EXTENSION_OUTPUT_DIR}"
)