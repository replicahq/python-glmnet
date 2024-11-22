cmake_minimum_required(VERSION 3.15)
project(glmnet LANGUAGES Fortran)

# Detect if we're building inside scikit-build-core
if(DEFINED SKBUILD)
    message(STATUS "Building with scikit-build-core version: ${SKBUILD_CORE_VERSION}")
else()
    message(STATUS "Building outside of scikit-build-core.")
endif()

# Set Fortran flags for fixed-form
set(CMAKE_Fortran_FLAGS "${CMAKE_Fortran_FLAGS} -ffixed-form")

# Find Python components
find_package(Python COMPONENTS Interpreter Development.Module REQUIRED)

# Debug messages to check variables
message(STATUS "Python_EXECUTABLE: ${Python_EXECUTABLE}")
message(STATUS "Python_SOABI: ${Python_SOABI}")

# Retrieve the Python extension module suffix
if(SKBUILD)
    # Use SKBUILD_SOABI provided by scikit-build-core
    set(Python_EXTENSION_SUFFIX ".${SKBUILD_SOABI}${CMAKE_SHARED_MODULE_SUFFIX}")
else()
    # Fallback if not using scikit-build-core
    execute_process(
        COMMAND "${Python_EXECUTABLE}" -c "import sysconfig; print(sysconfig.get_config_var('EXT_SUFFIX'))"
        OUTPUT_VARIABLE Python_EXTENSION_SUFFIX
        OUTPUT_STRIP_TRAILING_WHITESPACE
    )
endif()

message(STATUS "Python extension module suffix: ${Python_EXTENSION_SUFFIX}")

# Then find NumPy
execute_process(
    COMMAND "${Python_EXECUTABLE}" -c "import numpy; print(numpy.get_include())"
    OUTPUT_VARIABLE NUMPY_INCLUDE_DIR
    OUTPUT_STRIP_TRAILING_WHITESPACE
    RESULT_VARIABLE NUMPY_FOUND
)

if(NOT NUMPY_FOUND EQUAL 0 OR NOT NUMPY_INCLUDE_DIR)
    message(FATAL_ERROR "NumPy is required to build this project")
endif()

# Enable Fortran 90 support
enable_language(Fortran)
set(CMAKE_Fortran_SOURCE_FILE_EXTENSIONS f90)

# Add Fortran library
add_library(_glmnet MODULE
    glmnet/src/glmnet/glmnet5.f
    glmnet/_glmnet.pyf
)

# Set the output directory for Fortran modules
set_target_properties(_glmnet PROPERTIES
    Fortran_MODULE_DIRECTORY "${CMAKE_CURRENT_BINARY_DIR}/modules"
)

# Set the SUFFIX property using the retrieved extension
set_target_properties(_glmnet PROPERTIES
    PREFIX ""
    SUFFIX "${Python_EXTENSION_SUFFIX}"
)

# Ensure the module is output to the appropriate directory
if(SKBUILD)
    set(LIBRARY_OUTPUT_DIR "${SKBUILD_PLATLIB_DIR}")
else()
    set(LIBRARY_OUTPUT_DIR "${CMAKE_CURRENT_BINARY_DIR}")
endif()

set_target_properties(_glmnet PROPERTIES
    LIBRARY_OUTPUT_DIRECTORY "${LIBRARY_OUTPUT_DIR}"
)

# Include directories
target_include_directories(_glmnet PRIVATE
    ${NUMPY_INCLUDE_DIR}
)

# Handle macOS-specific settings
if(CMAKE_Fortran_COMPILER_ID MATCHES "GNU")
    if(APPLE)
        # Handle macOS specific linking
        execute_process(
            COMMAND ${CMAKE_Fortran_COMPILER} -print-file-name=libgfortran.dylib
            OUTPUT_VARIABLE GFORTRAN_LIB
            OUTPUT_STRIP_TRAILING_WHITESPACE
        )
        get_filename_component(GFORTRAN_LIB_DIR "${GFORTRAN_LIB}" DIRECTORY)

        target_link_directories(_glmnet PRIVATE
            "${GFORTRAN_LIB_DIR}"
        )

        # Set the RPATH to include the directories
        set_target_properties(_glmnet PROPERTIES
            INSTALL_RPATH "@loader_path"
        )
    endif()
endif()

# Install the module to the appropriate directory
if(SKBUILD)
    install(TARGETS _glmnet
        LIBRARY DESTINATION "${SKBUILD_PLATLIB_DIR}"
    )
else()
    install(TARGETS _glmnet DESTINATION ".")
endif()
