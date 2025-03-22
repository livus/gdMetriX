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
Unit tests for crossing detection.
"""

import math
import random
import unittest
from itertools import combinations

from libpysal import weights
from libpysal.cg import voronoi_frames

import inspect
import networkx as nx

# noinspection PyUnresolvedReferences
import pytest

import crossing_test_helper
from gdMetriX import crossings
from gdMetriX.crossing_data_types import CrossingPoint


def _assert_crossing_equality(
    g,
    crossing_list,
    include_rotation: bool = False,
    include_node_crossings: bool = False,
):
    crossing_test_helper.assert_crossing_equality(
        g,
        crossing_list,
        crossings.get_crossings,
        include_rotation,
        include_node_crossings,
        title=inspect.getouterframes(inspect.currentframe(), 2)[1][3],
    )


class TestSimpleCrossings(unittest.TestCase):

    def test_empty_graph(self):
        g = nx.Graph()
        _assert_crossing_equality(g, [])

    def test_singleton(self):
        g = nx.Graph()
        g.add_node(1, pos=(0, 0))
        _assert_crossing_equality(g, [])

    def test_non_crossing_graph_without_verticals_or_horizontals(self):
        g = nx.Graph()
        g.add_node(1, pos=(2, 7))
        g.add_node(2, pos=(4, 7))
        g.add_node(3, pos=(7, 7))
        g.add_node(4, pos=(4, 6))
        g.add_node(5, pos=(1, 4))
        g.add_node(6, pos=(2, 4))
        g.add_node(7, pos=(3, 4))
        g.add_node(8, pos=(5, 4))
        g.add_node(9, pos=(7, 4))
        g.add_node(10, pos=(2, 3))
        g.add_node(11, pos=(7, 3))
        g.add_node(12, pos=(3, 2))
        g.add_node(13, pos=(4, 2))
        g.add_node(14, pos=(5, 2))
        g.add_node(15, pos=(7, 2))
        g.add_node(16, pos=(1, 1))
        g.add_node(17, pos=(2, 1))
        g.add_node(18, pos=(5, 1))
        g.add_node(19, pos=(6, 1))
        g.add_node(20, pos=(2, 0))
        g.add_edges_from(
            [
                (1, 5),
                (1, 7),
                (2, 9),
                (4, 8),
                (6, 13),
                (10, 16),
                (11, 18),
                (12, 17),
                (14, 20),
                (15, 19),
            ]
        )
        _assert_crossing_equality(g, [])

    def test_non_crossing_graph_1(self):
        g = nx.Graph()
        g.add_node(1, pos=(1, 1))
        g.add_node(2, pos=(3, 3))
        g.add_node(3, pos=(3, 1))
        g.add_node(4, pos=(4, 1))
        g.add_node(5, pos=(5, 4))
        g.add_node(6, pos=(1, 3))
        g.add_node(7, pos=(3, 5))
        g.add_node(8, pos=(4, 2))
        g.add_node(9, pos=(6, 5))
        g.add_node(10, pos=(8, 5))
        g.add_edges_from(
            [(1, 2), (2, 3), (2, 5), (2, 7), (4, 5), (5, 7), (6, 7), (9, 10)]
        )
        _assert_crossing_equality(g, [], True)

    def test_non_crossing_graph_2(self):
        g = nx.Graph()
        g.add_node(1, pos=(1, 1))
        g.add_node(2, pos=(9, 7))
        g.add_node(3, pos=(5, 7))
        g.add_node(4, pos=(5, 6))
        g.add_node(5, pos=(5, 5))
        g.add_node(6, pos=(5, 4))
        g.add_node(7, pos=(5, 3))
        g.add_node(8, pos=(5, 2))
        g.add_node(9, pos=(5, 1))
        g.add_edges_from(
            [
                (1, 3),
                (1, 4),
                (1, 5),
                (1, 6),
                (1, 7),
                (1, 8),
                (1, 9),
                (2, 3),
                (2, 4),
                (2, 5),
                (2, 6),
                (2, 7),
                (2, 8),
                (2, 9),
            ]
        )
        _assert_crossing_equality(g, [], True)

    def test_simple_crossing_0(self):
        g = nx.Graph()
        g.add_node(1, pos=(0, 0))
        g.add_node(2, pos=(1, 0))
        g.add_node(3, pos=(1, 1))
        g.add_node(4, pos=(0, 1))
        g.add_edges_from([(1, 3), (2, 4)])
        _assert_crossing_equality(
            g, [crossings.Crossing(crossings.CrossingPoint(0.5, 0.5), {(1, 3), (2, 4)})]
        )

    def test_simple_crossing_1(self):
        g = nx.Graph()
        g.add_node(1, pos=(0, 0))
        g.add_node(2, pos=(1, 0))
        g.add_node(3, pos=(1, 1))
        g.add_node(4, pos=(0, 1))
        g.add_edges_from([(1, 2), (1, 3), (1, 4), (2, 3), (2, 4), (3, 4)])
        _assert_crossing_equality(
            g, [crossings.Crossing(crossings.CrossingPoint(0.5, 0.5), {(1, 3), (2, 4)})]
        )

    def test_simple_crossing_2(self):
        g = nx.Graph()
        g.add_node(1, pos=(1, 1))
        g.add_node(2, pos=(4, 4))
        g.add_node(3, pos=(1, 2))
        g.add_node(4, pos=(4, 5))
        g.add_node(5, pos=(1, 3))
        g.add_node(6, pos=(4, 6))
        g.add_node(7, pos=(1, 4))
        g.add_node(8, pos=(4, 7))
        g.add_node(9, pos=(3, 7))
        g.add_node(10, pos=(3, 1))
        g.add_edges_from([(1, 2), (3, 4), (5, 6), (7, 8), (9, 10)])
        _assert_crossing_equality(
            g,
            [
                crossings.Crossing(crossings.CrossingPoint(3, 3), {(1, 2), (9, 10)}),
                crossings.Crossing(crossings.CrossingPoint(3, 4), {(3, 4), (9, 10)}),
                crossings.Crossing(crossings.CrossingPoint(3, 5), {(5, 6), (9, 10)}),
                crossings.Crossing(crossings.CrossingPoint(3, 6), {(7, 8), (9, 10)}),
            ],
        )

    def test_end_point_crossing(self):
        g = nx.Graph()
        g.add_node(1, pos=(0, 5))
        g.add_node(2, pos=(4, 5))
        g.add_node(3, pos=(0, 4))
        g.add_node(4, pos=(4, 4))
        g.add_node(5, pos=(2, 3))
        g.add_node(6, pos=(0, 0))
        g.add_node(7, pos=(4, 0))
        g.add_edges_from([(1, 5), (2, 5), (3, 7), (4, 6)])
        _assert_crossing_equality(
            g, [crossings.Crossing(crossings.CrossingPoint(2, 2), {(3, 7), (4, 6)})]
        )

    def test_non_crossing_graph_directed(self):
        g = nx.DiGraph()
        g.add_node(1, pos=(1, 1))
        g.add_node(2, pos=(3, 3))
        g.add_node(3, pos=(3, 1))
        g.add_node(4, pos=(4, 1))
        g.add_node(5, pos=(5, 4))
        g.add_node(6, pos=(1, 3))
        g.add_node(7, pos=(3, 5))
        g.add_node(8, pos=(4, 2))
        g.add_node(9, pos=(6, 5))
        g.add_node(10, pos=(8, 5))
        g.add_edges_from(
            [(1, 2), (2, 3), (2, 5), (2, 7), (4, 5), (5, 7), (6, 7), (9, 10)]
        )
        _assert_crossing_equality(g, [], True)

    def test_crossing_graph_directed(self):
        g = nx.DiGraph()
        g.add_node(1, pos=(0, 0))
        g.add_node(2, pos=(1, 0))
        g.add_node(3, pos=(1, 1))
        g.add_node(4, pos=(0, 1))
        g.add_edges_from([(1, 3), (2, 4)])
        _assert_crossing_equality(
            g, [crossings.Crossing(crossings.CrossingPoint(0.5, 0.5), {(1, 3), (2, 4)})]
        )

    def test_self_loop(self):
        g = nx.DiGraph()
        g.add_node(1, pos=(0, 0))
        g.add_edge(1, 1)

        _assert_crossing_equality(g, [], True, True)

    def test_self_loop_in_edge(self):
        g = nx.DiGraph()
        g.add_node(1, pos=(0, 0))
        g.add_node(2, pos=(-1, 0))
        g.add_node(3, pos=(1, 0))
        g.add_edge(1, 1)
        g.add_edge(2, 3)

        _assert_crossing_equality(g, [], True)

    def test_self_loop_in_edge_2(self):
        g = nx.DiGraph()
        g.add_node(1, pos=(0, 0))
        g.add_node(2, pos=(-1, 0))
        g.add_node(3, pos=(1, 0))
        g.add_edge(1, 1)
        g.add_edge(2, 3)

        _assert_crossing_equality(
            g,
            [crossings.Crossing(crossings.CrossingPoint(0, 0), {(2, 3), (1, 1)})],
            True,
            True,
        )

    def test_self_loop_in_crossing(self):
        g = nx.DiGraph()
        g.add_node(1, pos=(0, 0))
        g.add_node(2, pos=(-1, -1))
        g.add_node(3, pos=(1, 1))
        g.add_node(4, pos=(-1, 1))
        g.add_node(5, pos=(1, -1))
        g.add_edges_from([(1, 1), (2, 3), (4, 5)])

        _assert_crossing_equality(
            g,
            [crossings.Crossing(crossings.CrossingPoint(0, 0), {(2, 3), (4, 5)})],
            True,
        )

    def test_self_loop_in_crossing_2(self):
        g = nx.DiGraph()
        g.add_node(1, pos=(0, 0))
        g.add_node(2, pos=(-1, -1))
        g.add_node(3, pos=(1, 1))
        g.add_node(4, pos=(-1, 1))
        g.add_node(5, pos=(1, -1))
        g.add_edges_from([(1, 1), (2, 3), (4, 5)])

        _assert_crossing_equality(
            g,
            [
                crossings.Crossing(
                    crossings.CrossingPoint(0, 0), {(1, 1), (2, 3), (4, 5)}
                )
            ],
            True,
            True,
        )


class TestCrossingsInvolvingVertices(unittest.TestCase):

    def test_vertex_at_edge_1(self):
        g = nx.Graph()
        g.add_node(1, pos=(0, 0))
        g.add_node(2, pos=(0, 2))
        g.add_node(3, pos=(0, 1))
        g.add_node(4, pos=(1, 2))
        g.add_edges_from([(1, 2), (3, 4)])
        _assert_crossing_equality(
            g,
            [crossings.Crossing(crossings.CrossingPoint(0, 1), {(1, 2), (3, 4)})],
            include_node_crossings=True,
        )

    def test_vertex_at_edge_2(self):
        g = nx.Graph()
        g.add_node(1, pos=(0, 0))
        g.add_node(2, pos=(0, 2))
        g.add_node(3, pos=(0, 1))
        g.add_node(4, pos=(1, 1))
        g.add_edges_from([(1, 2), (3, 4)])
        _assert_crossing_equality(
            g,
            [crossings.Crossing(crossings.CrossingPoint(0, 1), {(1, 2), (3, 4)})],
            include_node_crossings=True,
        )

    def test_vertex_at_edge_3(self):
        g = nx.Graph()
        g.add_node(1, pos=(0, 0))
        g.add_node(2, pos=(0, 2))
        g.add_node(3, pos=(0, 1))
        g.add_node(4, pos=(1, 0))
        g.add_edges_from([(1, 2), (3, 4)])
        _assert_crossing_equality(
            g,
            [crossings.Crossing(crossings.CrossingPoint(0, 1), {(1, 2), (3, 4)})],
            include_node_crossings=True,
        )

    def test_vertex_at_edge_4(self):
        g = nx.Graph()
        g.add_node(1, pos=(0, 1))
        g.add_node(2, pos=(2, 1))
        g.add_node(3, pos=(1, 1))
        g.add_node(4, pos=(1, 0))

        g.add_edges_from([(1, 2), (3, 4)])
        _assert_crossing_equality(
            g,
            [crossings.Crossing(crossings.CrossingPoint(1, 1), {(1, 2), (3, 4)})],
            include_node_crossings=True,
        )

    def test_vertex_at_edge_5(self):
        g = nx.Graph()
        g.add_node(1, pos=(0, 1))
        g.add_node(2, pos=(2, 1))
        g.add_node(3, pos=(1, 1))
        g.add_node(4, pos=(0, 0))
        g.add_edges_from([(1, 2), (3, 4)])
        _assert_crossing_equality(
            g,
            [crossings.Crossing(crossings.CrossingPoint(1, 1), {(1, 2), (3, 4)})],
            include_node_crossings=True,
        )

    def test_vertex_at_edge_6(self):
        g = nx.Graph()
        g.add_node(1, pos=(0, 1))
        g.add_node(2, pos=(2, 1))
        g.add_node(3, pos=(1, 1))
        g.add_node(4, pos=(2, 0))
        g.add_edges_from([(1, 2), (3, 4)])
        _assert_crossing_equality(
            g,
            [crossings.Crossing(crossings.CrossingPoint(1, 1), {(1, 2), (3, 4)})],
            include_node_crossings=True,
        )

    def test_vertex_at_edge_7(self):
        g = nx.Graph()
        g.add_node(1, pos=(0, 1))
        g.add_node(2, pos=(2, 1))
        g.add_node(3, pos=(1, 1))
        g.add_node(4, pos=(1, 0))

        g.add_edges_from([(1, 2), (3, 4)])
        _assert_crossing_equality(
            g,
            [crossings.Crossing(crossings.CrossingPoint(1, 1), {(1, 2), (3, 4)})],
            True,
            True,
        )

    def test_vertex_at_edge_8(self):
        g = nx.Graph()
        g.add_node(1, pos=(0, 1))
        g.add_node(2, pos=(2, 1))
        g.add_node(3, pos=(1, 1))
        g.add_node(4, pos=(0, 0))
        g.add_edges_from([(1, 2), (3, 4)])
        _assert_crossing_equality(
            g,
            [crossings.Crossing(crossings.CrossingPoint(1, 1), {(1, 2), (3, 4)})],
            True,
            True,
        )

    def test_vertex_at_edge_9(self):
        g = nx.Graph()
        g.add_node(1, pos=(0, 1))
        g.add_node(2, pos=(2, 1))
        g.add_node(3, pos=(1, 1))
        g.add_node(4, pos=(2, 0))
        g.add_edges_from([(1, 2), (3, 4)])
        _assert_crossing_equality(
            g,
            [crossings.Crossing(crossings.CrossingPoint(1, 1), {(1, 2), (3, 4)})],
            True,
            True,
        )

    def test_vertex_at_edge_1_disabled(self):
        g = nx.Graph()
        g.add_node(1, pos=(0, 0))
        g.add_node(2, pos=(0, 2))
        g.add_node(3, pos=(0, 1))
        g.add_node(4, pos=(1, 2))
        g.add_edges_from([(1, 2), (3, 4)])
        _assert_crossing_equality(g, [])

    def test_vertex_at_edge_2_disabled(self):
        g = nx.Graph()
        g.add_node(1, pos=(0, 0))
        g.add_node(2, pos=(0, 2))
        g.add_node(3, pos=(0, 1))
        g.add_node(4, pos=(1, 1))
        g.add_edges_from([(1, 2), (3, 4)])
        _assert_crossing_equality(g, [])

    def test_vertex_at_edge_3_disabled(self):
        g = nx.Graph()
        g.add_node(1, pos=(0, 0))
        g.add_node(2, pos=(0, 2))
        g.add_node(3, pos=(0, 1))
        g.add_node(4, pos=(1, 0))
        g.add_edges_from([(1, 2), (3, 4)])
        _assert_crossing_equality(g, [])

    def test_vertex_at_edge_4_disabled(self):
        g = nx.Graph()
        g.add_node(1, pos=(0, 1))
        g.add_node(2, pos=(2, 1))
        g.add_node(3, pos=(1, 1))
        g.add_node(4, pos=(1, 0))

        g.add_edges_from([(1, 2), (3, 4)])
        _assert_crossing_equality(g, [])

    def test_vertex_at_edge_5_disabled(self):
        g = nx.Graph()
        g.add_node(1, pos=(0, 1))
        g.add_node(2, pos=(2, 1))
        g.add_node(3, pos=(1, 1))
        g.add_node(4, pos=(0, 0))
        g.add_edges_from([(1, 2), (3, 4)])
        _assert_crossing_equality(g, [])

    def test_vertex_at_edge_6_disabled(self):
        g = nx.Graph()
        g.add_node(1, pos=(0, 1))
        g.add_node(2, pos=(2, 1))
        g.add_node(3, pos=(1, 1))
        g.add_node(4, pos=(2, 0))
        g.add_edges_from([(1, 2), (3, 4)])
        _assert_crossing_equality(g, [])

    def test_vertex_at_edge_7_disabled(self):
        g = nx.Graph()
        g.add_node(1, pos=(0, 1))
        g.add_node(2, pos=(2, 1))
        g.add_node(3, pos=(1, 1))
        g.add_node(4, pos=(1, 0))

        g.add_edges_from([(1, 2), (3, 4)])
        _assert_crossing_equality(g, [], True)

    def test_vertex_at_edge_8_disabled(self):
        g = nx.Graph()
        g.add_node(1, pos=(0, 1))
        g.add_node(2, pos=(2, 1))
        g.add_node(3, pos=(1, 1))
        g.add_node(4, pos=(0, 0))
        g.add_edges_from([(1, 2), (3, 4)])
        _assert_crossing_equality(g, [], True)

    def test_vertex_at_edge_9_disabled(self):
        g = nx.Graph()
        g.add_node(1, pos=(0, 1))
        g.add_node(2, pos=(2, 1))
        g.add_node(3, pos=(1, 1))
        g.add_node(4, pos=(2, 0))
        g.add_edges_from([(1, 2), (3, 4)])
        _assert_crossing_equality(g, [], True)

    def test_vertex_at_vertex_1(self):
        g = nx.Graph()
        g.add_node(1, pos=(-2, -3))
        g.add_node(2, pos=(0, 0))
        g.add_node(3, pos=(-1, 1))
        g.add_node(4, pos=(0, 0))
        g.add_edges_from([(1, 2), (3, 4)])
        _assert_crossing_equality(
            g,
            [crossings.Crossing(crossings.CrossingPoint(0, 0), {(1, 2), (3, 4)})],
            True,
            True,
        )

    def test_vertex_at_vertex_2(self):
        g = nx.Graph()
        g.add_node(1, pos=(-2, -3))
        g.add_node(2, pos=(0, 0))
        g.add_node(3, pos=(-1, 1))
        g.add_node(4, pos=(0, 0))
        g.add_edges_from([(1, 2), (3, 4)])
        _assert_crossing_equality(g, [], True)


class TestHorizontalCrossings(unittest.TestCase):

    def test_vertical_horizontal_crossing(self):
        g = nx.Graph()
        g.add_node(1, pos=(0, 1))
        g.add_node(2, pos=(2, 1))
        g.add_node(3, pos=(1, 0))
        g.add_node(4, pos=(1, 2))
        g.add_edges_from([(1, 2), (3, 4)])
        _assert_crossing_equality(
            g, [crossings.Crossing(crossings.CrossingPoint(1, 1), {(1, 2), (3, 4)})]
        )

    def test_horizontal_line_with_vertex_crossing(self):
        g = nx.Graph()
        g.add_node(1, pos=(0, 1))
        g.add_node(2, pos=(1, 1))
        g.add_node(3, pos=(2, 1))
        g.add_node(4, pos=(3, 1))
        g.add_node(5, pos=(0, 0))
        g.add_node(6, pos=(3, 2))

        g.add_edges_from([(1, 4), (2, 5), (3, 6)])
        _assert_crossing_equality(
            g,
            crossings.get_crossings_quadratic(g, include_node_crossings=True),
            include_node_crossings=True,
        )

    def test_horizontal_multiple_crossing_lines(self):
        g = nx.Graph()
        g.add_node(1, pos=(0, 1))
        g.add_node(2, pos=(5, 1))
        g.add_node(3, pos=(1, 0))
        g.add_node(4, pos=(1, 2))
        g.add_node(5, pos=(2, 0))
        g.add_node(6, pos=(2, 2))
        g.add_node(7, pos=(3, 0))
        g.add_node(8, pos=(3, 2))
        g.add_node(9, pos=(4, 0))
        g.add_node(10, pos=(4, 2))
        g.add_edges_from([(1, 2), (3, 4), (5, 6), (7, 8), (9, 10)])

        _assert_crossing_equality(
            g,
            [
                crossings.Crossing(crossings.CrossingPoint(1, 1), {(1, 2), (3, 4)}),
                crossings.Crossing(crossings.CrossingPoint(2, 1), {(1, 2), (5, 6)}),
                crossings.Crossing(crossings.CrossingPoint(3, 1), {(1, 2), (7, 8)}),
                crossings.Crossing(crossings.CrossingPoint(4, 1), {(1, 2), (9, 10)}),
            ],
        )

    def test_overlapping_horizontal_lines(self):
        g = nx.Graph()
        g.add_node(1, pos=(0, 2.6))
        g.add_node(2, pos=(2, 2.6))
        g.add_node(3, pos=(1, 2.6))
        g.add_node(4, pos=(4, 2.6))
        g.add_edges_from([(1, 2), (3, 4)])

        _assert_crossing_equality(
            g,
            crossings.get_crossings_quadratic(g, include_node_crossings=True),
            include_node_crossings=True,
        )

    def test_crossing_over_horizontal_overlap(self):
        g = nx.Graph()
        g.add_node(1, pos=(0, 2.6))
        g.add_node(2, pos=(2, 2.6))
        g.add_node(3, pos=(1, 2.6))
        g.add_node(4, pos=(4, 2.6))
        g.add_node(5, pos=(1.8, 2))
        g.add_node(6, pos=(1.2, 3))
        g.add_edges_from([(1, 2), (3, 4), (5, 6)])

        _assert_crossing_equality(
            g,
            crossings.get_crossings_quadratic(g, include_node_crossings=True),
            include_node_crossings=True,
        )

    def test_crossing_over_horizontal_overlap_2(self):
        g = nx.Graph()
        g.add_node(1, pos=(0, 2.6))
        g.add_node(2, pos=(2, 2.6))
        g.add_node(3, pos=(1, 2.6))
        g.add_node(4, pos=(4, 2.6))
        g.add_node(5, pos=(1.8, 2))
        g.add_node(6, pos=(1.2, 3))
        g.add_node(7, pos=(-1, 2.6))
        g.add_node(8, pos=(5, 2.6))
        g.add_edges_from([(1, 2), (3, 4), (5, 6), (7, 8)])

        _assert_crossing_equality(
            g,
            crossings.get_crossings_quadratic(g, include_node_crossings=True),
            include_node_crossings=True,
        )

    def test_horizontal_edge_possibly_hiding_leftmost_edge_at_crossing(self):
        g = nx.Graph()

        g.add_node(1, pos=(0, 10))
        g.add_node(2, pos=(10, 10))
        g.add_node(3, pos=(4, 9))
        g.add_node(4, pos=(6, 11))
        g.add_node(5, pos=(4, 11))
        g.add_node(6, pos=(6, 9))
        g.add_edges_from([(1, 2), (3, 4), (5, 6)])

        _assert_crossing_equality(
            g,
            crossings.get_crossings_quadratic(g, include_node_crossings=False),
            include_node_crossings=False,
        )

    def test_horizontal_edges_just_touching(self):
        g = nx.Graph()
        g.add_node(1, pos=(2, 2))
        g.add_node(2, pos=(3, 2))
        g.add_node(3, pos=(3, 2))
        g.add_node(4, pos=(4, 2))
        g.add_edges_from([(1, 2), (3, 4)])

        _assert_crossing_equality(
            g,
            crossings.get_crossings_quadratic(g, include_node_crossings=True),
            include_node_crossings=True,
        )

    def test_horizontal_edges_just_touching_2(self):
        g = nx.Graph()
        g.add_node(1, pos=(2, 2))
        g.add_node(2, pos=(3, 2))
        g.add_node(3, pos=(3, 2))
        g.add_node(4, pos=(4, 2))
        g.add_edges_from([(1, 2), (3, 4)])

        _assert_crossing_equality(g, [], include_node_crossings=False)

    def test_horizontal_edges_just_touching_3(self):
        g = nx.Graph()
        g.add_node(1, pos=(2, 2))
        g.add_node(2, pos=(3, 2))
        g.add_node(3, pos=(3, 2))
        g.add_node(4, pos=(4, 3))
        g.add_edges_from([(1, 2), (3, 4)])

        _assert_crossing_equality(
            g,
            crossings.get_crossings_quadratic(g, include_node_crossings=True),
            include_node_crossings=True,
        )

    def test_horizontal_edges_just_touching_4(self):
        g = nx.Graph()
        g.add_node(1, pos=(2, 2))
        g.add_node(2, pos=(3, 2))
        g.add_node(3, pos=(3, 2))
        g.add_node(4, pos=(4, 3))
        g.add_edges_from([(1, 2), (3, 4)])

        _assert_crossing_equality(g, [], include_node_crossings=False)


class TestOverlappingCrossings(unittest.TestCase):

    def test_overlapping_crossing_1(self):
        g = nx.Graph()
        g.add_node(1, pos=(0, 0))
        g.add_node(2, pos=(10, 0))
        g.add_node(3, pos=(3, 0))
        g.add_node(4, pos=(7, 0))
        g.add_edges_from([(1, 2), (3, 4)])
        _assert_crossing_equality(
            g,
            [
                crossings.Crossing(
                    crossings.CrossingLine(CrossingPoint(3, 0), CrossingPoint(7, 0)),
                    {(1, 2), (3, 4)},
                )
            ],
        )

    def test_overlapping_crossing_2(self):
        g = nx.Graph()
        g.add_node(1, pos=(0, 0))
        g.add_node(2, pos=(7, 0))
        g.add_node(3, pos=(3, 0))
        g.add_node(4, pos=(10, 0))
        g.add_edges_from([(1, 2), (3, 4)])
        _assert_crossing_equality(
            g,
            [
                crossings.Crossing(
                    crossings.CrossingLine(CrossingPoint(3, 0), CrossingPoint(7, 0)),
                    {(1, 2), (3, 4)},
                )
            ],
        )

    def test_overlapping_crossing_3(self):
        g = nx.Graph()
        g.add_node(1, pos=(0, 0))
        g.add_node(2, pos=(0, 10))
        g.add_node(3, pos=(0, 3))
        g.add_node(4, pos=(0, 7))
        g.add_edges_from([(1, 2), (3, 4)])
        _assert_crossing_equality(
            g,
            [
                crossings.Crossing(
                    crossings.CrossingLine(CrossingPoint(0, 3), CrossingPoint(0, 7)),
                    {(1, 2), (3, 4)},
                )
            ],
        )

    def test_overlapping_crossing_4(self):
        g = nx.Graph()
        g.add_node(1, pos=(0, 0))
        g.add_node(2, pos=(0, 7))
        g.add_node(3, pos=(0, 3))
        g.add_node(4, pos=(0, 10))
        g.add_edges_from([(1, 2), (3, 4)])
        _assert_crossing_equality(
            g,
            [
                crossings.Crossing(
                    crossings.CrossingLine(CrossingPoint(0, 3), CrossingPoint(0, 7)),
                    {(1, 2), (3, 4)},
                )
            ],
        )

    def test_overlapping_edges_crossing_another(self):
        g = nx.Graph()
        g.add_node(1, pos=(0, 0))
        g.add_node(2, pos=(1, 1))
        g.add_node(3, pos=(2, 2))
        g.add_node(4, pos=(3, 3))
        g.add_node(5, pos=(0, 1.5))
        g.add_node(6, pos=(3, 1.5))
        g.add_edges_from([(1, 4), (2, 3), (5, 6)])
        _assert_crossing_equality(
            g,
            [
                crossings.Crossing(
                    crossings.CrossingLine(CrossingPoint(1, 1), CrossingPoint(2, 2)),
                    {(1, 4), (2, 3)},
                ),
                crossings.Crossing(
                    crossings.CrossingPoint(1.5, 1.5), {(1, 4), (2, 3), (5, 6)}
                ),
            ],
        )

    def test_overlapping_edges_crossing_another_2(self):
        g = nx.Graph()
        g.add_node(1, pos=(0, 0))
        g.add_node(2, pos=(1, 1))
        g.add_node(3, pos=(2, 2))
        g.add_node(4, pos=(3, 3))
        g.add_node(5, pos=(0, 1.5))
        g.add_node(6, pos=(3, 1.5))
        g.add_edges_from([(1, 3), (2, 4), (5, 6)])
        _assert_crossing_equality(
            g,
            [
                crossings.Crossing(
                    crossings.CrossingLine(CrossingPoint(1, 1), CrossingPoint(2, 2)),
                    {(1, 3), (2, 4)},
                ),
                crossings.Crossing(
                    crossings.CrossingPoint(1.5, 1.5), {(1, 3), (2, 4), (5, 6)}
                ),
            ],
        )

    def test_overlapping_edges_common_endpoint(self):
        g = nx.Graph()
        g.add_node(1, pos=(0, 0))
        g.add_node(2, pos=(3, -2))
        g.add_node(3, pos=(6, -4))

        g.add_edges_from([(1, 2), (1, 3)])

        _assert_crossing_equality(
            g,
            [
                crossings.Crossing(
                    crossings.CrossingLine(CrossingPoint(0, 0), CrossingPoint(3, -2)),
                    {(1, 2), (1, 3)},
                )
            ],
            True,
        )


class TestCommonEndpointCrossings(unittest.TestCase):

    def test_crossings_with_common_vertex(self):
        g = nx.Graph()
        g.add_node(1, pos=(0, 2))
        g.add_node(2, pos=(3, 2))
        g.add_node(3, pos=(1, 0))
        g.add_node(4, pos=(4, 0))

        g.add_node(5, pos=(1, 2))

        g.add_edges_from([(1, 4), (2, 3), (3, 5)])
        _assert_crossing_equality(
            g,
            [
                crossings.Crossing(crossings.CrossingPoint(1.0, 1.5), {(3, 5), (1, 4)}),
                crossings.Crossing(crossings.CrossingPoint(2.0, 1.0), {(2, 3), (1, 4)}),
            ],
        )

    def test_crossings_with_common_vertex_2(self):
        g = nx.Graph()
        g.add_node(1, pos=(0, 2))
        g.add_node(2, pos=(2, 2))
        g.add_node(3, pos=(1, 0))
        g.add_node(4, pos=(3, 0))

        g.add_node(5, pos=(1, 2))
        g.add_node(6, pos=(0, 1))

        g.add_edges_from([(1, 4), (2, 3), (3, 5), (4, 6)])

        _assert_crossing_equality(g, crossings.get_crossings_quadratic(g))


class TestComplexCrossingScenarios(unittest.TestCase):

    def test_multiple_edges_at_crossing(self):
        g = nx.Graph()
        g.add_node(1, pos=(-1, 1))
        g.add_node(2, pos=(0, 1))
        g.add_node(3, pos=(1, 1))
        g.add_node(4, pos=(-1, 0))
        g.add_node(5, pos=(1, 0))
        g.add_node(6, pos=(-1, -1))
        g.add_node(7, pos=(0, -1))
        g.add_node(8, pos=(1, -1))
        edges = {(1, 8), (2, 7), (3, 6), (4, 5)}
        g.add_edges_from(edges)
        _assert_crossing_equality(
            g, [crossings.Crossing(crossings.CrossingPoint(0, 0), edges)]
        )

    def test_no_crossing_with_shared_endpoint(self):
        g = nx.Graph()
        g.add_node(1, pos=(0, 0))
        g.add_node(2, pos=(1, 0))
        g.add_node(3, pos=(0, 1))
        g.add_edges_from([(1, 2), (2, 3)])
        _assert_crossing_equality(g, [], True)

    def test_single_crossing_containing_all_types(self):
        g = nx.Graph()
        g.add_node(1, pos=(-2, 4))
        g.add_node(2, pos=(-3, 3))
        g.add_node(3, pos=(1, 3))
        g.add_node(4, pos=(2, 3))
        g.add_node(5, pos=(-2, 2))
        g.add_node(6, pos=(2, 1))
        g.add_node(7, pos=(3, 1))
        g.add_node(8, pos=(0, 0))
        g.add_node(9, pos=(0.25, -2))
        g.add_node(10, pos=(-3, -4))
        g.add_node(11, pos=(-1, -4))
        g.add_node(12, pos=(1, -4))
        g.add_node(13, pos=(2, -4))
        g.add_node(14, pos=(-2, -6))
        g.add_edges_from(
            [
                (1, 13),
                (2, 11),
                (3, 14),
                (4, 8),
                (5, 8),
                (6, 8),
                (7, 12),
                (8, 9),
                (8, 10),
            ]
        )
        _assert_crossing_equality(
            g,
            [
                crossings.Crossing(
                    crossings.CrossingPoint(0, 0),
                    {(3, 14), (5, 8), (6, 8), (8, 10), (1, 13), (8, 9), (4, 8)},
                ),
                crossings.Crossing(
                    crossings.CrossingPoint(
                        1.44444444444444444444, -2.88888888888888888
                    ),
                    {(1, 13), (7, 12)},
                ),
                crossings.Crossing(
                    crossings.CrossingPoint(-1.1538461538461537, -3.4615384615384617),
                    {(3, 14), (2, 11)},
                ),
                crossings.Crossing(
                    crossings.CrossingPoint(-1.5517241379310345, -2.0689655172413794),
                    {(8, 10), (2, 11)},
                ),
            ],
            include_node_crossings=True,
        )

    def test_low_precision_group_crossing(self):
        g = nx.Graph()
        g.add_node(1, pos=(0, 3))
        g.add_node(2, pos=(2, 2.5))
        g.add_node(3, pos=(3.5, 3.5))
        g.add_node(4, pos=(4, 4.5))
        g.add_node(5, pos=(3, 0))
        g.add_node(6, pos=(0, 0))
        edges = [(1, 5), (2, 6), (3, 6), (4, 6)]
        g.add_edges_from(edges)

        crossing_list = crossings.get_crossings(g, precision=0.142)
        assert len(crossing_list) == 1
        assert math.isclose(crossing_list[0].pos[0], 1.5, rel_tol=0.142)
        assert math.isclose(crossing_list[0].pos[1], 1.5, rel_tol=0.142)

        # Note that we explicitly do not check for the contained edges as grouping crossings together which are not
        #  actually crossing at the same point

    def test_random_graph(self):
        random.seed(9018098129039)
        success_count = 0
        for i in range(0, 25):
            for j in range(0, 10):
                print(f"Current graph: {success_count}")
                random_graph = nx.fast_gnp_random_graph(
                    i, random.uniform(0.1, 1), random.randint(1, 10000000)
                )
                random_embedding = {
                    n: [random.randint(-1000, 1000), random.randint(-1000, 1000)]
                    for n in range(0, i + 1)
                }
                nx.set_node_attributes(random_graph, random_embedding, "pos")
                _assert_crossing_equality(
                    random_graph,
                    crossings.get_crossings_quadratic(random_graph),
                    include_node_crossings=True,
                )
                success_count += 1

    def test_intertwined_crossings_1(self):
        g = nx.Graph()
        g.add_nodes_from(range(0, 8))
        nx.set_node_attributes(
            g,
            {
                0: {"pos": [374, 427]},
                1: {"pos": [-214, -668]},
                2: {"pos": [605, 60]},
                3: {"pos": [439, 832]},
                4: {"pos": [910, 706]},
                5: {"pos": [338, 772]},
                6: {"pos": [-974, -948]},
                7: {"pos": [282, 760]},
            },
        )
        g.add_edges_from(
            [(0, 7), (0, 2), (1, 3), (1, 4), (2, 5), (2, 6), (5, 6), (5, 7)]
        )

        _assert_crossing_equality(
            g,
            crossings.get_crossings_quadratic(g),
            include_node_crossings=True,
        )

    def test_intertwined_crossings_2(self):
        g = nx.Graph()
        g.add_nodes_from(range(0, 15))
        nx.set_node_attributes(
            g,
            {
                0: {"pos": [-704, -795]},
                1: {"pos": [-616, 80]},
                2: {"pos": [376, -400]},
                3: {"pos": [-613, -542]},
                4: {"pos": [-261, 256]},
                5: {"pos": [-304, 721]},
                6: {"pos": [475, -560]},
                7: {"pos": [152, -854]},
                8: {"pos": [-487, 347]},
                9: {"pos": [207, -340]},
                10: {"pos": [-406, 122]},
                11: {"pos": [-102, 528]},
                12: {"pos": [199, -795]},
                13: {"pos": [309, -924]},
                14: {"pos": [59, -355]},
            },
        )
        g.add_edges_from([(6, 7), (1, 13), (4, 12), (7, 12), (0, 9), (10, 12)])

        # Remove empty nodes
        nodes_to_remove = [
            node for node, degree in dict(g.degree()).items() if degree == 0
        ]
        g.remove_nodes_from(nodes_to_remove)

        _assert_crossing_equality(
            g,
            crossings.get_crossings_quadratic(g),
            include_node_crossings=False,
        )

    def test_intertwined_crossings_3(self):
        g = nx.Graph()
        g.add_nodes_from([1, 2, 3, 4, 6, 8, 9])
        g.add_edges_from([(1, 8), (2, 9), (3, 6), (4, 9)])
        nx.set_node_attributes(
            g,
            {
                1: {"pos": [62, 170]},
                2: {"pos": [679, 196]},
                3: {"pos": [20, -674]},
                4: {"pos": [800, 375]},
                6: {"pos": [-841, 91]},
                8: {"pos": [-865, -969]},
                9: {"pos": [317, 170]},
            },
        )

        _assert_crossing_equality(
            g,
            crossings.get_crossings_quadratic(g),
            include_node_crossings=False,
        )

    def test_intertwined_crossings_4(self):
        g = nx.Graph()
        g.add_nodes_from([0, 1, 2, 3, 4, 5, 6])
        g.add_edges_from([(0, 5), (1, 4), (2, 3), (5, 6)])
        nx.set_node_attributes(
            g,
            {
                0: {"pos": [-524, 438]},
                1: {"pos": [-150, -984]},
                2: {"pos": [149, -584]},
                3: {"pos": [-917, -284]},
                4: {"pos": [54, -459]},
                5: {"pos": [-812, -284]},
                6: {"pos": [850, 971]},
            },
        )

        _assert_crossing_equality(
            g,
            crossings.get_crossings_quadratic(g),
            include_node_crossings=False,
        )

    def test_intertwined_crossings_5(self):
        g = nx.Graph()
        g.add_nodes_from([0, 1, 2, 3, 4, 5, 6])
        g.add_edges_from([(0, 5), (0, 6), (1, 6), (2, 3), (4, 6)])
        nx.set_node_attributes(
            g,
            {
                0: {"pos": [-392, -371]},
                1: {"pos": [671, 736]},
                2: {"pos": [-575, 85]},
                3: {"pos": [148, -927]},
                4: {"pos": [308, 654]},
                5: {"pos": [-28, 624]},
                6: {"pos": [29, 85]},
            },
        )

        _assert_crossing_equality(
            g,
            crossings.get_crossings_quadratic(g),
            include_node_crossings=False,
        )

    def test_intertwined_crossings_6(self):
        g = nx.Graph()
        g.add_nodes_from([4, 9, 12, 13, 14, 15, 18])
        g.add_edges_from([(4, 15), (9, 15), (12, 14), (13, 18)])
        nx.set_node_attributes(
            g,
            {
                4: {"pos": [209, 838]},
                9: {"pos": [-635, 780]},
                12: {"pos": [-486, -89]},
                13: {"pos": [-274, -553]},
                14: {"pos": [-402, -880]},
                15: {"pos": [-210, -89]},
                18: {"pos": [-433, -754]},
            },
        )

        _assert_crossing_equality(
            g,
            crossings.get_crossings_quadratic(g),
            include_node_crossings=False,
        )

    def test_intertwined_crossings_7(self):
        g = nx.Graph()
        g.add_nodes_from([0, 1, 2, 4, 5, 6, 7])
        g.add_edges_from([(0, 2), (1, 6), (1, 4), (5, 7)])
        nx.set_node_attributes(
            g,
            {
                0: {"pos": [-429, -575]},
                1: {"pos": [81, 603]},
                2: {"pos": [-148, 585]},
                4: {"pos": [892, 710]},
                5: {"pos": [-132, -434]},
                6: {"pos": [589, 626]},
                7: {"pos": [-964, 603]},
            },
        )

        _assert_crossing_equality(
            g,
            crossings.get_crossings_quadratic(g),
            include_node_crossings=False,
        )

    def test_intertwined_crossings_8(self):
        g = nx.Graph()
        g.add_nodes_from([1, 3, 6, 9, 10, 11, 12, 13, 15, 16, 17, 18])
        g.add_edges_from(
            [(1, 15), (3, 10), (6, 17), (9, 18), (9, 10), (11, 16), (12, 13)]
        )
        # g.add_edges_from([(1, 4), (1, 15), (7, 10), (9, 10), (9, 18), (11, 16), (12, 13)])
        # g.add_edges_from([(1, 15), (1, 5), (3, 10), (6, 17), (9, 10), (9, 18), (11, 16)])
        nx.set_node_attributes(
            g,
            {
                1: {"pos": [-871, -865]},
                3: {"pos": [-464, -669]},
                6: {"pos": [-601, -346]},
                9: {"pos": [143, 59]},
                10: {"pos": [-32, 94]},
                11: {"pos": [530, 785]},
                12: {"pos": [-14, 434]},
                13: {"pos": [-474, -702]},
                15: {"pos": [162, 267]},
                16: {"pos": [-494, -559]},
                17: {"pos": [802, 318]},
                18: {"pos": [-372, 162]},
            },
        )

        _assert_crossing_equality(
            g,
            crossings.get_crossings_quadratic(g),
            include_node_crossings=False,
        )

    def test_intertwined_crossings_9(self):
        g = nx.Graph()
        g.add_nodes_from([0, 1, 2, 3, 5, 7, 9, 10, 11, 12, 13, 14, 15, 16])
        g.add_edges_from(
            [
                (0, 12),
                (0, 14),
                (1, 15),
                (2, 16),
                (2, 5),
                (3, 15),
                (5, 7),
                (9, 15),
                (9, 13),
                (10, 15),
                (10, 11),
                (11, 15),
            ]
        )
        nx.set_node_attributes(
            g,
            {
                0: {"pos": [-459, -324]},
                1: {"pos": [-758, 851]},
                2: {"pos": [825, -608]},
                3: {"pos": [774, 530]},
                5: {"pos": [-370, 713]},
                7: {"pos": [-859, -552]},
                9: {"pos": [566, -144]},
                10: {"pos": [742, -259]},
                11: {"pos": [36, -151]},
                12: {"pos": [495, -571]},
                13: {"pos": [151, -780]},
                14: {"pos": [-314, 159]},
                15: {"pos": [4, -324]},
                16: {"pos": [-216, -292]},
            },
        )

        _assert_crossing_equality(
            g,
            crossings.get_crossings_quadratic(g),
            include_node_crossings=False,
        )

    """
    def test_graph_minimizer(self):

        edges = [(0, 4), (0, 11), (0, 13), (0, 8), (0, 12), (0, 14), (0, 10), (0, 16), (0, 5), (0, 7), (0, 3), (0, 1),
                 (0, 15), (0, 9), (1, 10), (1, 5), (1, 4), (1, 13), (1, 9), (1, 14), (1, 12), (1, 16), (1, 15), (1, 8),
                 (1, 6), (1, 7), (1, 11), (2, 9), (2, 4), (2, 7), (2, 8), (2, 6), (2, 10), (2, 5), (2, 3), (2, 15),
                 (2, 12), (2, 16), (2, 14), (3, 11), (3, 9), (3, 14), (3, 15), (3, 12), (3, 8), (3, 13), (3, 7),
                 (3, 16), (3, 4), (3, 6), (3, 10), (4, 7), (4, 12), (4, 6), (4, 13), (4, 15), (4, 14), (4, 5), (4, 9),
                 (4, 10), (5, 7), (5, 6), (5, 16), (5, 11), (5, 13), (5, 15), (5, 10), (5, 9), (5, 14), (6, 7), (6, 15),
                 (6, 11), (6, 13), (6, 16), (6, 14), (6, 9), (6, 10), (6, 8), (7, 15), (7, 14), (7, 12), (7, 11),
                 (7, 13), (7, 16), (7, 9), (7, 8), (8, 10), (8, 13), (8, 14), (8, 12), (8, 9), (8, 11), (9, 10),
                 (9, 12), (9, 11), (9, 14), (9, 15), (9, 16), (9, 13), (10, 15), (10, 11), (10, 13), (10, 14), (10, 16),
                 (10, 12), (11, 16), (11, 13), (11, 12), (11, 15), (11, 14), (12, 14), (12, 13), (12, 15), (12, 16),
                 (13, 16), (13, 14), (13, 15), (14, 16), (15, 16)]

        while True:
            random.shuffle(edges)
            count = 0

            found_any = False

            for subset in combinations(edges, len(edges) - 1):
                count += 1
                g = nx.Graph()
                g.add_nodes_from(range(0, 17))
                nx.set_node_attributes(g,
                                       {0: {'pos': [-459, -324]}, 1: {'pos': [-758, 851]}, 2: {'pos': [825, -608]},
                                        3: {'pos': [774, 530]}, 4: {'pos': [-421, -529]}, 5: {'pos': [-370, 713]},
                                        6: {'pos': [720, 856]}, 7: {'pos': [-859, -552]}, 8: {'pos': [-660, -745]},
                                        9: {'pos': [566, -144]}, 10: {'pos': [742, -259]}, 11: {'pos': [36, -151]},
                                        12: {'pos': [495, -571]}, 13: {'pos': [151, -780]}, 14: {'pos': [-314, 159]},
                                        15: {'pos': [4, -324]}, 16: {'pos': [-216, -292]}}
                                       )
                g.add_edges_from(subset)

                crossings_a = sorted(crossings.get_crossings(g))
                crossings_b = sorted(crossings.get_crossings_quadratic(g))

                if crossings_a != crossings_b:
                    min_length = len(subset)
                    min_edges = subset
                    edges = list(subset)
                    found_any = True

                    print(f"Min edge size: {min_length}")
                    print(f"Edges: {min_edges}")
                    print(f"Graphs tested: {count}")

                    with open("./test_results.txt", "w") as file:
                        g_copy = g.copy()

                        nodes_to_remove = [node for node, degree in dict(g.degree()).items() if degree == 0]
                        g_copy.remove_nodes_from(nodes_to_remove)

                        print(g_copy.order())
                        print(list(g_copy.edges()))
                        print(dict(g_copy.nodes(data=True)))
                        print(nx.get_node_attributes(g, "pos"))

                        file.write(f"\n\ng = nx.Graph()")
                        file.write(f"\ng.add_nodes_from({str(list(g_copy.nodes()))})")
                        file.write(f"\ng.add_edges_from({g_copy.edges()})")
                        file.write(f"\nnx.set_node_attributes(g, {str(dict(g_copy.nodes(data=True)))})\n")

                    break
            if not found_any:
                print(f"{len(edges)}: {count}")
                assert False
            print(f"{len(edges)}: {count}")
    """

    def test_random_graph_2(self):
        random.seed(9018098129039)
        success_count = 0
        for i in range(0, 25):
            for j in range(0, 10):
                print(f"Current graph: {success_count}")
                random_graph = nx.fast_gnp_random_graph(
                    i, random.uniform(0.1, 1), random.randint(1, 10000000)
                )
                random_embedding = {
                    n: [random.randint(-1000, 1000), random.randint(-1000, 1000)]
                    for n in range(0, i + 1)
                }
                nx.set_node_attributes(random_graph, random_embedding, "pos")
                _assert_crossing_equality(
                    random_graph, crossings.get_crossings_quadratic(random_graph)
                )
                success_count += 1

    def test_random_line_graph(self):
        # Random graph that should be in normal position

        random.seed(38528349829348)
        success_count = 0
        for i in range(0, 50):
            for j in range(0, 2):
                print(f"Current graph: {success_count}")
                random_graph = nx.Graph()

                for node in range(i):
                    random_graph.add_nodes_from([f"{i}a", f"{j}b"])
                    random_graph.add_edge(f"{i}a", f"{j}b")

                random_embedding = {
                    node: [random.randint(-1000, 1000), random.randint(-1000, 1000)]
                    for node in random_graph.nodes()
                }
                nx.set_node_attributes(random_graph, random_embedding, "pos")

                _assert_crossing_equality(
                    random_graph,
                    crossings.get_crossings_quadratic(random_graph),
                    include_node_crossings=True,
                )
                success_count += 1

    def test_edge_with_length_0(self):
        g = nx.Graph()
        g.add_node(0, pos=(0, 0))
        g.add_node(1, pos=(0, 0))
        g.add_edge(0, 1)

        crossing_list = crossings.get_crossings(g)

        assert len(crossing_list) == 0

    def test_edge_with_length_0_in_edge(self):
        g = nx.Graph()

        g.add_node(0, pos=(0, 0))
        g.add_node(1, pos=(0, 0))
        g.add_node(2, pos=(-1, 0))
        g.add_node(3, pos=(1, 0))
        g.add_edges_from([(0, 1), (2, 3)])

        _assert_crossing_equality(
            g,
            [crossings.Crossing(crossings.CrossingPoint(0, 0), {(0, 1), (2, 3)})],
            True,
            True,
        )

    def test_edge_with_length_0_in_crossing(self):
        g = nx.Graph()

        g.add_node(0, pos=(0, 0))
        g.add_node(1, pos=(0, 0))
        g.add_node(2, pos=(-1, -1))
        g.add_node(3, pos=(1, 1))
        g.add_node(4, pos=(1, -1))
        g.add_node(5, pos=(-1, 1))
        g.add_edges_from([(0, 1), (2, 3), (4, 5)])

        _assert_crossing_equality(
            g,
            [
                crossings.Crossing(
                    crossings.CrossingPoint(0, 0), {(0, 1), (2, 3), (4, 5)}
                )
            ],
            True,
            True,
        )

    def test_edge_with_length_0_in_crossing_2(self):
        g = nx.Graph()

        g.add_node(0, pos=(0, 0))
        g.add_node(1, pos=(0, 0))
        g.add_node(2, pos=(-1, -1))
        g.add_node(3, pos=(1, 1))
        g.add_node(4, pos=(1, -1))
        g.add_node(5, pos=(-1, 1))
        g.add_edges_from([(0, 1), (2, 3), (4, 5)])

        _assert_crossing_equality(
            g,
            [
                crossings.Crossing(
                    crossings.CrossingPoint(0, 0), {(0, 1), (2, 3), (4, 5)}
                )
            ],
            True,
            True,
        )

    def test_random_graph_small_grid(self):
        """
        Due to the smaller area, we expect much more edge cases such as:
            - Multiple crossings on the same point
            - Horizontal edges
            - Vertices on edges (we count those as crossings as well)
        """
        random.seed(19031023901923)
        success_count = 0
        for i in range(0, 25):
            print(f"Current graph: {success_count}")
            random_graph = nx.fast_gnp_random_graph(
                i, random.uniform(0.1, 1), random.randint(1, 1000000)
            )
            random_embedding = {
                n: [random.randint(-1, 1), random.randint(-1, 1)]
                for n in range(0, i + 1)
            }
            nx.set_node_attributes(random_graph, random_embedding, "pos")
            _assert_crossing_equality(
                random_graph,
                crossings.get_crossings_quadratic(
                    random_graph, include_node_crossings=True
                ),
                include_node_crossings=True,
            )
            success_count += 1

    def test_random_graph_small_grid_2(self):
        """
        Due to the smaller area, we expect much more edge cases such as:
            - Multiple crossings on the same point
            - Horizontal edges
            - Vertices on edges (we count those as crossings as well)
        """
        random.seed(19031023901923)
        success_count = 0
        for i in range(0, 25):
            print(f"Current graph: {success_count}")
            random_graph = nx.fast_gnp_random_graph(
                i, random.uniform(0.1, 1), random.randint(1, 1000000)
            )
            random_embedding = {
                n: [random.randint(-1, 1), random.randint(-1, 1)]
                for n in range(0, i + 1)
            }
            nx.set_node_attributes(random_graph, random_embedding, "pos")
            _assert_crossing_equality(
                random_graph, crossings.get_crossings_quadratic(random_graph)
            )
            success_count += 1

    def test_overlapping_edges_crossing_another_at_vertex(self):
        g = nx.Graph()
        g.add_node(1, pos=(0, 0))
        g.add_node(2, pos=(1, 1))
        g.add_node(3, pos=(2, 2))
        g.add_node(4, pos=(3, 3))
        g.add_node(5, pos=(1.5, 1.5))
        g.add_node(6, pos=(3, 1.5))
        g.add_edges_from([(1, 3), (2, 4), (5, 6)])
        _assert_crossing_equality(
            g,
            [
                crossings.Crossing(
                    crossings.CrossingLine(CrossingPoint(1, 1), CrossingPoint(2, 2)),
                    {(1, 3), (2, 4)},
                ),
                crossings.Crossing(
                    crossings.CrossingPoint(1.5, 1.5), {(1, 3), (2, 4), (5, 6)}
                ),
            ],
            include_node_crossings=True,
        )

    def test_overlapping_edges_crossing_another_at_vertex_2(self):
        g = nx.Graph()
        g.add_node(1, pos=(0, 0))
        g.add_node(2, pos=(1, 1))
        g.add_node(3, pos=(2, 2))
        g.add_node(4, pos=(3, 3))
        g.add_node(5, pos=(1.5, 1.5))
        g.add_node(6, pos=(3, 1.5))
        g.add_edges_from([(1, 3), (2, 4), (5, 6)])
        _assert_crossing_equality(
            g,
            [
                crossings.Crossing(
                    crossings.CrossingLine(CrossingPoint(1, 1), CrossingPoint(2, 2)),
                    {(1, 3), (2, 4)},
                )
            ],
        )

    def test_random_planar_graphs(self):

        for i in range(20, 40):
            n = i * 5
            coordinates = [
                (random.uniform(0, 1), random.uniform(0, 1)) for _ in range(0, n)
            ]

            # Generate delaunay
            cells, generators = voronoi_frames(coordinates, clip="convex hull")
            delaunay = weights.Rook.from_dataframe(cells)
            delaunay_graph = delaunay.to_networkx()

            pos = dict(zip(delaunay_graph.nodes, coordinates))

            for node, value in pos.items():
                delaunay_graph.nodes[node]["pos"] = value

            _assert_crossing_equality(delaunay_graph, [])
