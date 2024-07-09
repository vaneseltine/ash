"""
See: https://nox.thea.codes/en/stable/cookbook.html
"""

import os
import re
from pathlib import Path
from typing import Any

import nox
from nox.sessions import Session

os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
IN_CI = os.getenv("CI", "").lower() == "true"


nox.options.default_venv_backend = "venv"
nox.options.reuse_existing_virtualenvs = "yes"
nox.options.error_on_external_run = "yes"

# Default run
nox.options.sessions = [
    "lint_black",
    "lint_pylint",
    "lint_pyright",
    "test_pytest",
    "test_coverage",
    "lint_todos",
]

CODE_DIR = "ash"


def run(session: Session, cmd: str, **kwargs: dict[str, Any]):
    _ = session.run(*cmd.split(), **kwargs)  # pyright: ignore[reportArgumentType]


def install(session: Session, cmd: str, **kwargs: dict[str, Any]):
    _ = session.install(*cmd.split(), **kwargs)  # pyright: ignore[reportArgumentType]


def supported_pythons(classifiers_file: str | Path = "pyproject.toml"):
    """
    Parse all supported Python classifiers.

    E.g., pyproject.toml including:

        "Programming Language :: Python",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Programming Language :: Python :: 3 :: Only",

    Becomes:

        ['3.12', '3.13']

    Note that comments are included in this search.
    """
    pattern = re.compile(r"Programming Language :: Python :: ([0-9]+\.[0-9.]+)")
    pythons = pattern.findall(Path(classifiers_file).read_text())
    return pythons


@nox.session(python=False)
def lint_black(session: Session):
    run(session, "python -m black .")


@nox.session(python=False)
def lint_pylint(session: Session):
    run(session, f"python -m pylint {CODE_DIR} --score=no")


@nox.session(python=False)
def lint_pyright(session: Session):
    run(
        session,
        f"python -m pyright {CODE_DIR}",
        env={"PYRIGHT_PYTHON_FORCE_VERSION": "latest"},  # hush
    )


@nox.session(python=False)
def test_pytest(session: Session):
    """
    Simple, non-environment run with coverage.

    pytest-xdist can be installed to allow threaded parallel testing with "-n auto."
    But it takes a couple seconds just to spin up the workers, so unless testing is
    taking long enough to compensate, it's overkill.
    """
    run(session, "python -m coverage run -m pytest --durations=5")
    run(session, "python -m coverage report")


@nox.session(python=supported_pythons(), reuse_venv=False)
def test_pytest_multipython(session: Session):
    install(session, "-r requirements-dev.txt")
    install(session, "-e .")
    run(session, "python -m run -m pytest")


@nox.session(python=False)
def test_coverage(session: Session):
    # run(session, "coveralls", success_codes=[0, 1]) # requires public GitHub
    run(session, "python -m coverage html")


@nox.session(python=False)
def lint_todos(_):
    for file in Path(".").glob("*/*.py"):
        result = search_in_file(file, "((TODO|FIXME|XXX).*)")
        for line in result:
            print(f"{file.name:>20}: {line}")


def search_in_file(path: Path, pattern: str, encoding: str = "utf-8"):
    text = Path(path).read_text(encoding)
    results = re.compile(pattern).findall(text)
    return [line for line, _match in results]
