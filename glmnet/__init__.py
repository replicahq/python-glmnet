import importlib.util
import warnings
from importlib.metadata import version, PackageNotFoundError
from pathlib import Path

# Try to import _glmnet, and build it if it's not found
try:
    from . import _glmnet
except ImportError:
    # Try to build the module if it's not found
    try:
        current_dir = Path(__file__).parent
        build_module_path = current_dir / "build_module.py"
        
        if build_module_path.exists():
            # Load and run the build_module.py
            spec = importlib.util.spec_from_file_location("build_module", build_module_path)
            build_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(build_module)
            
            # Call the build_module function
            result = build_module.build_module()
            
            if result == 0:
                # Try to import again
                try:
                    from . import _glmnet
                except ImportError:
                    warnings.warn("Failed to import _glmnet even after building. Some functionality may be limited.")
            else:
                warnings.warn("Failed to build _glmnet. Some functionality may be limited.")
        else:
            warnings.warn("Could not find build_module.py. Some functionality may be limited.")
    except Exception as e:
        warnings.warn(f"Error trying to build _glmnet: {str(e)}. Some functionality may be limited.")

from .logistic import LogitNet
from .linear import ElasticNet

__all__ = ['LogitNet', 'ElasticNet']

try:
    __version__ = version("glmnet")
except PackageNotFoundError:
    # package is not installed
    __version__ = "unknown"
