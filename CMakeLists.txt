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

# Install pyf file (needed for f2py)
configure_file(
    "${CMAKE_SOURCE_DIR}/glmnet/_glmnet.pyf"
    "${CMAKE_CURRENT_BINARY_DIR}/_glmnet.pyf"
    COPYONLY
)

# Install Fortran source file
configure_file(
    "${CMAKE_SOURCE_DIR}/glmnet/src/glmnet/glmnet5.f"
    "${CMAKE_CURRENT_BINARY_DIR}/glmnet5.f"
    COPYONLY
)

# Create a custom target for building the extension module with f2py
# We'll use build_ext to handle this outside of CMake
add_custom_target(copy_fortran_files ALL
    DEPENDS 
        "${CMAKE_CURRENT_BINARY_DIR}/_glmnet.pyf"
        "${CMAKE_CURRENT_BINARY_DIR}/glmnet5.f"
    COMMENT "Copied Fortran files for external f2py build"
)

# Create directory structure
if(SKBUILD)
    file(MAKE_DIRECTORY "${CMAKE_CURRENT_BINARY_DIR}/glmnet/src")
else()
    file(MAKE_DIRECTORY "${CMAKE_CURRENT_BINARY_DIR}/glmnet/src")
endif()

# Install all necessary files
if(SKBUILD)
    # Install Python files
    install(FILES
        "${CMAKE_SOURCE_DIR}/glmnet/__init__.py"
        "${CMAKE_SOURCE_DIR}/glmnet/linear.py"
        "${CMAKE_SOURCE_DIR}/glmnet/logistic.py"
        "${CMAKE_SOURCE_DIR}/glmnet/util.py"
        "${CMAKE_SOURCE_DIR}/glmnet/scorer.py"
        "${CMAKE_SOURCE_DIR}/glmnet/errors.py"
        "${CMAKE_SOURCE_DIR}/glmnet/doc.py"
        DESTINATION "${SKBUILD_PLATLIB_DIR}/glmnet"
    )
    
    # Install build module script
    install(FILES
        "${CMAKE_SOURCE_DIR}/glmnet/build_module.py"
        DESTINATION "${SKBUILD_PLATLIB_DIR}/glmnet"
    )
    
    # Install pyf file
    install(FILES
        "${CMAKE_SOURCE_DIR}/glmnet/_glmnet.pyf"
        DESTINATION "${SKBUILD_PLATLIB_DIR}/glmnet"
    )
    
    # Install Fortran source file
    install(FILES
        "${CMAKE_SOURCE_DIR}/glmnet/src/glmnet/glmnet5.f"
        DESTINATION "${SKBUILD_PLATLIB_DIR}/glmnet/src"
    )
    
    # Create an empty src directory
    install(DIRECTORY
        DESTINATION "${SKBUILD_PLATLIB_DIR}/glmnet/src"
    )
else()
    # Install Python files
    install(FILES
        "${CMAKE_SOURCE_DIR}/glmnet/__init__.py"
        "${CMAKE_SOURCE_DIR}/glmnet/linear.py"
        "${CMAKE_SOURCE_DIR}/glmnet/logistic.py"
        "${CMAKE_SOURCE_DIR}/glmnet/util.py"
        "${CMAKE_SOURCE_DIR}/glmnet/scorer.py"
        "${CMAKE_SOURCE_DIR}/glmnet/errors.py"
        "${CMAKE_SOURCE_DIR}/glmnet/doc.py"
        DESTINATION "glmnet"
    )
    
    # Install build module script
    install(FILES
        "${CMAKE_SOURCE_DIR}/glmnet/build_module.py"
        DESTINATION "glmnet"
    )
    
    # Install pyf file
    install(FILES
        "${CMAKE_SOURCE_DIR}/glmnet/_glmnet.pyf"
        DESTINATION "glmnet"
    )
    
    # Install Fortran source file
    install(FILES
        "${CMAKE_SOURCE_DIR}/glmnet/src/glmnet/glmnet5.f"
        DESTINATION "glmnet/src"
    )
    
    # Create an empty src directory
    install(DIRECTORY
        DESTINATION "glmnet/src"
    )
endif()

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
        
        message(STATUS "gfortran library directory: ${GFORTRAN_LIB_DIR}")
        message(STATUS "quadmath library directory: ${QUADMATH_LIB_DIR}")
    endif()
endif()