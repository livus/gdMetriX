# Contributing to gdMetriX

Thank you for your interest in contributing! There are several ways to help:

- **Report a bug or unexpected behaviour** — [open a bug report](https://github.com/livus/gdMetriX/issues/new?template=bug_report.md)
- **Request a new feature or metric** — [open a feature request](https://github.com/livus/gdMetriX/issues/new?template=feature_request.md)
- **Contribute code** — see the sections below to get started

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

## Adding a metric

Every function that takes a graph must declare how it responds to edge geometry, i.e. to drawings
whose edges are drawn as polylines or curves rather than as straight lines. Apply the
`@bend_support(...)` decorator from `gdMetriX.bend_support` as the outermost decorator:

```python
@bend_support(BendSupport.STRAIGHT_LINE_ONLY)
@common.resolve_pos
def my_metric(g, pos=None):
    ...
```

Pick the classification by what the metric actually reads:

| | |
|---|---|
| `GEOMETRY_INDEPENDENT` | The metric is defined over the node positions alone. Note that this also has to hold for everything it calls — a metric that delegates to a `STRAIGHT_LINE_ONLY` helper is not geometry-independent, however node-based its own definition is. |
| `STRAIGHT_LINE_ONLY` | The metric assumes straight edges. It is wrapped so that it raises `BendsNotSupportedError` on a drawing carrying edge geometry, rather than silently measuring a different drawing than the one given. |
| `SUPPORTED` | The metric reads the edge geometry and respects it. |

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
