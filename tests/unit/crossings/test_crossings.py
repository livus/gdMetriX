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

import inspect
import math
import unittest

import networkx as nx

# noinspection PyUnresolvedReferences
import pytest

from . import crossing_test_helper
from gdMetriX import crossings
from gdMetriX.utils import numeric
from gdMetriX.utils.sweep_line import CrossingPoint


def _assert_crossing_equality(
    g,
    crossing_list,
    include_rotation: bool = False,
    include_node_crossings: bool = False,
    consider_singletons: bool = False,
):
    crossing_test_helper.assert_crossing_equality(
        g,
        crossing_list,
        crossings.get_crossings,
        include_rotation,
        include_node_crossings,
        consider_singletons,
        title=inspect.getouterframes(inspect.currentframe(), 2)[1][3],
    )


class TestMultiGraphs(unittest.TestCase):

    def test_empty_multi_graph(self):
        g = nx.MultiGraph()

        def _test_multi_graph():
            crossings.get_crossings(g)

        pytest.raises(ValueError, _test_multi_graph)

    def test_empty_multi_di_graph(self):
        g = nx.MultiDiGraph()

        def _test_multi_graph():
            crossings.get_crossings(g)

        pytest.raises(ValueError, _test_multi_graph)


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


class TestSelfLoops(unittest.TestCase):

    def test_simple_self_loop_1(self):
        g = nx.DiGraph()
        g.add_node(1, pos=(0, 0))
        g.add_edge(1, 1)

        _assert_crossing_equality(g, [], True)

    def test_simple_self_loop_2(self):
        g = nx.DiGraph()
        g.add_node(1, pos=(0, 0))
        g.add_edge(1, 1)

        _assert_crossing_equality(g, [], True, True)

    def test_simple_self_loop_3(self):
        g = nx.DiGraph()
        g.add_node(1, pos=(0, 0))
        g.add_edge(1, 1)

        _assert_crossing_equality(g, [], True, True, True)

    def test_self_loop_in_edge_1(self):
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

    def test_self_loop_at_endpoint_1(self):
        g = nx.Graph()
        g.add_node(1, pos=(0, 0))
        g.add_node(2, pos=(1, 1))
        g.add_node(3, pos=(0, 0))
        g.add_edges_from([(1, 2), (3, 3)])

        _assert_crossing_equality(g, [], True)

    def test_self_loop_at_endpoint_2(self):
        g = nx.Graph()
        g.add_node(1, pos=(0, 0))
        g.add_node(2, pos=(1, 1))
        g.add_node(3, pos=(0, 0))
        g.add_edges_from([(1, 2), (3, 3)])

        _assert_crossing_equality(
            g,
            [crossings.Crossing(crossings.CrossingPoint(0, 0), {(1, 2), (3, 3)})],
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

    def test_self_loop_plus_normal_edge_1(self):
        g = nx.Graph()
        g.add_node(1, pos=(0, 0))
        g.add_node(2, pos=(1, 1))
        g.add_edges_from([(1, 1), (1, 2)])

        _assert_crossing_equality(g, [], True)

    def test_self_loop_plus_normal_edge_2(self):
        g = nx.Graph()
        g.add_node(1, pos=(0, 0))
        g.add_node(2, pos=(1, 1))
        g.add_edges_from([(1, 1), (1, 2)])

        _assert_crossing_equality(g, [], True, True)

    def test_self_loop_plus_normal_edge_3(self):
        g = nx.Graph()
        g.add_node(1, pos=(0, 0))
        g.add_node(2, pos=(1, 1))
        g.add_edges_from([(1, 1), (1, 2)])

        _assert_crossing_equality(g, [], True, True, True)

    def test_complex_crossing_point_1(self):
        g = nx.Graph()
        g.add_node(1, pos=(0, 0))
        g.add_node(2, pos=(1, 1))
        g.add_node(3, pos=(1, 0))
        g.add_node(4, pos=(0, 1))
        g.add_node(5, pos=(0.5, 0.5))
        g.add_node(6, pos=(0.5, 2))
        g.add_node(7, pos=(0.5, 0.5))
        g.add_edges_from([(1, 2), (3, 4), (5, 6), (7, 7)])

        _assert_crossing_equality(
            g,
            [crossings.Crossing(crossings.CrossingPoint(0.5, 0.5), {(1, 2), (3, 4)})],
            True,
        )

    def test_complex_crossing_point_2(self):
        g = nx.Graph()
        g.add_node(1, pos=(0, 0))
        g.add_node(2, pos=(1, 1))
        g.add_node(3, pos=(1, 0))
        g.add_node(4, pos=(0, 1))
        g.add_node(5, pos=(0.5, 0.5))
        g.add_node(6, pos=(0.5, 2))
        g.add_node(7, pos=(0.5, 0.5))
        g.add_edges_from([(1, 2), (3, 4), (5, 6), (7, 7)])

        _assert_crossing_equality(
            g,
            [
                crossings.Crossing(
                    crossings.CrossingPoint(0.5, 0.5), {(1, 2), (3, 4), (5, 6), (7, 7)}
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

    def test_endpoint_at_crossing_1(self):
        g = nx.Graph()
        g.add_node(1, pos=(0, 0))
        g.add_node(2, pos=(1, 1))
        g.add_node(3, pos=(1, 0))
        g.add_node(4, pos=(0, 1))
        g.add_node(5, pos=(0.5, 0.5))
        g.add_node(6, pos=(0.5, 1))
        g.add_edges_from([(1, 2), (3, 4), (5, 6)])

        _assert_crossing_equality(
            g,
            [crossings.Crossing(crossings.CrossingPoint(0.5, 0.5), {(1, 2), (3, 4)})],
            True,
        )

    def test_endpoint_at_crossing_2(self):
        g = nx.Graph()
        g.add_node(1, pos=(0, 0))
        g.add_node(2, pos=(1, 1))
        g.add_node(3, pos=(1, 0))
        g.add_node(4, pos=(0, 1))
        g.add_node(5, pos=(0.5, 0.5))
        g.add_node(6, pos=(0.5, 1))
        g.add_edges_from([(1, 2), (3, 4), (5, 6)])

        _assert_crossing_equality(
            g,
            [
                crossings.Crossing(
                    crossings.CrossingPoint(0.5, 0.5), {(1, 2), (3, 4), (5, 6)}
                )
            ],
            True,
            True,
        )


class TestSingletons(unittest.TestCase):

    def test_invalid_parameter_combination(self):
        g = nx.Graph()
        g.add_node(0, pos=(0, 0))
        g.add_node(1, pos=(1, 1))
        g.add_edges_from([(0, 1)])

        def _invalid_params():
            crossings.get_crossings_quadratic(
                g, include_node_crossings=False, consider_singletons=True
            )

        pytest.raises(ValueError, _invalid_params)

    def test_valid_parameter_combination(self):
        g = nx.Graph()
        g.add_node(0, pos=(0, 0))
        g.add_node(1, pos=(1, 1))
        g.add_edges_from([(0, 1)])

        crossings.get_crossings_quadratic(
            g, include_node_crossings=True, consider_singletons=False
        )
        crossings.get_crossings_quadratic(
            g, include_node_crossings=True, consider_singletons=True
        )
        crossings.get_crossings_quadratic(
            g, include_node_crossings=False, consider_singletons=False
        )

    def test_singleton_on_edge_1(self):
        g = nx.Graph()
        g.add_node(1, pos=(0, 0))
        g.add_node(2, pos=(2, 2))
        g.add_node(3, pos=(1, 1))
        g.add_edges_from([(2, 3)])
        _assert_crossing_equality(g, [], True)

    def test_singleton_on_edge_2(self):
        g = nx.Graph()
        g.add_node(1, pos=(0, 0))
        g.add_node(2, pos=(2, 2))
        g.add_node(3, pos=(1, 1))
        g.add_edges_from([(1, 2)])
        _assert_crossing_equality(g, [], True, True)

    def test_singleton_on_edge_3(self):
        g = nx.Graph()
        g.add_node(1, pos=(0, 0))
        g.add_node(2, pos=(2, 2))
        g.add_node(3, pos=(1, 1))
        g.add_edges_from([(1, 2)])
        _assert_crossing_equality(
            g,
            [crossings.Crossing(crossings.CrossingPoint(1, 1), {(1, 2)}, {3})],
            False,
            True,
            True,
        )

    def test_singleton_on_endpoint_1(self):
        g = nx.Graph()
        g.add_node(1, pos=(0, 0))
        g.add_node(2, pos=(2, 0))
        g.add_node(3, pos=(2, 0))
        g.add_edges_from([(1, 2)])

        _assert_crossing_equality(g, [], True)

    def test_singleton_on_endpoint_2(self):
        g = nx.Graph()
        g.add_node(1, pos=(0, 0))
        g.add_node(2, pos=(2, 0))
        g.add_node(3, pos=(2, 0))
        g.add_edges_from([(1, 2)])

        _assert_crossing_equality(g, [], True, True)

    def test_singleton_on_endpoint_3(self):
        g = nx.Graph()
        g.add_node(1, pos=(0, 0))
        g.add_node(2, pos=(2, 0))
        g.add_node(3, pos=(2, 0))
        g.add_edges_from([(1, 2)])

        _assert_crossing_equality(
            g,
            [crossings.Crossing(crossings.CrossingPoint(2, 0), {(1, 2)}, {3})],
            False,
            True,
            True,
        )

    def test_two_overlapping_singletons_1(self):
        g = nx.Graph()
        g.add_node(1, pos=(2, 0))
        g.add_node(2, pos=(2, 0))

        _assert_crossing_equality(g, [], True)

    def test_two_overlapping_singletons_2(self):
        g = nx.Graph()
        g.add_node(1, pos=(2, 0))
        g.add_node(2, pos=(2, 0))

        _assert_crossing_equality(g, [], True, True)

    def test_two_overlapping_singletons_3(self):
        g = nx.Graph()
        g.add_node(1, pos=(2, 0))
        g.add_node(2, pos=(2, 0.1))
        g.add_node(3, pos=(2, 0))

        _assert_crossing_equality(
            g,
            [crossings.Crossing(crossings.CrossingPoint(2, 0), set(), {1, 3})],
            False,
            True,
            True,
        )

    def test_singleton_at_crossing_1(self):
        g = nx.Graph()
        g.add_node(1, pos=(0, 0))
        g.add_node(2, pos=(1, 1))
        g.add_node(3, pos=(1, 0))
        g.add_node(4, pos=(0, 1))
        g.add_node(5, pos=(0.5, 0.5))
        g.add_edges_from([(1, 2), (3, 4)])

        _assert_crossing_equality(
            g,
            [crossings.Crossing(crossings.CrossingPoint(0.5, 0.5), {(1, 2), (3, 4)})],
            True,
        )

    def test_singleton_at_crossing_2(self):
        g = nx.Graph()
        g.add_node(1, pos=(0, 0))
        g.add_node(2, pos=(1, 1))
        g.add_node(3, pos=(1, 0))
        g.add_node(4, pos=(0, 1))
        g.add_node(5, pos=(0.5, 0.5))
        g.add_edges_from([(1, 2), (3, 4)])

        _assert_crossing_equality(
            g,
            [crossings.Crossing(crossings.CrossingPoint(0.5, 0.5), {(1, 2), (3, 4)})],
            True,
            True,
        )

    def test_singleton_at_crossing_3(self):
        g = nx.Graph()
        g.add_node(1, pos=(0, 0))
        g.add_node(2, pos=(1, 1))
        g.add_node(3, pos=(1, 0))
        g.add_node(4, pos=(0, 1))
        g.add_node(5, pos=(0.5, 0.5))
        g.add_edges_from([(1, 2), (3, 4)])

        _assert_crossing_equality(
            g,
            [
                crossings.Crossing(
                    crossings.CrossingPoint(0.5, 0.5), {(1, 2), (3, 4)}, {5}
                )
            ],
            False,
            True,
            True,
        )

    def test_singleton_at_endpoint_crossing_1(self):
        g = nx.Graph()
        g.add_node(1, pos=(0, 0))
        g.add_node(2, pos=(2, 0))
        g.add_node(3, pos=(1, 0))
        g.add_node(4, pos=(1, 1))
        g.add_node(5, pos=(1, 0))
        g.add_edges_from([(1, 2), (3, 4)])

        _assert_crossing_equality(g, [], True)

    def test_singleton_at_endpoint_crossing_2(self):
        g = nx.Graph()
        g.add_node(1, pos=(0, 0))
        g.add_node(2, pos=(2, 0))
        g.add_node(3, pos=(1, 0))
        g.add_node(4, pos=(1, 1))
        g.add_node(5, pos=(1, 0))
        g.add_edges_from([(1, 2), (3, 4)])

        _assert_crossing_equality(
            g,
            [crossings.Crossing(crossings.CrossingPoint(1, 0), {(1, 2), (3, 4)})],
            True,
            True,
        )

    def test_singleton_at_endpoint_crossing_3(self):
        g = nx.Graph()
        g.add_node(1, pos=(0, 0))
        g.add_node(2, pos=(2, 0))
        g.add_node(3, pos=(1, 0))
        g.add_node(4, pos=(1, 1))
        g.add_node(5, pos=(1, 0))
        g.add_edges_from([(1, 2), (3, 4)])

        _assert_crossing_equality(
            g,
            [crossings.Crossing(crossings.CrossingPoint(1, 0), {(1, 2), (3, 4)}, {5})],
            False,
            True,
            True,
        )

    def test_singleton_at_self_loop_1(self):
        g = nx.Graph()
        g.add_node(1, pos=(0, 0))
        g.add_node(2, pos=(0, 0))
        g.add_edges_from([(1, 1)])

        _assert_crossing_equality(g, [], True)

    def test_singleton_at_self_loop_2(self):
        g = nx.Graph()
        g.add_node(1, pos=(0, 0))
        g.add_node(2, pos=(0, 0))
        g.add_edges_from([(1, 1)])

        _assert_crossing_equality(g, [], True, True)

    def test_singleton_at_self_loop_3(self):
        g = nx.Graph()
        g.add_node(1, pos=(0, 0))
        g.add_node(2, pos=(0, 0))
        g.add_edges_from([(1, 1)])

        _assert_crossing_equality(
            g,
            [crossings.Crossing(crossings.CrossingPoint(0, 0), {(1, 1)}, {2})],
            False,
            True,
            True,
        )


class TestLengthZeroEdges(unittest.TestCase):

    def test_single_edge_1(self):
        g = nx.Graph()
        g.add_node(1, pos=(2.6, -3))
        g.add_node(2, pos=(2.6, -3))
        g.add_edges_from([(1, 2)])

        _assert_crossing_equality(g, [], False)

    def test_single_edge_2(self):
        g = nx.Graph()
        g.add_node(1, pos=(2.6, -3))
        g.add_node(2, pos=(2.6, -3))
        g.add_edges_from([(1, 2)])

        _assert_crossing_equality(g, [], False, True)

    def test_single_edge_3(self):
        g = nx.Graph()
        g.add_node(1, pos=(2.6, -3))
        g.add_node(2, pos=(2.6, -3))
        g.add_edges_from([(1, 2)])

        _assert_crossing_equality(g, [], False, True, True)

    def test_edge_on_singleton_1(self):
        g = nx.Graph()
        g.add_node(1, pos=(2.6, -3))
        g.add_node(2, pos=(2.6, -3))
        g.add_node(3, pos=(2.6, -3))
        g.add_edges_from([(1, 2)])

        _assert_crossing_equality(g, [], False)

    def test_edge_on_singleton_2(self):
        g = nx.Graph()
        g.add_node(1, pos=(2.6, -3))
        g.add_node(2, pos=(2.6, -3))
        g.add_node(3, pos=(2.6, -3))
        g.add_edges_from([(1, 2)])

        _assert_crossing_equality(g, [], False, True)

    def test_edge_on_singleton_3(self):
        g = nx.Graph()
        g.add_node(1, pos=(2.6, -3))
        g.add_node(2, pos=(2.6, -3))
        g.add_node(3, pos=(2.6, -3))
        g.add_edges_from([(1, 2)])

        _assert_crossing_equality(
            g,
            [crossings.Crossing(crossings.CrossingPoint(2.6, -3), {(1, 2)}, {3})],
            False,
            True,
            True,
        )

    def test_edge_on_endpoint_1(self):
        g = nx.Graph()
        g.add_node(1, pos=(4, 13))
        g.add_node(2, pos=(4, 13))
        g.add_node(3, pos=(4, 13))
        g.add_node(4, pos=(4, 165))
        g.add_edges_from([(1, 2), (3, 4)])

        _assert_crossing_equality(g, [], False)

    def test_edge_on_endpoint_2(self):
        g = nx.Graph()
        g.add_node(1, pos=(4, 13))
        g.add_node(2, pos=(4, 13))
        g.add_node(3, pos=(4, 13))
        g.add_node(4, pos=(4, 165))
        g.add_edges_from([(1, 2), (3, 4)])

        _assert_crossing_equality(
            g,
            [crossings.Crossing(crossings.CrossingPoint(4, 13), {(1, 2), (3, 4)})],
            False,
            True,
        )

    def test_edge_on_edge_1(self):
        g = nx.Graph()
        g.add_node(1, pos=(0, 0))
        g.add_node(2, pos=(458929, -458929))
        g.add_node(3, pos=(123, -123))
        g.add_node(4, pos=(123, -123))
        g.add_edges_from([(1, 2), (3, 4)])

        _assert_crossing_equality(g, [], False, False)

    def test_edge_on_edge_2(self):
        g = nx.Graph()
        g.add_node(1, pos=(0, 0))
        g.add_node(2, pos=(458929, -458929))
        g.add_node(3, pos=(123, -123))
        g.add_node(4, pos=(123, -123))
        g.add_edges_from([(1, 2), (3, 4)])

        _assert_crossing_equality(
            g,
            [crossings.Crossing(crossings.CrossingPoint(123, -123), {(1, 2), (3, 4)})],
            False,
            True,
        )

    def test_edge_on_crossing_1(self):
        g = nx.Graph()
        g.add_node(1, pos=(0, 0))
        g.add_node(2, pos=(1, 1))
        g.add_node(3, pos=(1, 0))
        g.add_node(4, pos=(0, 1))
        g.add_node(5, pos=(0.5, 0.5))
        g.add_node(6, pos=(0.5, 0.5))
        g.add_edges_from([(1, 2), (3, 4), (5, 6)])

        _assert_crossing_equality(
            g,
            [crossings.Crossing(crossings.CrossingPoint(0.5, 0.5), {(1, 2), (3, 4)})],
            False,
        )

    def test_edge_on_crossing_2(self):
        g = nx.Graph()
        g.add_node(1, pos=(0, 0))
        g.add_node(2, pos=(1, 1))
        g.add_node(3, pos=(1, 0))
        g.add_node(4, pos=(0, 1))
        g.add_node(5, pos=(0.5, 0.5))
        g.add_node(6, pos=(0.5, 0.5))
        g.add_edges_from([(1, 2), (3, 4), (5, 6)])

        _assert_crossing_equality(
            g,
            [
                crossings.Crossing(
                    crossings.CrossingPoint(0.5, 0.5), {(1, 2), (3, 4), (5, 6)}
                )
            ],
            False,
            True,
        )

    def test_complex_scenario_1(self):
        g = nx.Graph()
        g.add_node(1, pos=(0, 0))
        g.add_node(2, pos=(1, 1))
        g.add_node(3, pos=(1, 0))
        g.add_node(4, pos=(0, 1))
        g.add_node(5, pos=(0.5, 0.5))
        g.add_node(6, pos=(0.5, 1000))
        g.add_node(7, pos=(0.5, 0.5))
        g.add_node(8, pos=(0.5, 0.5))
        g.add_edges_from([(1, 2), (3, 4), (5, 6), (7, 8)])

        _assert_crossing_equality(
            g,
            [crossings.Crossing(crossings.CrossingPoint(0.5, 0.5), {(1, 2), (3, 4)})],
            True,
        )

    def test_complex_scenario_2(self):
        g = nx.Graph()
        g.add_node(1, pos=(0, 0))
        g.add_node(2, pos=(1, 1))
        g.add_node(3, pos=(1, 0))
        g.add_node(4, pos=(0, 1))
        g.add_node(5, pos=(0.5, 0.5))
        g.add_node(6, pos=(0.5, 1000))
        g.add_node(7, pos=(0.5, 0.5))
        g.add_node(8, pos=(0.5, 0.5))
        g.add_node(9, pos=(0.5, 0.5))
        g.add_edges_from([(1, 2), (3, 4), (5, 6), (7, 8)])

        _assert_crossing_equality(
            g,
            [
                crossings.Crossing(
                    crossings.CrossingPoint(0.5, 0.5), {(1, 2), (3, 4), (5, 6), (7, 8)}
                )
            ],
            False,
            True,
        )

    def test_edge_with_common_endpoint_1(self):
        g = nx.Graph()
        g.add_node(1, pos=(0, 0))
        g.add_node(2, pos=(0, 0))
        g.add_node(3, pos=(1, 1))
        g.add_edges_from([(1, 2), (3, 1)])

        _assert_crossing_equality(g, [], True)

    def test_edge_with_common_endpoint_2(self):
        g = nx.Graph()
        g.add_node(1, pos=(0, 0))
        g.add_node(2, pos=(0, 0))
        g.add_node(3, pos=(1, 1))
        g.add_edges_from([(1, 2), (3, 1)])

        _assert_crossing_equality(
            g,
            [crossings.Crossing(crossings.CrossingPoint(0, 0), {(1, 2), (1, 3)})],
            True,
            True,
        )

    def test_edge_with_common_endpoint_3(self):
        g = nx.Graph()
        g.add_node(1, pos=(0, 0))
        g.add_node(2, pos=(0, 0))
        g.add_node(3, pos=(0, 0))
        g.add_edges_from([(1, 2), (3, 1)])

        _assert_crossing_equality(g, [], True)

    def test_edge_with_common_endpoint_4(self):
        g = nx.Graph()
        g.add_node(1, pos=(0, 0))
        g.add_node(2, pos=(0, 0))
        g.add_node(3, pos=(0, 0))
        g.add_edges_from([(1, 2), (3, 1)])

        _assert_crossing_equality(
            g,
            [crossings.Crossing(crossings.CrossingPoint(0, 0), {(1, 2), (1, 3)})],
            True,
            True,
        )

    def test_edge_with_self_loop_1(self):
        g = nx.Graph()
        g.add_node(1, pos=(0, 0))
        g.add_node(2, pos=(0, 0))
        g.add_edges_from([(1, 1), (1, 2)])

        _assert_crossing_equality(g, [], True)

    def test_edge_with_self_loop_2(self):
        g = nx.Graph()
        g.add_node(1, pos=(0, 0))
        g.add_node(2, pos=(0, 0))
        g.add_edges_from([(1, 1), (1, 2)])

        _assert_crossing_equality(
            g,
            [crossings.Crossing(crossings.CrossingPoint(0, 0), {(1, 2), (1, 1)})],
            True,
            True,
        )

    def test_edge_on_self_loop_1(self):
        g = nx.Graph()
        g.add_node(1, pos=(0, 0))
        g.add_node(2, pos=(0, 0))
        g.add_node(3, pos=(0, 0))
        g.add_edges_from([(1, 1), (2, 3)])

        _assert_crossing_equality(g, [], True)

    def test_edge_on_self_loop_2(self):
        g = nx.Graph()
        g.add_node(1, pos=(0, 0))
        g.add_node(2, pos=(0, 0))
        g.add_node(3, pos=(0, 0))
        g.add_edges_from([(1, 1), (2, 3)])

        _assert_crossing_equality(
            g,
            [crossings.Crossing(crossings.CrossingPoint(0, 0), {(2, 3), (1, 1)})],
            True,
            True,
        )

    def test_edge_on_other_length_zero_edge_1(self):
        g = nx.Graph()
        g.add_node(1, pos=(0, 0))
        g.add_node(2, pos=(0, 0))
        g.add_node(3, pos=(0, 0))
        g.add_node(4, pos=(0, 0))
        g.add_edges_from([(1, 2), (3, 4)])

        _assert_crossing_equality(g, [], True)

    def test_edge_on_other_length_zero_edge_2(self):
        g = nx.Graph()
        g.add_node(1, pos=(0, 0))
        g.add_node(2, pos=(0, 0))
        g.add_node(3, pos=(0, 0))
        g.add_node(4, pos=(0, 0))
        g.add_edges_from([(1, 2), (3, 4)])

        _assert_crossing_equality(
            g,
            [crossings.Crossing(crossings.CrossingPoint(0, 0), {(1, 2), (3, 4)})],
            True,
            True,
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


class TestNearCollinearOverlaps(unittest.TestCase):
    """
    Two segments that are *almost* collinear - every point of one lies within
    `numeric.get_precision()` of the other's infinite line - should be reported
    as an overlapping `CrossingLine`, the same as if they were exactly
    collinear. See `tests/unit/utils/test_intersections.py`
    (`TestNearCollinearOverlaps`) for the same two cases tested directly
    against `check_lines`.

    `test_segment_tilted_within_precision_of_collinear_should_overlap` is left
    intentionally failing - not a `check_lines` bug, but a separate,
    pre-existing `crossings.py` sweep-line event-handling bug that this
    overlap shape happens to trigger. See "Open: `horizontal_edges.remove()`
    fails for a near-collinear, non-exactly-horizontal pair" in
    `KNOWN_ISSUES_SWEEP_LINE.md`.
    """

    def test_segment_tilted_within_precision_of_collinear_should_overlap(self):
        g = nx.Graph()
        g.add_node(1, pos=(0, 0))
        g.add_node(2, pos=(10, 0))
        g.add_node(3, pos=(2, 6e-10))
        g.add_node(4, pos=(8, -6e-10))
        g.add_edges_from([(1, 2), (3, 4)])
        _assert_crossing_equality(
            g,
            [
                crossings.Crossing(
                    crossings.CrossingLine(CrossingPoint(2, 0), CrossingPoint(8, 0)),
                    {(1, 2), (3, 4)},
                )
            ],
        )

    def test_segment_shifted_within_precision_of_collinear_should_overlap(self):
        g = nx.Graph()
        g.add_node(1, pos=(0, 0))
        g.add_node(2, pos=(10, 0))
        g.add_node(3, pos=(2, 5e-10))
        g.add_node(4, pos=(8, 5e-10))
        g.add_edges_from([(1, 2), (3, 4)])
        _assert_crossing_equality(
            g,
            [
                crossings.Crossing(
                    crossings.CrossingLine(CrossingPoint(2, 0), CrossingPoint(8, 0)),
                    {(1, 2), (3, 4)},
                )
            ],
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
.
        previous_precision = numeric.get_precision()
        try:
            crossing_list = crossings.get_crossings(g, precision=0.142)
        finally:
            numeric.set_precision(previous_precision)

        assert len(crossing_list) == 1
        assert math.isclose(crossing_list[0].pos[0], 1.5, rel_tol=0.142)
        assert math.isclose(crossing_list[0].pos[1], 1.5, rel_tol=0.142)

        # Note that we explicitly do not check for the contained edges as grouping crossings together which are not
        #  actually crossing at the same point

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

    def test_crossing_line_crossed_by_two_edges(self):
        g = nx.Graph()
        g.add_nodes_from([0, 1, 2, 4, 5, 6, 7])
        g.add_edges_from([(0, 4), (0, 6), (1, 4), (2, 5), (5, 7)])
        nx.set_node_attributes(g, {0: {'pos': [0, 1]}, 1: {'pos': [0, 0]}, 2: {'pos': [0, -1]}, 4: {'pos': [-1, -1]}, 5: {'pos': [-1, 0]}, 6: {'pos': [-1, -1]}, 7: {'pos': [0, -1]}})

        _assert_crossing_equality(g, crossings.get_crossings_quadratic(g))

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


class TestNonGeneralPositionRegressions(unittest.TestCase):
    """
    Concrete, previously-failing instances found while debugging the sweep-line
    implementation's handling of non-general-position degeneracies (several edges
    meeting at exactly the same point, in ways the general adjacent-pair sweep
    doesn't naturally discover).
    """

    def test_prune_does_not_merge_unrelated_node_crossing_with_overlap(self):
        # Nodes 4 and 6 coincide at (1, -1). (6, 8) is collinear with (4, 8)
        # (already reported separately as a Line crossing) and merely shares node 6
        # with (6, 7) - it has no genuine point-crossing role at (1, -1) and must
        # not be merged into that point crossing by Crossing.prune().
        g = nx.Graph()
        g.add_edges_from([(4, 8), (6, 7), (6, 8)])
        nx.set_node_attributes(
            g, {4: [1, -1], 6: [1, -1], 7: [0, -1], 8: [0, 1]}, "pos"
        )
        _assert_crossing_equality(
            g,
            crossings.get_crossings_quadratic(g, include_node_crossings=True),
            include_node_crossings=True,
        )

    def test_collinear_group_overlap_not_missed_via_adjacency_chain(self):
        # Nodes {0, 3, 5, 8} coincide at (0, 1) and {2, 7} coincide at (0, -1), so
        # (0,2), (0,7), (2,3), (2,5), (2,8), (5,7), (7,8) are all the same fully
        # overlapping line segment. The old grouping algorithm walked candidates in
        # sorted-by-x order and chained together only adjacent overlapping pairs -
        # with other, non-overlapping edges interleaved at the same x, the chain
        # broke and silently dropped members of the group.
        g = nx.Graph()
        g.add_edges_from(
            [
                (0, 1), (0, 2), (0, 3), (0, 4), (0, 6), (0, 7), (0, 8),
                (1, 2), (1, 5), (1, 6), (1, 7), (1, 8),
                (2, 3), (2, 5), (2, 7), (2, 8),
                (3, 5), (3, 6), (3, 8),
                (4, 6), (4, 8),
                (5, 6), (5, 7), (5, 8),
                (6, 7), (6, 8),
                (7, 8),
            ]
        )
        nx.set_node_attributes(
            g,
            {
                0: [0, 1], 1: [-1, 0], 2: [0, -1], 3: [0, 1], 4: [1, -1],
                5: [0, 1], 6: [1, -1], 7: [0, -1], 8: [0, 1],
            },
            "pos",
        )
        _assert_crossing_equality(
            g,
            crossings.get_crossings_quadratic(g, include_node_crossings=True),
            include_node_crossings=True,
        )

    def test_edge_through_collinear_group_found_on_stale_tree(self):
        # Edge (9, 10) genuinely crosses two other edges at the exact same point,
        # but is never adjacent to either of them anywhere in the sweep before
        # that point (a third, share-endpoint-excluded edge always sits between
        # them). The old `get_range` used bounding-box pruning during tree descent
        # that assumed the tree's structure matches sorted order at the queried
        # height; since (9, 10) was never explicitly reordered, that assumption
        # broke and the pruning silently skipped the subtree containing it.
        g = nx.Graph()
        g.add_edges_from(
            [
                (0, 1), (0, 2), (0, 3), (0, 4), (0, 5), (0, 6), (0, 7), (0, 8),
                (0, 9), (0, 12),
                (1, 2), (1, 3), (1, 4), (1, 5), (1, 6), (1, 7), (1, 9), (1, 11),
                (1, 12),
                (2, 3), (2, 4), (2, 8), (2, 9), (2, 11),
                (3, 5), (3, 6), (3, 7), (3, 8), (3, 9), (3, 10), (3, 11),
                (4, 5), (4, 6), (4, 7), (4, 8), (4, 9), (4, 11), (4, 12),
                (5, 6), (5, 7), (5, 10), (5, 12),
                (6, 9), (6, 10), (6, 11), (6, 12),
                (7, 8), (7, 10), (7, 11), (7, 12),
                (8, 9), (8, 10), (8, 12),
                (9, 10), (9, 11), (9, 12),
                (10, 11), (10, 12), (10, 13), (10, 14),
                (11, 12), (11, 13), (11, 14),
                (12, 14),
                (13, 14),
            ]
        )
        nx.set_node_attributes(
            g,
            {
                0: [1, -1], 1: [1, 1], 2: [-1, -1], 3: [-1, 0], 4: [1, 1],
                5: [1, 1], 6: [-1, 1], 7: [-1, 1], 8: [-1, 1], 9: [1, 0],
                10: [0, 1], 11: [1, 1], 12: [0, -1], 13: [-1, -1], 14: [-1, -1],
            },
            "pos",
        )
        _assert_crossing_equality(
            g,
            crossings.get_crossings_quadratic(g, include_node_crossings=True),
            include_node_crossings=True,
        )

    def test_crossing_against_one_of_several_exactly_tied_outer_edges(self):
        # (8, 12) crosses a collinear group of edges ((5,11), (6,11), (7,14),
        # (11,13), (11,14), all the same line) at a point further down the sweep
        # than where (8, 12) last had a registered event. get_left/get_right can
        # only return one of several edges that are exactly tied with it at that
        # other point (here, tied with another, unrelated edge) - so without
        # checking the rest of that tie, the crossing was never queued at all.
        g = nx.Graph()
        g.add_edges_from(
            [
                (0, 2), (0, 4), (0, 5), (0, 6), (0, 8), (0, 9), (0, 11), (0, 12),
                (0, 13), (0, 14),
                (1, 2), (1, 5), (1, 8), (1, 10), (1, 11),
                (2, 3), (2, 4), (2, 5), (2, 10), (2, 11), (2, 13),
                (3, 5), (3, 8), (3, 9), (3, 10), (3, 12), (3, 13), (3, 14),
                (4, 8), (4, 9), (4, 10), (4, 11),
                (5, 6), (5, 8), (5, 9), (5, 10), (5, 11), (5, 12), (5, 13),
                (6, 8), (6, 9), (6, 10), (6, 12), (6, 13),
                (7, 10), (7, 11), (7, 12), (7, 14),
                (8, 9), (8, 10), (8, 12),
                (9, 10), (9, 11), (9, 12),
                (10, 11), (10, 12), (10, 13), (10, 14),
                (11, 12), (11, 13), (11, 14),
                (12, 14),
                (13, 14),
            ]
        )
        nx.set_node_attributes(
            g,
            {
                0: [-1, 0], 1: [1, 0], 2: [1, 0], 3: [1, 0], 4: [-1, 0],
                5: [-1, -1], 6: [-1, -1], 7: [1, 1], 8: [-1, 1], 9: [1, 0],
                10: [0, 1], 11: [1, 1], 12: [0, -1], 13: [-1, -1], 14: [-1, -1],
            },
            "pos",
        )
        _assert_crossing_equality(
            g,
            crossings.get_crossings_quadratic(g, include_node_crossings=True),
            include_node_crossings=True,
        )

    def test_get_left_get_right_find_closest_match_not_just_any_match(self):
        # (13, 19) and (42, 46) genuinely cross at (0, -0.4). Right before that,
        # they're already directly adjacent on the sweep line with nothing between
        # them - but get_left/get_right used to descend into only one subtree per
        # node based on a comparison against that node alone (the same kind of
        # structural-staleness trap fixed for get_range earlier): for an edge that
        # was last explicitly reordered somewhere else entirely (here, (42, 46) at
        # an earlier 5-way crossing through the origin), that descent could walk
        # straight past the actual closest match and return some other,
        # technically-valid-but-wrong neighbour instead - here (14, 17), which
        # never registers the crossing with (13, 19) that's actually about to
        # happen.
        g = nx.Graph()
        g.add_edges_from(
            [
                (8, 29), (12, 29), (13, 19), (14, 17), (17, 23),
                (18, 27), (21, 27), (32, 54), (42, 46),
            ]
        )
        nx.set_node_attributes(
            g,
            {
                32: [-1, 2], 8: [-2, 1], 42: [0, -3], 12: [-1, -2], 13: [-3, 2],
                14: [1, -2], 46: [0, 1], 17: [-1, 2], 18: [1, 1], 19: [2, -2],
                21: [3, 2], 54: [1, -2], 23: [2, -3], 27: [-3, -2], 29: [1, 2],
            },
            "pos",
        )
        _assert_crossing_equality(
            g, crossings.get_crossings_quadratic(g)
        )

    def test_interior_list_reorder_is_not_corrupted_by_interleaving(self):
        # Four edges - (0,1), (2,3), (4,5), (6,7) - all pass through the exact
        # same point (0, 0): three distinct slopes plus the vertical (6, 7).
        # _handle_event's "reverse the order of interior edges" loop processes
        # this tied group by removing and immediately reinserting each edge in
        # turn (in arbitrary set-iteration order), rather than removing the
        # whole group first and only then reinserting it. While edge A is being
        # reinserted, some of its true new neighbours may already be back in
        # their new position while others are still missing entirely - an
        # inconsistent intermediate tree state that can structurally misplace
        # an edge relative to others it's never been directly compared to.
        #
        # (8, 9) crosses three of the four concurrent edges further down the
        # sweep, at three separate points. With the AVL tree's get_left/
        # get_right/get_range reverted to plain pruning (no full traversal),
        # this corruption causes the crossing with (4, 5) specifically -
        # (4, 5) being whichever edge ends up structurally misplaced - to be
        # silently dropped entirely, even though it's a perfectly ordinary,
        # non-degenerate crossing on its own.
        g = nx.Graph()
        g.add_edges_from([(0, 1), (2, 3), (4, 5), (6, 7), (8, 9)])
        nx.set_node_attributes(
            g,
            {
                0: [2, 2], 1: [-2, -2], 2: [6, 2], 3: [-6, -2], 4: [2, 6],
                5: [-2, -6], 6: [0, 9], 7: [0, -6], 8: [-2, 8], 9: [-1, -8],
            },
            "pos",
        )
        _assert_crossing_equality(
            g, crossings.get_crossings_quadratic(g)
        )

    def test_zero_length_edge_does_not_steal_the_extreme_slot(self):
        # (15, 22) is a zero-length edge (both endpoints coincide at (0, 1)). At
        # the event where it and (11, 22) both start, _get_extreme_edges used to
        # pick between them by x at a probe height - but a zero-length edge's x
        # is constant regardless of height, so it could spuriously look "more
        # extreme" than the genuinely sloped (11, 22), which is the one that
        # actually goes on to cross (9, 21) later. Testing only the (wrongly)
        # chosen representative against the outer edge silently missed that
        # crossing entirely.
        g = nx.Graph()
        g.add_edges_from([(9, 21), (11, 22), (15, 22)])
        nx.set_node_attributes(
            g, {9: [1, 0], 11: [1, -1], 15: [0, 1], 21: [-1, 1], 22: [0, 1]}, "pos"
        )
        _assert_crossing_equality(g, crossings.get_crossings_quadratic(g))

    def test_collinear_group_member_with_matching_extent_not_skipped(self):
        # (6, 8), (8, 9) and (8, 12) are all on the same vertical line (x=2), but
        # with different finite extents: y in [1,2], [-2,2] and [0,2]
        # respectively. (0, 7) crosses that line at (2, -1), which only (8, 9)'s
        # extent actually reaches. _get_extreme_edges picks just one
        # representative of this tied group to test against (0, 7); if that
        # happens to be (6, 8) or (8, 12) instead of (8, 9), check_lines correctly
        # reports no intersection for that pair (the point is outside their
        # extent) - and the genuine crossing with (8, 9) was never tried as a
        # separate pairing.
        g = nx.Graph()
        g.add_edges_from([(0, 7), (6, 8), (8, 9), (8, 11), (8, 12), (8, 14)])
        nx.set_node_attributes(
            g,
            {
                0: [3, 1], 6: [2, 1], 7: [1, -3], 8: [2, 2], 9: [2, -2],
                11: [0, -2], 12: [2, 0], 14: [-3, 1],
            },
            "pos",
        )
        _assert_crossing_equality(
            g,
            crossings.get_crossings_quadratic(g, include_node_crossings=True),
            include_node_crossings=True,
        )
