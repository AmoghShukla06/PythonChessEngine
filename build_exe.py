#!/usr/bin/env python3
"""
Cross-platform build script for the Chess Engine.
Compiles the C++ engine and packages everything into a standalone executable.

Usage:
    python build_exe.py

Requirements (auto-installed if missing):
    pip install pyinstaller pybind11
"""

import os
import platform
import subprocess
import sys
import shutil


def run(cmd, **kwargs):
    """Run a command, print it, and check for errors."""
    print(f"\n>>> {cmd}")
    subprocess.check_call(cmd, shell=True, **kwargs)


def ensure_dependencies():
    """Install build dependencies if missing."""
    for pkg in ["pyinstaller", "pybind11"]:
        try:
            __import__(pkg.replace("-", "_"))
        except ImportError:
            print(f"Installing {pkg}...")
            run(f"{sys.executable} -m pip install {pkg}")


def get_pybind11_includes():
    """Get pybind11 include flags."""
    result = subprocess.check_output(
        [sys.executable, "-m", "pybind11", "--includes"],
        text=True
    ).strip()
    return result


def get_ext_suffix():
    """Get the platform-specific extension suffix for Python C modules."""
    import sysconfig
    return sysconfig.get_config_var("EXT_SUFFIX")


def compile_cpp_engine():
    """Compile the C++ chess engine into a shared library."""
    system = platform.system()
    ext = get_ext_suffix()
    includes = get_pybind11_includes()
    output = f"chess_engine_cpp{ext}"

    print(f"\n=== Compiling C++ engine for {system} ===")
    print(f"Output: {output}")

    if system == "Windows":
        # Windows: Try MSVC (cl.exe) first, fall back to g++ (MinGW)
        python_includes = subprocess.check_output(
            [sys.executable, "-c",
             "import sysconfig; print(sysconfig.get_path('include'))"],
            text=True
        ).strip()
        python_lib_dir = subprocess.check_output(
            [sys.executable, "-c",
             "import sysconfig; print(sysconfig.get_config_var('installed_base'))"],
            text=True
        ).strip()

        # Use .pyd extension on Windows
        output = "chess_engine_cpp.pyd"

        if shutil.which("cl"):
            # MSVC
            run(
                f'cl /O2 /std:c++17 /EHsc /LD {includes} '
                f'/I"{python_includes}" '
                f'bitboard.cpp chess_engine.cpp '
                f'/link /LIBPATH:"{python_lib_dir}\\libs" '
                f'/OUT:{output}'
            )
        elif shutil.which("g++"):
            # MinGW
            python_dll = subprocess.check_output(
                [sys.executable, "-c",
                 "import sysconfig; print(sysconfig.get_config_var('LDLIBRARY') or '')"],
                text=True
            ).strip()
            run(
                f'g++ -O3 -Wall -shared -std=c++17 '
                f'{includes} '
                f'-I"{python_includes}" '
                f'bitboard.cpp chess_engine.cpp '
                f'-L"{python_lib_dir}\\libs" '
                f'-lpython312 '
                f'-o {output}'
            )
        else:
            print("ERROR: No C++ compiler found. Install Visual Studio Build Tools or MinGW.")
            sys.exit(1)

    elif system == "Darwin":
        # macOS: use clang++ (comes with Xcode Command Line Tools)
        compiler = "clang++" if shutil.which("clang++") else "g++"
        run(
            f'{compiler} -O3 -Wall -shared -std=c++17 -fPIC -undefined dynamic_lookup '
            f'{includes} '
            f'bitboard.cpp chess_engine.cpp '
            f'-o {output}'
        )

    else:
        # Linux
        run(
            f'g++ -O3 -Wall -shared -std=c++17 -fPIC '
            f'{includes} '
            f'bitboard.cpp chess_engine.cpp '
            f'-o {output}'
        )

    if not any(os.path.exists(f) for f in [output, "chess_engine_cpp.pyd"]):
        print("ERROR: Compilation failed — output file not found.")
        sys.exit(1)

    print(f"✓ Compiled: {output}")
    return output


def build_executable(so_file):
    """Use PyInstaller to create a standalone executable."""
    system = platform.system()
    print(f"\n=== Building standalone executable with PyInstaller ===")

    # Determine data separator (: on Unix, ; on Windows)
    sep = ";" if system == "Windows" else ":"

    # Build the PyInstaller command
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", "ChessEngine",
        "--onedir",
        "--windowed" if system != "Linux" else "--console",
        # Bundle the compiled C++ engine
        "--add-binary", f"{so_file}{sep}.",
        # Bundle piece images
        "--add-data", f"pieces{sep}pieces",
        # Bundle background
        "--add-data", f"background.gif{sep}.",
        # Hidden imports for the wrapper
        "--hidden-import", "chess_engine_cpp",
        "--hidden-import", "chess_engine_wrapper",
        "--hidden-import", "ui",
        # Don't ask for confirmation
        "--noconfirm",
        # Clean build
        "--clean",
        # Entry point
        "main.py",
    ]

    print(f"\n>>> {' '.join(cmd)}")
    subprocess.check_call(cmd)

    dist_path = os.path.join("dist", "ChessEngine")
    if os.path.exists(dist_path):
        print(f"\n✅ SUCCESS! Executable created at: {dist_path}/")
        print(f"   Run it with: {'dist/ChessEngine/ChessEngine.exe' if system == 'Windows' else 'dist/ChessEngine/ChessEngine'}")
    else:
        print("ERROR: PyInstaller build failed.")
        sys.exit(1)


def main():
    # Ensure we're in the project root
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)

    print("=" * 60)
    print("  Chess Engine — Cross-Platform Build Script")
    print(f"  Platform: {platform.system()} {platform.machine()}")
    print("=" * 60)

    ensure_dependencies()
    so_file = compile_cpp_engine()
    build_executable(so_file)


if __name__ == "__main__":
    main()
