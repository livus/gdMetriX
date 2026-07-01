# Contributing to gdMetriX

Thank you for your interest in contributing! Here is everything you need to get started.

## Setting up a development environment

Clone the repository and install the package in editable mode together with the test dependencies:

```shell
git clone https://github.com/livus/gdMetriX.git
cd gdMetriX
pip install -e ".[test]"
```

## Code style

gdMetriX uses [Black](https://black.readthedocs.io/) for formatting. All pull requests are checked automatically by CI.

To avoid a failed CI run, install the pre-commit hook so Black runs locally before every commit:

```shell
pip install pre-commit
pre-commit install
```

After this, any `git commit` will automatically verify formatting. If a file needs changes, the commit is blocked and Black tells you which files to fix — run `black src/` to apply them, then commit again.

To check or fix formatting manually at any time:

```shell
black --check src/   # check only
black src/           # fix in place
```

## Running the tests

```shell
pytest
```

Long-running stress tests are skipped by default. To include them:

```shell
pytest --runslow
```

## Submitting a pull request

1. Fork the repository and create a branch for your change.
2. Make your changes and ensure `pytest` and `black --check src/` both pass.
3. Open a pull request against `main`. The CI will run tests and a formatting check automatically.
