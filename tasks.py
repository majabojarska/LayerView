"""
Tasks for maintaining the project.

Execute 'invoke --list' for guidance on using Invoke
"""
import platform
import shutil
import webbrowser
from pathlib import Path

from invoke import task
from PyQt5 import uic

ROOT_DIR = Path(__file__).parent
TEST_DIR = ROOT_DIR.joinpath("tests")
SOURCE_DIR = ROOT_DIR.joinpath("layerview")
PYUIC_DIR = ROOT_DIR.joinpath("layerview/app/pyuic")
TOX_DIR = ROOT_DIR.joinpath(".tox")
COVERAGE_FILE = ROOT_DIR.joinpath(".coverage")
COVERAGE_DIR = ROOT_DIR.joinpath("htmlcov")
COVERAGE_REPORT = COVERAGE_DIR.joinpath("index.html")
DOCS_DIR = ROOT_DIR.joinpath("docs")
DOCS_BUILD_DIR = DOCS_DIR.joinpath("_build")
DOCS_INDEX = DOCS_BUILD_DIR.joinpath("index.html")
UML_DIR = ROOT_DIR.joinpath("diagrams/uml")
PYTHON_DIRS = [str(d) for d in [SOURCE_DIR, TEST_DIR]]

PYREVERSE_OPTS = "-o svg -ASmy -f ALL -a1 -s1 -p"


def _delete_file(file):
    try:
        file.unlink(missing_ok=True)
    except TypeError:
        # missing_ok argument added in 3.8
        try:
            file.unlink()
        except FileNotFoundError:
            pass


def _run(c, command):
    return c.run(command, pty=platform.system() != "Windows")


@task(help={"check": "Checks if source is formatted without applying changes"})
def format(c, check=False):
    """Format code."""
    python_dirs_string = " ".join(PYTHON_DIRS)
    # Run isort
    isort_options = f"--recursive {'--check-only --diff' if check else ''}"
    _run(c, f"isort {isort_options} {python_dirs_string}")
    # Run black
    black_options = "--diff --check" if check else ""
    _run(c, f"black {black_options} {python_dirs_string}")


@task
def lint(c):
    """Lint code with flake8."""
    _run(c, f"flake8 --exclude {PYUIC_DIR} {' '.join(PYTHON_DIRS)}")


@task
def test(c):
    """Run tests."""
    _run(c, "tox")


@task(help={"publish": "Publish the result via coveralls"})
def coverage(c, publish=False):
    """Create coverage report."""
    _run(c, f"coverage run --source {SOURCE_DIR} -m pytest")
    _run(c, "coverage report")
    if publish:
        # Publish the results via coveralls
        _run(c, "coveralls")
    else:
        # Build a local report
        _run(c, "coverage html")
        webbrowser.open(COVERAGE_REPORT.as_uri())


# Cleaning


@task
def docs_clean(c):
    """Clean up files from documentation build."""
    _run(c, f"rm -rf {DOCS_BUILD_DIR}")


@task
def pyuic_clean(c):
    """Clean up files from pyuic build."""
    for file in PYUIC_DIR.glob("*.py"):
        if file.name != "__init__.py":
            print(f"Deleting {file.relative_to(ROOT_DIR)}")
            _delete_file(file)


@task
def build_clean(c):
    """Clean up files from package building."""
    _run(c, "rm -fr build/")
    _run(c, "rm -fr dist/")
    _run(c, "rm -fr .eggs/")
    _run(c, "find . -name '*.egg-info' -exec rm -fr {} +")
    _run(c, "find . -name '*.egg' -exec rm -f {} +")


@task
def python_clean(c):
    """
    Clean up python file artifacts
    """
    _run(c, "find . -name '*.pyc' -exec rm -f {} +")
    _run(c, "find . -name '*.pyo' -exec rm -f {} +")
    _run(c, "find . -name '*~' -exec rm -f {} +")
    _run(c, "find . -name '__pycache__' -exec rm -fr {} +")


@task
def test_clean(c):
    """
    Clean up files from testing
    """
    _delete_file(COVERAGE_FILE)
    shutil.rmtree(TOX_DIR, ignore_errors=True)
    shutil.rmtree(COVERAGE_DIR, ignore_errors=True)


@task(pre=[build_clean, python_clean, pyuic_clean, test_clean, docs_clean])
def clean(c):
    """
    Runs all clean sub-tasks
    """
    pass


# Build & Release


@task(pre=[docs_clean], help={"launch": "Launch documentation in the web browser"})
def docs(c, launch=False):
    """
    Generate documentation
    """
    _run(c, f"sphinx-build -b html {DOCS_DIR} {DOCS_BUILD_DIR}")
    if launch:
        webbrowser.open(DOCS_INDEX.as_uri())


@task(pyuic_clean)
def pyuic(c):
    """
    Build Qt *.ui files as Python modules via pyuic.
    """
    dir_designer = ROOT_DIR / "designer"
    for path_ui in dir_designer.glob("*.ui"):
        path_py = PYUIC_DIR / f"{path_ui.stem}.py"
        print(
            f"Compiling {path_ui.relative_to(ROOT_DIR)} → "
            f"{path_py.relative_to(ROOT_DIR)}"
        )
        with open(path_py, "w") as path_py_handle:
            uic.compileUi(uifile=str(path_ui.absolute()), pyfile=path_py_handle)


@task(pre=[clean, pyuic])
def dist(c):
    """
    Build source and wheel packages
    """
    _run(c, "poetry build")


@task(pre=[clean, dist])
def release(c):
    """
    Make a release of the python package to pypi
    """
    _run(c, "poetry publish")
