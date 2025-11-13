# Qt GUI Application
cmake_minimum_required(VERSION 3.15)

# Enable Qt MOC, UIC, RCC
set(CMAKE_AUTOMOC ON)
set(CMAKE_AUTOUIC ON)
set(CMAKE_AUTORCC ON)

# Find Qt packages
if(Qt6_FOUND)
    find_package(Qt6 REQUIRED COMPONENTS Core Widgets)
    set(QT_VERSION_MAJOR 6)
else()
    find_package(Qt5 5.15 REQUIRED COMPONENTS Core Widgets)
    set(QT_VERSION_MAJOR 5)
endif()

# GUI source files
set(GUI_SOURCES
    main.cpp
    main_window.cpp
    main_window.hpp
)

# Create executable
add_executable(fdc_gui ${GUI_SOURCES})

# Set macOS bundle properties
set_target_properties(fdc_gui PROPERTIES
    MACOSX_BUNDLE TRUE
    MACOSX_BUNDLE_GUI_IDENTIFIER org.fdc-railway.manager
    MACOSX_BUNDLE_BUNDLE_NAME "FDC Railway Manager"
    MACOSX_BUNDLE_BUNDLE_VERSION ${PROJECT_VERSION}
    MACOSX_BUNDLE_SHORT_VERSION_STRING ${PROJECT_VERSION}
    OUTPUT_NAME "FDC Railway Manager"
)

# Link libraries
target_link_libraries(fdc_gui PRIVATE
    fdc_core
    Boost::graph
    nlohmann_json::nlohmann_json
)

# Link Qt libraries
if(Qt6_FOUND)
    target_link_libraries(fdc_gui PRIVATE Qt6::Core Qt6::Widgets)
else()
    target_link_libraries(fdc_gui PRIVATE Qt5::Core Qt5::Widgets)
endif()

# macOS deployment - copy Qt frameworks into bundle
if(APPLE)
    # Find macdeployqt
    if(Qt6_FOUND)
        get_target_property(QT_QMAKE_EXECUTABLE Qt6::qmake IMPORTED_LOCATION)
    else()
        get_target_property(QT_QMAKE_EXECUTABLE Qt5::qmake IMPORTED_LOCATION)
    endif()
    
    get_filename_component(QT_BIN_DIR "${QT_QMAKE_EXECUTABLE}" DIRECTORY)
    find_program(MACDEPLOYQT_EXECUTABLE macdeployqt HINTS "${QT_BIN_DIR}")
    
    if(MACDEPLOYQT_EXECUTABLE)
        # Deploy Qt frameworks
        add_custom_command(TARGET fdc_gui POST_BUILD
            COMMAND "${MACDEPLOYQT_EXECUTABLE}" 
                "$<TARGET_BUNDLE_DIR:fdc_gui>"
                -always-overwrite
            COMMENT "Running macdeployqt to bundle Qt frameworks..."
        )
        
        # Code sign the bundle (ad-hoc signature for development)
        add_custom_command(TARGET fdc_gui POST_BUILD
            COMMAND codesign --force --deep --sign - "$<TARGET_BUNDLE_DIR:fdc_gui>"
            COMMENT "Signing application bundle..."
        )
    else()
        message(WARNING "macdeployqt not found - Qt frameworks will not be bundled")
    endif()
endif()

# Install target
install(TARGETS fdc_gui
    BUNDLE DESTINATION .
    RUNTIME DESTINATION bin
)
