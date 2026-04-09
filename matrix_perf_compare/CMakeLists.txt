cmake_minimum_required(VERSION 3.16)
project(matrix_perf_compare C CXX)

set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED ON)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Default to Release
if(NOT CMAKE_BUILD_TYPE)
  set(CMAKE_BUILD_TYPE Release CACHE STRING "Build type" FORCE)
endif()

# Common compile flags
if(CMAKE_C_COMPILER_ID MATCHES "GNU|Clang")
  add_compile_options(-O2 -Wall -Wextra)
endif()

# ---- Eigen: prefer system install, fall back to FetchContent ----
find_package(Eigen3 3.3 QUIET NO_MODULE)
if(NOT Eigen3_FOUND)
  include(FetchContent)
  FetchContent_Declare(
    eigen
    GIT_REPOSITORY https://gitlab.com/libeigen/eigen.git
    GIT_TAG        3.4.0
    GIT_SHALLOW    TRUE
  )
  set(EIGEN_BUILD_DOC OFF CACHE BOOL "" FORCE)
  set(EIGEN_BUILD_TESTING OFF CACHE BOOL "" FORCE)
  set(EIGEN_BUILD_PKGCONFIG OFF CACHE BOOL "" FORCE)
  FetchContent_MakeAvailable(eigen)
endif()

# ---- Include directories ----
set(INCLUDE_DIR ${CMAKE_CURRENT_SOURCE_DIR}/include)

# ---- C static library ----
add_library(c_matrix STATIC
  src/c/matrix.c
  src/c/ops.c
)
target_include_directories(c_matrix PUBLIC ${INCLUDE_DIR})

# ---- C benchmark executable ----
add_executable(c_matrix_bench src/c/benchmarks_c.c)
target_link_libraries(c_matrix_bench PRIVATE c_matrix m)
target_include_directories(c_matrix_bench PRIVATE ${INCLUDE_DIR})

# ---- C++ benchmark executable ----
add_executable(cpp_matrix_bench src/cpp/benchmarks_cpp.cpp)
target_link_libraries(cpp_matrix_bench PRIVATE Eigen3::Eigen c_matrix)
target_include_directories(cpp_matrix_bench PRIVATE ${INCLUDE_DIR})

# ---- C tests ----
add_executable(c_matrix_tests tests/c/test_matrix.c)
target_link_libraries(c_matrix_tests PRIVATE c_matrix m)
target_include_directories(c_matrix_tests PRIVATE ${INCLUDE_DIR})

# ---- C++ tests ----
add_executable(cpp_matrix_tests tests/cpp/test_eigen_ops.cpp)
target_link_libraries(cpp_matrix_tests PRIVATE Eigen3::Eigen c_matrix m)
target_include_directories(cpp_matrix_tests PRIVATE ${INCLUDE_DIR})

# ---- CTest integration ----
enable_testing()
add_test(NAME c_tests   COMMAND c_matrix_tests)
add_test(NAME cpp_tests COMMAND cpp_matrix_tests)

# ---- Optional run_benchmarks target ----
add_custom_target(run_benchmarks
  COMMAND c_matrix_bench
  COMMAND cpp_matrix_bench
  DEPENDS c_matrix_bench cpp_matrix_bench
  WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
  COMMENT "Running all benchmarks"
)
