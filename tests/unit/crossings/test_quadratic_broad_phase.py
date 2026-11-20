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
Tests for the broad phase of :func:`gdMetriX.crossings.get_crossings_quadratic`.

The quadratic algorithm is the reference every other crossing test compares against, so its broad
phase must never change a result: it may only rule out pairs of edges that check_lines would not
report anyway. These tests run the same drawings with the broad phase forced on and switched off,
and require the exact same output - including the order of the crossings and every float bit of
their positions. The drawings are chosen to stress the margins the broad phase relies on: edges
that are collinear or parallel within about the precision, edges shorter than the precision,
coordinates far larger than the precision, and precisions other than the default.
"""

import itertools
import math
import random

import networkx as nx
import pytest

from gdMetriX import crossings


@pytest.fixture
def broad_phase(monkeypatch):
    """Returns a function computing the quadratic crossings with the broad phase on or off."""

    def _run(g, enabled: bool, **kwargs):
        threshold = 0 if enabled else math.inf
        monkeypatch.setattr(crossings, "_BROAD_PHASE_MIN_EDGES", threshold)
        return repr(crossings.get_crossings_quadratic(g, **kwargs))

    return _run


def _segments(pairs) -> nx.Graph:
    g = nx.Graph()
    for i, (a, b) in enumerate(pairs):
        g.add_node(f"{i}a", pos=a)
        g.add_node(f"{i}b", pos=b)
        g.add_edge(f"{i}a", f"{i}b")
    return g


def _near_collinear(rng: random.Random) -> nx.Graph:
    """Segments along one line, each nudged off it by about the precision."""
    angle = rng.uniform(0, math.pi)
    dx, dy = math.cos(angle), math.sin(angle)
    ox, oy = rng.uniform(-50, 50), rng.uniform(-50, 50)
    offsets = [0, 1e-11, 5e-10, 9e-10, 1e-9, 1.1e-9, 3e-9, 1e-8, 1e-6, 1e-3]

    pairs = []
    for _ in range(rng.randint(2, 8)):
        t0, t1 = sorted((rng.uniform(-20, 20), rng.uniform(-20, 20)))
        if rng.random() < 0.2:
            t1 = t0 + rng.choice([0, 1e-12, 1e-10, 1e-9, 2e-9, 1e-8, 1e-7])
        off0 = rng.choice(offsets) * rng.choice([-1, 1])
        off1 = rng.choice(offsets) * rng.choice([-1, 1])
        pairs.append(
            (
                (ox + dx * t0 - dy * off0, oy + dy * t0 + dx * off0),
                (ox + dx * t1 - dy * off1, oy + dy * t1 + dx * off1),
            )
        )
    # Some segments crossing that line
    for _ in range(rng.randint(0, 3)):
        t = rng.uniform(-20, 20)
        cx, cy = ox + dx * t, oy + dy * t
        s = rng.uniform(0.5, 5)
        pairs.append(((cx + dy * s, cy - dx * s), (cx - dy * s, cy + dx * s)))
    rng.shuffle(pairs)
    return _segments(pairs)


def _tiny_segments(rng: random.Random) -> nx.Graph:
    """Segments far shorter than the precision, scattered among and on longer ones."""
    pairs = []
    for _ in range(rng.randint(2, 6)):
        a = (rng.uniform(-3, 3), rng.uniform(-3, 3))
        angle = rng.uniform(0, 2 * math.pi)
        length = rng.choice([1e-13, 1e-11, 5e-10, 1e-9, 3e-9, 1e-7, 1e-5, 2])
        pairs.append(
            (a, (a[0] + length * math.cos(angle), a[1] + length * math.sin(angle)))
        )
    for _ in range(rng.randint(1, 4)):
        pairs.append(
            (
                (rng.uniform(-3, 3), rng.uniform(-3, 3)),
                (rng.uniform(-3, 3), rng.uniform(-3, 3)),
            )
        )
    # A tiny segment lying right on a long one
    a, b = pairs[-1]
    t = rng.random()
    p = (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
    pairs.append((p, (p[0] + 1e-11, p[1] - 1e-11)))
    rng.shuffle(pairs)
    return _segments(pairs)


def _random_graph(rng: random.Random, n, p, coordinate_range, integer=True):
    g = nx.fast_gnp_random_graph(n, p, rng.randint(1, 10**8))
    draw = rng.randint if integer else rng.uniform
    nx.set_node_attributes(
        g,
        {
            v: (
                draw(-coordinate_range, coordinate_range),
                draw(-coordinate_range, coordinate_range),
            )
            for v in g
        },
        "pos",
    )
    return g


def _drawings(kind: str, count: int):
    rng = random.Random(f"broad-phase-{kind}")
    for _ in range(count):
        if kind == "near_collinear":
            yield _near_collinear(rng), {}
        elif kind == "tiny_segments":
            yield _tiny_segments(rng), {}
        elif kind == "degenerate_grid":
            g = _random_graph(
                rng, rng.randint(3, 16), rng.uniform(0.1, 1.0), rng.choice([1, 2])
            )
            yield g, {"include_node_crossings": True}
        elif kind == "large_coordinates":
            scale = rng.choice([1e6, 1e9, 1e12])
            g = _random_graph(
                rng, rng.randint(4, 12), rng.uniform(0.2, 0.9), scale, integer=False
            )
            yield g, {}
        elif kind == "other_precisions":
            g = _random_graph(
                rng, rng.randint(4, 14), rng.uniform(0.1, 0.8), rng.choice([2, 10, 100])
            )
            yield g, {"precision": rng.choice([0.0, 1e-12, 1e-6, 1e-3, 0.1])}
        elif kind == "singletons":
            g = _random_graph(rng, rng.randint(3, 12), rng.uniform(0.2, 0.9), 2)
            for k in range(rng.randint(1, 3)):
                g.add_node(f"s{k}", pos=(rng.randint(-2, 2), rng.randint(-2, 2)))
            yield g, {"include_node_crossings": True, "consider_singletons": True}


_KINDS = [
    "near_collinear",
    "tiny_segments",
    "degenerate_grid",
    "large_coordinates",
    "other_precisions",
    "singletons",
]


class TestBroadPhaseNeverChangesTheResult:

    @pytest.mark.parametrize("kind", _KINDS)
    @pytest.mark.parametrize("include_node_crossings", [False, True])
    def test_same_result_with_and_without(
        self, broad_phase, kind, include_node_crossings
    ):
        for g, kwargs in _drawings(kind, 40):
            kwargs.setdefault("include_node_crossings", include_node_crossings)
            if kwargs.get("consider_singletons"):
                kwargs["include_node_crossings"] = True

            assert broad_phase(g, True, **kwargs) == broad_phase(g, False, **kwargs)


class TestCandidatePairs:

    @staticmethod
    def _infos(segments):
        g = _segments(segments)
        positions = crossings._convert_to_crossing_points(g, None)
        return [
            crossings.SweepLineEdgeInfo.from_edge(edge, positions) for edge in g.edges()
        ]

    def test_without_broad_phase_all_pairs_in_order(self, monkeypatch):
        monkeypatch.setattr(crossings, "_BROAD_PHASE_MIN_EDGES", math.inf)
        infos = self._infos([((i, 0), (i, 1)) for i in range(5)])

        assert list(crossings._candidate_pairs(infos, 1e-9)) == list(
            itertools.combinations(range(5), 2)
        )

    def test_pairs_are_in_combination_order(self, monkeypatch):
        monkeypatch.setattr(crossings, "_BROAD_PHASE_MIN_EDGES", 0)
        rng = random.Random(5)
        infos = self._infos(
            [
                (
                    (rng.uniform(0, 10), rng.uniform(0, 10)),
                    (rng.uniform(0, 10), rng.uniform(0, 10)),
                )
                for _ in range(30)
            ]
        )

        pairs = list(crossings._candidate_pairs(infos, 1e-9))

        assert pairs == sorted(pairs)
        assert all(i < j for i, j in pairs)

    def test_rules_out_edges_far_apart(self, monkeypatch):
        monkeypatch.setattr(crossings, "_BROAD_PHASE_MIN_EDGES", 0)
        # Parallel, short segments far apart from each other
        infos = self._infos([((10 * i, 0), (10 * i + 1, 1)) for i in range(20)])

        assert list(crossings._candidate_pairs(infos, 1e-9)) == []

    def test_rules_out_edges_on_one_side_of_each_other(self, monkeypatch):
        monkeypatch.setattr(crossings, "_BROAD_PHASE_MIN_EDGES", 0)
        # Overlapping bounding boxes, but no point in common
        infos = self._infos([((0, 0), (10, 10)), ((1, 0), (10, 9))])

        assert list(crossings._candidate_pairs(infos, 1e-9)) == []

    def test_keeps_edges_touching_within_precision(self, monkeypatch):
        monkeypatch.setattr(crossings, "_BROAD_PHASE_MIN_EDGES", 0)
        infos = self._infos([((0, 0), (10, 0)), ((5, 5e-10), (5, 10))])

        assert list(crossings._candidate_pairs(infos, 1e-9)) == [(0, 1)]

    def test_keeps_every_pair_of_an_edge_shorter_than_the_margin(self, monkeypatch):
        monkeypatch.setattr(crossings, "_BROAD_PHASE_MIN_EDGES", 0)
        infos = self._infos(
            [((0, 0), (1, 0)), ((100, 100), (100, 100 + 1e-9)), ((50, 0), (51, 0))]
        )

        assert list(crossings._candidate_pairs(infos, 1e-9)) == [(0, 1), (1, 2)]

    @pytest.mark.parametrize("bad", [math.inf, -math.inf, math.nan])
    def test_falls_back_to_all_pairs_for_non_finite_coordinates(self, monkeypatch, bad):
        monkeypatch.setattr(crossings, "_BROAD_PHASE_MIN_EDGES", 0)
        infos = self._infos([((0, 0), (1, 1)), ((5, 5), (6, 6)), ((bad, 0), (1, 0))])

        assert list(crossings._candidate_pairs(infos, 1e-9)) == list(
            itertools.combinations(range(3), 2)
        )

    @pytest.mark.parametrize("count", [0, 1])
    def test_fewer_than_two_edges(self, monkeypatch, count):
        monkeypatch.setattr(crossings, "_BROAD_PHASE_MIN_EDGES", 0)
        infos = self._infos([((0, 0), (1, 1))] * count)

        assert list(crossings._candidate_pairs(infos, 1e-9)) == []
