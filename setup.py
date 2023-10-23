import os
import shutil
import sys

import pybind11
import setuptools

from pybind11.setup_helpers import build_ext as _build_ext

__FETCH_LLVM_VERSION__ = "17.0.2"


class build_ext(_build_ext):

    def build_extension(self, ext):
        if isinstance(ext, AnyFile):
            dir = os.path.abspath(os.path.dirname(self.get_ext_fullpath(ext.name)))
            os.makedirs(dir, exist_ok=True)
            ext.build(self.get_ext_fullpath(ext.name))
        else:
            return super().build_extension(ext)

    def get_ext_filename(self, ext_name):
        ret = super().get_ext_filename(ext_name)
        base_name = None
        for ext in self.extensions:
            # note: this reverse search is not safe, when two extensions have the same ends, a conflict will occur.
            # e.g `a.b.c` and `a.e.b.c` will cause a conflict.
            # Since the ext name of AnyFile extension is not important, you should name the AnyFile extension
            # in a way that it will not conflict with other extensions.
            if isinstance(ext, AnyFile) and ext.name.endswith(ext_name):
                assert base_name is None, "Duplicate base name found, please rename the AnyFile extension."
                base_name = ext.output_file_name
        if base_name:
            return os.path.join(os.path.dirname(ret), base_name)
        else:
            return ret


class AnyFile(setuptools.Extension):
    """Package any **single** file into the package.

    Mainly used for packing extra library files that reside outside the python source tree.
    """

    def __init__(self, ext_name, src_file_path, output_so_name, *args, **kwargs):
        super().__init__(ext_name, [], *args, **kwargs)
        self.src_path = src_file_path
        self.output_file_name = output_so_name

    def build(self, write_to: str):
        shutil.copy(self.src_path, write_to)


class CMakePylibtooling(AnyFile):

    def __init__(self):
        super().__init__("pylibtooling._C", None, None)

    def get_llvm_src_dir(self):
        # use home cache by default
        llvm_src_dir = os.path.join(os.path.expanduser("~"), ".cache", "pylibtooling", "llvm_src_dir",
                                    f"{__FETCH_LLVM_VERSION__}")
        if "PYLIBTOOLING_LLVM_LLVM_SRC_DIR" in os.environ:
            llvm_src_dir = os.environ.get("PYLIBTOOLING_LLVM_LLVM_SRC_DIR")

        file_name = f"llvm-project-{__FETCH_LLVM_VERSION__}.src.tar.xz"
        url_link = f"https://github.com/llvm/llvm-project/releases/download/llvmorg-{__FETCH_LLVM_VERSION__}/{file_name}"
        os.makedirs(llvm_src_dir, exist_ok=True)
        # if empty dir, download llvm
        if len(os.listdir(llvm_src_dir)) == 0:
            print(f"Downloading llvm source code from {url_link}")
            if os.system(f"wget {url_link} -O {llvm_src_dir}/{file_name}") != 0:
                os.remove(f"{llvm_src_dir}/{file_name}")
                raise RuntimeError(f"Download llvm source code failed, please check your network connection.")
            if os.system(f"tar -xf {llvm_src_dir}/{file_name} -C {llvm_src_dir} --strip-components=1") != 0:
                raise RuntimeError(f"Extract llvm source code failed, please check your tar command.")
        return llvm_src_dir

    def build(self, write: str):
        # use home cache by default
        python_version = f"{sys.version_info.major}.{sys.version_info.minor}"
        build_dir = os.path.join(os.path.expanduser("~"), ".cache", "pylibtooling", "build_dir",
                                 f"{__FETCH_LLVM_VERSION__}", python_version)
        if "PYLIBTOOLING_LLVM_BUILD_DIR" in os.environ:
            build_dir = os.environ.get("PYLIBTOOLING_LLVM_BUILD_DIR")

        output_so_dir = os.path.join(build_dir, "pylibtooling_lib_out")
        llvm_src_dir = self.get_llvm_src_dir()
        cmake_defs = {
            "pybind11_DIR": pybind11.get_cmake_dir(),
            "CMAKE_BUILD_TYPE": "Release",
            "LLVM_SOURCE_DIR": llvm_src_dir,
            "LLVM_ENABLE_PROJECTS": '"clang;"',
            "LLVM_ENABLE_RTTI": "ON",
            "LLVM_CCACHE_BUILD": "ON",
            "LLVM_USE_SPLIT_DWARF": "ON",
            "EXTENSION_OUTPUT_DIR": output_so_dir,
            "CMAKE_CXX_COMPILER_LAUNCHER": "ccache",
        }
        def_args = [f"-D{k}={v}" for k, v in cmake_defs.items()]
        configure_args = ["-GNinja", "-S", "c_src", "-B", build_dir, "--fresh"] + def_args
        build_args = ["--build", build_dir, "--target", "_C"]
        os.makedirs(build_dir, exist_ok=True)
        if os.system(f"cmake {' '.join(configure_args)}") != 0:
            raise RuntimeError(f"cmake configure failed, please check your cmake command.")
        if os.system(f"cmake {' '.join(build_args)}") != 0:
            raise RuntimeError(f"cmake build failed, please check your cmake command.")
        # find so file under output_so_dir
        found = False
        for f in os.listdir(output_so_dir):
            if f.endswith(".so"):
                src_path = os.path.join(output_so_dir, f)
                shutil.copy(src_path, write)
                found = True
        if not found:
            raise RuntimeError("Cannot find build output")


ext_modules = [
    CMakePylibtooling()
]

setuptools.setup(
    ext_modules=ext_modules,
    cmdclass={"build_ext": build_ext},
)
