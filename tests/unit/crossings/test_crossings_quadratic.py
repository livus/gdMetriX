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

import unittest

import networkx as nx

# noinspection PyUnresolvedReferences
import pytest

import crossing_test_helper
from gdMetriX import crossings
from gdMetriX.crossing_data_types import CrossingPoint, CrossingLine


def __assert_crossing_equality__(
    g,
    crossing_list,
    include_rotation: bool = False,
    include_node_crossings: bool = False,
):
    crossing_test_helper.assert_crossing_equality(
        g,
        crossing_list,
        crossings.get_crossings_quadratic,
        include_rotation,
        include_node_crossings,
    )


class TestSimpleCrossings(unittest.TestCase):

    def test_empty_graph(self):
        g = nx.Graph()
        __assert_crossing_equality__(g, [])

    def test_singleton(self):
        g = nx.Graph()
        g.add_node(1, pos=(0, 0))
        __assert_crossing_equality__(g, [])

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
        __assert_crossing_equality__(g, [])

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
        __assert_crossing_equality__(g, [], True)

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
        __assert_crossing_equality__(g, [], True)

    def test_simple_crossing_0(self):
        g = nx.Graph()
        g.add_node(1, pos=(0, 0))
        g.add_node(2, pos=(1, 0))
        g.add_node(3, pos=(1, 1))
        g.add_node(4, pos=(0, 1))
        g.add_edges_from([(1, 3), (2, 4)])
        __assert_crossing_equality__(
            g, [crossings.Crossing(crossings.CrossingPoint(0.5, 0.5), {(1, 3), (2, 4)})]
        )

    def test_simple_crossing_1(self):
        g = nx.Graph()
        g.add_node(1, pos=(0, 0))
        g.add_node(2, pos=(1, 0))
        g.add_node(3, pos=(1, 1))
        g.add_node(4, pos=(0, 1))
        g.add_edges_from([(1, 2), (1, 3), (1, 4), (2, 3), (2, 4), (3, 4)])
        __assert_crossing_equality__(
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
        __assert_crossing_equality__(
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
        __assert_crossing_equality__(
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
        __assert_crossing_equality__(g, [], True)

    def test_crossing_graph_directed(self):
        g = nx.DiGraph()
        g.add_node(1, pos=(0, 0))
        g.add_node(2, pos=(1, 0))
        g.add_node(3, pos=(1, 1))
        g.add_node(4, pos=(0, 1))
        g.add_edges_from([(1, 3), (2, 4)])
        __assert_crossing_equality__(
            g, [crossings.Crossing(crossings.CrossingPoint(0.5, 0.5), {(1, 3), (2, 4)})]
        )

    def test_self_loop(self):
        g = nx.DiGraph()
        g.add_node(1, pos=(0, 0))
        g.add_edge(1, 1)

        __assert_crossing_equality__(g, [], True, True)

    def test_self_loop_in_edge(self):
        g = nx.DiGraph()
        g.add_node(1, pos=(0, 0))
        g.add_node(2, pos=(-1, 0))
        g.add_node(3, pos=(1, 0))
        g.add_edge(1, 1)
        g.add_edge(2, 3)

        __assert_crossing_equality__(g, [], True)

    def test_self_loop_in_edge_2(self):
        g = nx.DiGraph()
        g.add_node(1, pos=(0, 0))
        g.add_node(2, pos=(-1, 0))
        g.add_node(3, pos=(1, 0))
        g.add_edge(1, 1)
        g.add_edge(2, 3)

        __assert_crossing_equality__(
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

        __assert_crossing_equality__(
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

        __assert_crossing_equality__(
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
        __assert_crossing_equality__(
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
        __assert_crossing_equality__(
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
        __assert_crossing_equality__(
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
        __assert_crossing_equality__(
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
        __assert_crossing_equality__(
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
        __assert_crossing_equality__(
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
        __assert_crossing_equality__(
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
        __assert_crossing_equality__(
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
        __assert_crossing_equality__(
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
        __assert_crossing_equality__(g, [])

    def test_vertex_at_edge_2_disabled(self):
        g = nx.Graph()
        g.add_node(1, pos=(0, 0))
        g.add_node(2, pos=(0, 2))
        g.add_node(3, pos=(0, 1))
        g.add_node(4, pos=(1, 1))
        g.add_edges_from([(1, 2), (3, 4)])
        __assert_crossing_equality__(g, [])

    def test_vertex_at_edge_3_disabled(self):
        g = nx.Graph()
        g.add_node(1, pos=(0, 0))
        g.add_node(2, pos=(0, 2))
        g.add_node(3, pos=(0, 1))
        g.add_node(4, pos=(1, 0))
        g.add_edges_from([(1, 2), (3, 4)])
        __assert_crossing_equality__(g, [])

    def test_vertex_at_edge_4_disabled(self):
        g = nx.Graph()
        g.add_node(1, pos=(0, 1))
        g.add_node(2, pos=(2, 1))
        g.add_node(3, pos=(1, 1))
        g.add_node(4, pos=(1, 0))

        g.add_edges_from([(1, 2), (3, 4)])
        __assert_crossing_equality__(g, [])

    def test_vertex_at_edge_5_disabled(self):
        g = nx.Graph()
        g.add_node(1, pos=(0, 1))
        g.add_node(2, pos=(2, 1))
        g.add_node(3, pos=(1, 1))
        g.add_node(4, pos=(0, 0))
        g.add_edges_from([(1, 2), (3, 4)])
        __assert_crossing_equality__(g, [])

    def test_vertex_at_edge_6_disabled(self):
        g = nx.Graph()
        g.add_node(1, pos=(0, 1))
        g.add_node(2, pos=(2, 1))
        g.add_node(3, pos=(1, 1))
        g.add_node(4, pos=(2, 0))
        g.add_edges_from([(1, 2), (3, 4)])
        __assert_crossing_equality__(g, [])

    def test_vertex_at_edge_7_disabled(self):
        g = nx.Graph()
        g.add_node(1, pos=(0, 1))
        g.add_node(2, pos=(2, 1))
        g.add_node(3, pos=(1, 1))
        g.add_node(4, pos=(1, 0))

        g.add_edges_from([(1, 2), (3, 4)])
        __assert_crossing_equality__(g, [], True)

    def test_vertex_at_edge_8_disabled(self):
        g = nx.Graph()
        g.add_node(1, pos=(0, 1))
        g.add_node(2, pos=(2, 1))
        g.add_node(3, pos=(1, 1))
        g.add_node(4, pos=(0, 0))
        g.add_edges_from([(1, 2), (3, 4)])
        __assert_crossing_equality__(g, [], True)

    def test_vertex_at_edge_9_disabled(self):
        g = nx.Graph()
        g.add_node(1, pos=(0, 1))
        g.add_node(2, pos=(2, 1))
        g.add_node(3, pos=(1, 1))
        g.add_node(4, pos=(2, 0))
        g.add_edges_from([(1, 2), (3, 4)])
        __assert_crossing_equality__(g, [], True)

    def test_vertex_at_vertex_1(self):
        g = nx.Graph()
        g.add_node(1, pos=(-2, -3))
        g.add_node(2, pos=(0, 0))
        g.add_node(3, pos=(-1, 1))
        g.add_node(4, pos=(0, 0))
        g.add_edges_from([(1, 2), (3, 4)])
        __assert_crossing_equality__(
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
        __assert_crossing_equality__(g, [], True)


class TestOverlappingCrossings(unittest.TestCase):

    def test_overlapping_crossing_1(self):
        g = nx.Graph()
        g.add_node(1, pos=(0, 0))
        g.add_node(2, pos=(10, 0))
        g.add_node(3, pos=(3, 0))
        g.add_node(4, pos=(7, 0))
        g.add_edges_from([(1, 2), (3, 4)])
        __assert_crossing_equality__(
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
        __assert_crossing_equality__(
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
        __assert_crossing_equality__(
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
        __assert_crossing_equality__(
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
        __assert_crossing_equality__(
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
        __assert_crossing_equality__(
            g,
            [
                crossings.Crossing(
                    CrossingLine(CrossingPoint(1, 1), CrossingPoint(2, 2)),
                    {(1, 3), (2, 4)},
                ),
                crossings.Crossing(CrossingPoint(1.5, 1.5), {(1, 3), (2, 4), (5, 6)}),
            ],
        )

    def test_overlapping_edges_common_endpoint(self):
        g = nx.Graph()
        g.add_node(1, pos=(0, 0))
        g.add_node(2, pos=(3, -2))
        g.add_node(3, pos=(6, -4))

        g.add_edges_from([(1, 2), (1, 3)])

        __assert_crossing_equality__(
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
        __assert_crossing_equality__(
            g,
            [
                crossings.Crossing(crossings.CrossingPoint(1.0, 1.5), {(3, 5), (1, 4)}),
                crossings.Crossing(crossings.CrossingPoint(2.0, 1.0), {(2, 3), (1, 4)}),
            ],
        )


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
        __assert_crossing_equality__(
            g, [crossings.Crossing(crossings.CrossingPoint(0, 0), edges)]
        )

    def test_no_crossing_with_shared_endpoint(self):
        g = nx.Graph()
        g.add_node(1, pos=(0, 0))
        g.add_node(2, pos=(1, 0))
        g.add_node(3, pos=(0, 1))
        g.add_edges_from([(1, 2), (2, 3)])
        __assert_crossing_equality__(g, [], True)

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
        __assert_crossing_equality__(
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

    def test_edge_with_length_0(self):
        g = nx.Graph()
        g.add_node(0, pos=(0, 0))
        g.add_node(1, pos=(0, 0))
        g.add_edge(0, 1)

        crossing_list = crossings.get_crossings_quadratic(g)

        assert len(crossing_list) == 0

    def test_edge_with_length_0_in_edge(self):
        g = nx.Graph()

        g.add_node(0, pos=(0, 0))
        g.add_node(1, pos=(0, 0))
        g.add_node(2, pos=(-1, 0))
        g.add_node(3, pos=(1, 0))
        g.add_edges_from([(0, 1), (2, 3)])

        __assert_crossing_equality__(
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

        __assert_crossing_equality__(
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

        __assert_crossing_equality__(
            g,
            [
                crossings.Crossing(
                    crossings.CrossingPoint(0, 0), {(0, 1), (2, 3), (4, 5)}
                )
            ],
            True,
            True,
        )

    def test_overlapping_edges_crossing_another_at_vertex(self):
        g = nx.Graph()
        g.add_node(1, pos=(0, 0))
        g.add_node(2, pos=(1, 1))
        g.add_node(3, pos=(2, 2))
        g.add_node(4, pos=(3, 3))
        g.add_node(5, pos=(1.5, 1.5))
        g.add_node(6, pos=(3, 1.5))
        g.add_edges_from([(1, 3), (2, 4), (5, 6)])
        __assert_crossing_equality__(
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
        __assert_crossing_equality__(
            g,
            [
                crossings.Crossing(
                    crossings.CrossingLine(CrossingPoint(1, 1), CrossingPoint(2, 2)),
                    {(1, 3), (2, 4)},
                )
            ],
        )


class TestGroupingOfOverlappingCrossings(unittest.TestCase):

    def test_multiple_edges_crossing_in_same_point(self):
        g = nx.Graph()
        g.add_node(1, pos=(-1, 0))
        g.add_node(2, pos=(1, 0))
        g.add_node(3, pos=(0, 1))
        g.add_node(4, pos=(0, -1))
        g.add_node(5, pos=(1, 1))
        g.add_node(6, pos=(-1, -1))

        g.add_edge(1, 2)
        g.add_edge(3, 4)
        g.add_edge(5, 6)

        crossing_list = crossings.get_crossings_quadratic(g)
        assert len(crossing_list) == 1

        crossing = crossing_list[0]
        assert len(crossing.involved_edges) == 3

    def test_multiple_edges_crossing_in_same_point_2(self):
        g = nx.Graph()
        g.add_node(1, pos=(-1, 0))
        g.add_node(2, pos=(1, 0))
        g.add_node(3, pos=(0, 1))
        g.add_node(4, pos=(0, -1))
        g.add_node(5, pos=(1, 1))
        g.add_node(6, pos=(-1, -1))
        g.add_node(7, pos=(1, -1))
        g.add_node(8, pos=(-1, 1))

        g.add_edge(1, 2)
        g.add_edge(3, 4)
        g.add_edge(5, 6)
        g.add_edge(7, 8)

        crossing_list = crossings.get_crossings_quadratic(g)
        assert len(crossing_list) == 1

        crossing = crossing_list[0]
        assert len(crossing.involved_edges) == 4

    def test_multiple_edges_crossing_in_same_point_3(self):
        g = nx.Graph()
        g.add_node(1, pos=(-1, 0))
        g.add_node(2, pos=(1, 0))
        g.add_node(3, pos=(0, 1))
        g.add_node(4, pos=(0, -1))
        g.add_node(5, pos=(1, 1))
        g.add_node(6, pos=(-1, -1))
        g.add_node(7, pos=(1, -1))
        g.add_node(8, pos=(-1, 1))

        g.add_edge(1, 2)
        g.add_edge(3, 4)
        g.add_edge(5, 6)
        g.add_edge(7, 8)

        crossing_list = crossings.get_crossings_quadratic(g)
        assert len(crossing_list) == 1

        crossing = crossing_list[0]
        assert len(crossing.involved_edges) == 4
