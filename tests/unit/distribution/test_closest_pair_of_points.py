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
import unittest
import random

import networkx as nx

# noinspection PyUnresolvedReferences
import pytest

# noinspection PyUnresolvedReferences
import pytest_socket

from gdMetriX import distribution


def brute_force_closest(pos):
    """ Slow reference implementation of closest pair of points for testing purposes """
    pts = list(pos.items())
    best = None
    pair = None
    for i in range(len(pts)):
        for j in range(i + 1, len(pts)):
            (ki, (xi, yi)) = pts[i]
            (kj, (xj, yj)) = pts[j]
            d = math.hypot(xi - xj, yi - yj)
            if best is None or d < best:
                best = d
                pair = (ki, kj)
    return pair, best


def assert_matches_bruteforce(testcase, g):
    """ Assert that the closest pair of points found by the efficient algorithm is the same as the brute-force one """
    a, b, d = distribution.closest_pair_of_points(g)
    print(a, b, d)
    pos = {n: g.nodes[n]["pos"] for n in g.nodes}
    (p, q), ref = brute_force_closest(pos)
    print(p, q, ref)
    testcase.assertAlmostEqual(d, ref, places=9)


class TestClosestPairOfPoints(unittest.TestCase):

    def test_empty_graph(self):
        g = nx.Graph()

        closest_pair = distribution.closest_pair_of_points(g)
        assert closest_pair == (None, None, None)

    def test_singleton(self):
        g = nx.Graph()
        g.add_node(0, pos=(1, 4))

        closest_pair = distribution.closest_pair_of_points(g)
        assert closest_pair == (None, None, None)

    def test_simple_pair(self):
        g = nx.Graph()
        g.add_node(0, pos=(0, 0))
        g.add_node(1, pos=(3, 4))

        closest_pair = distribution.closest_pair_of_points(g)
        assert closest_pair == (1, 0, 5.0) or closest_pair == (0, 1, 5.0)

    def test_grid(self):
        g = nx.Graph()
        grid_size = 50
        for i in range(0, grid_size):
            for j in range(0, grid_size):
                g.add_node(grid_size * i + j, pos=(i, j))

        g.add_node(grid_size * grid_size, pos=(0.4, 0.4))

        closest_pair = distribution.closest_pair_of_points(g)

        assert closest_pair[0] == 0 or closest_pair[1] == 0
        assert closest_pair[1] == grid_size ** 2 or closest_pair[1] == grid_size ** 2
        assert closest_pair[0] != closest_pair[1]
        assert math.isclose(closest_pair[2], math.sqrt((0.4 ** 2) * 2))

    def test_node_pair(self):
        g = nx.Graph()
        g.add_node(1, pos=(0, 3))
        g.add_node(2, pos=(4, 0))

        a, b, distance = distribution.closest_pair_of_points(g)

        assert a == 1 or a == 2
        assert b == 1 or b == 2
        assert a != b
        assert distance == 5

    def test_same_x_position(self):
        g = nx.Graph()
        g.add_node(1, pos=(0, 1))
        g.add_node(2, pos=(0, 2))
        g.add_node(3, pos=(0, 4))
        g.add_node(4, pos=(0, 8))
        g.add_node(5, pos=(0, 16))

        a, b, distance = distribution.closest_pair_of_points(g)

        assert a == 1 or a == 2
        assert b == 1 or b == 2
        assert a != b
        assert distance == 1

    def test_same_y_position(self):
        g = nx.Graph()
        g.add_node(1, pos=(1, 0))
        g.add_node(2, pos=(2, 0))
        g.add_node(3, pos=(4, 0))
        g.add_node(4, pos=(8, 0))
        g.add_node(5, pos=(16, 0))

        a, b, distance = distribution.closest_pair_of_points(g)

        assert a == 1 or a == 2
        assert b == 1 or b == 2
        assert a != b
        assert distance == 1

    def test_small_graph(self):
        g = nx.Graph()
        g.add_node(1, pos=(0, 0))
        g.add_node(2, pos=(3, 1))
        g.add_node(3, pos=(1, 2))
        g.add_node(4, pos=(3, 3))
        g.add_node(5, pos=(2, 4))
        g.add_node(6, pos=(0, 4))

        a, b, distance = distribution.closest_pair_of_points(g)

        assert a == 4 or a == 5
        assert b == 4 or b == 5
        assert a != b
        assert distance == math.sqrt(2)

    def test_bruteforce_regression(self):
        g = nx.Graph()
        g.add_node(0, pos=(0, 0))
        g.add_node(1, pos=(100, 0))
        g.add_node(2, pos=(1, 0))  # closest is 0–2
        assert_matches_bruteforce(self, g)

    def test_split_pair(self):
        g = nx.Graph()
        pts = [(-1, 0), (-1, 2), (-1, 4), (1, 1), (1, 3), (1, 5)]
        for i, p in enumerate(pts):
            g.add_node(i, pos=p)
        assert_matches_bruteforce(self, g)

    def test_points_on_median(self):
        g = nx.Graph()
        pts = [(0, 0), (0, 1), (0, 2), (0, 3), (1, 1.4)]
        for i, p in enumerate(pts):
            g.add_node(i, pos=p)
        assert_matches_bruteforce(self, g)

    def test_duplicates(self):
        g = nx.Graph()
        pts = [(1, 1), (2, 2), (1, 1), (5, 5)]
        for i, p in enumerate(pts):
            g.add_node(i, pos=p)
        assert_matches_bruteforce(self, g)

    def test_precision(self):
        g = nx.Graph()
        g.add_node(0, pos=(0, 0))
        g.add_node(1, pos=(1e-12, 0))
        g.add_node(2, pos=(1, 1))
        assert_matches_bruteforce(self, g)

    def test_random(self):
        for _ in range(100):
            g = nx.Graph()
            for i in range(30):
                g.add_node(i, pos=(random.random(), random.random()))
            assert_matches_bruteforce(self, g)
