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
