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

import networkx as nx

# noinspection PyUnresolvedReferences
import pytest

# noinspection PyUnresolvedReferences
import pytest_socket

from gdMetriX import distribution
from gdMetriX.common import Vector


class TestCenterOfMass(unittest.TestCase):

    def test_empty_graph(self):
        g = nx.Graph()
        center = distribution.center_of_mass(g)

        assert center is None

    def test_singleton(self):
        g = nx.Graph()
        g.add_node(1, pos=(12, 9))
        center = distribution.center_of_mass(g)

        assert center == Vector(12, 9)

    def test_rectangle(self):
        g = nx.Graph()
        g.add_node(1, pos=(-1, -1))
        g.add_node(2, pos=(-1, 1))
        g.add_node(3, pos=(1, -1))
        g.add_node(4, pos=(1, 1))
        g.add_edges_from([(1, 2), (2, 3), (3, 4), (4, 1)])

        center = distribution.center_of_mass(g)
        assert center == Vector(0, 0)

    def test_rectangle_weighted(self):
        g = nx.Graph()
        g.add_node(1, pos=(-1, -1))
        g.add_node(2, pos=(-1, 1))
        g.add_node(3, pos=(1, -1))
        g.add_node(4, pos=(1, 1))
        g.add_edges_from([(1, 2), (2, 3), (3, 4), (4, 1)])

        weight = {1: 1, 2: 1, 3: 1, 4: 2}

        center = distribution.center_of_mass(g, weight=weight)
        assert center == Vector(0.2, 0.2)

    def test_rectangle_weighted_with_weight_as_string(self):
        g = nx.Graph()
        g.add_node(1, pos=(-1, -1), weight=1)
        g.add_node(2, pos=(-1, 1), weight=1)
        g.add_node(3, pos=(1, -1), weight=1)
        g.add_node(4, pos=(1, 1), weight=2)
        g.add_edges_from([(1, 2), (2, 3), (3, 4), (4, 1)])

        center = distribution.center_of_mass(g, weight="weight")
        assert center == Vector(0.2, 0.2)

    def test_circle(self):
        g = nx.Graph()

        for i in range(0, 3600):
            g.add_node(i, pos=(math.sin(i / 10), math.cos(i / 10)))

        center = distribution.center_of_mass(g)

        print(center)

        assert -0.01 <= center.x <= 0.01
        assert -0.01 <= center.y <= 0.01
