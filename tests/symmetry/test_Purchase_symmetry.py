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
    Unit tests for the node-based symmetry proposed by Purchase
"""

import math
import random
import unittest

import networkx as nx
import numpy as np
# noinspection PyUnresolvedReferences
import pytest
# noinspection PyUnresolvedReferences
import pytest_socket

from gdMetriX import symmetry as sym


class TextReflectPointAroundPerpendicularBisector(unittest.TestCase):

    def test_vertical_flip_line(self):
        a = np.array([-1, 0])
        b = np.array([1, 0])

        p = np.array([1, 1])

        flipped = sym._flip_point_around_axis(p, a, b)

        math.isclose(flipped[0], -1)
        math.isclose(flipped[1], 1)

    def test_vertical_flip_line_2(self):
        a = np.array([-1, 2])
        b = np.array([1, 2])

        p = np.array([1, 1])

        flipped = sym._flip_point_around_axis(p, a, b)

        math.isclose(flipped[0], -1)
        math.isclose(flipped[1], 1)

    def test_vertical_flip_line_3(self):
        a = np.array([1, 2])
        b = np.array([3, 2])

        p = np.array([3, 1])

        flipped = sym._flip_point_around_axis(p, a, b)

        math.isclose(flipped[0], 1)
        math.isclose(flipped[1], 1)

    def test_horizontal_flip_line(self):
        a = np.array([0, -1])
        b = np.array([0, 1])

        p = np.array([1, 1])

        flipped = sym._flip_point_around_axis(p, a, b)

        math.isclose(flipped[0], 1)
        math.isclose(flipped[1], -1)

    def test_horizontal_flip_line_2(self):
        a = np.array([2, -1])
        b = np.array([2, 1])

        p = np.array([1, 1])

        flipped = sym._flip_point_around_axis(p, a, b)

        assert math.isclose(flipped[0], 1)
        assert math.isclose(flipped[1], -1)

    def test_horizontal_flip_line_3(self):
        a = np.array([2, 1])
        b = np.array([2, 2])

        p = np.array([1, 3])

        flipped = sym._flip_point_around_axis(p, a, b)

        assert math.isclose(flipped[0], 1)
        assert math.isclose(flipped[1], 0)

    def test_flip_on_line(self):
        a = np.array([1, 1])
        b = np.array([3, 3])
        p = np.array([2, 2])

        flipped = sym._flip_point_around_axis(p, a, b)

        assert math.isclose(flipped[0], 2)
        assert math.isclose(flipped[1], 2)

    def test_45_degrees(self):
        a = np.array([1, 0])
        b = np.array([0, 1])
        p = np.array([1, 2])

        flipped = sym._flip_point_around_axis(p, a, b)

        math.isclose(flipped[0], 2)
        math.isclose(flipped[0], 1)


class TestPurchaseSymmetry(unittest.TestCase):

    def test_empty_graph(self):
        g = nx.Graph()
        symmetry = sym.reflective_symmetry(g)
        print(symmetry)
        assert symmetry == 1

    def test_single_node(self):
        g = nx.Graph()
        g.add_node(1, pos=(123, -45))
        symmetry = sym.reflective_symmetry(g)
        print(symmetry)
        assert symmetry == 1

    def test_single_edge(self):
        g = nx.Graph()
        g.add_node(1, pos=(123, -45))
        g.add_node(2, pos=(1, 1))
        g.add_edge(1, 2)
        symmetry = sym.reflective_symmetry(g)
        print(symmetry)
        assert symmetry == 1

    def test_cycle_close_to_one(self):
        g = nx.Graph()

        for i in range(0, 10):
            g.add_node(i, pos=(math.sin(math.radians(i * 36)), math.cos(math.radians(i * 36))))
            g.add_edge(i, (i + 1) % 10)

        symmetry = sym.reflective_symmetry(g)
        print(symmetry)
        assert 0.95 < symmetry <= 1

    def test_simple_rectangle_close_to_one(self):
        g = nx.Graph()

        g.add_node(1, pos=(-1, -1))
        g.add_node(2, pos=(-1, 1))
        g.add_node(3, pos=(1, 1))
        g.add_node(4, pos=(1, -1))
        g.add_edges_from([(1, 2), (2, 3), (3, 4), (4, 1)])

        symmetry = sym.reflective_symmetry(g, threshold=2)
        print(symmetry)
        assert 0.95 < symmetry <= 1

    def test_single_edge_and_singleton_should_return_zero(self):
        g = nx.Graph()
        g.add_node(1, pos=(1, 1))
        g.add_node(2, pos=(4, 3))
        g.add_node(3, pos=(-1, 2))
        g.add_edge(1, 2)

        symmetry = sym.reflective_symmetry(g)
        print(symmetry)
        assert symmetry == 0

    def test_random_graph_in_range(self):
        random.seed(45345)
        for i in range(0, 16):
            random_graph = nx.fast_gnp_random_graph(int(i / 2), random.uniform(0.1, 1), random.randint(1, 10000000))
            random_embedding = {n: [random.randint(-100, 100), random.randint(-100, 100)] for n in range(0, i + 1)}

            symmetry = sym.reflective_symmetry(random_graph, random_embedding)
            print(i, symmetry)

            assert 0 <= symmetry <= 1

    def test_right_angle_crossing(self):
        g = nx.Graph()
        g.add_node(1, pos=(-1, 0))
        g.add_node(2, pos=(1, 0))
        g.add_node(3, pos=(0, -1))
        g.add_node(4, pos=(0, 1))
        g.add_edges_from([(1, 2), (3, 4)])

        symmetry = sym.reflective_symmetry(g, threshold=2)

        assert symmetry == 1

    def test_right_angle_crossing_with_different_fraction(self):
        g = nx.Graph()
        g.add_node(1, pos=(-1, 0))
        g.add_node(2, pos=(1, 0))
        g.add_node(3, pos=(0, -1))
        g.add_node(4, pos=(0, 1))
        g.add_edges_from([(1, 2), (3, 4)])

        symmetry = sym.reflective_symmetry(g, threshold=2, fraction=0.5)

        assert symmetry == 1
