# Core library source files
set(FDC_CORE_SOURCES
    node.cpp
    edge.cpp
    train.cpp
    # Additional sources will be added here
)

# Create core library
add_library(fdc_core STATIC ${FDC_CORE_SOURCES})

# Link dependencies
target_link_libraries(fdc_core
    PUBLIC
        Boost::graph
        nlohmann_json::nlohmann_json
)

# Include directories
target_include_directories(fdc_core
    PUBLIC
        $<BUILD_INTERFACE:${CMAKE_SOURCE_DIR}/include>
        $<INSTALL_INTERFACE:include>
)

# Compiler warnings
if(MSVC)
    target_compile_options(fdc_core PRIVATE /W4)
else()
    target_compile_options(fdc_core PRIVATE -Wall -Wextra -Wpedantic)
endif()
