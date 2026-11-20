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
Tests for scoping the global numeric precision: a function taking a ``precision`` argument applies
it for the duration of the call only, and leaves the precision as it found it.
"""

import networkx as nx
import pytest

from gdMetriX import crossings
from gdMetriX.utils import numeric


class TestPrecisionContext:

    def test_applies_within_and_restores_after(self):
        before = numeric.get_precision()

        with numeric.precision_context(0.5):
            assert numeric.get_precision() == 0.5

        assert numeric.get_precision() == before

    def test_restores_after_an_exception(self):
        before = numeric.get_precision()

        with pytest.raises(RuntimeError):
            with numeric.precision_context(0.5):
                raise RuntimeError()

        assert numeric.get_precision() == before

    def test_nests(self):
        with numeric.precision_context(0.5):
            with numeric.precision_context(0.25):
                assert numeric.get_precision() == 0.25
            assert numeric.get_precision() == 0.5


@numeric.applies_precision
def _seen_precision(a, b=None, precision: float = 1e-3):
    return numeric.get_precision()


class TestAppliesPrecision:

    def test_default(self):
        assert _seen_precision(1) == 1e-3

    def test_keyword(self):
        assert _seen_precision(1, precision=0.25) == 0.25

    def test_positional(self):
        assert _seen_precision(1, 2, 0.25) == 0.25

    def test_restores_after_the_call(self):
        with numeric.precision_context(1e-6):
            _seen_precision(1, precision=0.25)
            assert numeric.get_precision() == 1e-6

    def test_restores_after_an_exception(self):
        @numeric.applies_precision
        def _fail(precision: float = 0.25):
            raise RuntimeError()

        before = numeric.get_precision()
        with pytest.raises(RuntimeError):
            _fail()
        assert numeric.get_precision() == before

    def test_keeps_the_signature(self):
        assert _seen_precision.__name__ == "_seen_precision"
        assert "precision" in _seen_precision.__wrapped__.__code__.co_varnames

    def test_without_precision_parameter(self):
        with pytest.raises(TypeError):

            @numeric.applies_precision
            def _no_precision(a):
                return a

    def test_required_precision_missing(self):
        @numeric.applies_precision
        def _required(precision):
            return precision

        before = numeric.get_precision()
        with pytest.raises(TypeError):
            _required()
        assert numeric.get_precision() == before
        assert _required(0.25) == 0.25


def _crossing_drawing() -> nx.Graph:
    g = nx.Graph()
    g.add_nodes_from(
        [
            (0, {"pos": (0, 0)}),
            (1, {"pos": (2, 2)}),
            (2, {"pos": (0, 2)}),
            (3, {"pos": (2, 0)}),
        ]
    )
    g.add_edges_from([(0, 1), (2, 3)])
    return g


_PUBLIC_FUNCTIONS = [
    crossings.get_crossings,
    crossings.get_crossings_quadratic,
    crossings.number_of_crossings,
    crossings.crossing_density,
    crossings.crossing_angular_resolution,
    crossings.planarize,
]


class TestCrossingFunctionsDoNotLeakTheirPrecision:

    @pytest.mark.parametrize("function", _PUBLIC_FUNCTIONS, ids=lambda f: f.__name__)
    def test_given_precision(self, function):
        with numeric.precision_context(1e-6):
            function(_crossing_drawing(), precision=0.1)
            assert numeric.get_precision() == 1e-6

    @pytest.mark.parametrize("function", _PUBLIC_FUNCTIONS, ids=lambda f: f.__name__)
    def test_default_precision(self, function):
        with numeric.precision_context(1e-6):
            function(_crossing_drawing())
            assert numeric.get_precision() == 1e-6

    def test_later_comparisons_are_unaffected(self):
        crossings.get_crossings(_crossing_drawing(), precision=0.1)

        assert not numeric.numeric_eq(0, 0.05)

    @pytest.mark.parametrize("quadratic", [False, True])
    def test_the_given_precision_is_applied(self, quadratic):
        g = nx.Graph()
        # Node 2 lies 0.05 off edge (0, 1): on it at precision 0.1, apart from it at 1e-9
        g.add_nodes_from(
            [
                (0, {"pos": (0, 0)}),
                (1, {"pos": (2, 0)}),
                (2, {"pos": (1, 0.05)}),
                (3, {"pos": (1, 2)}),
            ]
        )
        g.add_edges_from([(0, 1), (2, 3)])

        def count(**kwargs):
            return crossings.number_of_crossings(
                g,
                include_node_crossings=True,
                use_quadratic_algorithm=quadratic,
                **kwargs,
            )

        assert count(precision=0.1) == 1
        assert count() == 0
