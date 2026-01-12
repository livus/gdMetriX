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

from gdMetriX import distribution


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
