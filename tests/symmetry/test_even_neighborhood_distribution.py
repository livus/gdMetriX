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
    Unit tests for the Force-based symmetry metric
"""

import math
import random
import unittest

import networkx as nx
# noinspection PyUnresolvedReferences
import pytest

from gdMetriX import symmetry as sym


class TestEvenNeighborhoodDistribution(unittest.TestCase):

    def test_empty_graph(self):
        g = nx.Graph()
        symmetry = sym.even_neighborhood_distribution(g)
        print(symmetry)
        assert symmetry == 1

    def test_single_node(self):
        g = nx.Graph()
        g.add_node(1, pos=(123, -45))
        symmetry = sym.even_neighborhood_distribution(g)
        print(symmetry)
        assert symmetry == 1

    def test_single_edge(self):
        g = nx.Graph()
        g.add_node(1, pos=(123, -45))
        g.add_node(2, pos=(1, 1))
        g.add_edge(1, 2)
        symmetry = sym.even_neighborhood_distribution(g)
        print(symmetry)
        assert symmetry == 1

    def test_star(self):
        g = nx.Graph()
        g.add_node('mid', pos=(0, 0))

        for i in range(0, 360):
            g.add_node(i, pos=(math.sin(math.radians(i)), math.cos(math.radians(i))))
            g.add_edge(i, 'mid')

        symmetry = sym.even_neighborhood_distribution(g)
        print(symmetry)
        assert symmetry == 1

    def test_odd_star(self):
        g = nx.Graph()
        g.add_node('mid', pos=(0, 0))
        g.add_node(1, pos=(1, 1))
        g.add_node(2, pos=(-1, -1))
        g.add_node(3, pos=(-1, 1))
        g.add_node(4, pos=(1, -1))
        g.add_node(5, pos=(0, 1))

        g.add_edges_from([('mid', 1), ('mid', 2), ('mid', 3), ('mid', 4), ('mid', 5)])

        symmetry = sym.even_neighborhood_distribution(g)
        print(symmetry)
        assert symmetry == pytest.approx(1 - (1 / 6) / math.sqrt(2))

    def test_random_graph_in_range(self):
        random.seed(45345)
        for i in range(0, 100):
            random_graph = nx.fast_gnp_random_graph(i, random.uniform(0.1, 1), random.randint(1, 10000000))
            random_embedding = {n: [random.uniform(-100, 100), random.uniform(-100, 100)] for n in range(0, i + 1)}

            symmetry = sym.even_neighborhood_distribution(random_graph, random_embedding)
            print(i, symmetry)

            assert 0 <= symmetry <= 1
