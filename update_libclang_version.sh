#!/bin/bash
set -ex

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
pushd $SCRIPT_DIR

VERSION=17.0.2
CACHE_DIR=~/.cache/pylibtooling/llvm_src_dir/${VERSION}
mkdir -p ${CACHE_DIR}
FILE=llvm-project-${VERSION}.src.tar.xz
LINK=https://github.com/llvm/llvm-project/releases/download/llvmorg-${VERSION}/${FILE}
sed -i 's/__CLANG_VERSION__ = "[0-9]*\.[0-9]*\.[0-9]*"/__CLANG_VERSION__ = "'${VERSION}'"/g' pylibtooling/__init__.py
sed -i -E "s/[0-9]+\.[0-9]+\.[0-9]+/${VERSION}/g" c_src/cfg.yaml
sed -i 's/__FETCH_LLVM_VERSION__ = "[0-9]*\.[0-9]*\.[0-9]*"/__FETCH_LLVM_VERSION__ = "'${VERSION}'"/g' setup.py

# download cache

mkdir -p download_cache
pushd download_cache
if [ ! -f ${CACHE_DIR}/${FILE} ]; then
    wget ${LINK} -O ${CACHE_DIR}/${FILE}
    tar -xvf ${CACHE_DIR}/${FILE} -C ${CACHE_DIR} --strip-components=1
fi

if [ ! -d ${VERSION} ]; then
    ln -s ${CACHE_DIR} ${VERSION}
fi
popd

# build extension
mkdir -p cmake_build
python3 -m venv cmake_build/_pylibtooling_venv
source cmake_build/_pylibtooling_venv/bin/activate
pip install pybind11

cmake -S ./c_src -B cmake_build  \
-Dpybind11_DIR=`pybind11-config --cmakedir` \
-DCMAKE_BUILD_TYPE=Release \
-DLLVM_SOURCE_DIR=${SCRIPT_DIR}/download_cache/${VERSION} \
-DLLVM_ENABLE_PROJECTS="clang;" \
-DLLVM_ENABLE_RTTI=ON \
-DLLVM_CCACHE_BUILD=ON \
-DLLVM_USE_SPLIT_DWARF=ON \
-DCMAKE_CXX_COMPILER_LAUNCHER=ccache \
-GNinja
cmake --build cmake_build --target dummy

# rengerate bindings
pip install git+https://github.com/edimetia3d/pybind11_weaver.git@main
pybind11-weaver --config c_src/cfg.yaml

# exit
popd