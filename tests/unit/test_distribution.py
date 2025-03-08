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
        assert closest_pair[1] == grid_size**2 or closest_pair[1] == grid_size**2
        assert closest_pair[0] != closest_pair[1]
        assert math.isclose(closest_pair[2], math.sqrt((0.4**2) * 2))

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


class TestConcentration(unittest.TestCase):

    def test_empty_graph(self):
        g = nx.Graph()
        concentration = distribution.concentration(g)
        print(concentration)

        assert concentration == 0

    def test_singleton(self):
        g = nx.Graph()
        concentration = distribution.concentration(g)
        print(concentration)

        assert concentration == 0

    def test_pair(self):
        g = nx.Graph()
        g.add_node(1, pos=(-9.3, 0.45))
        g.add_node(2, pos=(3, 7.6))

        concentration = distribution.concentration(g)
        print(concentration)

        assert concentration == 0

    def test_simple_quadrants(self):
        g = nx.Graph()
        g.add_node(1, pos=(1, 1))
        g.add_node(2, pos=(-1, -1))
        g.add_node(3, pos=(-1, 1))
        g.add_node(4, pos=(1, -1))

        concentration = distribution.concentration(g)
        print(concentration)

        assert concentration == 0

    def test_tuple_in_cell(self):
        g = nx.Graph()
        g.add_node(1, pos=(1, 1))
        g.add_node(2, pos=(0, 0))
        g.add_node(3, pos=(0.1, 0.1))

        concentration = distribution.concentration(g)
        print(concentration)

        assert math.isclose(concentration, 0.5)  # 0.5 = sum(max-1) / (n-1) = 1/2

    def test_tuple_in_cell_two_tuples(self):
        g = nx.Graph()
        g.add_node(1, pos=(1, 1))
        g.add_node(2, pos=(0, 0))
        g.add_node(3, pos=(0.1, 0.1))
        g.add_node(4, pos=(0.9, 0.9))

        concentration = distribution.concentration(g)
        print(concentration)

        assert math.isclose(
            concentration, 2 / 3
        )  # 2/3 = sum(max-1) / (n-1) = (1+1) / 3

    def test_tuple_in_cell_2(self):
        g = nx.Graph()
        g.add_node(1, pos=(1, 1))
        g.add_node(2, pos=(0, 0))
        g.add_node(3, pos=(0.1, 0.1))
        g.add_node(4, pos=(0, 1))
        g.add_node(5, pos=(1, 0))

        concentration = distribution.concentration(g)
        print(concentration)

        assert math.isclose(concentration, 0.25)  # 0.5 = sum(max-1) / (n-1) = 1/4

    def test_tuple_in_cell_two_tuples_2(self):
        g = nx.Graph()
        g.add_node(1, pos=(1, 1))
        g.add_node(2, pos=(0, 0))
        g.add_node(3, pos=(0.1, 0.1))
        g.add_node(4, pos=(0.9, 0.9))
        g.add_node(5, pos=(0, 1))
        g.add_node(6, pos=(1, 0))

        concentration = distribution.concentration(g)
        print(concentration)

        assert math.isclose(
            concentration, 2 / 5
        )  # 2/3 = sum(max-1) / (n-1) = (1+1) / 5

    def test_big_grid(self):
        g = nx.Graph()

        grid_size = 10

        for i in range(0, grid_size):
            for j in range(0, grid_size):
                g.add_node(i * grid_size + j, pos=(i, j))

        concentration = distribution.concentration(g)
        print(concentration)

        assert concentration == 0

    def test_big_grid_2(self):
        g = nx.Graph()

        grid_size = 10

        for i in range(0, grid_size):
            for j in range(0, grid_size):
                g.add_node(i * grid_size + j, pos=(i, j))

        g.add_node("special", pos=(0, 0))

        concentration = distribution.concentration(g)
        print(concentration)

        assert concentration == 1 / 100

    def test_negative_grid_size_should_raise(self):
        def _call_with_invalid_grid_size():
            g = nx.Graph()
            g.add_node(1, pos=(0, 0))
            g.add_node(2, pos=(1, 1))

            distribution.concentration(g, grid_size=-1)

        self.assertRaises(ValueError, _call_with_invalid_grid_size)

    def test_too_small_cell_size_should_raise(self):
        def _call_with_invalid_grid_size():
            g = nx.Graph()
            g.add_node(1, pos=(0, 0))
            g.add_node(2, pos=(1, 1))

            distribution.concentration(g, grid_size=3)

        self.assertRaises(ValueError, _call_with_invalid_grid_size)

    def test_custom_grid_size_simple_rectangle(self):

        g = nx.Graph()
        g.add_node(1, pos=(1, 1))
        g.add_node(2, pos=(1, 0))
        g.add_node(3, pos=(0, 1))
        g.add_node(4, pos=(0, 0))

        concentration = distribution.concentration(g, grid_size=1)
        print(concentration)

        assert concentration == 0

    def test_custom_grid_size_simple_rectangle_2(self):

        g = nx.Graph()
        g.add_node(1, pos=(1, 1))
        g.add_node(2, pos=(1, 0))
        g.add_node(3, pos=(0, 1))
        g.add_node(4, pos=(0, 0))

        concentration = distribution.concentration(g, grid_size=2)
        print(concentration)

        assert concentration == 0

    def test_custom_bounding_box(self):
        g = nx.Graph()
        g.add_node(1, pos=(1, 1))
        g.add_node(2, pos=(0, 0))
        g.add_node(3, pos=(0.1, 0.1))

        concentration = distribution.concentration(g, bounding_box=(0, 0, 2, 2))
        print(concentration)

        assert math.isclose(concentration, 0.5)  # 0.5 = sum(max-1) / (n-1) = 1/2


class TestHomogeneity(unittest.TestCase):

    def test_empty_graph(self):
        g = nx.Graph()
        homogeneity = distribution.homogeneity(g)
        print(homogeneity)
        assert homogeneity == 0

    def test_singleton(self):
        g = nx.Graph()
        g.add_node(1, pos=(3, 4))
        homogeneity = distribution.homogeneity(g)
        print(homogeneity)
        assert homogeneity == 0

    def test_rectangle(self):
        g = nx.Graph()
        g.add_node(1, pos=(0, 0))
        g.add_node(2, pos=(0, 1))
        g.add_node(3, pos=(1, 0))
        g.add_node(4, pos=(1, 1))

        homogeneity = distribution.homogeneity(g)
        print(homogeneity)
        assert homogeneity == 0

    def test_rectangle_2(self):
        g = nx.Graph()
        g.add_node(1, pos=(-1, -0.74))
        g.add_node(2, pos=(-0.5, 0.11))
        g.add_node(3, pos=(0.1, -1))
        g.add_node(4, pos=(1, 1))

        homogeneity = distribution.homogeneity(g)
        print(homogeneity)
        assert homogeneity == 0

    def test_uneven_rectangle(self):
        g = nx.Graph()
        g.add_node(1, pos=(0, 0))
        g.add_node(2, pos=(0, 1))
        g.add_node(3, pos=(1, 0))
        g.add_node(4, pos=(1, 1))
        g.add_node(5, pos=(0.584, 0.71))

        homogeneity = distribution.homogeneity(g)
        print(homogeneity)
        assert homogeneity == 0.5

    def test_uneven_rectangle_2(self):
        g = nx.Graph()
        g.add_node(1, pos=(-1, -1))
        g.add_node(2, pos=(-0.5, 1))
        g.add_node(3, pos=(0.1, 0.2))
        g.add_node(4, pos=(1, 1))

        homogeneity = distribution.homogeneity(g)
        print(homogeneity)
        assert homogeneity == 0.5

    def test_big_even_graph(self):
        random.seed(19459843452)

        g = nx.Graph()
        g.add_node("bound1", pos=(-1, -1))
        g.add_node("bound2", pos=(-1, 1))
        g.add_node("bound3", pos=(1, -1))
        g.add_node("bound4", pos=(1, 1))

        for i in range(2500):
            g.add_node(i * 4, pos=(random.uniform(-1, 0), random.uniform(-1, 0)))
            g.add_node(i * 4 + 1, pos=(random.uniform(0, 1), random.uniform(-1, 0)))
            g.add_node(i * 4 + 2, pos=(random.uniform(-1, 0), random.uniform(0, 1)))
            g.add_node(i * 4 + 3, pos=(random.uniform(0, 1), random.uniform(0, 1)))

        homogeneity = distribution.homogeneity(g)
        print(homogeneity)

        assert homogeneity == 0

    def test_big_even_graph_slightly_uneven(self):
        random.seed(19459843452)

        for n_quad in range(10, 256):
            g = nx.Graph()
            g.add_node("bound1", pos=(-1, -1))
            g.add_node("bound2", pos=(-1, 1))
            g.add_node("bound3", pos=(1, -1))
            g.add_node("bound4", pos=(1, 1))

            for i in range(n_quad - 1):
                g.add_node(i * 4, pos=(random.uniform(-1, 0), random.uniform(-1, 0)))
                g.add_node(i * 4 + 1, pos=(random.uniform(0, 1), random.uniform(-1, 0)))
                g.add_node(i * 4 + 2, pos=(random.uniform(-1, 0), random.uniform(0, 1)))
                g.add_node(i * 4 + 3, pos=(random.uniform(0, 1), random.uniform(0, 1)))

            g.add_node("odd_one", pos=(0.5, 0.5))
            homogeneity = distribution.homogeneity(g)
            print(homogeneity)

            assert math.isclose(1 - (1 / (n_quad + 1)), homogeneity)

    def test_big_uneven_graph(self):

        random.seed(932498219)

        g = nx.Graph()
        g.add_node("bound1", pos=(-1, -1))
        g.add_node("bound2", pos=(-1, 1))
        g.add_node("bound3", pos=(1, -1))
        g.add_node("bound4", pos=(1, 1))

        for i in range(96):
            g.add_node(i, pos=(random.uniform(0, 1), random.uniform(0, 1)))

        homogeneity = distribution.homogeneity(g)
        print(homogeneity)

        assert math.isclose(1, homogeneity)


class TestBalance(unittest.TestCase):

    def test_horizontal_balance_empty_graph(self):
        g = nx.Graph()

        balance = distribution.horizontal_balance(g)

        assert balance == 0

    def test_horizontal_balance_singleton(self):
        g = nx.Graph()
        g.add_node(1, pos=(0, 0))

        balance = distribution.horizontal_balance(g)

        assert balance == 0

    def test_horizontal_balance_singleton_2(self):
        g = nx.Graph()
        g.add_node(1, pos=(-3, 7))

        balance = distribution.horizontal_balance(g)

        assert balance == 0

    def test_horizontal_balance_singleton_absolute(self):
        g = nx.Graph()
        g.add_node(1, pos=(-3, 7))

        balance = distribution.horizontal_balance(g, use_relative_coordinates=False)

        assert balance == 1

    def test_horizontal_balance_evenly_spaced(self):
        g = nx.Graph()
        g.add_node(1, pos=(1, 1))
        g.add_node(2, pos=(-1, 1))
        g.add_node(3, pos=(1, -1))
        g.add_node(4, pos=(-1, -1))

        balance = distribution.horizontal_balance(g)

        assert balance == 0

    def test_horizontal_balance_evenly_spaced_absolute(self):
        g = nx.Graph()
        g.add_node(1, pos=(1, 1))
        g.add_node(2, pos=(-1, 1))
        g.add_node(3, pos=(1, -1))
        g.add_node(4, pos=(-1, -1))

        balance = distribution.horizontal_balance(g, use_relative_coordinates=False)

        assert balance == 0

    def test_horizontal_balance_center_vertex(self):
        g = nx.Graph()
        g.add_node(1, pos=(1, 1))
        g.add_node(2, pos=(1, 3))
        g.add_node(3, pos=(1, -1))

        balance = distribution.horizontal_balance(g)

        assert balance == 0

    def test_horizontal_balance_unbalanced_absolute(self):
        g = nx.Graph()
        g.add_node(1, pos=(1, 1))
        g.add_node(2, pos=(1, 3))
        g.add_node(3, pos=(1, -1))

        balance = distribution.horizontal_balance(g, use_relative_coordinates=False)

        assert balance == 1 / 3

    def test_horizontal_balance_unbalanced_absolute_2(self):
        g = nx.Graph()
        g.add_node(1, pos=(1, -1))
        g.add_node(2, pos=(1, -3))
        g.add_node(3, pos=(1, 1))

        balance = distribution.horizontal_balance(g, use_relative_coordinates=False)

        assert balance == -1 / 3

    def test_horizontal_balance_unbalanced(self):
        g = nx.Graph()
        g.add_node(1, pos=(1, 2))
        g.add_node(2, pos=(1, 3))
        g.add_node(3, pos=(1, -1))

        balance = distribution.horizontal_balance(g)

        assert balance == 1 / 3

    def test_horizontal_balance_unbalanced_with_center_vertex(self):
        g = nx.Graph()
        g.add_node(1, pos=(1, 2))
        g.add_node(2, pos=(1, 3))
        g.add_node(3, pos=(1, -1))
        g.add_node(4, pos=(1, 1))

        balance = distribution.horizontal_balance(g)

        assert balance == 1 / 4

    def test_horizontal_balance_unbalanced_2(self):
        g = nx.Graph()
        g.add_node(1, pos=(1, -2))
        g.add_node(2, pos=(1, -3))
        g.add_node(3, pos=(1, 1))

        balance = distribution.horizontal_balance(g)

        assert balance == -1 / 3

    def test_horizontal_balance_unbalanced_with_center_vertex_2(self):
        g = nx.Graph()
        g.add_node(1, pos=(1, -2))
        g.add_node(2, pos=(1, -3))
        g.add_node(3, pos=(1, 1))
        g.add_node(4, pos=(1, -1))

        balance = distribution.horizontal_balance(g)

        assert balance == -1 / 4

    def test_vertical_balance_empty_graph(self):
        g = nx.Graph()

        balance = distribution.vertical_balance(g)

        assert balance == 0

    def test_vertical_balance_singleton(self):
        g = nx.Graph()
        g.add_node(1, pos=(0, 0))

        balance = distribution.vertical_balance(g)

        assert balance == 0

    def test_vertical_balance_singleton_2(self):
        g = nx.Graph()
        g.add_node(1, pos=(-3, 7))

        balance = distribution.vertical_balance(g)

        assert balance == 0

    def test_vertical_balance_singleton_absolute(self):
        g = nx.Graph()
        g.add_node(1, pos=(-3, 7))

        balance = distribution.vertical_balance(g, use_relative_coordinates=False)

        assert balance == -1

    def test_vertical_balance_evenly_spaced(self):
        g = nx.Graph()
        g.add_node(1, pos=(1, 1))
        g.add_node(2, pos=(-1, 1))
        g.add_node(3, pos=(1, -1))
        g.add_node(4, pos=(-1, -1))

        balance = distribution.vertical_balance(g)

        assert balance == 0

    def test_vertical_balance_evenly_spaced_absolute(self):
        g = nx.Graph()
        g.add_node(1, pos=(1, 1))
        g.add_node(2, pos=(-1, 1))
        g.add_node(3, pos=(1, -1))
        g.add_node(4, pos=(-1, -1))

        balance = distribution.vertical_balance(g, use_relative_coordinates=False)

        assert balance == 0

    def test_vertical_balance_center_vertex(self):
        g = nx.Graph()
        g.add_node(1, pos=(1, 1))
        g.add_node(2, pos=(3, 1))
        g.add_node(3, pos=(-1, 1))

        balance = distribution.vertical_balance(g)

        assert balance == 0

    def test_vertical_balance_unbalanced_absolute(self):
        g = nx.Graph()
        g.add_node(1, pos=(1, 1))
        g.add_node(2, pos=(3, 1))
        g.add_node(3, pos=(-1, 1))

        balance = distribution.vertical_balance(g, use_relative_coordinates=False)

        assert balance == 1 / 3

    def test_vertical_balance_unbalanced_absolute_2(self):
        g = nx.Graph()
        g.add_node(1, pos=(-1, 1))
        g.add_node(2, pos=(-3, 1))
        g.add_node(3, pos=(1, 1))

        balance = distribution.vertical_balance(g, use_relative_coordinates=False)

        assert balance == -1 / 3

    def test_vertical_balance_unbalanced(self):
        g = nx.Graph()
        g.add_node(1, pos=(2, 1))
        g.add_node(2, pos=(3, 1))
        g.add_node(3, pos=(-1, 1))

        balance = distribution.vertical_balance(g)

        assert balance == 1 / 3

    def test_vertical_balance_unbalanced_with_center_vertex(self):
        g = nx.Graph()
        g.add_node(1, pos=(2, 1))
        g.add_node(2, pos=(3, 1))
        g.add_node(3, pos=(-1, 1))
        g.add_node(4, pos=(1, 1))

        balance = distribution.vertical_balance(g)

        assert balance == 1 / 4

    def test_vertical_balance_unbalanced_2(self):
        g = nx.Graph()
        g.add_node(1, pos=(-2, 1))
        g.add_node(2, pos=(-3, 1))
        g.add_node(3, pos=(1, 1))

        balance = distribution.vertical_balance(g)

        assert balance == -1 / 3

    def test_vertical_balance_unbalanced_with_center_vertex_2(self):
        g = nx.Graph()
        g.add_node(1, pos=(-2, 1))
        g.add_node(2, pos=(-3, 1))
        g.add_node(3, pos=(1, 1))
        g.add_node(4, pos=(-1, 1))

        balance = distribution.vertical_balance(g)

        assert balance == -1 / 4


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


class TestNodeOrthogonality(unittest.TestCase):

    def test_empty_graph(self):
        g = nx.Graph()

        orthogonality = distribution.node_orthogonality(g)
        assert orthogonality == 0

    def test_singleton(self):
        g = nx.Graph()
        g.add_node(1, pos=(-3, 12))

        orthogonality = distribution.node_orthogonality(g)
        assert orthogonality == 1

    def test_given_dimensions(self):
        g = nx.Graph()

        for i in range(0, 982):
            g.add_node(i)

        orthogonality = distribution.node_orthogonality(g, width=10, height=5)

        assert orthogonality == 982 / 50

    def test_integer_width(self):

        g = nx.Graph()
        for i in range(1, 100):
            g.add_node(i, pos=(i, 0))

        orthogonality = distribution.node_orthogonality(g, height=2)

        assert orthogonality == 1 / 2

    def test_integer_height(self):

        g = nx.Graph()
        for i in range(1, 100):
            g.add_node(i, pos=(i, 0))

        orthogonality = distribution.node_orthogonality(g, height=2)

        assert orthogonality == 1 / 2


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

    def test_dataset_exceeding_recursion_depth(self):
        # The recursive implementation is limited do to the limited recursion depth
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
