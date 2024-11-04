cmake_minimum_required(VERSION 3.15)
project(glmnet LANGUAGES Fortran)

# Set policy for new behavior regarding find_package(Python)
if(POLICY CMP0148)
  cmake_policy(SET CMP0148 NEW)
endif()

# Find Python
find_package(Python 3.6 
    REQUIRED 
    COMPONENTS 
        Interpreter 
        Development.Module 
    OPTIONAL_COMPONENTS 
        NumPy
)

if(NOT Python_NumPy_FOUND)
    execute_process(
        COMMAND "${Python_EXECUTABLE}" -c "import numpy; print(numpy.get_include())"
        OUTPUT_VARIABLE Python_NumPy_INCLUDE_DIRS
        OUTPUT_STRIP_TRAILING_WHITESPACE
        RESULT_VARIABLE _NUMPY_SEARCH_SUCCESS
    )
    if(_NUMPY_SEARCH_SUCCESS MATCHES 0)
        set(Python_NumPy_FOUND TRUE)
    endif()
endif()

if(NOT Python_NumPy_FOUND)
    message(FATAL_ERROR "NumPy is required to build this project")
endif()

# Enable Fortran 90 support
enable_language(Fortran)
set(CMAKE_Fortran_SOURCE_FILE_EXTENSIONS f90)

# Add Fortran library
add_library(_glmnet MODULE
    glmnet/src/glmnet/glmnet5.f90
    glmnet/_glmnet.pyf
)

target_include_directories(_glmnet PRIVATE 
    ${Python_NumPy_INCLUDE_DIRS}
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

# Set the output directory and naming convention for the extension
set_target_properties(_glmnet PROPERTIES
    PREFIX ""
    OUTPUT_NAME "_glmnet"
    SUFFIX "${Python_EXTENSION_SUFFIX}"
    Fortran_MODULE_DIRECTORY "${CMAKE_CURRENT_BINARY_DIR}/modules"
)
