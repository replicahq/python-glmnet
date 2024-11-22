cmake_minimum_required(VERSION 3.15)
project(glmnet LANGUAGES Fortran)

# Set Fortran flags for fixed-form
set(CMAKE_Fortran_FLAGS "${CMAKE_Fortran_FLAGS} -ffixed-form")

# Set policy for new behavior regarding find_package(Python3)
if(POLICY CMP0148)
  cmake_policy(SET CMP0148 NEW)
endif()

# Find Python3 first
find_package(Python3
    REQUIRED
    COMPONENTS
        Interpreter
        Development.Module
)

# Then find NumPy
execute_process(
    COMMAND "${Python3_EXECUTABLE}" -c "import numpy; print(numpy.get_include())"
    RESULT_VARIABLE NUMPY_FOUND
    OUTPUT_VARIABLE NUMPY_INCLUDE_DIR
    OUTPUT_STRIP_TRAILING_WHITESPACE
)

if(NOT NUMPY_FOUND EQUAL 0)
    message(STATUS "NumPy not found. Attempting to install...")
    execute_process(
        COMMAND "${Python3_EXECUTABLE}" -m pip install numpy
        RESULT_VARIABLE NUMPY_INSTALL_RESULT
    )
    if(NOT NUMPY_INSTALL_RESULT EQUAL 0)
        message(FATAL_ERROR "Failed to install NumPy")
    endif()
    execute_process(
        COMMAND "${Python3_EXECUTABLE}" -c "import numpy; print(numpy.get_include())"
        RESULT_VARIABLE NUMPY_FOUND
        OUTPUT_VARIABLE NUMPY_INCLUDE_DIR
        OUTPUT_STRIP_TRAILING_WHITESPACE
    )
endif()

if(NOT NUMPY_FOUND EQUAL 0)
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

# Set Fortran specific properties
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
        set_target_properties(_glmnet PROPERTIES
            LINK_FLAGS "-Wl,-rpath,${GFORTRAN_LIB_DIR}:${QUADMATH_LIB_DIR}"
        )
    endif()
endif()

# Set the output directory for Fortran modules
set_target_properties(_glmnet PROPERTIES
    Fortran_MODULE_DIRECTORY "${CMAKE_CURRENT_BINARY_DIR}/modules"
)

# Retrieve the Python extension module suffix
execute_process(
    COMMAND "${Python3_EXECUTABLE}" -c "import sysconfig; print(sysconfig.get_config_var('EXT_SUFFIX'))"
    OUTPUT_VARIABLE PYTHON_EXT_SUFFIX
    OUTPUT_STRIP_TRAILING_WHITESPACE
)

# Debug message to check the retrieved suffix
message(STATUS "Python extension module suffix: ${PYTHON_EXT_SUFFIX}")

# Use Python3 variables for extension suffix
set_target_properties(_glmnet PROPERTIES
    PREFIX ""
    SUFFIX "${PYTHON_EXT_SUFFIX}"
)

# Ensure the module is output to the current directory
set_target_properties(_glmnet PROPERTIES
    LIBRARY_OUTPUT_DIRECTORY "${CMAKE_CURRENT_BINARY_DIR}"
)

# Include directories
target_include_directories(_glmnet PRIVATE
    ${NUMPY_INCLUDE_DIR}
)

install(TARGETS _glmnet DESTINATION .)
