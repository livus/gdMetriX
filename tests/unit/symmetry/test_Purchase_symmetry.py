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


class TestInputValidation(unittest.TestCase):

    def setUp(self):
        self.g = nx.Graph()
        self.g.add_node(1, pos=(0, 0))
        self.g.add_node(2, pos=(1, 0))
        self.g.add_edge(1, 2)

    def test_zero_threshold_raises(self):
        with self.assertRaises(ValueError):
            sym.reflective_symmetry(self.g, threshold=0)

    def test_negative_threshold_raises(self):
        with self.assertRaises(ValueError):
            sym.reflective_symmetry(self.g, threshold=-1)

    def test_zero_tolerance_raises(self):
        with self.assertRaises(ValueError):
            sym.reflective_symmetry(self.g, tolerance=0)

    def test_negative_tolerance_raises(self):
        with self.assertRaises(ValueError):
            sym.reflective_symmetry(self.g, tolerance=-1e-3)


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
            g.add_node(
                i, pos=(math.sin(math.radians(i * 36)), math.cos(math.radians(i * 36)))
            )
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
            random_graph = nx.fast_gnp_random_graph(
                int(i / 2), random.uniform(0.1, 1), random.randint(1, 10000000)
            )
            random_embedding = {
                n: [random.randint(-100, 100), random.randint(-100, 100)]
                for n in range(0, i + 1)
            }

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

        assert symmetry == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# Tests exposing known deviations from the Purchase paper and Mooney's
# reference implementation.  Each class documents one specific difference.
# All tests in these classes are currently expected to fail (xfail) and will
# turn green once the corresponding bug is fixed.
# ---------------------------------------------------------------------------


class TestThresholdBoundary:
    """
    Bug: the threshold check uses ``<= threshold`` (requires *more* than
    threshold edges) instead of ``< threshold`` (requires *at least* threshold
    edges).  The paper says "at least THRESHOLD edges which are mirrored".
    """

    def test_exactly_threshold_mirrored_edges_should_be_counted(self):
        """
        Two vertical edges that are perfect mirrors of each other around x=0.
        With threshold=2 there are exactly 2 mirrored edges, which the paper
        says should be counted (>= threshold).  The current implementation
        skips them (<= threshold) and returns 0 instead of 1.
        """
        g = nx.Graph()
        # Left vertical edge A-B and right vertical edge C-D are mirrors of
        # each other around the y-axis (x=0).
        g.add_node("A", pos=(-1, 1))
        g.add_node("B", pos=(-1, -1))
        g.add_node("C", pos=(1, 1))
        g.add_node("D", pos=(1, -1))
        g.add_edges_from([("A", "B"), ("C", "D")])

        result = sym.reflective_symmetry(g, threshold=2)

        # Perfectly symmetric graph: paper gives 1.0; current code gives 0.0.
        assert result > 0

    def test_fewer_than_threshold_mirrored_edges_should_not_be_counted(self):
        """Sanity check: 1 edge + 1 isolated node (giving non-zero convex hull
        area) cannot satisfy threshold=2 mirror pairs → result = 0.
        Isolated node is needed so the convex hull area is > 0 and the
        early-exit branch is not taken."""
        g = nx.Graph()
        g.add_node(1, pos=(-1, 1))
        g.add_node(2, pos=(1, 1))
        g.add_node(3, pos=(0, -1))  # isolated; keeps hull area > 0
        g.add_edge(1, 2)

        result = sym.reflective_symmetry(g, threshold=2)

        assert result == 0


class TestSubgraphEdgeSelection:
    """
    Bug: the implementation finds mirrored *nodes* and then takes the induced
    subgraph, which can include edges that have no mirror counterpart.  The
    paper (and Mooney) identify mirrored *edge pairs* directly; only edges
    whose mirror edge also exists are included in the symmetric subgraph.

    Consequence: our implementation over-counts the subgraph area and can
    report non-zero symmetry for graphs that have no reflective symmetry at
    all (in the edge-pair sense).
    """

    def test_non_mirrored_diagonal_edge_should_not_inflate_symmetry(self):
        """
        Graph has a horizontal edge A-B (which mirrors to itself around the
        vertical axis) and a diagonal edge A-D (whose mirror B-C does not
        exist).

        Paper: the symmetric subgraph for the vertical axis contains only
        A-B; its convex hull area is 0 (two collinear points), so it
        contributes nothing.  No other axis produces a non-zero-area
        symmetric subgraph → result = 0.

        Current implementation: mirrored_nodes = {A,B,C,D}, induced subgraph
        contains both A-B *and* A-D.  The induced nodes fill the full
        2×2 square (area=4), yielding a false result of 1.0.
        """
        g = nx.Graph()
        g.add_node("A", pos=(-1, 1))
        g.add_node("B", pos=(1, 1))
        g.add_node("C", pos=(-1, -1))
        g.add_node("D", pos=(1, -1))
        # A-B is symmetric around x=0 (maps to itself).
        # A-D is NOT symmetric: its mirror would be B-C, which is absent.
        g.add_edges_from([("A", "B"), ("A", "D")])

        result = sym.reflective_symmetry(g, threshold=1)

        assert result == 0

    def test_fully_mirrored_edges_give_nonzero_symmetry(self):
        """Sanity check: both diagonals of a square are present (and are each
        other's mirror) → the graph has genuine reflective symmetry."""
        g = nx.Graph()
        g.add_node("A", pos=(-1, 1))
        g.add_node("B", pos=(1, 1))
        g.add_node("C", pos=(-1, -1))
        g.add_node("D", pos=(1, -1))
        # Both diagonals present: A-D and B-C mirror each other around y=0.
        g.add_edges_from([("A", "D"), ("B", "C")])

        result = sym.reflective_symmetry(g, threshold=1)

        assert result > 0


class TestSubgraphSymmetryValue:
    """
    Bug: ``_subgraph_symmetry`` computes the factor P×Q by comparing the
    *two endpoints of the same edge* (pair_1[0] vs pair_1[1] and
    pair_2[0] vs pair_2[1]).  The paper (Fig. 4 / Fig. 8) specifies that P
    compares the *first endpoint of e* with the *first endpoint of its mirror f*
    (i.e. ``type(a)`` vs ``type(mirror_of_a)``), and Q does the same for the
    second endpoints.

    For a perfectly symmetric crossing, the crossing node maps to *itself*
    under the symmetry, so:
      - real node 1 ↔ real node 2  →  P = 1
      - crossing c  ↔ crossing c   →  Q = 1
      → P×Q = 1 → sub_sym = 1.0

    Current code instead checks ``type(1) != type(c)`` (mixed, different) and
    ``type(2) != type(c)`` (mixed, different), giving factor = 0.5 × 0.5 =
    0.25 for every edge pair, so sub_sym = 0.25.
    """

    def test_symmetric_crossing_with_fraction_should_give_full_symmetry(self):
        """
        Two edges crossing at a right angle form a perfectly symmetric graph.
        After planarisation, edge (1, c) maps to edge (2, c):
          - node 1 (real) corresponds to node 2 (real)  → P = 1
          - crossing c corresponds to crossing c          → Q = 1
        So the paper's sub_sym = 1.0 and the overall result should be 1.0.
        """
        g = nx.Graph()
        g.add_node(1, pos=(-1, 0))
        g.add_node(2, pos=(1, 0))
        g.add_node(3, pos=(0, -1))
        g.add_node(4, pos=(0, 1))
        g.add_edges_from([(1, 2), (3, 4)])

        result = sym.reflective_symmetry(g, threshold=2, fraction=0.5)

        assert result == pytest.approx(1.0)

    @pytest.mark.xfail(
        reason=(
            "Same root bug as above: when a real node maps to a crossing node "
            "(asymmetric crossing configuration), the paper's P = FRACTION, "
            "but the current code computes the wrong endpoints to compare."
        ),
        strict=False,
    )
    def test_asymmetric_node_types_in_mirror_reduce_symmetry_value(self):
        """
        A T-shaped crossing: one straight edge plus one edge whose endpoint
        lies on the straight edge.  After planarisation the crossing node c
        maps to a regular node on one axis, so the paper would apply the
        FRACTION penalty only to that pairing.

        This test verifies the *direction* of the penalty: result with
        fraction=0.5 should be strictly less than the same graph with
        fraction=1, and strictly greater than 0.
        """
        g = nx.Graph()
        # Horizontal edge plus a vertical edge starting from the axis midpoint
        # to one side only → asymmetric crossing configuration.
        g.add_node(1, pos=(-1, 0))
        g.add_node(2, pos=(1, 0))
        g.add_node(3, pos=(0, 1))
        g.add_edges_from([(1, 2), (2, 3)])

        result_default = sym.reflective_symmetry(g, threshold=1, fraction=1.0)
        result_penalised = sym.reflective_symmetry(g, threshold=1, fraction=0.5)

        assert 0 < result_penalised < result_default
