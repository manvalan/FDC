# Examples

add_executable(basic_example basic_example.cpp)
target_link_libraries(basic_example PRIVATE fdc_core)

add_executable(network_example network_example.cpp)
target_link_libraries(network_example PRIVATE fdc_core)
