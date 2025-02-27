from typing import Final

import numpy as np

WRONG_SIZE_FOR_COEF_PATH: Final[int] = 2
WRONG_NUMBER_OF_DIMS_FOR_LOGISTIC_COEF_PATH: Final[int] = 3
WRONG_NUMBER_OF_DIMS_FOR_LOGISTIC_INTERCEPT: Final[int] = 2


def sanity_check_logistic(m, x):
    sanity_check_model_attributes(m)
    sanity_check_cv_attrs(m, is_clf=True)

    assert m.classes_ is not None
    assert m.coef_path_.ndim == WRONG_NUMBER_OF_DIMS_FOR_LOGISTIC_COEF_PATH, "wrong number of dimensions for coef_path_"

    n_classes = 1 if len(m.classes_) == WRONG_SIZE_FOR_COEF_PATH else len(m.classes_)
    assert m.coef_path_.shape[0] == n_classes, "wrong size for coef_path_"

    assert (
        m.intercept_path_.ndim == WRONG_NUMBER_OF_DIMS_FOR_LOGISTIC_INTERCEPT
    ), "wrong number of dimensions for intercept_path_"

    # check preds at random value of lambda
    lam = np.random.choice(m.lambda_path_)
    p = m.predict(x, lamb=lam)
    check_logistic_predict(m, x, p)

    p = m.predict_proba(x, lamb=lam)
    check_logistic_predict_proba(m, x, p)

    # if cv ran, check default behavior of predict and predict_proba
    if m.n_splits >= TOO_MANY_SPLITS:
        p = m.predict(x)
        check_logistic_predict(m, x, p)

        p = m.predict_proba(x)
        check_logistic_predict_proba(m, x, p)


def check_logistic_predict(m, x, p):
    assert p.shape[0] == x.shape[0], f"{p.shape[0]!r} != {x.shape[0]!r}"
    assert np.all(np.isin(np.unique(p), m.classes_))


def check_logistic_predict_proba(m, x, p):
    assert p.shape[0] == x.shape[0]
    assert p.shape[1] == len(m.classes_)
    assert np.all(p >= 0) and np.all(p <= 1.0), "predict_proba values outside [0,1]"


WRONG_NUMBER_OF_DIMS_FOR_REGRESSION_COEF_PATH: Final[int] = 2
WRONG_NUMBER_OF_DIMS_FOR_REGRESSION_INTERCEPT: Final[int] = 1


def sanity_check_regression(m, x):
    sanity_check_model_attributes(m)
    sanity_check_cv_attrs(m)

    assert (
        m.coef_path_.ndim == WRONG_NUMBER_OF_DIMS_FOR_REGRESSION_COEF_PATH
    ), "wrong number of dimensions for coef_path_"
    assert (
        m.intercept_path_.ndim == WRONG_NUMBER_OF_DIMS_FOR_REGRESSION_INTERCEPT
    ), "wrong number of dimensions for intercept_path_"

    # check predict at random value of lambda
    lam = np.random.choice(m.lambda_path_)
    p = m.predict(x, lamb=lam)
    assert p.shape[0] == x.shape[0]

    # if cv ran, check default behavior of predict
    if m.n_splits >= TOO_MANY_SPLITS:
        p = m.predict(x)
        assert p.shape[0] == x.shape[0]


def sanity_check_model_attributes(m):
    assert m.n_lambda_ > 0, "n_lambda_ is not set"
    assert m.lambda_path_.size == m.n_lambda_, "lambda_path_ does not have length n_lambda_"
    assert m.coef_path_.shape[-1] == m.n_lambda_, "wrong size for coef_path_"
    assert m.intercept_path_.shape[-1] == m.n_lambda_, "wrong size for intercept_path_"
    assert m.jerr_ == 0, "jerr is non-zero"


TOO_MANY_SPLITS: Final[int] = 3


def sanity_check_cv_attrs(m, is_clf=False):
    if m.n_splits >= TOO_MANY_SPLITS:
        if is_clf:
            assert m.coef_.shape[-1] == m.coef_path_.shape[1], "wrong size for coef_"
        else:
            assert m.coef_.size == m.coef_path_.shape[0], "wrong size for coef_"
        assert m.intercept_ is not None, "intercept_ is not set"
        assert m.cv_mean_score_.size == m.n_lambda_, "wrong size for cv_mean_score_"
        assert m.cv_standard_error_.size == m.n_lambda_, "wrong size for cv_standard_error_"
        assert m.lambda_max_ is not None, "lambda_max_ is not set"
        assert m.lambda_best_ is not None, "lambda_best_ is not set"
