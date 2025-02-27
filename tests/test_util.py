import numpy as np
import pytest

from glmnet.util import _interpolate_model


@pytest.fixture
def lambda_path():
    return np.array((0.99,))


@pytest.fixture
def coef_path(rng):
    return rng.random(size=(5, 1))


@pytest.fixture
def intercept_path(rng):
    return rng.random(size=(1,))


def test_interpolate_model_intercept_only(lambda_path, coef_path, intercept_path):
    # would be nice to use assertWarnsRegex to check the message, but this
    # fails due to http://bugs.python.org/issue20484
    with pytest.warns(RuntimeWarning, match="lambda_path has a single value.*"):
        _interpolate_model(
            lambda_path,
            coef_path,
            intercept_path,
            0.99,
        )
