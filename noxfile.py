import os
import sys
from pathlib import Path

import nox

PACKAGE = "glmnet"
PYTHON_VERSIONS = ["3.10", "3.11", "3.12", "3.13"] # no 3.9 because sweet christmas does it want to fail to install
LATEST_VERSION = PYTHON_VERSIONS[-2] # since 3.13 isn't *officially* released yet
NUMPY_VERSIONS = ["2.1.3", "2.0.2", "1.26.4", "1.25.2", "1.24.4"]
os.environ.update(
    {
        "PDM_IGNORE_SAVED_PYTHON": "1",
        "PDM_IGNORE_ACTIVE_VENV": "0",
    }
)
nox.needs_version = ">=2024.4.15"
nox.options.sessions = (
    "mypy",
    "tests",
)

locations = (
    "src",
    "tests",
)


@nox.session(python=LATEST_VERSION, reuse_venv=True)
def lockfile(session) -> None:
    """Run the test suite."""
    session.run_always("pdm", "lock", external=True)


@nox.session(python=LATEST_VERSION)
def lint(session) -> None:
    """Lint using ruff."""
    args = session.posargs or locations
    session.install("ruff")
    session.run("ruff", "check", "--fix", *args)
    session.run("ruff", "format", *args)


@nox.session(python=LATEST_VERSION, reuse_venv=False)
def mypy(session) -> None:
    """Type-check using mypy."""
    session.install("mypy")
    session.install(".", external=True)
    session.run(
        "mypy",
        "--install-types",
        "--non-interactive",
        f"--python-executable={sys.executable}",
        "noxfile.py",
    )


@nox.session()
# numpy >=2.1 requires python 3.10-3.13
@nox.parametrize(
    "python,numpy",
    [   (python, numpy)
        for python in PYTHON_VERSIONS
        for numpy in NUMPY_VERSIONS
        if (python, numpy) not in [
            # ("3.9", "2.1.3"),
            # ("3.9", "2.0.2"),
            ("3.12", "1.25.2"),
            ("3.12", "1.24.4"),
            ("3.13", "1.25.2"),
            ("3.13", "1.24.4")
            ]
    ]
    )
def tests(session, numpy) -> None:
    """Run the test suite."""
    # session.install("pdm")
    # session.run("pdm", "lock")
    session.install("cython", f"numpy=={numpy}")
    session.install("meson-python", "ninja", "setuptools")
    session.install("pytest>=8.3.3","pytest-lazy-fixtures>=1.1.1","pytest-randomly>=3.16.0","pytest-xdist[psutil]>=3.6.1", "coverage[toml]")
    session.install(".", external=True)
    session.run("python", "-c", "'import numpy; print(numpy.__version__)'")
    session.run(
        # running in parallel doesn't work I think because of not setting a seed
        # "coverage", "run", "--parallel", "-m", "pytest", "--numprocesses", "auto", "--random-order", external=True
        "coverage", "run", "-m", "pytest", "tests"
    )


@nox.session(python=LATEST_VERSION, reuse_venv=True)
def coverage(session) -> None:
    """Produce the coverage report."""
    args = session.posargs or ["report"]
    session.install("coverage[toml]", "codecov", external=True)

    if not session.posargs and any(Path().glob(".coverage.*")):
        session.run("coverage", "combine")

    session.run("coverage", "json", "--fail-under=0")
    session.run("codecov", *args)
