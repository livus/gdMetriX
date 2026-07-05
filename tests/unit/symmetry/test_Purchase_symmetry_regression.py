# gdMetriX
#
# Copyright (C) 2026  Martin Nöllenburg, Sebastian Röder, Markus Wallinger
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
Regression tests for the optimized ``gdMetriX.symmetry.reflective_symmetry``.

The shipped ``reflective_symmetry`` is an optimized implementation of the
Purchase 2002 axial-symmetry metric. These tests pin it against the original
naive implementation, kept out of the package in ``_reference_symmetry`` (see
that module) purely as the test oracle: the two must agree to within
floating-point tolerance on every input.

The oracle itself has an :math:`O(n^7)` worst case, so the graphs used here are
kept small and sparse (and use ``threshold >= 2``) to keep the *reference*
implementation tractable. Inputs on which the shared ``crossings.planarize``
preprocessing raises (overlapping/collinear edges) are handled explicitly,
since both implementations share that step.
"""

import math
import random
import unittest

import networkx as nx

# noinspection PyUnresolvedReferences
import pytest

# noinspection PyUnresolvedReferences
import pytest_socket

from gdMetriX import crossings
from gdMetriX import symmetry as sym

from . import _reference_symmetry as reference


# ---------------------------------------------------------------------------
# The fast implementation must reproduce the same input validation and
# trivial-case behavior as the original.
# ---------------------------------------------------------------------------


class TestFastInputValidation(unittest.TestCase):

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


class TestFastTrivialCases(unittest.TestCase):

    def test_empty_graph(self):
        assert sym.reflective_symmetry(nx.Graph()) == 1

    def test_single_node(self):
        g = nx.Graph()
        g.add_node(1, pos=(123, -45))
        assert sym.reflective_symmetry(g) == 1

    def test_single_edge(self):
        g = nx.Graph()
        g.add_node(1, pos=(123, -45))
        g.add_node(2, pos=(1, 1))
        g.add_edge(1, 2)
        assert sym.reflective_symmetry(g) == 1

    def test_single_edge_and_singleton_should_return_zero(self):
        g = nx.Graph()
        g.add_node(1, pos=(1, 1))
        g.add_node(2, pos=(4, 3))
        g.add_node(3, pos=(-1, 2))
        g.add_edge(1, 2)
        assert sym.reflective_symmetry(g) == 0

    def test_no_edges_but_positive_area_returns_zero(self):
        # Isolated nodes give a positive convex-hull area (so the metric does
        # not short-circuit) but edge_subgraph drops every node, leaving nothing
        # to match. Both implementations must return 0 rather than crash.
        g = nx.Graph()
        g.add_node(1, pos=(0, 0))
        g.add_node(2, pos=(4, 0))
        g.add_node(3, pos=(2, 3))
        assert reference.reflective_symmetry(g) == 0
        assert sym.reflective_symmetry(g) == 0


# ---------------------------------------------------------------------------
# Regression battery: fast vs. original on a variety of drawings.
# ---------------------------------------------------------------------------


def _rectangle():
    g = nx.Graph()
    g.add_node(1, pos=(-1, -1))
    g.add_node(2, pos=(-1, 1))
    g.add_node(3, pos=(1, 1))
    g.add_node(4, pos=(1, -1))
    g.add_edges_from([(1, 2), (2, 3), (3, 4), (4, 1)])
    return g


def _cycle(n):
    g = nx.Graph()
    for i in range(n):
        g.add_node(
            i,
            pos=(
                math.sin(math.radians(i * 360 / n)),
                math.cos(math.radians(i * 360 / n)),
            ),
        )
        g.add_edge(i, (i + 1) % n)
    return g


def _grid(k):
    base = nx.grid_2d_graph(k, k)
    mapping = {node: i for i, node in enumerate(base.nodes())}
    g = nx.relabel_nodes(base, mapping)
    for node, i in mapping.items():
        g.nodes[i]["pos"] = (float(node[0]), float(node[1]))
    return g


def _right_angle_cross():
    g = nx.Graph()
    g.add_node(1, pos=(-1, 0))
    g.add_node(2, pos=(1, 0))
    g.add_node(3, pos=(0, -1))
    g.add_node(4, pos=(0, 1))
    g.add_edges_from([(1, 2), (3, 4)])
    return g


def _house():
    g = nx.Graph()
    g.add_node(1, pos=(-1, -1))
    g.add_node(2, pos=(-1, 1))
    g.add_node(3, pos=(1, 1))
    g.add_node(4, pos=(1, -1))
    g.add_node(5, pos=(0, 2))
    g.add_edges_from([(1, 2), (2, 3), (3, 4), (4, 1), (2, 5), (3, 5)])
    return g


def _square_with_pendant():
    g = nx.Graph()
    g.add_node(1, pos=(-1, -1))
    g.add_node(2, pos=(-1, 1))
    g.add_node(3, pos=(1, 1))
    g.add_node(4, pos=(1, -1))
    g.add_node(5, pos=(-2, -2))
    g.add_edges_from([(1, 2), (2, 3), (3, 4), (4, 1), (1, 5)])
    return g


DETERMINISTIC_GRAPHS = {
    "rectangle": _rectangle(),
    "cycle6": _cycle(6),
    "cycle8": _cycle(8),
    "cycle10": _cycle(10),
    "grid3": _grid(3),
    "grid4": _grid(4),
    "right_angle_cross": _right_angle_cross(),
    "house": _house(),
    "square_with_pendant": _square_with_pendant(),
}


def _random_sparse_graphs():
    """Small, sparse drawings (mostly trees + a spare edge) that keep the
    O(n^7) oracle tractable while still producing crossings/partial symmetry."""
    graphs = {}
    for seed in range(14):
        rng = random.Random(3000 + seed)
        n = rng.randint(6, 9)
        try:
            g = nx.random_labeled_tree(n, seed=seed)
        except AttributeError:  # networkx < 3.2
            g = nx.random_tree(n, seed=seed)
        if seed % 2 == 0 and n >= 2:
            a, b = rng.sample(list(g.nodes()), 2)
            g.add_edge(a, b)
        for node in g.nodes():
            g.nodes[node]["pos"] = (rng.uniform(-5, 5), rng.uniform(-5, 5))
        graphs[f"random{seed}"] = g
    return graphs


RANDOM_GRAPHS = _random_sparse_graphs()

ALL_GRAPHS = {**DETERMINISTIC_GRAPHS, **RANDOM_GRAPHS}


@pytest.mark.parametrize("name", list(ALL_GRAPHS.keys()))
@pytest.mark.parametrize("threshold", [2, 3])
@pytest.mark.parametrize("fraction", [0.0, 0.5, 1.0])
def test_fast_matches_original(name, threshold, fraction):
    g = ALL_GRAPHS[name]

    try:
        expected = reference.reflective_symmetry(
            g, threshold=threshold, fraction=fraction
        )
    except crossings.OverlappingEdgesError:
        # Overlapping (collinear) edges are undefined for the shared
        # crossings.planarize preprocessing; both implementations reject them,
        # so there is no defined value to compare here. Assert the fast version
        # rejects them the same way.
        with pytest.raises(crossings.OverlappingEdgesError):
            sym.reflective_symmetry(g, threshold=threshold, fraction=fraction)
        return

    actual = sym.reflective_symmetry(g, threshold=threshold, fraction=fraction)

    assert actual == pytest.approx(expected, abs=1e-9)


@pytest.mark.parametrize("tolerance", [1e-2, 0.5, 3.0])
def test_fast_matches_original_across_tolerance(tolerance):
    # A larger tolerance changes which nodes are considered mirrored; the fast
    # version must track the original through that regime too.
    g = _grid(4)
    expected = reference.reflective_symmetry(g, threshold=2, tolerance=tolerance)
    actual = sym.reflective_symmetry(g, threshold=2, tolerance=tolerance)
    assert actual == pytest.approx(expected, abs=1e-9)


def test_fast_reproduces_intermediate_value():
    """A drawing whose symmetry is strictly between 0 and 1 - this is where the
    axis-deduplication / multiplicity weighting actually matters, since the same
    axis is generated by several node pairs and must be counted with the right
    multiplicity."""
    g = RANDOM_GRAPHS["random10"]

    expected = reference.reflective_symmetry(g, threshold=2, fraction=0.5)
    actual = sym.reflective_symmetry(g, threshold=2, fraction=0.5)

    assert 0 < expected < 1  # guards that this case is genuinely non-trivial
    assert actual == pytest.approx(expected, abs=1e-9)


def test_both_implementations_reject_overlapping_edges():
    """Overlapping (collinear) edges are undefined for the shared planarize
    step; both the original and the fast metric must surface the same specific
    error rather than an obscure TypeError."""
    g = nx.Graph()
    g.add_node("A", pos=(0, 0))
    g.add_node("B", pos=(3, 0))
    g.add_node("C", pos=(1, 0))
    g.add_node("D", pos=(4, 0))
    # Off-axis isolated node so the convex-hull area is > 0 and the metric does
    # not short-circuit before reaching the planarize step.
    g.add_node("E", pos=(2, 5))
    g.add_edges_from([("A", "B"), ("C", "D")])

    with pytest.raises(crossings.OverlappingEdgesError):
        reference.reflective_symmetry(g, threshold=2)
    with pytest.raises(crossings.OverlappingEdgesError):
        sym.reflective_symmetry(g, threshold=2)


def test_fast_result_in_unit_interval_on_random_graphs():
    rng = random.Random(987)
    for _ in range(20):
        n = rng.randint(2, 10)
        g = nx.fast_gnp_random_graph(
            n, rng.uniform(0.1, 0.8), seed=rng.randint(0, 10**7)
        )
        pos = {node: (rng.randint(-50, 50), rng.randint(-50, 50)) for node in g.nodes()}
        result = sym.reflective_symmetry(g, pos)
        assert 0 <= result <= 1
