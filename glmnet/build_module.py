#!/usr/bin/env python
"""
Script to build the _glmnet extension module.
"""
import os
import sys
import subprocess
from pathlib import Path


def build_module():
    """Build the _glmnet extension module."""
    # Get the directory where this script is located
    script_dir = Path(__file__).parent.absolute()
    
    # Change to the glmnet directory
    os.chdir(script_dir)
    
    print(f"Building _glmnet extension module in {script_dir}")
    
    # Try to find the source file in several possible locations
    src_file = None
    possible_locations = [
        script_dir / 'src' / 'glmnet5.f',
        script_dir / 'src' / 'glmnet' / 'glmnet5.f',
        Path('/usr/local/lib/python3.11/site-packages/glmnet/src/glmnet5.f'),
        Path('/opt/homebrew/lib/python3.11/site-packages/glmnet/src/glmnet5.f')
    ]
    
    for loc in possible_locations:
        if loc.exists():
            src_file = loc
            break
    
    if src_file is None:
        print("ERROR: Could not find glmnet5.f in any of the expected locations")
        return 1
    
    # Make sure the interface file exists
    pyf_file = script_dir / '_glmnet.pyf'
    if not pyf_file.exists():
        print(f"ERROR: Could not find {pyf_file}")
        return 1
    
    # Call f2py to build the extension module
    cmd = [
        sys.executable, 
        "-m", "numpy.f2py", 
        "-c",
        str(pyf_file),
        str(src_file),
        "-m", "_glmnet",
        "--fcompiler=gnu95",
        "--f77flags=-fdefault-real-8", 
        "--f90flags=-fdefault-real-8"
    ]
    
    try:
        result = subprocess.run(cmd, check=True)
        print("Successfully built _glmnet extension module")
        return 0
    except subprocess.CalledProcessError as e:
        print(f"Failed to build _glmnet extension module: {e}")
        return e.returncode


if __name__ == "__main__":
    sys.exit(build_module())