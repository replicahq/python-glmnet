from copy import deepcopy

import numpy as np
import numpy.testing as nptst
import pytest
from pytest_lazy_fixtures import lf
from scipy.sparse import csr_matrix
from sklearn.datasets import make_regression
from sklearn.metrics import r2_score

# from sklearn.utils.estimator_checks import parametrize_with_checks
from glmnet import ElasticNet
from tests.util import sanity_check_regression


@pytest.fixture
def x_y():
    np.random.seed(488881)
    return make_regression(n_samples=1000, random_state=561)


@pytest.fixture
def x(x_y):
    return x_y[0]


@pytest.fixture
def y(x_y):
    return x_y[1]


@pytest.fixture
def x_sparse(x_y):
    return csr_matrix(x_y[0])


@pytest.fixture
def x_y_wide():
    return make_regression(n_samples=100, n_features=150, random_state=1105)


@pytest.fixture
def x_wide(x_y_wide):
    return x_y_wide[0]


@pytest.fixture
def y_wide(x_y_wide):
    return x_y_wide[1]


@pytest.fixture
def x_wide_sparse(x_wide):
    return csr_matrix(x_wide)


@pytest.fixture(
    params=[
        (lf("x"), lf("y")),
        (lf("x_sparse"), lf("y")),
        (lf("x_wide"), lf("y_wide")),
        (lf("x_wide_sparse"), lf("y_wide")),
    ]
)
def x_y_inputs(request):
    return request.param


@pytest.fixture(
    params=[
        (lf("x"), lf("y")),
        (lf("x_sparse"), lf("y")),
    ]
)
def x_y_tall_inputs(request):
    return request.param


@pytest.fixture(
    params=[
        (lf("x_wide"), lf("y_wide")),
        (lf("x_wide_sparse"), lf("y_wide")),
    ]
)
def x_y_wide_inputs(request):
    return request.param


# NOT creating a lot of models with specific seeds
# if it is important, we can try changing the seed
# per-func
@pytest.fixture
def m():
    return ElasticNet()


@pytest.fixture
def m_alphas(alphas):
    return ElasticNet(alpha=alphas, random_state=2465)


@pytest.fixture
def m_nsplits(n_splits):
    return ElasticNet(n_splits=n_splits, random_state=6601)


@pytest.fixture(
    params=[
        "r2",
        "mean_squared_error",
        "mean_absolute_error",
        "median_absolute_error",
    ]
)
def scoring(request):
    return request.param


@pytest.fixture
def m_scoring(scoring):
    return ElasticNet(scoring=scoring)


# I don't think I understand what this test
# does enough to fix this right now?
# @pytest.mark.filterwarnings
# @parametrize_with_checks([ElasticNet()])
# def test_sklearn_compatible_estimator(estimator, check):
#     check(estimator)


@pytest.mark.parametrize("inputs", [(lf("x_y_inputs"))])
def test_with_defaults(m, inputs):
    # print(f"{meta_inputs=}")
    x, y = inputs
    m = m.fit(x, y)
    sanity_check_regression(m, x)

    # check selection of lambda_best
    assert m.lambda_best_inx_ <= m.lambda_max_inx_

    # check full path predict
    p = m.predict(x, lamb=m.lambda_path_)
    assert p.shape[-1] == m.lambda_path_.size


@pytest.mark.parametrize("inputs", [(lf("x_y_inputs"))])
def test_one_row_predict(m, inputs):
    # Verify that predicting on one row gives only one row of output
    X, y = inputs
    m.fit(X, y)
    p = m.predict(X[0].reshape((1, -1)))
    assert p.shape == (1,)


@pytest.mark.parametrize("inputs", [(lf("x_y_inputs"))])
def test_one_row_predict_with_lambda(m, inputs):
    # One row to predict along with lambdas should give 2D output
    X, y = inputs
    m.fit(X, y)
    p = m.predict(X[0].reshape((1, -1)), lamb=[20, 10])
    assert p.shape == (1, 2)


def test_with_single_var(m, min_acceptable_correlation):
    x = np.random.rand(500, 1)
    y = (1.3 * x).ravel()

    m = m.fit(x, y)
    score = r2_score(y, m.predict(x))
    assert score >= min_acceptable_correlation


def test_with_no_predictor_variance(m):
    x = np.ones((500, 1))
    y = np.random.rand(500)

    with pytest.raises(ValueError, match=r".*7777.*"):
        m.fit(x, y)


@pytest.mark.parametrize("inputs", [(lf("x_y_inputs"))])
def test_relative_penalties(m, inputs):
    x, y = inputs
    m1 = m
    m2 = deepcopy(m1)
    p = x.shape[1]

    # m1 no relative penalties applied
    m1.fit(x, y)

    # find the nonzero indices from LASSO
    nonzero = np.nonzero(m1.coef_)

    # unpenalize those nonzero coefs
    penalty = np.repeat(1, p)
    penalty[nonzero] = 0

    # refit the model with the unpenalized coefs
    m2.fit(x, y, relative_penalties=penalty)

    # verify that the unpenalized coef ests exceed the penalized ones
    # in absolute value
    assert np.all(np.abs(m1.coef_) <= np.abs(m2.coef_))


@pytest.mark.parametrize("m_alpha", [(lf("m_alphas"))])
def test_alphas(x, y, m_alpha, min_acceptable_correlation):
    m_alpha = m_alpha.fit(x, y)
    score = r2_score(y, m_alpha.predict(x))
    assert score >= min_acceptable_correlation


@pytest.fixture
def m_with_limits(x):
    return ElasticNet(lower_limits=np.repeat(-1, x.shape[1]), upper_limits=0, alpha=0)


# TODO I think it should be possible to merge the tall and wide
# tests here, I just haven't figured exactly how yet
def test_coef_limits(m_with_limits, x, y):
    m_with_limits = m_with_limits.fit(x, y)
    assert np.all(m_with_limits.coef_ >= -1)
    assert np.all(m_with_limits.coef_ <= 0)


@pytest.mark.parametrize("inputs,m_score", [(lf("x_y_inputs"), lf("m_scoring"))])
def test_cv_scoring(inputs, m_score, min_acceptable_correlation):
    x, y = inputs
    m_score = m_score.fit(x, y)
    score = r2_score(y, m_score.predict(x))
    assert score >= min_acceptable_correlation


@pytest.fixture
def m_nosplits():
    return ElasticNet(n_splits=0)


# @pytest.mark.parametrize("inputs", [(lf("x_y_inputs"))])
def test_predict_without_cv(x_y, m_nosplits):
    x, y = x_y
    m_nosplits = m_nosplits.fit(x, y)

    # should not make prediction unless value is passed for lambda
    with pytest.raises(ValueError):
        m_nosplits.predict(x)


@pytest.mark.xfail
def test_coef_interpolation(x_y, m_nosplits):
    x, y = x_y
    m_nosplits = m_nosplits.fit(x, y)

    # predict for a value of lambda between two values on the computed path
    lamb_lo = m_nosplits.lambda_path_[1]
    lamb_hi = m_nosplits.lambda_path_[2]

    # a value not equal to one on the computed path
    lamb_mid = (lamb_lo + lamb_hi) / 2.0

    pred_lo = m_nosplits.predict(x, lamb=lamb_lo)
    pred_hi = m_nosplits.predict(x, lamb=lamb_hi)
    pred_mid = m_nosplits.predict(x, lamb=lamb_mid)

    nptst.assert_allclose(pred_lo, pred_mid)
    nptst.assert_allclose(pred_hi, pred_mid)


def test_lambda_clip_warning(x_y, m_nosplits):
    x, y = x_y
    m_nosplits = m_nosplits.fit(x, y)

    # we should get a warning when we ask for predictions at values of
    # lambda outside the range of lambda_path_
    with pytest.warns(RuntimeWarning):
        # note, lambda_path_ is in decreasing order
        m_nosplits.predict(x, lamb=m_nosplits.lambda_path_[0] + 1)

    with pytest.warns(RuntimeWarning):
        m_nosplits.predict(x, lamb=m_nosplits.lambda_path_[-1] - 1)


@pytest.fixture
def m_random(random_int):
    return ElasticNet(random_state=random_int)


def test_random_state_cv(m_random, random_int, x_y):
    x, y = x_y
    m_random.fit(x, y)
    # print(dir(m_random._cv))
    assert m_random._cv.random_state == random_int


@pytest.fixture
def m_3_splits(max_features):
    return ElasticNet(n_splits=3, random_state=42, max_features=max_features)


@pytest.mark.parametrize("inputs", [(lf("x_y_wide_inputs"))])
def test_max_features(inputs, m_3_splits, max_features):
    x, y = inputs
    m_3_splits = m_3_splits.fit(x, y)
    num_features = np.count_nonzero(m_3_splits.coef_)
    assert num_features <= max_features
