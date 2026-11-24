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
Tests for :func:`gdMetriX.crossings.has_crossings`, which stops at the first crossing it finds: it
must be true exactly when :func:`gdMetriX.crossings.get_crossings_quadratic` finds at least one
crossing, and the crossing it stops at (see ``crossings._first_crossing``) must be one the full
search reports as well.
"""

import random

import networkx as nx
import pytest

from gdMetriX import crossings, distribution
from gdMetriX.crossings import _quadratic


def _drawing(points, edges, singletons=()):
    g = nx.Graph()
    for node, position in points.items():
        g.add_node(node, pos=position)
    g.add_edges_from(edges)
    for node, position in singletons:
        g.add_node(node, pos=position)
    return g


def _random_drawings(seed, count):
    rng = random.Random(seed)
    for _ in range(count):
        kind = rng.choice(["grid", "grid", "float", "singletons"])
        n = rng.randint(2, 14)
        g = nx.fast_gnp_random_graph(n, rng.uniform(0.1, 0.9), rng.randint(1, 10**8))
        if kind == "float":
            positions = {v: (rng.uniform(-5, 5), rng.uniform(-5, 5)) for v in g}
        else:
            r = rng.choice([1, 2, 3])
            positions = {v: (rng.randint(-r, r), rng.randint(-r, r)) for v in g}
        nx.set_node_attributes(g, positions, "pos")

        kwargs = {"include_node_crossings": rng.random() < 0.5}
        if kind == "singletons":
            for k in range(rng.randint(1, 3)):
                g.add_node(f"s{k}", pos=(rng.randint(-2, 2), rng.randint(-2, 2)))
            kwargs = {"include_node_crossings": True, "consider_singletons": True}
        yield g, kwargs


def _assert_consistent(g, **kwargs):
    full = crossings.get_crossings_quadratic(g, **kwargs)
    found = crossings._first_crossing(g, **kwargs)

    assert crossings.has_crossings(g, **kwargs) == bool(full)
    assert (found is not None) == bool(full)

    if found is not None:
        assert len(found) > 1
        # The crossing is one the full search reports too: at the same position, with (a part of)
        # the same edges and isolated nodes
        assert any(
            # CrossingLine.__eq__ cannot compare with a point, so compare like with like
            type(found.pos) is type(crossing.pos)
            and found.pos == crossing.pos
            and found.involved_edges <= crossing.involved_edges
            and found.involved_singletons <= crossing.involved_singletons
            for crossing in full
        )


class TestHasCrossingsAgreesWithTheFullSearch:

    @pytest.mark.parametrize("seed", range(6))
    def test_random_drawings(self, seed):
        for g, kwargs in _random_drawings(seed, 80):
            _assert_consistent(g, **kwargs)

    @pytest.mark.parametrize("seed", range(3))
    def test_random_drawings_with_broad_phase(self, monkeypatch, seed):
        monkeypatch.setattr(_quadratic, "BROAD_PHASE_MIN_EDGES", 0)
        for g, kwargs in _random_drawings(100 + seed, 60):
            _assert_consistent(g, **kwargs)


class TestHasCrossingsCases:

    def test_no_crossing(self):
        g = _drawing({0: (0, 0), 1: (1, 0), 2: (0, 1), 3: (1, 1)}, [(0, 1), (2, 3)])
        assert not crossings.has_crossings(g)
        assert crossings._first_crossing(g) is None

    def test_proper_crossing(self):
        g = _drawing({0: (0, 0), 1: (2, 2), 2: (0, 2), 3: (2, 0)}, [(0, 1), (2, 3)])
        assert crossings.has_crossings(g)
        assert crossings._first_crossing(g).involved_edges == {(0, 1), (2, 3)}

    def test_several_crossings(self):
        g = _drawing(
            {0: (0, 0), 1: (4, 4), 2: (0, 4), 3: (4, 0), 4: (0, 2), 5: (4, 2)},
            [(0, 1), (2, 3), (4, 5)],
        )
        assert crossings.has_crossings(g)

    def test_empty_graph(self):
        assert not crossings.has_crossings(nx.Graph())

    def test_positions_given_separately(self):
        g = nx.Graph([(0, 1), (2, 3)])
        pos = {0: (0, 0), 1: (2, 2), 2: (0, 2), 3: (2, 0)}
        assert crossings.has_crossings(g, pos)

    def test_does_not_leak_its_precision(self):
        from gdMetriX.utils import numeric

        before = numeric.get_precision()
        g = _drawing({0: (0, 0), 1: (2, 2), 2: (0, 2), 3: (2, 0)}, [(0, 1), (2, 3)])
        crossings.has_crossings(g, precision=0.1)
        assert numeric.get_precision() == before

    @pytest.mark.parametrize(
        "graph", [nx.MultiGraph(), None], ids=["multigraph", "none"]
    )
    def test_invalid_graph(self, graph):
        with pytest.raises(ValueError):
            crossings.has_crossings(graph)

    def test_singletons_need_node_crossings(self):
        with pytest.raises(ValueError):
            crossings.has_crossings(nx.Graph(), consider_singletons=True)

    @pytest.mark.parametrize("include_node_crossings", [False, True])
    def test_endpoint_on_an_edge(self, include_node_crossings):
        # Node 2 lies on edge (0, 1): a crossing only with include_node_crossings
        g = _drawing({0: (0, 0), 1: (2, 0), 2: (1, 0), 3: (1, 2)}, [(0, 1), (2, 3)])
        assert (
            crossings.has_crossings(g, include_node_crossings=include_node_crossings)
            == include_node_crossings
        )
        _assert_consistent(g, include_node_crossings=include_node_crossings)

    def test_adjacent_edges_do_not_cross(self):
        g = _drawing({0: (0, 0), 1: (1, 1), 2: (2, 0)}, [(0, 1), (1, 2)])
        assert not crossings.has_crossings(g)

    def test_overlapping_edges(self):
        g = _drawing({0: (0, 0), 1: (2, 0), 2: (1, 0), 3: (3, 0)}, [(0, 1), (2, 3)])
        assert crossings.has_crossings(g)
        assert isinstance(crossings._first_crossing(g).pos, crossings.CrossingLine)

    def test_isolated_node_on_an_edge(self):
        # Found by continuing the search, as no pair of edges crosses
        g = _drawing({0: (0, 0), 1: (2, 0)}, [(0, 1)], singletons=[("s", (1, 0))])
        kwargs = {"include_node_crossings": True, "consider_singletons": True}
        assert crossings.has_crossings(g, **kwargs)
        assert crossings._first_crossing(g, **kwargs).involved_singletons == {"s"}


class TestClosestPairOfElementsWithCrossings:

    def test_returns_two_crossing_edges(self):
        g = _drawing({0: (0, 0), 1: (2, 2), 2: (0, 2), 3: (2, 0)}, [(0, 1), (2, 3)])
        a, b, distance = distribution.closest_pair_of_elements(
            g, consider_crossings=True
        )
        assert {a, b} == {(0, 1), (2, 3)}
        assert distance == 0

    def test_without_crossings(self):
        g = _drawing({0: (0, 0), 1: (2, 0), 2: (0, 1), 3: (2, 1)}, [(0, 1), (2, 3)])
        a, b, distance = distribution.closest_pair_of_elements(
            g, consider_crossings=True
        )
        assert distance == pytest.approx(1)
