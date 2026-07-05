# gdMetriX
#
# Copyright (C) 2026  Martin Nöllenburg, Sebastian Röder, Markus Wallinger
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
Tests marked `slow` (stress tests and all integration tests) are skipped by
default, but stay collected - unlike `-m "not slow"` deselection, which removes
them from `--collect-only` entirely and hides them from VS Code's Test Explorer.
Run them explicitly with `pytest --runslow ...`.

.vscode/settings.json passes --runslow to every VS Code-initiated run, so slow
tests run for real when you pick and run a specific test/class/file in VS Code,
while a plain terminal `pytest` keeps skipping them by default.
"""

import pytest


def pytest_addoption(parser):
    parser.addoption(
        "--runslow",
        action="store_true",
        default=False,
        help="run tests marked 'slow' instead of skipping them",
    )


def pytest_collection_modifyitems(config, items):
    if config.getoption("--runslow"):
        return
    skip_slow = pytest.mark.skip(reason="need --runslow option to run")
    for item in items:
        if "slow" in item.keywords:
            item.add_marker(skip_slow)
