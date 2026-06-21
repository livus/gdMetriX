# gdMetriX
#
# Copyright (C) 2024  Martin Nöllenburg, Sebastian Röder, Markus Wallinger
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
Unittests for distribution.py
"""

import math
import random
import unittest
import sys

import networkx as nx

# noinspection PyUnresolvedReferences
import pytest

# noinspection PyUnresolvedReferences
import pytest_socket

from gdMetriX import distribution, common


def _brute_force_closest_pair_of_elements(g, pos):
    """ Slow O(n*m) reference implementation, mirroring the loop closest_pair_of_elements used to use """
    best = None
    best_pair = (None, None)

    nodes = list(g.nodes())
    for i in range(len(nodes)):
        for j in range(i + 1, len(nodes)):
            a, b = nodes[i], nodes[j]
            d = math.dist(pos[a], pos[b])
            if best is None or d < best:
                best = d
                best_pair = (a, b)

    for edge in g.edges():
        for node in g.nodes():
            if node in edge:
                continue
            d = common.LineSegment(
                common.Vector.from_point(pos[edge[0]]),
                common.Vector.from_point(pos[edge[1]]),
            ).distance_to_point(common.Vector.from_point(pos[node]))
            if best is None or d < best:
                best = d
                best_pair = (node, edge)

    return best_pair, best


def _assert_matches_bruteforce(testcase, g):
    pos = nx.get_node_attributes(g, "pos")
    a, b, d = distribution.closest_pair_of_elements(g)
    _, ref = _brute_force_closest_pair_of_elements(g, pos)
    testcase.assertAlmostEqual(d, ref, places=9)


class TestClosestPairOfGraphElements(unittest.TestCase):

    def test_empty_graph(self):
        g = nx.Graph()

        closest_pair = distribution.closest_pair_of_elements(g)
        assert closest_pair == (None, None, None)

    def test_singleton(self):
        g = nx.Graph()
        g.add_node(0, pos=(1, 4))

        closest_pair = distribution.closest_pair_of_elements(g)
        assert closest_pair == (None, None, None)

    def test_simple_pair(self):
        g = nx.Graph()
        g.add_node(0, pos=(0, 0))
        g.add_node(1, pos=(3, 4))
        g.add_edge(0, 1)

        closest_pair = distribution.closest_pair_of_elements(g)
        assert closest_pair == (1, 0, 5.0) or closest_pair == (0, 1, 5.0)

    def test_node_closer_to_endpoint_a(self):
        g = nx.Graph()
        g.add_node(1, pos=(0, 0))
        g.add_node(2, pos=(1, 0))
        g.add_node(3, pos=(-0.5, 0.5))
        g.add_edge(1, 2)

        closest_pair = distribution.closest_pair_of_elements(g)

        assert closest_pair[0] == 1 or closest_pair[1] == 1
        assert closest_pair[0] == 3 or closest_pair[1] == 3
        assert math.isclose(closest_pair[2], math.sqrt(0.5))

    def test_node_closer_to_edge_itself(self):
        g = nx.Graph()
        g.add_node(1, pos=(0, 0))
        g.add_node(2, pos=(1, 0))
        g.add_node(3, pos=(0.5, 0.5))
        g.add_edge(1, 2)

        closest_pair = distribution.closest_pair_of_elements(g)

        assert closest_pair[0] == (1, 2) or closest_pair[1] == (1, 2)
        assert closest_pair[0] == 3 or closest_pair[1] == 3
        assert math.isclose(closest_pair[2], 0.5)

    def test_node_closer_to_endpoint_b(self):
        g = nx.Graph()
        g.add_node(1, pos=(0, 0))
        g.add_node(2, pos=(1, 0))
        g.add_node(3, pos=(1.5, -0.5))
        g.add_edge(1, 2)

        closest_pair = distribution.closest_pair_of_elements(g)

        assert closest_pair[0] == 2 or closest_pair[1] == 2
        assert closest_pair[0] == 3 or closest_pair[1] == 3
        assert math.isclose(closest_pair[2], math.sqrt(0.5))

    def test_long_edge(self):
        g = nx.Graph()
        g.add_node(1, pos=(-1000, -1000))
        g.add_node(2, pos=(1000, 1000))
        g.add_node(3, pos=(-1, 1))
        g.add_edge(1, 2)

        closest_pair = distribution.closest_pair_of_elements(g)

        assert closest_pair[0] == (1, 2) or closest_pair[1] == (1, 2)
        assert closest_pair[0] == 3 or closest_pair[1] == 3
        assert math.isclose(closest_pair[2], math.sqrt(2))

    def test_vertical_edge(self):
        # Vertical edges have no well-defined y-at-x and are handled as a special case
        g = nx.Graph()
        g.add_node(1, pos=(0, 0))
        g.add_node(2, pos=(0, 10))
        g.add_node(3, pos=(0.5, 5))
        g.add_edge(1, 2)

        closest_pair = distribution.closest_pair_of_elements(g)

        assert closest_pair[0] == (1, 2) or closest_pair[1] == (1, 2)
        assert closest_pair[0] == 3 or closest_pair[1] == 3
        assert math.isclose(closest_pair[2], 0.5)

    def test_horizontal_edge(self):
        g = nx.Graph()
        g.add_node(1, pos=(0, 0))
        g.add_node(2, pos=(10, 0))
        g.add_node(3, pos=(5, 0.5))
        g.add_edge(1, 2)

        closest_pair = distribution.closest_pair_of_elements(g)

        assert closest_pair[0] == (1, 2) or closest_pair[1] == (1, 2)
        assert closest_pair[0] == 3 or closest_pair[1] == 3
        assert math.isclose(closest_pair[2], 0.5)

    def test_steep_edge_outside_x_range(self):
        """
        Regression test for the bounding-box active window in _ClosestPairSweep: for a steep
        (near-vertical) edge, the closest point can lie in the segment's *interior* even when the
        query node's x lies outside the edge's [x_min, x_max] range. An implementation that only
        keeps an edge active while the sweep is literally inside its x-range (or that orders the
        active set by a single y-at-x key, as an earlier draft of this algorithm did) would miss
        this entirely.
        """
        g = nx.Graph()
        g.add_node(1, pos=(0, 0))
        g.add_node(2, pos=(1, 1000))  # steep edge: x spans only [0, 1], y spans [0, 1000]
        g.add_edge(1, 2)
        g.add_node(3, pos=(-0.01, 500))  # x lies outside [0, 1], but close to the segment's interior

        closest_pair = distribution.closest_pair_of_elements(g)

        assert closest_pair[0] == (1, 2) or closest_pair[1] == (1, 2)
        assert closest_pair[0] == 3 or closest_pair[1] == 3
        # Ground truth from the already-trusted distance_to_point formula - if the sweep instead
        # reported the distance to the nearest endpoint (~500), this would catch it.
        assert math.isclose(closest_pair[2], 0.5099997450001912)

    def test_duplicate_node_positions(self):
        g = nx.Graph()
        g.add_node(1, pos=(0, 0))
        g.add_node(2, pos=(0, 0))  # exact duplicate position
        g.add_node(3, pos=(100, 100))
        g.add_node(4, pos=(200, 200))
        g.add_edge(3, 4)

        closest_pair = distribution.closest_pair_of_elements(g)

        assert closest_pair[2] == 0.0
        assert {closest_pair[0], closest_pair[1]} == {1, 2}

    def test_node_exactly_on_edge(self):
        g = nx.Graph()
        g.add_node(1, pos=(0, 0))
        g.add_node(2, pos=(10, 0))
        g.add_node(3, pos=(5, 0))  # lies exactly on the edge
        g.add_edge(1, 2)

        closest_pair = distribution.closest_pair_of_elements(g)

        assert math.isclose(closest_pair[2], 0.0, abs_tol=1e-12)
        assert closest_pair[0] == (1, 2) or closest_pair[1] == (1, 2)
        assert closest_pair[0] == 3 or closest_pair[1] == 3

    def test_self_loop(self):
        # A self-loop is a degenerate, zero-length "edge" - distance_to_point already handles
        # zero-length segments, this just checks the sweep doesn't choke on one.
        g = nx.Graph()
        g.add_node(1, pos=(0, 0))
        g.add_node(2, pos=(0.1, 0))
        g.add_edge(1, 1)

        closest_pair = distribution.closest_pair_of_elements(g)

        assert math.isclose(closest_pair[2], 0.1)

    def test_precision_small_distances(self):
        # Mirrors test_precision in test_closest_pair_of_points.py, extended to node-edge pairs
        g = nx.Graph()
        g.add_node(0, pos=(0, 0))
        g.add_node(1, pos=(1e-12, 0))
        g.add_node(2, pos=(1, 1))
        g.add_node(3, pos=(2, 0))
        g.add_edge(2, 3)
        _assert_matches_bruteforce(self, g)

    def test_precision_tiny_cluster(self):
        # All points crammed into a region far smaller than the library's default numeric
        # precision (1e-9) - the true minimum distance must still be found, not snapped to zero.
        g = nx.Graph()
        g.add_node(0, pos=(0, 0))
        g.add_node(1, pos=(1e-13, 0))
        g.add_node(2, pos=(5e-13, 5e-13))
        g.add_node(3, pos=(2e-12, 2e-12))
        g.add_edge(2, 3)
        _assert_matches_bruteforce(self, g)

    def test_large_coordinate_scale_with_tiny_answer(self):
        # A small, precise answer must still be found correctly even with unrelated nodes at a
        # vastly larger coordinate magnitude elsewhere in the same graph.
        g = nx.Graph()
        g.add_node(0, pos=(0.0, 0.0))
        g.add_node(1, pos=(1.0, 0.0))
        g.add_edge(0, 1)
        g.add_node(2, pos=(0.5, 1e-7))
        g.add_node(3, pos=(1e9, 1e9))
        g.add_node(4, pos=(1e9 + 1e6, 1e9 + 1e6))
        _assert_matches_bruteforce(self, g)

    def test_bruteforce_regression(self):
        g = nx.Graph()
        g.add_node(0, pos=(0, 0))
        g.add_node(1, pos=(10, 10))
        g.add_node(2, pos=(0, 10))
        g.add_node(3, pos=(10, 0))
        g.add_node(4, pos=(5, 0.1))
        g.add_edge(0, 1)
        g.add_edge(2, 3)
        _assert_matches_bruteforce(self, g)

    def test_random_small(self):
        random.seed(1)
        for _ in range(200):
            g = nx.gnp_random_graph(10, 0.3, seed=random.randint(0, sys.maxsize))
            for n in g.nodes():
                g.nodes[n]["pos"] = (random.random(), random.random())
            _assert_matches_bruteforce(self, g)

    def test_random_with_vertical_and_horizontal_edges(self):
        random.seed(2)
        for _ in range(200):
            g = nx.gnp_random_graph(10, 0.3, seed=random.randint(0, sys.maxsize))
            xs = [round(random.random(), 1) for _ in range(4)]
            ys = [round(random.random(), 1) for _ in range(4)]
            for n in g.nodes():
                # Snap coordinates onto a coarse grid so vertical/horizontal edges occur frequently
                g.nodes[n]["pos"] = (random.choice(xs), random.choice(ys))
            _assert_matches_bruteforce(self, g)

    def test_random_bigger(self):
        random.seed(3)
        for _ in range(20):
            g = nx.gnp_random_graph(40, 0.2, seed=random.randint(0, sys.maxsize))
            for n in g.nodes():
                g.nodes[n]["pos"] = (random.random(), random.random())
            _assert_matches_bruteforce(self, g)
