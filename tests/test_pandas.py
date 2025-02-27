# what is the point of this?
# Pandas isn't required nor is it an
# optional dependency.
from importlib.util import find_spec

import pytest
from sklearn.datasets import make_classification, make_regression

from glmnet import ElasticNet, LogitNet

from .util import sanity_check_logistic, sanity_check_regression


@pytest.fixture
def elastic_net_model():
    return ElasticNet(n_splits=3, random_state=123)


@pytest.fixture
def logit_net_model():
    return LogitNet(n_splits=3, random_state=123)


@pytest.mark.skipif(not find_spec("pandas"), reason="Pandas is required")
def test_elasticnet_pandas(elastic_net_model):
    import pandas as pd

    x, y = make_regression(random_state=561)
    df = pd.DataFrame(x)
    df["y"] = y

    elastic_net_model = elastic_net_model.fit(df.drop(["y"], axis=1), df.y)
    sanity_check_regression(elastic_net_model, x)


@pytest.mark.skipif(not find_spec("pandas"), reason="Pandas is required")
def test_logitnet_pandas(logit_net_model):
    import pandas as pd

    x, y = make_classification(random_state=1105)
    df = pd.DataFrame(x)
    df["y"] = y

    logit_net_model = logit_net_model.fit(df.drop(["y"], axis=1), df.y)
    sanity_check_logistic(logit_net_model, x)
