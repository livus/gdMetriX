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

import networkx as nx

# noinspection PyUnresolvedReferences
import pytest

# noinspection PyUnresolvedReferences
import pytest_socket

from gdMetriX import distribution


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
