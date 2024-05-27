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
    Unit tests for the crossing angular resolution.
"""

import unittest

import networkx as nx
# noinspection PyUnresolvedReferences
import pytest

from gdMetriX import crossings


class TestCrossingAngles(unittest.TestCase):

    def test_simple_crossing(self):
        g = nx.Graph()
        g.add_node(1, pos=(0, 0))
        g.add_node(2, pos=(1, 1))
        g.add_node(3, pos=(1, 0))
        g.add_node(4, pos=(0, 1))

        g.add_edges_from([(1, 2), (3, 4)])

        all_crossings = crossings.get_crossings(g)
        print(all_crossings)

        assert len(all_crossings) == 1

        crossing_angles = crossings.crossing_angles(all_crossings[0], nx.get_node_attributes(g, 'pos'), True)
        print(crossing_angles)

        assert len(crossing_angles) == 4
        assert crossing_angles[0] == 90
        assert crossing_angles[1] == 90
        assert crossing_angles[2] == 90
        assert crossing_angles[3] == 90

    def test_vertex_at_edge(self):
        g = nx.Graph()
        g.add_node(1, pos=(0, 0))
        g.add_node(2, pos=(5, 0))
        g.add_node(3, pos=(3, 5))
        g.add_node(4, pos=(3, 0))
        g.add_edges_from([(1, 2), (3, 4)])

        all_crossings = crossings.get_crossings(g, include_node_crossings=True)

        assert len(all_crossings) == 1

        crossing_angles = crossings.crossing_angles(all_crossings[0], nx.get_node_attributes(g, 'pos'), True)
        print(crossing_angles)

        assert len(crossing_angles) == 3
        assert crossing_angles[0] == 90
        assert crossing_angles[1] == 180
        assert crossing_angles[2] == 90

    def test_crossing_angular_resolution(self):
        g = nx.Graph()
        g.add_node(1, pos=(0, 0))
        g.add_node(2, pos=(5, 0))
        g.add_node(3, pos=(3, 5))
        g.add_node(4, pos=(3, 0))
        g.add_edges_from([(1, 2), (3, 4)])

        crossing_angular_resolution = crossings.crossing_angular_resolution(g, include_node_crossings=True)
        assert crossing_angular_resolution == 1

    def test_crossing_angular_resolution_2(self):
        g = nx.Graph()
        g.add_node(1, pos=(0, 0))
        g.add_node(2, pos=(1, 1))
        g.add_node(3, pos=(1, 0))
        g.add_node(4, pos=(0, 1))

        g.add_edges_from([(1, 2), (3, 4)])

        crossing_angular_resolution = crossings.crossing_angular_resolution(g, include_node_crossings=True)
        assert crossing_angular_resolution == 1

    def test_crossing_angular_resolution_3(self):
        g = nx.Graph()
        g.add_node(1, pos=(0, 0))
        g.add_node(2, pos=(1, 0))
        g.add_node(3, pos=(-1, -1))
        g.add_node(4, pos=(1, 1))
        g.add_edges_from([(1, 2), (3, 4)])

        crossing_angular_resolution = crossings.crossing_angular_resolution(g, include_node_crossings=True)
        assert crossing_angular_resolution == 0.5

    def test_crossing_angular_resolution_3(self):
        g = nx.Graph()
        g.add_node(1, pos=(0, 0))
        g.add_node(2, pos=(1, 0))
        g.add_node(3, pos=(-1, -1))
        g.add_node(4, pos=(1, 1))
        g.add_node(5, pos=(5, 5))
        g.add_node(6, pos=(6, 6))
        g.add_node(7, pos=(5, 6))
        g.add_node(8, pos=(6, 5))
        g.add_edges_from([(1, 2), (3, 4), (5, 6), (7, 8)])

        crossing_angular_resolution = crossings.crossing_angular_resolution(g, include_node_crossings=True)
        assert crossing_angular_resolution == 0.75
