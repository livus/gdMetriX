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
    Unittests for boundary.py
"""

import math
import random
import unittest

import networkx as nx
# noinspection PyUnresolvedReferences
import pytest
# noinspection PyUnresolvedReferences
import pytest_socket

from gdMetriX import boundary


class TestArea(unittest.TestCase):

    def test_empty_graph(self):
        g = nx.Graph()
        area = boundary.area(g)

        assert area == 0

    def test_single_node(self):
        g = nx.Graph()
        g.add_node(1, pos=(-4, 159.0))
        area = boundary.area(g)

        assert area == 0

    def test_node_pair(self):
        g = nx.Graph()
        g.add_node(1, pos=(0, 3))
        g.add_node(2, pos=(4, 0))
        area = boundary.area(g)

        assert area == 12

    def test_line(self):
        g = nx.Graph()
        g.add_node(1, pos=(0, 1))
        g.add_node(2, pos=(0, 2))
        g.add_node(3, pos=(0, 4))
        g.add_node(4, pos=(0, 8))
        g.add_node(5, pos=(0, 16))

        area = boundary.area(g)

        assert area == 0

    def test_line_2(self):
        g = nx.Graph()
        g.add_node(1, pos=(1, 0))
        g.add_node(2, pos=(2, 0))
        g.add_node(3, pos=(4, 0))
        g.add_node(4, pos=(8, 0))
        g.add_node(5, pos=(16, 0))
        area = boundary.area(g)

        assert area == 0

    def test_rectangle(self):
        g = nx.Graph()
        g.add_node(1, pos=(0, 0))
        g.add_node(2, pos=(1, 0))
        g.add_node(3, pos=(1, 1))
        g.add_node(4, pos=(0, 1))
        area = boundary.area(g)

        assert area == 1

    def test_circle(self):
        g = nx.Graph()
        for i in range(0, 360):
            g.add_node(i, pos=(math.sin(math.radians(i)), math.cos(math.radians(i))))
            if i < 360 - 1:
                g.add_edge(i, i + 1)
        area = boundary.area(g)

        assert area == 4

    def test_empty_graph_tight(self):
        g = nx.Graph()
        area = boundary.area_tight(g)

        assert area == 0

    def test_single_node_tight(self):
        g = nx.Graph()
        g.add_node(1, pos=(-4, 159.0))
        area = boundary.area_tight(g)

        assert area == 0

    def test_node_pair_tight(self):
        g = nx.Graph()
        g.add_node(1, pos=(0, 3))
        g.add_node(2, pos=(4, 0))
        area = boundary.area_tight(g)

        assert area == 0

    def test_line_tight(self):
        g = nx.Graph()
        g.add_node(1, pos=(0, 1))
        g.add_node(2, pos=(0, 2))
        g.add_node(3, pos=(0, 4))
        g.add_node(4, pos=(0, 8))
        g.add_node(5, pos=(0, 16))

        area = boundary.area_tight(g)

        assert area == 0

    def test_line_2_tight(self):
        g = nx.Graph()
        g.add_node(1, pos=(1, 0))
        g.add_node(2, pos=(2, 0))
        g.add_node(3, pos=(4, 0))
        g.add_node(4, pos=(8, 0))
        g.add_node(5, pos=(16, 0))
        area = boundary.area_tight(g)

        assert area == 0

    def test_rectangle_tight(self):
        g = nx.Graph()
        g.add_node(1, pos=(0, 0))
        g.add_node(2, pos=(1, 0))
        g.add_node(3, pos=(1, 1))
        g.add_node(4, pos=(0, 1))
        area = boundary.area_tight(g)

        assert area == 1

    def test_circle_tight(self):
        g = nx.Graph()
        for i in range(0, 360):
            g.add_node(i, pos=(math.sin(math.radians(i)), math.cos(math.radians(i))))
            if i < 360 - 1:
                g.add_edge(i, i + 1)
        area = boundary.area_tight(g)

        assert math.isclose(area, math.pi, rel_tol=10e-2)


class TestBorder(unittest.TestCase):

    def test_border_empty_graph(self):
        g = nx.Graph()
        border = boundary.bounding_box(g)
        assert border is None

    def test_border_singleton(self):
        g = nx.Graph()
        g.add_node(1, pos=(0, 0))
        border = boundary.bounding_box(g)

        assert border == (0, 0, 0, 0)

    def test_border_rectangle(self):
        g = nx.Graph()
        g.add_node(1, pos=(0, 0))
        g.add_node(2, pos=(1, 0))
        g.add_node(3, pos=(1, 1))
        g.add_node(4, pos=(0, 1))

        border = boundary.bounding_box(g)

        assert border == (0, 0, 1, 1)

    def test_border_rectangle_2(self):
        g = nx.Graph()
        g.add_node(1, pos=(-5, -1))
        g.add_node(2, pos=(2, -1))
        g.add_node(3, pos=(2, 3))
        g.add_node(4, pos=(-5, 3))

        border = boundary.bounding_box(g)

        assert border == (-5, -1, 2, 3)


class TestHighAndWidth(unittest.TestCase):

    def test_height_empty_graph(self):
        g = nx.Graph()
        height = boundary.height(g)
        assert height == 0

    def test_height_singleton(self):
        g = nx.Graph()
        g.add_node(1, pos=(0, 0))
        height = boundary.height(g)

        assert height == 0

    def test_height_rectangle(self):
        g = nx.Graph()
        g.add_node(1, pos=(-5, -1))
        g.add_node(2, pos=(2, -1))
        g.add_node(3, pos=(2, 3))
        g.add_node(4, pos=(-5, 3))

        height = boundary.height(g)

        assert height == 4

    def test_width_empty_graph(self):
        g = nx.Graph()
        width = boundary.width(g)
        assert width == 0

    def test_width_singleton(self):
        g = nx.Graph()
        g.add_node(1, pos=(0, 0))
        width = boundary.width(g)

        assert width == 0

    def test_width_rectangle_2(self):
        g = nx.Graph()
        g.add_node(1, pos=(-5, -1))
        g.add_node(2, pos=(2, -1))
        g.add_node(3, pos=(2, 3))
        g.add_node(4, pos=(-5, 3))

        width = boundary.width(g)

        assert width == 7


class TestAspectRatio(unittest.TestCase):

    def test_empty_graph(self):
        g = nx.Graph()
        ratio = boundary.aspect_ratio(g)
        assert ratio is None

    def test_singleton(self):
        g = nx.Graph()
        g.add_node(1, pos=(0, 0))
        ratio = boundary.aspect_ratio(g)

        assert ratio == 1

    def test_line(self):
        g = nx.Graph()
        g.add_node(1, pos=(0, 0))
        g.add_node(2, pos=(0, 1))
        g.add_node(3, pos=(0, 2))
        g.add_node(4, pos=(0, 3))
        g.add_node(5, pos=(0, 4))

        ratio = boundary.aspect_ratio(g)

        assert ratio == 0

    def test_line_2(self):
        g = nx.Graph()
        g.add_node(1, pos=(0, 0))
        g.add_node(2, pos=(1, 0))
        g.add_node(3, pos=(2, 0))
        g.add_node(4, pos=(3, 0))
        g.add_node(5, pos=(4, 0))

        ratio = boundary.aspect_ratio(g)

        assert ratio == 0

    def test_aspect_ratio(self):
        g = nx.Graph()
        g.add_node(1, pos=(0, 0))
        g.add_node(2, pos=(2, 3))
        g.add_node(3, pos=(1, 1))
        g.add_node(3, pos=(2, 2))
        g.add_node(3, pos=(7, 4))

        ratio = boundary.aspect_ratio(g)

        assert math.isclose(ratio, 4 / 7)

    def test_aspect_ratio_2(self):
        g = nx.Graph()
        g.add_node(1, pos=(0, 0))
        g.add_node(2, pos=(3, 2))
        g.add_node(3, pos=(1, 1))
        g.add_node(3, pos=(2, 2))
        g.add_node(3, pos=(4, 7))

        ratio = boundary.aspect_ratio(g)

        assert math.isclose(ratio, 4 / 7)


class TestNormalizePosition(unittest.TestCase):

    def test_empty_graph(self):
        g = nx.Graph()
        pos = boundary.normalize_positions(g)

        assert pos == {}

    def test_singleton_graph(self):
        g = nx.Graph()
        g.add_node(1, pos=(-2.4, 5))
        pos = boundary.normalize_positions(g)

        assert pos == {1: (0, 0)}

    def test_rectangle(self):
        g = nx.Graph()
        g.add_node(1, pos=(5.5, 5.5))
        g.add_node(2, pos=(0, 0))
        g.add_node(3, pos=(5.5, 0))
        g.add_node(4, pos=(0, 5.5))
        pos = boundary.normalize_positions(g)

        assert pos == {1: (0.5, 0.5), 2: (-0.5, -0.5), 3: (0.5, -0.5), 4: (-0.5, 0.5)}

    def test_rectangle_2(self):
        random.seed(3940230490234)
        for i in range(0, 100):
            start_x = random.uniform(-1000, 1000)
            start_y = random.uniform(-1000, 1000)
            size = random.uniform(1, 1000)
            g = nx.Graph()
            g.add_node(1, pos=(start_x, start_y))
            g.add_node(2, pos=(start_x + size, start_y))
            g.add_node(3, pos=(start_x + size, start_y + size))
            g.add_node(4, pos=(start_x, start_y + size))

            pos = boundary.normalize_positions(g)

            assert (math.isclose(pos[1][0], -0.5))
            assert (math.isclose(pos[1][1], -0.5))
            assert (math.isclose(pos[2][0], 0.5))
            assert (math.isclose(pos[2][1], -0.5))
            assert (math.isclose(pos[3][0], 0.5))
            assert (math.isclose(pos[3][1], 0.5))
            assert (math.isclose(pos[4][0], -0.5))
            assert (math.isclose(pos[4][1], 0.5))

    def test_line(self):
        g = nx.Graph()
        g.add_node(1, pos=(1, 0))
        g.add_node(2, pos=(2, 0))
        g.add_node(3, pos=(3, 0))

        pos = boundary.normalize_positions(g)

        assert pos[1] == (-0.5, 0)
        assert pos[2] == (0, 0)
        assert pos[3] == (0.5, 0)

    def test_line_2(self):
        g = nx.Graph()
        g.add_node(1, pos=(1, 5))
        g.add_node(2, pos=(2, 5))
        g.add_node(3, pos=(3, 5))

        pos = boundary.normalize_positions(g)

        assert pos[1] == (-0.5, 0)
        assert pos[2] == (0, 0)
        assert pos[3] == (0.5, 0)

    def test_rectangle_3(self):
        g = nx.Graph()
        g.add_node(1, pos=(0, 0))
        g.add_node(2, pos=(4, 0))
        g.add_node(3, pos=(0, 2))
        g.add_node(4, pos=(4, 2))

        pos = boundary.normalize_positions(g)

        assert pos[1] == (-0.5, -0.25)
        assert pos[2] == (0.5, -0.25)
        assert pos[3] == (-0.5, 0.25)
        assert pos[4] == (0.5, 0.25)

    def test_rectangle_4(self):
        g = nx.Graph()
        g.add_node(1, pos=(0, 0))
        g.add_node(2, pos=(0, 4))
        g.add_node(3, pos=(2, 0))
        g.add_node(4, pos=(2, 4))

        pos = boundary.normalize_positions(g)

        print(pos)

        assert pos[1] == (-0.25, -0.5)
        assert pos[2] == (-0.25, 0.5)
        assert pos[3] == (0.25, -0.5)
        assert pos[4] == (0.25, 0.5)

    def test_rectangle_without_preserving_aspect_ratio(self):
        random.seed(1938459234)

        for i in range(0, 3500):
            height = random.uniform(0.001, 10000)
            width = random.uniform(0.001, 10000)
            x = random.uniform(-10000, 10000)
            y = random.uniform(-10000, 10000)

            g = nx.Graph()
            g.add_node(1, pos=(x, y))
            g.add_node(2, pos=(x, y + height))
            g.add_node(3, pos=(x + width, y))
            g.add_node(4, pos=(x + width, y + height))

            pos = boundary.normalize_positions(g, preserve_aspect_ratio=False)

            assert pos == {1: (-0.5, -0.5), 2: (-0.5, 0.5), 3: (0.5, -0.5), 4: (0.5, 0.5)}

    def test_horizontal_graph_in_horizontal_box_1(self):
        g = nx.Graph()
        g.add_node(1, pos=(-1, -1))
        g.add_node(2, pos=(3, -1))
        g.add_node(3, pos=(-1, 1))
        g.add_node(4, pos=(3, 1))

        pos = boundary.normalize_positions(g, box=(1, 1, 5, 2))

        print(pos)

        assert pos[1] == (2, 1)
        assert pos[2] == (4, 1)
        assert pos[3] == (2, 2)
        assert pos[4] == (4, 2)

    def test_horizontal_graph_in_horizontal_box_2(self):
        g = nx.Graph()
        g.add_node(1, pos=(-1, -1))
        g.add_node(2, pos=(3, -1))
        g.add_node(3, pos=(-1, 0))
        g.add_node(4, pos=(3, 0))

        pos = boundary.normalize_positions(g, box=(1, 1, 5, 3))

        print(pos)

        assert pos[1] == (1, 1.5)
        assert pos[2] == (5, 1.5)
        assert pos[3] == (1, 2.5)
        assert pos[4] == (5, 2.5)

    def test_vertical_graph_in_vertical_box_1(self):
        g = nx.Graph()
        g.add_node(1, pos=(-1, -1))
        g.add_node(2, pos=(-1, 3))
        g.add_node(3, pos=(1, -1))
        g.add_node(4, pos=(1, 3))

        pos = boundary.normalize_positions(g, box=(1, 1, 2, 5))

        print(pos)

        assert pos[1] == (1, 2)
        assert pos[2] == (1, 4)
        assert pos[3] == (2, 2)
        assert pos[4] == (2, 4)

    def test_vertical_graph_in_vertical_box_2(self):
        g = nx.Graph()
        g.add_node(1, pos=(-1, -1))
        g.add_node(2, pos=(-1, 3))
        g.add_node(3, pos=(0, -1))
        g.add_node(4, pos=(0, 3))

        pos = boundary.normalize_positions(g, box=(1, 1, 3, 5))

        print(pos)

        assert pos[1] == (1.5, 1)
        assert pos[2] == (1.5, 5)
        assert pos[3] == (2.5, 1)
        assert pos[4] == (2.5, 5)

    def test_horizontal_graph_in_vertical_box(self):
        g = nx.Graph()
        g.add_node(1, pos=(0, 5))
        g.add_node(2, pos=(10, 0))
        g.add_node(3, pos=(10, 5))
        g.add_node(4, pos=(0, 0))
        g.add_node(5, pos=(5, 2.5))

        pos = boundary.normalize_positions(g, box=(-5, -5, 0, 5))

        print(pos)

        assert pos[1] == (-5, 1.25)
        assert pos[2] == (0, -1.25)
        assert pos[3] == (0, 1.25)
        assert pos[4] == (-5, -1.25)
        assert pos[5] == (-2.5, 0)

    def test_vertical_graph_in_horizontal_box(self):
        g = nx.Graph()
        g.add_node(1, pos=(5, 0))
        g.add_node(2, pos=(0, 10))
        g.add_node(3, pos=(5, 10))
        g.add_node(4, pos=(0, 0))
        g.add_node(5, pos=(2.5, 5))

        pos = boundary.normalize_positions(g, box=(-5, -5, 5, 0))

        print(pos)

        assert pos[1] == (1.25, -5)
        assert pos[2] == (-1.25, 0)
        assert pos[3] == (1.25, 0)
        assert pos[4] == (-1.25, -5)
        assert pos[5] == (0, -2.5)
