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
    Unittests for visual symmetry
"""

import math
import random
import unittest

import networkx as nx
# noinspection PyUnresolvedReferences
import pytest
# noinspection PyUnresolvedReferences
import pytest_socket

from gdMetriX import symmetry as sym


class TestInHouseSymmetry(unittest.TestCase):

    def test_empty_graph(self):
        g = nx.Graph()
        symmetry = sym.visual_symmetry(g)
        print(symmetry)
        assert symmetry == 1

    def test_single_node(self):
        g = nx.Graph()
        symmetry = sym.visual_symmetry(g)
        g.add_node(1, pos=(123, -45))
        print(symmetry)
        assert symmetry == 1

    def test_cycle_close_to_one(self):
        g = nx.Graph()

        for i in range(0, 360):
            g.add_node(i, pos=(math.sin(math.radians(i)), math.cos(math.radians(i))))

        symmetry = sym.visual_symmetry(g)
        print(symmetry)
        assert symmetry > 0.95

    def test_cycle_with_edges_close_to_one(self):
        g = nx.Graph()

        for i in range(0, 360):
            g.add_node(i, pos=(math.sin(math.radians(i)), math.cos(math.radians(i))))
            if i < 360 - 1:
                g.add_edge(i, i + 1)

        symmetry = sym.visual_symmetry(g)
        print(symmetry)
        assert symmetry > 0.95

    def test_rectangle_close_to_one(self):
        g = nx.Graph()

        for i in range(50):
            g.add_node(i, pos=(0, i))
            g.add_node(i + 50, pos=(50, i))

        for i in range(50):
            g.add_node(i + 100, pos=(i, 0))
            g.add_node(i + 150, pos=(i, 50))

        symmetry = sym.visual_symmetry(g)
        print(symmetry)
        assert symmetry > 0.95

    def test_simple_rectangle_close_to_one(self):
        g = nx.Graph()

        g.add_node(1, pos=(-1, -1))
        g.add_node(2, pos=(-1, 1))
        g.add_node(3, pos=(1, 1))
        g.add_node(4, pos=(1, -1))
        g.add_edges_from([(1, 2), (2, 3), (3, 4), (4, 1)])

        symmetry = sym.visual_symmetry(g)
        print(symmetry)
        assert symmetry > 0.95

    def test_big_random_graph_undirected_is_deterministic(self):
        graph_size = 100
        random.seed(2308590348590)
        g = nx.fast_gnp_random_graph(graph_size, 0.5, 30219490182903)
        random_embedding = {n: [random.randint(-10000, 10000), random.randint(-10000, 10000)] for n in
                            range(0, graph_size + 1)}
        symmetry_a = sym.visual_symmetry(g, random_embedding)
        symmetry_b = sym.visual_symmetry(g, random_embedding)
        print(symmetry_a)
        print(symmetry_b)
        print(symmetry_a - symmetry_b)
        assert abs(symmetry_a - symmetry_b) < 1e-08

    def test_big_random_graph_directed_is_deterministic(self):
        graph_size = 25
        random.seed(9132809123)
        g = nx.fast_gnp_random_graph(graph_size, 0.5, 2348923409890890123, True)
        random_embedding = {n: [random.randint(-10000, 10000), random.randint(-10000, 10000)] for n in
                            range(0, graph_size + 1)}

        symmetry_a = sym.visual_symmetry(g, random_embedding)
        symmetry_b = sym.visual_symmetry(g, random_embedding)
        print(symmetry_a)
        print(symmetry_b)
        print(symmetry_a - symmetry_b)
        assert abs(symmetry_a - symmetry_b) < 1e-08

    def test_stress_test_is_in_range(self):

        random.seed(124912399123)

        for i in range(1, 10):
            graph_size = random.randint(10, 64)
            print(i)
            print(graph_size)
            g = nx.fast_gnp_random_graph(graph_size, 0.5, 2348923409890890123, True)
            random_embedding = {n: [random.randint(-10000, 10000), random.randint(-10000, 10000)] for n in
                                range(0, graph_size + 1)}

            symmetry = sym.visual_symmetry(g, random_embedding)

            print(symmetry)

            assert 0 <= symmetry <= 1
