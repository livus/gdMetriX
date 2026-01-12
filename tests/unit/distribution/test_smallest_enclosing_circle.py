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
from gdMetriX.common import Vector, get_node_positions


class TestSmallestEnclosingCircle(unittest.TestCase):

    def test_empty_graph(self):
        g = nx.Graph()

        center, radius = distribution.smallest_enclosing_circle(g)
        assert center == Vector(0, 0)
        assert radius == 0

    def test_singleton(self):
        g = nx.Graph()
        g.add_node(1, pos=(-3, 12))

        center, radius = distribution.smallest_enclosing_circle(g)
        assert center == Vector(-3, 12)
        assert radius == 0

    def test_tuple(self):

        for _ in range(0, 10):
            g = nx.Graph()
            g.add_node(1, pos=(0, 0))
            g.add_node(2, pos=(0, 1))

            center, radius = distribution.smallest_enclosing_circle(g)
            print(center, radius)
            assert center == Vector(0, 0.5)
            assert radius == 0.5

    def test_circle(self):
        random.seed(31294908)

        # Try it a bunch of times as the algorithm is randomized
        for _ in range(0, 20):
            g = nx.Graph()

            for i in range(0, 360):
                g.add_node(i, pos=(math.sin(i), math.cos(i)))

            center, radius = distribution.smallest_enclosing_circle(g)

            assert math.isclose(center.x, 0, abs_tol=0.01)
            assert math.isclose(center.y, 0, abs_tol=0.01)
            assert math.isclose(radius, 1, abs_tol=0.01)

    def test_rectangle(self):
        random.seed(5913940234)

        for size in range(4, 128):
            g = nx.Graph()
            for i in range(0, size):
                g.add_node(i, pos=(0, i))
                g.add_node(size + i, pos=(i, 0))
                g.add_node(size * 2 + i, pos=(size, i))
                g.add_node(size * 3 + i, pos=(i, size))
            g.add_node(size * 4, pos=(size, size))

            center, radius = distribution.smallest_enclosing_circle(g)

            assert center.x == pytest.approx(size / 2)
            assert center.y == pytest.approx(size / 2)
            assert radius == pytest.approx(size * math.sqrt(2) / 2)

    def test_random_embedding_all_nodes_contained(self):

        for _ in range(0, 100):

            g = nx.Graph()

            for node in range(0, random.randint(5, 255)):
                g.add_node(
                    node, pos=(random.uniform(-100, 100), random.uniform(-100, 100))
                )

            center, radius = distribution.smallest_enclosing_circle(g)
            pos = get_node_positions(g)

            for node in g.nodes:
                point = Vector(pos[node][0], pos[node][1])
                assert point.distance(center) <= radius + 1e-06

    def test_minimal_circle_has_boundary_points(self):
        for _ in range(0, 100):
            g = nx.Graph()
            for node in range(random.randint(5, 150)):
                g.add_node(node, pos=(random.uniform(-100, 100), random.uniform(-100, 100)))

            center, radius = distribution.smallest_enclosing_circle(g)
            pos = get_node_positions(g)

            # Count points that lie *almost exactly* on the boundary
            on_boundary = 0
            for node in g.nodes:
                point = Vector(pos[node][0], pos[node][1])
                if math.isclose(point.distance(center), radius, abs_tol=1e-6):
                    on_boundary += 1

            assert on_boundary >= 2

    def test_dataset_exceeding_recursion_depth(self):
        # The recursive implementation is limited due to the limited recursion depth
        # This test checks that this is no longer the case

        g = nx.Graph()
        for node in range(0, sys.getrecursionlimit() * 2):
            g.add_node(node, pos=(random.uniform(-100, 100), random.uniform(-100, 100)))

        center, radius = distribution.smallest_enclosing_circle(g)
        assert radius > 0

    def test_large_dataset_with_defined_boundary_points(self):
        g = nx.Graph()

        # Equilateral triangle on unit circle
        A = (1, 0)
        B = (-0.5, math.sqrt(3) / 2)
        C = (-0.5, -math.sqrt(3) / 2)
        g.add_node("A", pos=A)
        g.add_node("B", pos=B)
        g.add_node("C", pos=C)

        # Nodes inside the triangle
        incircle_radius = math.sqrt(3) / 6
        for i in range(0, 250):
            r_prime = math.sqrt(random.uniform(0, 1)) * incircle_radius
            theta = random.uniform(0, 2 * math.pi)
            g.add_node(i, pos=(r_prime * math.cos(theta), r_prime * math.sin(theta)))

        center, radius = distribution.smallest_enclosing_circle(g)

        assert radius == pytest.approx(1)
        assert center.x == pytest.approx(0)
        assert center.y == pytest.approx(0)

    def test_duplicate_extremes(self):
        g = nx.Graph()
        g.add_node(1, pos=(0, 0))
        g.add_node(2, pos=(0, 0))
        g.add_node(3, pos=(1, 0))
        g.add_node(4, pos=(1, 1))
        g.add_node(5, pos=(0, 1))

        center, radius = distribution.smallest_enclosing_circle(g)

        assert center.x == pytest.approx(0.5)
        assert center.y == pytest.approx(0.5)
        assert radius == pytest.approx(math.sqrt(2)/2)

    def test_collinear_points(self):
        g = nx.Graph()
        g.add_node(1, pos=(0, 0))
        g.add_node(2, pos=(2, 0))
        g.add_node(3, pos=(1, 0))

        center, radius = distribution.smallest_enclosing_circle(g)

        assert center.x == pytest.approx(1)
        assert center.y == pytest.approx(0)
        assert radius == pytest.approx(1)

    def test_two_points_arbitrary(self):
        g = nx.Graph()
        g.add_node(1, pos=(-5, 7))
        g.add_node(2, pos=(3, -2))

        center, radius = distribution.smallest_enclosing_circle(g)

        expected_center_x = (-5 + 3) / 2
        expected_center_y = (7 + -2) / 2
        expected_radius = math.sqrt((3 - (-5))**2 + (-2 - 7)**2) / 2

        assert center.x == pytest.approx(expected_center_x)
        assert center.y == pytest.approx(expected_center_y)
        assert radius == pytest.approx(expected_radius)

    def test_vertical_line_points(self):
        g = nx.Graph()
        g.add_node(1, pos=(2, -1))
        g.add_node(2, pos=(2, 3))
        g.add_node(3, pos=(2, 0))

        center, radius = distribution.smallest_enclosing_circle(g)

        assert center.x == pytest.approx(2)
        assert center.y == pytest.approx(1)
        assert radius == pytest.approx(2)

    def test_horizontal_line_points(self):
        g = nx.Graph()
        g.add_node(1, pos=(-2, 5))
        g.add_node(2, pos=(3, 5))
        g.add_node(3, pos=(0, 5))

        center, radius = distribution.smallest_enclosing_circle(g)

        assert center.x == pytest.approx(0.5)
        assert center.y == pytest.approx(5)
        assert radius == pytest.approx(2.5)

    def test_repeated_singleton(self):
        g = nx.Graph()
        for i in range(10):
            g.add_node(i, pos=(1, 1))

        center, radius = distribution.smallest_enclosing_circle(g)

        assert center.x == pytest.approx(1)
        assert center.y == pytest.approx(1)
        assert radius == pytest.approx(0)

    def test_negative_coordinates(self):
        g = nx.Graph()
        g.add_node(1, pos=(-5, -3))
        g.add_node(2, pos=(-1, -8))
        g.add_node(3, pos=(-4, -2))

        center, radius = distribution.smallest_enclosing_circle(g)

        for node in g.nodes:
            point = Vector(*g.nodes[node]['pos'])
            assert point.distance(center) <= radius + 1e-6






