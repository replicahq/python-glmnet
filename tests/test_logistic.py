from copy import deepcopy

import numpy as np
import numpy.testing as nptst
import pytest
from pytest_lazy_fixtures import lf
from scipy.sparse import csr_matrix
from sklearn.datasets import make_classification
from sklearn.metrics import accuracy_score, f1_score
from sklearn.utils import class_weight

# from sklearn.utils.estimator_checks import parametrize_with_checks
from glmnet import LogitNet

# from tests.conftest import min_acceptable_accuracy
from tests.util import sanity_check_logistic


@pytest.fixture
def bn_x_y():
    np.random.seed(488881)
    return make_classification(n_samples=300, random_state=6601)


@pytest.fixture
def bn_x(bn_x_y):
    return bn_x_y[0]


@pytest.fixture
def bn_y(bn_x_y):
    return bn_x_y[1]


@pytest.fixture
def bn_x_sparse(bn_x_y):
    return csr_matrix(bn_x_y[0])


@pytest.fixture
def bn_x_y_wide():
    return make_classification(n_samples=100, n_features=150, random_state=1105)


@pytest.fixture
def bn_x_wide(bn_x_y_wide):
    return bn_x_y_wide[0]


@pytest.fixture
def bn_y_wide(bn_x_y_wide):
    return bn_x_y_wide[1]


@pytest.fixture
def bn_x_wide_sparse(bn_x_wide):
    return csr_matrix(bn_x_wide)


@pytest.fixture(
    params=[
        (lf("bn_x"), lf("bn_y")),
        (lf("bn_x_sparse"), lf("bn_y")),
        (lf("bn_x_wide"), lf("bn_y_wide")),
        (lf("bn_x_wide_sparse"), lf("bn_y_wide")),
    ]
)
def binomial_inputs(request):
    return request.param


@pytest.fixture
def mul_x_y():
    np.random.seed(488881)
    return make_classification(
        n_samples=400,
        n_classes=3,
        n_informative=15,
        n_features=25,
        random_state=10585,
    )


@pytest.fixture
def mul_x(mul_x_y):
    return mul_x_y[0]


@pytest.fixture
def mul_y(mul_x_y):
    return mul_x_y[1]


@pytest.fixture
def mul_x_sparse(mul_x_y):
    return csr_matrix(mul_x_y[0])


@pytest.fixture
def mul_x_y_wide():
    return make_classification(
        n_samples=400,
        n_classes=3,
        n_informative=15,
        n_features=500,
        random_state=15841,
    )


@pytest.fixture
def mul_x_wide(mul_x_y_wide):
    return mul_x_y_wide[0]


@pytest.fixture
def mul_y_wide(mul_x_y_wide):
    return mul_x_y_wide[1]


@pytest.fixture
def mul_x_wide_sparse(mul_x_wide):
    return csr_matrix(mul_x_wide)


@pytest.fixture(
    params=[
        (lf("mul_x"), lf("mul_y")),
        (lf("mul_x_sparse"), lf("mul_y")),
        (lf("mul_x_wide"), lf("mul_y_wide")),
        (lf("mul_x_wide_sparse"), lf("mul_y_wide")),
    ]
)
def multinomial_inputs(request):
    return request.param


@pytest.fixture(params=[0.0, 0.25, 0.50, 0.75, 1.0])
def alphas(request):
    return request.param


@pytest.fixture(
    params=[
        "accuracy",
        "roc_auc",
        "average_precision",
        "log_loss",
        "precision_macro",
        "precision_micro",
        "precision_weighted",
        "f1_micro",
        "f1_macro",
        "f1_weighted",
    ]
)
def scoring(request):
    return request.param


@pytest.fixture(
    params=[
        "accuracy",
        "log_loss",
        "precision_macro",
        "precision_micro",
        "precision_weighted",
        "f1_micro",
        "f1_macro",
        "f1_weighted",
    ]
)
def multinomial_scoring(request):
    return request.param


@pytest.fixture
def mutinomial_score_list():
    return [
        "accuracy",
        "log_loss",
        "precision_macro",
        "precision_micro",
        "precision_weighted",
        "f1_micro",
        "f1_macro",
        "f1_weighted",
    ]


# I don't think I understand what this test
# does enough to fix this right now?
# @pytest.mark.filterwarnings
# @parametrize_with_checks([LogitNet()])
# def test_estimator_interface(estimator, check):
#     check(estimator)


@pytest.fixture
def m():
    return LogitNet()


@pytest.mark.parametrize("inputs", [(lf("binomial_inputs")), (lf("multinomial_inputs"))])
def test_with_defaults(m, inputs):
    x, y = inputs
    m = m.fit(x, y)
    sanity_check_logistic(m, x)

    # check selection of lambda_best
    assert m.lambda_best_inx_ <= m.lambda_max_inx_

    # check full path predict
    p = m.predict(x, lamb=m.lambda_path_)
    assert p.shape[-1] == m.lambda_path_.size


# TODO: could probably parametrize predict/predict_proba
# but I don't want to get into that territory yet
@pytest.mark.parametrize("inputs", [(lf("binomial_inputs")), (lf("multinomial_inputs"))])
def test_one_row_predict(m, inputs):
    # Verify that predicting on one row gives only one row of output
    X, y = inputs
    m.fit(X, y)
    p = m.predict(X[0].reshape((1, -1)))
    assert p.shape == (1,)


@pytest.mark.parametrize("inputs", [(lf("binomial_inputs")), (lf("multinomial_inputs"))])
def test_one_row_predict_proba(m, inputs):
    # Verify that predict_proba on one row gives 2D output
    X, y = inputs
    m.fit(X, y)
    p = m.predict_proba(X[0].reshape((1, -1)))
    assert p.shape == (1, len(np.unique(y)))


@pytest.mark.parametrize("inputs", [(lf("binomial_inputs")), (lf("multinomial_inputs"))])
def test_one_row_predict_with_lambda(m, inputs):
    # One row to predict along with lambdas should give 2D output
    lamb = [0.01, 0.02, 0.04, 0.1]
    X, y = inputs
    m.fit(X, y)
    p = m.predict(X[0].reshape((1, -1)), lamb=lamb)
    assert p.shape == (1, len(lamb))


@pytest.fixture
def lamb():
    return [0.01, 0.02, 0.04, 0.1]


@pytest.mark.parametrize("inputs", [(lf("binomial_inputs")), (lf("multinomial_inputs"))])
def test_one_row_predict_proba_with_lambda(m, inputs, lamb):
    # One row to predict_proba along with lambdas should give 3D output
    X, y = inputs
    m.fit(X, y)
    p = m.predict_proba(X[0].reshape((1, -1)), lamb=lamb)
    assert p.shape == (1, len(np.unique(y)), len(lamb))


@pytest.fixture()
def malphas(alphas):
    return LogitNet(alpha=alphas, random_state=41041)


@pytest.mark.parametrize("malpha", [(lf("malphas"))])
def test_alphas(malpha, bn_x, bn_y, min_acceptable_accuracy):
    malpha = malpha.fit(bn_x, bn_y)
    score = accuracy_score(bn_y, malpha.predict(bn_x))
    assert score > min_acceptable_accuracy


@pytest.fixture
def lower_limits(bn_x):
    return np.repeat(-1, bn_x.shape[1])


@pytest.fixture
def upper_limits():
    return 0


@pytest.fixture
def m_coef_limits(lower_limits, upper_limits):
    return LogitNet(
        lower_limits=lower_limits,
        upper_limits=upper_limits,
        random_state=69265,
        alpha=0,
    )


def test_coef_limits(bn_x, bn_y, m_coef_limits):
    m_coef_limits = m_coef_limits.fit(bn_x, bn_y)
    assert np.all(m_coef_limits.coef_ >= -1)
    assert np.all(m_coef_limits.coef_ <= 0)


@pytest.fixture
def m_alpha_1():
    return LogitNet(alpha=1)


def test_relative_penalties(bn_x, bn_y, m_alpha_1):
    p = bn_x.shape[1]

    # m1 no relative penalties applied

    m_alpha_2 = deepcopy(m_alpha_1)
    m_alpha_1.fit(bn_x, bn_y)

    # find the nonzero indices from LASSO
    nonzero = np.nonzero(m_alpha_1.coef_[0])

    # unpenalize those nonzero coefs
    penalty = np.repeat(1, p)
    penalty[nonzero] = 0

    # refit the model with the unpenalized coefs
    m_alpha_2.fit(bn_x, bn_y, relative_penalties=penalty)

    # verify that the unpenalized coef ests exceed the penalized ones
    # in absolute value
    assert np.all(np.abs(m_alpha_1.coef_[0]) <= np.abs(m_alpha_2.coef_[0]))


@pytest.fixture
def min_n_splits():
    return 3


@pytest.fixture
def msplits(n_splits):
    return LogitNet(n_splits=n_splits, random_state=41041)


def test_n_splits(msplits, bn_x, bn_y, n_splits, min_n_splits):
    if n_splits > 0 and n_splits < min_n_splits:
        with pytest.raises(ValueError, match="n_splits must be at least 3"):
            msplits = msplits.fit(bn_x, bn_y)
    else:
        msplits = msplits.fit(bn_x, bn_y)
        sanity_check_logistic(msplits, bn_x)


@pytest.fixture
def m_scoring(scoring):
    return LogitNet(scoring=scoring)


def test_cv_scoring(m_scoring, bn_x, bn_y, min_acceptable_accuracy):
    m_scoring = m_scoring.fit(bn_x, bn_y)
    score = accuracy_score(bn_y, m_scoring.predict(bn_x))
    assert score > min_acceptable_accuracy


@pytest.fixture
def multiscoring(multinomial_scoring):
    return LogitNet(scoring=multinomial_scoring)


def test_cv_scoring_multinomial(m_scoring, mul_x, mul_y, mutinomial_score_list, even_miner_acceptable_accuracy):
    if m_scoring.scoring in mutinomial_score_list:
        m_scoring = m_scoring.fit(mul_x, mul_y)
        score = accuracy_score(mul_y, m_scoring.predict(mul_x))
        assert score >= even_miner_acceptable_accuracy
    else:
        with pytest.raises(ValueError, match=r".*multiclass.*"):
            m_scoring.fit(mul_x, mul_y)


@pytest.fixture
def m_no_splits():
    return LogitNet(n_splits=0)


def test_predict_without_cv(m_no_splits, bn_x, bn_y):
    m_no_splits = m_no_splits.fit(bn_x, bn_y)

    # should not make prediction unless value is passed for lambda
    with pytest.raises(ValueError):
        m_no_splits.predict(bn_x)


@pytest.mark.xfail
def test_coef_interpolation(m_no_splits):
    m_no_splits = m_no_splits.fit(bn_x, bn_y)

    # predict for a value of lambda between two values on the computed path
    lamb_lo = m_no_splits.lambda_path_[1]
    lamb_hi = m_no_splits.lambda_path_[2]

    # a value not equal to one on the computed path
    lamb_mid = (lamb_lo + lamb_hi) / 2.0

    pred_lo = m_no_splits.predict_proba(bn_x, lamb=lamb_lo)
    pred_hi = m_no_splits.predict_proba(bn_x, lamb=lamb_hi)
    pred_mid = m_no_splits.predict_proba(bn_x, lamb=lamb_mid)

    assert nptst.assert_allclose(pred_lo, pred_mid)
    assert nptst.assert_allclose(pred_hi, pred_mid)


def test_lambda_clip_warning(bn_x, bn_y, m_no_splits):
    m_no_splits = m_no_splits.fit(bn_x, bn_y)

    with pytest.warns(RuntimeWarning):
        m_no_splits.predict(bn_x, lamb=m_no_splits.lambda_path_[0] + 1)

    with pytest.warns(RuntimeWarning):
        m_no_splits.predict(bn_x, lamb=m_no_splits.lambda_path_[-1] - 1)


@pytest.fixture
def ones_like_y(bn_y):
    return np.ones_like(bn_y)


def test_single_class_exception(m, bn_x, ones_like_y):
    with pytest.raises(ValueError, match="Training data need to contain at least 2 classes."):
        m.fit(bn_x, ones_like_y)


@pytest.fixture
def m_random(random_int):
    return LogitNet(random_state=random_int)


def test_random_state_cv(m_random, bn_x, bn_y, random_int):
    m_random.fit(bn_x, bn_y)
    assert m_random._cv.random_state == random_int


@pytest.fixture
def m_maxfeatures(max_features):
    return LogitNet(max_features=max_features)


def test_max_features(m_maxfeatures, mul_x_wide_sparse, mul_y_wide, max_features):
    m_maxfeatures = m_maxfeatures.fit(mul_x_wide_sparse, mul_y_wide)
    num_features = np.count_nonzero(m_maxfeatures.coef_, axis=1)
    assert np.all(num_features <= max_features)


@pytest.fixture
def m_f1_micro():
    return LogitNet(scoring="f1_micro")


@pytest.fixture
def to_keep(mul_y):
    class_0_idx = np.where(mul_y == 0)
    to_drop = class_0_idx[0][:-3]
    to_keep = np.ones(len(mul_y), dtype=bool)
    to_keep[to_drop] = False
    return to_keep


@pytest.fixture
def kept_y(mul_y, to_keep):
    return mul_y[to_keep]


@pytest.fixture
def kept_x(mul_x_wide_sparse, to_keep):
    return mul_x_wide_sparse[to_keep]


@pytest.fixture
def sample_weight(kept_y):
    sample_weight = class_weight.compute_sample_weight("balanced", kept_y)
    sample_weight[0] = 0.0
    return sample_weight


@pytest.fixture
def unweighted_acc(m_f1_micro, kept_x, kept_y, sample_weight):
    m_f1_micro = m_f1_micro.fit(kept_x, kept_y)
    return f1_score(kept_y, m_f1_micro.predict(kept_x), sample_weight=sample_weight, average="micro")


@pytest.fixture
def weighted_acc(m_f1_micro, kept_x, kept_y, sample_weight):
    m_f1_micro = m_f1_micro.fit(kept_x, kept_y, sample_weight)
    return f1_score(kept_y, m_f1_micro.predict(kept_x), sample_weight=sample_weight, average="micro")


def test_use_sample_weights(weighted_acc, unweighted_acc):
    assert weighted_acc >= unweighted_acc
