cmake_minimum_required(VERSION 3.10)
project(c_cpp_comparison)

set(CMAKE_C_STANDARD 11)
set(CMAKE_CXX_STANDARD 17)

add_executable(a_qsort_c a_qsort_c.c)
add_executable(a_std_sort_cpp a_std_sort_cpp.cpp)
add_executable(b_callback_c b_callback_c.c)
add_executable(b_template_cpp b_template_cpp.cpp)
add_executable(e_runtime_table_c e_runtime_table_c.c)
add_executable(e_constexpr_table_cpp e_constexpr_table_cpp.cpp)
