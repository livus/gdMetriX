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
    Unit tests for the crossing metric.
"""

import random
import unittest

import networkx as nx
# noinspection PyUnresolvedReferences
import pytest

from gdMetriX import crossings


class TestMaxCrossingNumber(unittest.TestCase):
    def test_empty_graph(self):
        g = nx.Graph()

        c_max = crossings._c_max(g, False)
        assert c_max == 0

    def test_singleton(self):
        g = nx.Graph()
        g.add_node(1)

        c_max = crossings._c_max(g, False)
        assert c_max == 0

    def test_singletons(self):
        g = nx.Graph()
        for i in range(0, 100):
            g.add_node(i)

        c_max = crossings._c_max(g, False)
        assert c_max == 0

    def test_single_edges(self):
        g = nx.Graph()
        for i in range(0, 100):
            g.add_node(i)
            g.add_node(i + 0.5)
            g.add_edge(i, i + 0.5)

        c_max = crossings._c_max(g, False)
        assert c_max == 9900 / 2

    def test_triangle(self):
        g = nx.Graph()
        g.add_node(1)
        g.add_node(2)
        g.add_node(3)
        g.add_edge(1, 2)
        g.add_edge(2, 3)
        g.add_edge(3, 1)

        c_max = crossings._c_max(g, False)
        assert c_max == 0

    def test_triangles(self):
        g = nx.Graph()
        for i in range(0, 20):
            g.add_node(i + 0.1)
            g.add_node(i + 0.2)
            g.add_node(i + 0.3)
            g.add_edge(i + 0.1, i + 0.2)
            g.add_edge(i + 0.2, i + 0.3)
            g.add_edge(i + 0.3, i + 0.1)

        # Each pair of triangles can only cross six times => n choose 2 * 6
        c_max = crossings._c_max(g, False)

        assert c_max == 1710

    def test_triangles_sharing_edge(self):
        g = nx.Graph()
        g.add_node(1)
        g.add_node(2)
        g.add_node(3)
        g.add_node(4)
        g.add_edge(1, 2)
        g.add_edge(2, 3)
        g.add_edge(3, 1)
        g.add_edge(1, 4)
        g.add_edge(2, 4)

        c_max = crossings._c_max(g, False)
        assert c_max == 2

    def test_triangles_sharing_node(self):
        g = nx.Graph()
        g.add_node(1)
        g.add_node(2)
        g.add_node(3)
        g.add_node(4)
        g.add_node(5)
        g.add_edge(1, 2)
        g.add_edge(2, 3)
        g.add_edge(3, 1)
        g.add_edge(1, 4)
        g.add_edge(4, 5)
        g.add_edge(1, 5)

        c_max = crossings._c_max(g, False)
        assert c_max == 5

    def test_adjacent_edges(self):
        g = nx.Graph()
        g.add_node(1)
        g.add_node(2)
        g.add_node(3)
        g.add_edge(1, 2)
        g.add_edge(1, 3)

        c_max = crossings._c_max(g, False)
        assert c_max == 0

    def test_4cycle(self):
        g = nx.Graph()
        g.add_node(1)
        g.add_node(2)
        g.add_node(3)
        g.add_node(4)
        g.add_edge(1, 2)
        g.add_edge(2, 3)
        g.add_edge(3, 4)
        g.add_edge(4, 1)

        c_max = crossings._c_max(g, False)
        assert c_max == 2

    def test_digraph(self):
        g = nx.DiGraph()
        g.add_node(1)
        g.add_node(2)
        g.add_node(3)
        g.add_edge(1, 2)
        g.add_edge(2, 3)
        g.add_edge(3, 1)

        c_max = crossings._c_max(g, False)
        assert c_max == 0


class TestNumberCrossings(unittest.TestCase):

    def test_empty_graph(self):
        g = nx.Graph()

        n_crossings = crossings.number_of_crossings(g)
        assert n_crossings == 0

    def test_singleton(self):
        g = nx.Graph()
        g.add_node(1, pos=(0, 0))

        n_crossings = crossings.number_of_crossings(g)
        assert n_crossings == 0

    def test_single_crossing(self):
        g = nx.Graph()
        g.add_node(1, pos=(-1, 0))
        g.add_node(2, pos=(1, 0))
        g.add_node(3, pos=(0, 1))
        g.add_node(4, pos=(0, -1))

        g.add_edge(1, 2)
        g.add_edge(3, 4)

        n_crossings = crossings.number_of_crossings(g)
        assert n_crossings == 1

    def test_two_crossings_on_same_edge(self):
        g = nx.Graph()
        g.add_node(1, pos=(-1, 0))
        g.add_node(2, pos=(1, 0))
        g.add_node(3, pos=(0, 1))
        g.add_node(4, pos=(0, -1))
        g.add_node(5, pos=(0.5, 1))
        g.add_node(6, pos=(0.5, -1))

        g.add_edge(1, 2)
        g.add_edge(3, 4)
        g.add_edge(5, 6)

        n_crossings = crossings.number_of_crossings(g)
        assert n_crossings == 2

    def test_multiple_edges_crossing_in_same_point(self):
        g = nx.Graph()
        g.add_node(1, pos=(-1, 0))
        g.add_node(2, pos=(1, 0))
        g.add_node(3, pos=(0, 1))
        g.add_node(4, pos=(0, -1))
        g.add_node(5, pos=(1, 1))
        g.add_node(6, pos=(-1, -1))

        g.add_edge(1, 2)
        g.add_edge(3, 4)
        g.add_edge(5, 6)

        n_crossings = crossings.number_of_crossings(g)
        assert n_crossings == 3

    def test_multiple_edges_crossing_in_same_point_2(self):
        g = nx.Graph()
        g.add_node(1, pos=(-1, 0))
        g.add_node(2, pos=(1, 0))
        g.add_node(3, pos=(0, 1))
        g.add_node(4, pos=(0, -1))
        g.add_node(5, pos=(1, 1))
        g.add_node(6, pos=(-1, -1))
        g.add_node(7, pos=(1, -1))
        g.add_node(8, pos=(-1, 1))

        g.add_edge(1, 2)
        g.add_edge(3, 4)
        g.add_edge(5, 6)
        g.add_edge(7, 8)

        n_crossings = crossings.number_of_crossings(g)
        assert n_crossings == 6


class TestCrossingMetric(unittest.TestCase):
    def test_empty_graph(self):
        g = nx.Graph()

        metric = crossings.crossing_density(g)
        assert metric == 1

    def test_singleton(self):
        g = nx.Graph()
        g.add_node(1, pos=(0, 0))

        metric = crossings.crossing_density(g)
        assert metric == 1

    def test_random_graph(self):
        random.seed(943123)
        for i in range(0, 16):
            random_graph = nx.fast_gnp_random_graph(i, random.uniform(0.1, 1), random.randint(1, 10000000))
            random_embedding = {n: [random.randint(-100, 100), random.randint(-100, 100)] for n in range(0, i + 1)}
            nx.set_node_attributes(random_graph, random_embedding, "pos")

            metric = crossings.crossing_density(random_graph)
            assert 0 <= metric <= 1
