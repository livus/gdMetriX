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

import networkx as nx

# noinspection PyUnresolvedReferences
import pytest

# noinspection PyUnresolvedReferences
import pytest_socket

from gdMetriX import distribution


class TestGabrielRatio(object):

    def test_empty_graph(self):
        g = nx.Graph()

        ratio = distribution.gabriel_ratio(g)
        assert ratio == 1

    def test_singleton(self):
        g = nx.Graph()
        g.add_node(0, pos=(1, 4))

        ratio = distribution.gabriel_ratio(g)
        assert ratio == 1

    def test_simple_pair(self):
        g = nx.Graph()
        g.add_node(0, pos=(0, 0))
        g.add_node(1, pos=(3, 4))
        g.add_edge(0, 1)

        ratio = distribution.gabriel_ratio(g)
        assert ratio == 1

    def test_node_outside_circle(self):
        g = nx.Graph()
        g.add_node(1, pos=(0, 0))
        g.add_node(2, pos=(1, 0))
        g.add_node(3, pos=(-0.5, 0.5))
        g.add_edge(1, 2)

        ratio = distribution.gabriel_ratio(g)
        assert ratio == 1

    def test_node_on_circle(self):
        g = nx.Graph()
        g.add_node(1, pos=(0, 0))
        g.add_node(2, pos=(1, 0))
        g.add_node(3, pos=(0.5, 1))
        g.add_edge(1, 2)

        ratio = distribution.gabriel_ratio(g)
        assert ratio == 1

    def test_node_inside_circle(self):
        g = nx.Graph()
        g.add_node(1, pos=(0, 0))
        g.add_node(2, pos=(1, 0))
        g.add_node(3, pos=(0.5, 0.45))
        g.add_edge(1, 2)

        ratio = distribution.gabriel_ratio(g)
        assert ratio == 0

    def test_one_inside_one_outside(self):
        g = nx.Graph()
        g.add_node(1, pos=(0, 0))
        g.add_node(2, pos=(1, 0))
        g.add_node(3, pos=(0.5, 0.45))
        g.add_node(4, pos=(-0.5, 0.5))
        g.add_edge(1, 2)

        ratio = distribution.gabriel_ratio(g)
        assert ratio == 0.5

    def test_triangle_two_edges_one_violation(self):
        g = nx.Graph()
        g.add_node(1, pos=(0, 0))
        g.add_node(2, pos=(1, 0))
        g.add_node(3, pos=(0.5, 0.1))

        g.add_edge(1, 2)
        g.add_edge(1, 3)

        assert distribution.gabriel_ratio(g) == pytest.approx(0)

    def test_equilateral_triangle_all_edges(self):
        g = nx.Graph()
        g.add_node(1, pos=(0, 0))
        g.add_node(2, pos=(1, 0))
        g.add_node(3, pos=(0.5, math.sqrt(3) / 2))
        g.add_edges_from([(1, 2), (2, 3), (3, 1)])

        assert distribution.gabriel_ratio(g) == 1

    def test_triangle_all_edges_all_violated(self):
        g = nx.Graph()
        g.add_node(1, pos=(0, 0))
        g.add_node(2, pos=(1, 0))
        g.add_node(3, pos=(0.5, 0.05))

        g.add_edges_from([(1, 2), (2, 3), (1, 3)])

        assert distribution.gabriel_ratio(g) == 0

    def test_shallow_triangle(self):
        g = nx.Graph()
        g.add_node(1, pos=(0, 0))
        g.add_node(2, pos=(1, 0))
        g.add_node(3, pos=(0.5, 0.1))

        g.add_edge(1, 2)
        g.add_edge(1, 3)

        assert distribution.gabriel_ratio(g) == 0

    def test_multiple_edges(self):
        g = nx.Graph()
        g.add_node(1, pos=(0, 0))
        g.add_node(2, pos=(1, 0))
        g.add_node(3, pos=(0.5, 0.45))
        g.add_node(4, pos=(-0.5, 0.5))
        g.add_node(5, pos=(-1000, -1000))
        g.add_node(6, pos=(-800, -700))
        g.add_edge(1, 2)
        g.add_edge(5, 6)

        ratio = distribution.gabriel_ratio(g)
        assert ratio == 7 / 8

    @pytest.mark.parametrize("graph_size", [10, 50, 100, 150])
    def test_large_graph(self, graph_size):
        random.seed(9348092123)

        g = nx.Graph()

        for i in range(0, graph_size):
            g.add_node(i, pos=(random.uniform(0, 1000), random.uniform(0, 1000)))

            for j in range(0, i):
                if random.random() > 0.5:
                    g.add_edge(j, i)

        ratio = distribution.gabriel_ratio(g)

        assert 0 <= ratio <= 1

    def test_points_on_boundary_are_not_violations(self):
        g = nx.Graph()
        g.add_node(1, pos=(0, 0))
        g.add_node(2, pos=(2, 0))
        g.add_edge(1, 2)

        # Points exactly on the circle
        for i in range(3, 20):
            angle = i * 0.3
            x = 1 + math.cos(angle)
            y = math.sin(angle)
            g.add_node(i, pos=(x, y))

        ratio = distribution.gabriel_ratio(g)
        assert ratio == 1

    def test_normalization_independent_of_geometry(self):
        g = nx.Graph()

        g.add_node("A", pos=(0, 0))
        g.add_node("B", pos=(2, 0))
        g.add_node("C", pos=(100, 100))
        g.add_node("D", pos=(-100, -100))

        g.add_edge("A", "B")

        r1 = distribution.gabriel_ratio(g)

        # Move C and D inside the circle
        g.nodes["C"]["pos"] = (1, 0.1)
        g.nodes["D"]["pos"] = (1, -0.1)

        r2 = distribution.gabriel_ratio(g)

        # geometry changes violations, but denominator must not change
        assert r2 < r1
        assert r2 >= 0

    def test_edges_are_independent(self):
        g = nx.Graph()

        # First edge violated
        g.add_node("A", pos=(0, 0))
        g.add_node("B", pos=(2, 0))
        g.add_node("C", pos=(1, 0))

        g.add_edge("A", "B")

        # Second edge not violated
        g.add_node("D", pos=(10, 10))
        g.add_node("E", pos=(12, 10))
        g.add_edge("D", "E")

        ratio = distribution.gabriel_ratio(g)

        # One violated edge, one clean edge → ratio must be between 0 and 1
        assert 0 < ratio < 1

    def test_collinear_points_on_diameter(self):
        g = nx.Graph()
        g.add_node(1, pos=(0, 0))
        g.add_node(2, pos=(10, 0))
        g.add_edge(1, 2)

        for i in range(1, 9):
            g.add_node(100 + i, pos=(i, 0))

        ratio = distribution.gabriel_ratio(g)

        # all interior → full violation
        assert ratio == 0

    def test_random_graph_invariants(self):
        random.seed(1234)

        for _ in range(20):
            g = nx.Graph()
            n = random.randint(5, 30)

            for i in range(n):
                g.add_node(i, pos=(random.random(), random.random()))

            for i in range(n):
                for j in range(i + 1, n):
                    if random.random() < 0.3:
                        g.add_edge(i, j)

            ratio = distribution.gabriel_ratio(g)
            assert 0 <= ratio <= 1
