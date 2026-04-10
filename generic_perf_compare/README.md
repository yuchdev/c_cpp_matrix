# C vs C++ Benchmark Comparison

A set of small benchmarks that compare equivalent C and C++ implementations of common programming patterns — sorting, generic transforms, and compile-time lookup tables.

## Benchmark Groups

| Group | C source | C++ source | What it measures |
|-------|----------|-----------|-----------------|
| **a** | `a_qsort_c.c` | `a_std_sort_cpp.cpp` | `qsort` with a comparator function vs `std::sort` with a lambda |
| **b** | `b_callback_c.c` | `b_template_cpp.cpp` | Function-pointer callbacks vs template / lambda `apply_transform` |
| **e** | `e_runtime_table_c.c` | `e_constexpr_table_cpp.cpp` | Runtime initialisation of a 256-entry lookup table vs `constexpr` compile-time table |

## Requirements

### Common (all platforms)

| Tool | Minimum version | Notes |
|------|----------------|-------|
| CMake | 3.10 | Build system generator |
| C compiler | C11 support | gcc 5 / clang 3.6 / MSVC 2019 |
| C++ compiler | C++17 support | gcc 7 / clang 5 / MSVC 2017 15.3 |

---

### Windows

1. **Visual Studio 2019 or later** with the *Desktop development with C++* workload  
   — includes MSVC, CMake, and the Windows SDK.  
   Download: <https://visualstudio.microsoft.com/downloads/>

   **Or**, if you prefer the command line only:  
   *Build Tools for Visual Studio 2019/2022* (free):  
   <https://aka.ms/vs/17/release/vs_BuildTools.exe>

2. **CMake 3.10+** — bundled with Visual Studio, or install separately from <https://cmake.org/download/>.

3. *(Optional)* **Ninja** build tool for faster incremental builds:  
   `winget install Ninja-build.Ninja`

---

### macOS

1. **Xcode Command Line Tools** (Clang ≥ 10, C++17 support included):

   ```bash
   xcode-select --install
   ```

2. **CMake 3.10+**:

   ```bash
   # Homebrew
   brew install cmake

   # Or download the .dmg from https://cmake.org/download/
   ```

---

### Linux

1. **GCC 7+ or Clang 5+** (C11 + C++17):

   ```bash
   # Debian / Ubuntu
   sudo apt update && sudo apt install build-essential cmake

   # Fedora / RHEL / CentOS
   sudo dnf install gcc gcc-c++ cmake make

   # Arch Linux
   sudo pacman -S base-devel cmake
   ```

2. **CMake 3.10+** is included in the commands above. Verify with `cmake --version`.

---

## Building

### Linux / macOS

```bash
# Clone (if you haven't already)
git clone https://github.com/yuchdev/c_cpp.git
cd c_cpp

# Configure and build
cmake -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build
```

### Windows — Visual Studio IDE

1. Open Visual Studio and choose **File → Open → Folder…**, then select the repository root.  
   Visual Studio detects `CMakeLists.txt` automatically.
2. Select a build configuration (e.g. *x64-Release*) from the toolbar.
3. **Build → Build All** (or press **Ctrl+Shift+B**).

### Windows — Command Line (Developer PowerShell / cmd)

```powershell
# Configure (Visual Studio generator, 64-bit)
cmake -B cmake-build -G "Visual Studio 17 2022" -A x64

# Build Release configuration
cmake --build cmake-build --config Release
```

---

## Running the Benchmarks

After a successful build the executables are placed under `build/` (Linux/macOS) or `build\Release\` (Windows MSVC).

### Linux / macOS

```bash
# Sorting
./build/a_qsort_c
./build/a_std_sort_cpp

# Generic transform (callbacks vs templates)
./build/b_callback_c
./build/b_template_cpp

# Lookup table (runtime init vs constexpr)
./build/e_runtime_table_c
./build/e_constexpr_table_cpp
```

### Windows

```powershell
# Sorting
.\build\Release\a_qsort_c.exe
.\build\Release\a_std_sort_cpp.exe

# Generic transform
.\build\Release\b_callback_c.exe
.\build\Release\b_template_cpp.exe

# Lookup table
.\build\Release\e_runtime_table_c.exe
.\build\Release\e_constexpr_table_cpp.exe
```

> **Tip:** Build with optimizations enabled (`-DCMAKE_BUILD_TYPE=Release` / `--config Release`) when comparing C and C++ performance to get representative results.

## License

See [LICENSE](LICENSE) for details.