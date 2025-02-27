"""
The code below is a modified version of sklearn.metrics.scorer to allow for scoring
the entire lambda path of a glmnet model.

    - lambda parameter added to the scorers
    - scorers return an array of scores, [n_lambda,]
"""

# Authors: Andreas Mueller <amueller@ais.uni-bonn.de>
#          Lars Buitinck <L.J.Buitinck@uva.nl>
#          Arnaud Joly <arnaud.v.joly@gmail.com>
# License: Simplified BSD

from abc import ABCMeta, abstractmethod
from functools import partial

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    f1_score,
    log_loss,
    mean_absolute_error,
    mean_squared_error,
    median_absolute_error,
    precision_score,
    r2_score,
    recall_score,
    roc_auc_score,
)
from sklearn.utils.multiclass import type_of_target


class _BaseScorer(metaclass=ABCMeta):
    def __init__(self, score_func, sign, kwargs):
        self._kwargs = kwargs
        self._score_func = score_func
        self._sign = sign

    @abstractmethod
    def __call__(self, estimator, X, y, sample_weight=None):
        pass

    def __repr__(self):
        kwargs_string = "".join([f", {k!s}={v!s}" for k, v in self._kwargs.items()])
        return f"make_scorer({self._score_func.__name__}{'' if self._sign > 0 else ', greater_is_better=False'}{self._factory_args()}{kwargs_string})"

    def _factory_args(self):
        """Return non-default make_scorer arguments for repr."""
        return ""


class _PredictScorer(_BaseScorer):
    def __call__(self, estimator, X, y_true, sample_weight=None, lamb=None):
        """Evaluate predicted target values for X relative to y_true and one or
        more values for lambda.

        Parameters
        ----------
        estimator : object
            Trained estimator to use for scoring. Must have a predict_proba
            method; the output of that is used to compute the score.

        X : array-like or sparse matrix
            Test data that will be fed to estimator.predict.

        y_true : array-like
            Gold standard target values for X.

        sample_weight : array-like, optional (default=None)
            Sample weights.

        lamb : array, shape (n_lambda,)
            Values of lambda from lambda_path_ from which to score predictions.

        Returns
        -------
        score : array, shape (n_lambda,)
            Score function applied to prediction of estimator on X.
        """
        y_pred = estimator.predict(X, lamb=lamb)
        if sample_weight is not None:
            scores = np.apply_along_axis(
                lambda y_hat: self._score_func(y_true, y_hat, sample_weight=sample_weight, **self._kwargs),
                0,
                y_pred,
            )
        else:
            scores = np.apply_along_axis(lambda y_hat: self._score_func(y_true, y_hat, **self._kwargs), 0, y_pred)
        return self._sign * scores


class _ProbaScorer(_BaseScorer):
    def __call__(self, clf, X, y_true, sample_weight=None, lamb=None):
        """Evaluate predicted probabilities for X relative to y_true.

        Parameters
        ----------
        clf : object
            Trained classifier to use for scoring. Must have a predict_proba
            method; the output of that is used to compute the score.

        X : array-like or sparse matrix
            Test data that will be fed to clf.predict_proba.

        y_true : array-like
            Gold standard target values for X. These must be class labels,
            not probabilities.

        sample_weight : array-like, optional (default=None)
            Sample weights.

        lamb : array, shape (n_lambda,)
            Values of lambda from lambda_path_ from which to score predictions.

        Returns
        -------
        score : array, shape (n_lambda,)
            Score function applied to prediction of estimator on X.
        """
        y_pred = clf.predict_proba(X, lamb=lamb)  # y_pred shape (n_samples, n_classes, n_lambda)

        if sample_weight is not None:

            def score_func(y_hat):
                return self._score_func(y_true, y_hat, sample_weight=sample_weight, **self._kwargs)
        else:

            def score_func(y_hat):
                return self._score_func(y_true, y_hat, **self._kwargs)

        scores = np.zeros(y_pred.shape[-1])
        for i in range(len(scores)):
            scores[i] = score_func(y_pred[..., i])

        return self._sign * scores

    def _factory_args(self):
        return ", needs_proba=True"


class _ThresholdScorer(_BaseScorer):
    def __call__(self, clf, X, y_true, sample_weight=None, lamb=None):
        """Evaluate decision function output for X relative to y_true.

        Parameters
        ----------
        clf : object
            Trained classifier to use for scoring. Must have either a
            decision_function method or a predict_proba method; the output of
            that is used to compute the score.

        X : array-like or sparse matrix
            Test data that will be fed to clf.decision_function or
            clf.predict_proba.

        y_true : array-like
            Gold standard target values for X. These must be class labels,
            not decision function values.

        sample_weight : array-like, optional (default=None)
            Sample weights.

        lamb : array, shape (n_lambda,)
            Values of lambda from lambda_path_ from which to score predictions.

        Returns
        -------
        score : array, shape (n_lambda,)
            Score function applied to prediction of estimator on X.
        """
        y_type = type_of_target(y_true)
        if y_type not in ("binary", "multilabel-indicator"):
            msg = f"{y_type} format is not supported"
            raise ValueError(msg)

        y_pred = clf.decision_function(X, lamb=lamb)
        if sample_weight is not None:
            scores = np.apply_along_axis(
                lambda y_hat: self._score_func(y_true, y_hat, sample_weight=sample_weight, **self._kwargs),
                0,
                y_pred,
            )
        else:
            scores = np.apply_along_axis(lambda y_hat: self._score_func(y_true, y_hat, **self._kwargs), 0, y_pred)
        return self._sign * scores

    def _factory_args(self):
        return ", needs_threshold=True"


def get_scorer(scoring):
    if isinstance(scoring, str):
        try:
            scorer = SCORERS[scoring]
        except KeyError as e:
            msg = f"{scoring} is not a valid scoring value. Valid options are {sorted(SCORERS.keys())!s}"
            raise ValueError(msg) from e
    else:
        scorer = scoring
    return scorer


def _passthrough_scorer(estimator, *args, **kwargs):
    """Function that wraps estimator.score"""
    return estimator.score(*args, **kwargs)


def check_scoring(estimator, scoring=None, allow_none=False):
    """Determine scorer from user options.

    A TypeError will be thrown if the estimator cannot be scored.

    Parameters
    ----------
    estimator : estimator object implementing 'fit'
        The object to use to fit the data.

    scoring : string, callable or None, optional, default: None
        A string (see model evaluation documentation) or
        a scorer callable object / function with signature
        ``scorer(estimator, X, y)``.

    allow_none : boolean, optional, default: False
        If no scoring is specified and the estimator has no score function, we
        can either return None or raise an exception.

    Returns
    -------
    scoring : callable
        A scorer callable object / function with signature
        ``scorer(estimator, X, y)``.
    """
    has_scoring = scoring is not None
    if not hasattr(estimator, "fit"):
        msg = "estimator should a be an estimator implementing 'fit' method, {estimator!r} was passed"
        raise TypeError(msg)
    elif has_scoring:
        return get_scorer(scoring)
    elif hasattr(estimator, "score"):
        return _passthrough_scorer
    elif allow_none:
        return None
    else:
        msg = "If no scoring is specified, the estimator passed should have a 'score' method. The estimator {estimator!r} does not."
        raise TypeError(msg)


def make_scorer(
    score_func,
    greater_is_better=True,
    needs_proba=False,
    needs_threshold=False,
    **kwargs,
):
    """Make a scorer from a performance metric or loss function.

    This factory function wraps scoring functions for use in GridSearchCV
    and cross_val_score. It takes a score function, such as ``accuracy_score``,
    ``mean_squared_error``, ``adjusted_rand_index`` or ``average_precision``
    and returns a callable that scores an estimator's output.

    Read more in the :ref:`User Guide <scoring>`.

    Parameters
    ----------
    score_func : callable,
        Score function (or loss function) with signature
        ``score_func(y, y_pred, **kwargs)``.

    greater_is_better : boolean, default=True
        Whether score_func is a score function (default), meaning high is good,
        or a loss function, meaning low is good. In the latter case, the
        scorer object will sign-flip the outcome of the score_func.

    needs_proba : boolean, default=False
        Whether score_func requires predict_proba to get probability estimates
        out of a classifier.

    needs_threshold : boolean, default=False
        Whether score_func takes a continuous decision certainty.
        This only works for binary classification using estimators that
        have either a decision_function or predict_proba method.

        For example ``average_precision`` or the area under the roc curve
        can not be computed using discrete predictions alone.

    **kwargs : additional arguments
        Additional parameters to be passed to score_func.

    Returns
    -------
    scorer : callable
        Callable object that returns a scalar score; greater is better.

    Examples
    --------
    >>> from sklearn.metrics import fbeta_score, make_scorer
    >>> ftwo_scorer = make_scorer(fbeta_score, beta=2)
    >>> ftwo_scorer
    make_scorer(fbeta_score, beta=2)
    >>> from sklearn.grid_search import GridSearchCV
    >>> from sklearn.svm import LinearSVC
    >>> grid = GridSearchCV(LinearSVC(), param_grid={'C': [1, 10]},
    ...                     scoring=ftwo_scorer)
    """
    sign = 1 if greater_is_better else -1
    if needs_proba and needs_threshold:
        msg = "Set either needs_proba or needs_threshold to True, but not both."
        raise ValueError(msg)
    if needs_proba:
        cls = _ProbaScorer
    elif needs_threshold:
        cls = _ThresholdScorer
    else:
        cls = _PredictScorer
    return cls(score_func, sign, kwargs)


# Standard regression scores
r2_scorer = make_scorer(r2_score)
mean_squared_error_scorer = make_scorer(mean_squared_error, greater_is_better=False)
mean_absolute_error_scorer = make_scorer(mean_absolute_error, greater_is_better=False)
median_absolute_error_scorer = make_scorer(median_absolute_error, greater_is_better=False)

# Standard Classification Scores
accuracy_scorer = make_scorer(accuracy_score)
f1_scorer = make_scorer(f1_score)

# Score functions that need decision values
roc_auc_scorer = make_scorer(roc_auc_score, greater_is_better=True, needs_threshold=True)
average_precision_scorer = make_scorer(average_precision_score, needs_threshold=True)
precision_scorer = make_scorer(precision_score)
recall_scorer = make_scorer(recall_score)

# Score function for probabilistic classification
log_loss_scorer = make_scorer(log_loss, greater_is_better=False, needs_proba=True)

SCORERS = {
    "r2": r2_scorer,
    "median_absolute_error": median_absolute_error_scorer,
    "mean_absolute_error": mean_absolute_error_scorer,
    "mean_squared_error": mean_squared_error_scorer,
    "accuracy": accuracy_scorer,
    "roc_auc": roc_auc_scorer,
    "average_precision": average_precision_scorer,
    "log_loss": log_loss_scorer,
}

for name, metric in [
    ("precision", precision_score),
    ("recall", recall_score),
    ("f1", f1_score),
]:
    SCORERS[name] = make_scorer(metric)
    for average in ["macro", "micro", "samples", "weighted"]:
        qualified_name = f"{name}_{average}"
        SCORERS[qualified_name] = make_scorer(partial(metric, pos_label=None, average=average))
