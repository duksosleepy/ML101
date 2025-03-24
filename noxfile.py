"""
Nox configuration file for automation of testing and development tasks.
"""

import os
from pathlib import Path

import nox

# Set Python versions to use for testing
PYTHON_VERSIONS = ["3.11", "3.12", "3.13"]
DEFAULT_PYTHON = "3.12"

# Default environment for all sessions
DEFAULT_ENV = {
    "FORCE_COLOR": "3",
}

# Don't create .nox directory if in CI
nox.options.error_on_external_run = True
nox.options.error_on_missing_interpreters = False
nox.options.reuse_existing_virtualenvs = os.environ.get("CI") != "true"
nox.options.sessions = ["lint", "tests"]

# Directories to exclude
EXCLUDE_PATHS = [
    ".git",
    ".ruff_cache",
    ".nox",
    ".tox",
    "venv",
    ".venv",
    "__pycache__",
    "build",
    "dist",
    "alembic",
]


@nox.session
def lint(session):
    """
    Run all linting tasks.
    """
    session.install("-r", "requirements.txt")
    session.install("ruff", "flake8", "flake8-bugbear", "mypy", "codespell")

    print("Running ruff...")
    session.run("ruff", "check", ".")

    print("Running flake8...")
    session.run("flake8", "core", "dashboard")

    print("Running mypy...")
    session.run("mypy", "core", "dashboard")

    print("Running codespell...")
    session.run(
        "codespell", "core", "dashboard", "--skip", ",".join(EXCLUDE_PATHS)
    )


@nox.session
def format(session):
    """
    Run code formatting tools.
    """
    session.install("black", "ruff", "pycln", "pyupgrade")

    print("Running black...")
    session.run("black", "core", "dashboard")

    print("Running ruff with --fix...")
    session.run("ruff", "check", "--fix", ".")

    print("Running pycln...")
    session.run("pycln", "--all", "core", "dashboard")


@nox.session(python=PYTHON_VERSIONS)
def tests(session, hatch=False, vcs=True):
    """
    Run tests with pytest.

    Args:
        hatch: Use hatch for dependency management
        vcs: Include VCS files in the test
    """
    env = {**DEFAULT_ENV}

    # Install dependencies
    session.install("-r", "requirements.txt", "pytest", "pytest-cov")

    # Prepare test arguments
    test_args = ["pytest"]
    if session.posargs:
        test_args.extend(session.posargs)
    else:
        test_args.extend(["--cov=./", "--cov-report=xml"])

    # For hatch tests, we need to handle dependencies differently
    if hatch:
        try:
            session.install("hatch")
            if vcs:
                # Test with VCS files
                session.run(*test_args, env=env)
            else:
                # Test without VCS files
                session.run(*test_args, env={**env, "PYTHONPATH": ""})
        except Exception as e:
            session.log(f"Error running hatch tests: {e}")
            raise
    else:
        session.run(*test_args, env=env)


@nox.session
def nox(session, hatch=False, vcs=True):
    """
    Run noxfile tests - this validates the noxfile itself.

    Args:
        hatch: Use hatch for dependency management
        vcs: Include VCS files in the test
    """
    # Setup the environment
    env = {**DEFAULT_ENV}

    if hatch:
        try:
            session.install("hatch")
            if vcs:
                if session.posargs and session.posargs[0] == "docs":
                    # Test docs building
                    session.run("hatch", "run", "docs:build", env=env)
                else:
                    # Run basic tests
                    session.run("hatch", "run", "test", env=env)
            else:
                # Non-VCS test
                env["PYTHONPATH"] = ""
                session.run("hatch", "run", "test", env=env)
        except Exception as e:
            session.log(f"Error running hatch nox tests: {e}")
            raise
    else:
        session.log("Non-hatch nox testing not configured. Use hatch=True")


@nox.session
def docs(session):
    """
    Build documentation.
    """
    session.install("-r", "requirements.txt")
    session.install("sphinx", "sphinx-rtd-theme", "myst-parser")

    # Create docs directory if it doesn't exist
    docs_dir = Path("docs")
    if not docs_dir.exists():
        session.log("Creating docs directory")
        docs_dir.mkdir()

    # Build the documentation
    session.chdir("docs")
    session.run("sphinx-build", "-b", "html", ".", "_build/html")
