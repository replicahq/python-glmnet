cmake_minimum_required(VERSION 3.15)
project(glmnet LANGUAGES Fortran)

# Detect if we're building inside scikit-build-core
if(DEFINED SKBUILD)
    message(STATUS "Building with scikit-build-core version: ${SKBUILD_CORE_VERSION}")
else()
    message(STATUS "Building outside of scikit-build-core.")
endif()

# Reset Fortran flags to prevent unwanted flags
set(CMAKE_Fortran_FLAGS "")

# Set Fortran flags for default real kind
set(CMAKE_Fortran_FLAGS "${CMAKE_Fortran_FLAGS} -fdefault-real-8")

# Print the Fortran compiler flags
message(STATUS "CMAKE_Fortran_FLAGS: ${CMAKE_Fortran_FLAGS}")

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

# Generate wrapper code using f2py
execute_process(
    COMMAND "${Python_EXECUTABLE}" -m numpy.f2py
            "${CMAKE_SOURCE_DIR}/glmnet/_glmnet.pyf"
            -m _glmnet
            -h "${CMAKE_CURRENT_BINARY_DIR}/_glmnet_f2pywrappers.f90"
    WORKING_DIRECTORY "${CMAKE_CURRENT_BINARY_DIR}"
)

# Add Fortran library with wrapper code
add_library(_glmnet MODULE
    "${CMAKE_CURRENT_BINARY_DIR}/_glmnet_f2pywrappers.f90"
    glmnet/src/glmnet/glmnet5.f
)

# Set per-source file compilation flags
set_source_files_properties(
    "${CMAKE_CURRENT_BINARY_DIR}/_glmnet_f2pywrappers.f90"
    PROPERTIES COMPILE_FLAGS "-ffree-form"
)

set_source_files_properties(
    glmnet/src/glmnet/glmnet5.f
    PROPERTIES COMPILE_FLAGS "-ffixed-form"
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
    ${Python_INCLUDE_DIRS}
)

# Link against Python libraries if necessary
target_link_libraries(_glmnet PRIVATE ${Python_LIBRARIES})

# Handle macOS-specific settings
if(CMAKE_Fortran_COMPILER_ID MATCHES "GNU")
    if(APPLE)
        # Handle macOS specific linking
        execute_process(
            COMMAND ${CMAKE_Fortran_COMPILER} -print-file-name=libgfortran.dylib
            OUTPUT_VARIABLE GFORTRAN_LIB
            OUTPUT_STRIP_TRAILING_WHITESPACE
        )
        execute_process(
            COMMAND ${CMAKE_Fortran_COMPILER} -print-file-name=libquadmath.dylib
            OUTPUT_VARIABLE QUADMATH_LIB
            OUTPUT_STRIP_TRAILING_WHITESPACE
        )
        get_filename_component(GFORTRAN_LIB_DIR "${GFORTRAN_LIB}" DIRECTORY)
        get_filename_component(QUADMATH_LIB_DIR "${QUADMATH_LIB}" DIRECTORY)

        target_link_directories(_glmnet PRIVATE
            "${GFORTRAN_LIB_DIR}"
            "${QUADMATH_LIB_DIR}"
        )

        # Set the RPATH to include the directories
        set_target_properties(_glmnet PROPERTIES
            INSTALL_RPATH "${GFORTRAN_LIB_DIR};${QUADMATH_LIB_DIR}"
        )

        # Add linker flags
        target_link_libraries(_glmnet PRIVATE
            "-Wl,-rpath,${GFORTRAN_LIB_DIR}:${QUADMATH_LIB_DIR}"
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
