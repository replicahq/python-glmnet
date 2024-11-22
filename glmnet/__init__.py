from importlib.metadata import version, PackageNotFoundError

from .logistic import LogitNet
from .linear import ElasticNet

__all__ = ['LogitNet', 'ElasticNet']

try:
    __version__ = version("glmnet")
except PackageNotFoundError:
    # package is not installed
    __version__ = "unknown"
