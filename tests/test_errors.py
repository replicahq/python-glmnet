import pytest

from glmnet.errors import _check_error_flag


@pytest.mark.parametrize(
    "error_code,error_type,message",
    [
        (7777, ValueError, r".*7777.*"),
        (10000, ValueError, r".*10000.*"),
        (1234, RuntimeError, r".*1234.*"),
        (7778, RuntimeError, r".*7778.*"),
        (8002, ValueError, r"Probability for class 2.*"),
        (8004, ValueError, r"Probability for class 4.*"),
        (90000, ValueError, r".*90000.*"),
    ],
)
def test_errors(error_code, error_type, message):
    with pytest.raises(error_type, match=message):
        _check_error_flag(error_code)


@pytest.mark.parametrize(
    "error_code,error_type,message",
    [
        (-76, RuntimeWarning, r"Model did not converge"),
        (-20007, RuntimeWarning, r"Predicted probability close to 0 or 1 for lambda no. 7."),
    ],
)
def test_warnings(error_code, error_type, message):
    with pytest.warns(error_type, match=message):
        _check_error_flag(error_code)
