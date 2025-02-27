import numpy as np
import pytest


@pytest.fixture
def rng():
    return np.random.default_rng()


@pytest.fixture
def random_int(rng):
    return rng.integers(10000)


@pytest.fixture
def max_features():
    return 5


@pytest.fixture
def min_acceptable_correlation():
    return 0.90


@pytest.fixture
def min_acceptable_accuracy():
    return 0.85


@pytest.fixture
def even_miner_acceptable_accuracy():
    return 0.65


@pytest.fixture(params=[0.0, 0.25, 0.50, 0.75, 1.0])
def alphas(request):
    return request.param


@pytest.fixture(params=[-1, 0, 5])
def n_splits(request):
    return request.param


def record_numpy_version(record_property):
    record_property("numpy_version", np.__version__)