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
Stress tests for crossing detection.

These are marked `slow` and skipped by default (see conftest.py's `--runslow`
option and the `slow` marker registered in pyproject.toml) because they trade
runtime for much broader randomized coverage: many random graphs - including
deliberately degenerate ones with tiny coordinate ranges, lots of coincident
nodes, long collinear chains and multi-way crossings at a single point - are
generated and checked, asserting that the optimized sweep-line implementation
(`get_crossings`) agrees exactly with the brute-force quadratic reference
implementation (`get_crossings_quadratic`) on every single one of them.

Run explicitly with:

    pytest --runslow tests/unit/crossings/test_crossings_stress.py

Scale it up via environment variables:

    GD_METRIX_STRESS_ITERATIONS - random graphs per scenario (default varies)
    GD_METRIX_STRESS_MAX_NODES  - upper bound on graph size for the larger-scale
                                   scenarios (default varies)
    GD_METRIX_STRESS_CHUNK_SIZE - random graphs per chunk for the scenarios
                                   above (default varies per scenario)

For example, to let it run for a long search on a beefier machine:

    GD_METRIX_STRESS_ITERATIONS=200000 GD_METRIX_STRESS_MAX_NODES=400 \\
        pytest --runslow tests/unit/crossings/test_crossings_stress.py
"""

import math
import os
import random

import networkx as nx

# noinspection PyUnresolvedReferences
import pytest

from . import crossing_test_helper
from gdMetriX import crossings


def _iterations(default: int) -> int:
    return int(os.environ.get("GD_METRIX_STRESS_ITERATIONS", default))


def _max_nodes(default: int) -> int:
    return int(os.environ.get("GD_METRIX_STRESS_MAX_NODES", default))


def _chunk_size(default: int) -> int:
    return int(os.environ.get("GD_METRIX_STRESS_CHUNK_SIZE", default))


def _chunks(total: int, chunk_size: int):
    """Splits [0, total) into chunk_size-sized pieces: (chunk_index, start, end)."""
    if total <= 0:
        return []
    n_chunks = math.ceil(total / chunk_size)
    return [
        (
            chunk_index,
            chunk_index * chunk_size,
            min((chunk_index + 1) * chunk_size, total),
        )
        for chunk_index in range(n_chunks)
    ]


def _chunk_ids(chunks):
    return [f"{start}-{end}" for _, start, end in chunks]


def _assert_matches_quadratic(
    g: nx.Graph,
    include_node_crossings: bool = False,
    consider_singletons: bool = False,
) -> None:
    expected = crossings.get_crossings_quadratic(
        g,
        include_node_crossings=include_node_crossings,
        consider_singletons=consider_singletons,
    )
    crossing_test_helper.assert_crossing_equality(
        g,
        expected,
        crossings.get_crossings,
        include_node_crossings=include_node_crossings,
        consider_singletons=consider_singletons,
    )


def _random_graph(
    n: int, p: float, coordinate_range, integer_coordinates: bool = True
) -> nx.Graph:
    g = nx.fast_gnp_random_graph(n, p, random.randint(1, 10**8))
    if integer_coordinates:
        pos = {
            node: [
                random.randint(-coordinate_range, coordinate_range),
                random.randint(-coordinate_range, coordinate_range),
            ]
            for node in range(n)
        }
    else:
        pos = {
            node: [
                random.uniform(-coordinate_range, coordinate_range),
                random.uniform(-coordinate_range, coordinate_range),
            ]
            for node in range(n)
        }
    nx.set_node_attributes(g, pos, "pos")
    return g


@pytest.mark.slow
class TestStressTinyDegenerateGraphs(object):
    """
    Small graphs (a handful of nodes) squeezed into a tiny integer coordinate
    range. With that few possible positions, coincident nodes, collinear
    overlaps and multi-way crossings through a single point are the common case
    rather than the exception.
    """

    _tiny_chunks = _chunks(_iterations(3000), _chunk_size(100))

    @pytest.mark.parametrize("chunk", _tiny_chunks, ids=_chunk_ids(_tiny_chunks))
    def test_tiny_coordinate_range(self, chunk):
        chunk_index, start, end = chunk
        random.seed(424242 + chunk_index)
        for i in range(start, end):
            n = random.randint(3, 30)
            p = random.uniform(0.1, 1.0)
            coordinate_range = random.choice([1, 2, 3])
            g = _random_graph(n, p, coordinate_range)
            include_node_crossings = random.random() < 0.5
            _assert_matches_quadratic(g, include_node_crossings)

    _tiny_singleton_chunks = _chunks(_iterations(1000), _chunk_size(50))

    @pytest.mark.parametrize(
        "chunk", _tiny_singleton_chunks, ids=_chunk_ids(_tiny_singleton_chunks)
    )
    def test_tiny_coordinate_range_with_singletons(self, chunk):
        chunk_index, start, end = chunk
        random.seed(13371337 + chunk_index)
        for i in range(start, end):
            n = random.randint(3, 25)
            p = random.uniform(0.1, 1.0)
            coordinate_range = random.choice([1, 2, 3])
            g = _random_graph(n, p, coordinate_range)

            # A couple of isolated nodes that may or may not coincide with
            # something else already in the (tiny) coordinate range.
            next_node = n
            for _ in range(random.randint(1, 4)):
                g.add_node(
                    next_node,
                    pos=[
                        random.randint(-coordinate_range, coordinate_range),
                        random.randint(-coordinate_range, coordinate_range),
                    ],
                )
                next_node += 1

            _assert_matches_quadratic(
                g, include_node_crossings=True, consider_singletons=True
            )


@pytest.mark.slow
class TestStressMediumDegenerateGraphs(object):
    """
    Bigger than the tiny scenario above, but coordinates are still squeezed into
    a small range relative to the node count, so degeneracies stay common while
    there are enough edges for several of them to interact within one graph.
    """

    _medium_chunks = _chunks(_iterations(300), _chunk_size(10))

    @pytest.mark.parametrize("chunk", _medium_chunks, ids=_chunk_ids(_medium_chunks))
    def test_small_coordinate_range(self, chunk):
        chunk_index, start, end = chunk
        random.seed(271828182 + chunk_index)
        for i in range(start, end):
            n = random.randint(15, 60)
            p = random.uniform(0.05, 0.4)
            coordinate_range = random.choice([2, 3, 5, 8])
            g = _random_graph(n, p, coordinate_range)
            include_node_crossings = random.random() < 0.5
            _assert_matches_quadratic(g, include_node_crossings)


@pytest.mark.slow
class TestStressLargerGeneralPositionGraphs(object):
    """
    Larger graphs with a wide coordinate range, so most crossings end up in
    general position. Density is kept low so the O(E^2) quadratic reference
    stays tractable even with a few hundred nodes.
    """

    _larger_sparse_chunks = _chunks(_iterations(40), _chunk_size(2))

    @pytest.mark.parametrize(
        "chunk", _larger_sparse_chunks, ids=_chunk_ids(_larger_sparse_chunks)
    )
    def test_larger_sparse_graphs(self, chunk):
        chunk_index, start, end = chunk
        random.seed(31415926 + chunk_index)
        max_nodes = max(31, _max_nodes(150))
        for i in range(start, end):
            n = random.randint(30, max_nodes)
            p = random.uniform(0.01, 0.08)
            g = _random_graph(
                n, p, coordinate_range=100000, integer_coordinates=False
            )
            _assert_matches_quadratic(g, include_node_crossings=False)


@pytest.mark.slow
class TestStressGridLikeGraphs(object):
    """
    A heavily scaled-up version of test_random_graph_small_grid below: random
    graphs embedded on a tiny integer grid.
    """

    _grid_chunks = _chunks(_iterations(500), _chunk_size(20))

    @pytest.mark.parametrize("chunk", _grid_chunks, ids=_chunk_ids(_grid_chunks))
    def test_small_grid_many_iterations(self, chunk):
        chunk_index, start, end = chunk
        random.seed(19031023901924 + chunk_index)
        max_nodes = _max_nodes(40)
        for i in range(start, end):
            n = random.randint(2, max_nodes)
            g = nx.fast_gnp_random_graph(
                n, random.uniform(0.1, 1), random.randint(1, 10**8)
            )
            pos = {
                node: [random.randint(-1, 1), random.randint(-1, 1)]
                for node in range(n)
            }
            nx.set_node_attributes(g, pos, "pos")
            _assert_matches_quadratic(g, include_node_crossings=True)


@pytest.mark.slow
class TestStressPlanarGraphs(object):
    """
    Scaled-up version of test_random_planar_graphs below: Delaunay
    triangulations are planar by construction, so any crossing reported on one
    is necessarily wrong.
    """

    _planar_chunks = _chunks(_iterations(20), _chunk_size(1))

    @pytest.mark.parametrize("chunk", _planar_chunks, ids=_chunk_ids(_planar_chunks))
    def test_larger_delaunay_triangulations(self, chunk):
        from libpysal import weights
        from libpysal.cg import voronoi_frames

        chunk_index, start, end = chunk
        random.seed(271828 + chunk_index)
        max_nodes = _max_nodes(500)
        for i in range(start, end):
            n = random.randint(200, max_nodes)
            coordinates = [
                (random.uniform(0, 1), random.uniform(0, 1)) for _ in range(n)
            ]

            cells, generators = voronoi_frames(coordinates, clip="convex hull")
            delaunay = weights.Rook.from_dataframe(cells)
            delaunay_graph = delaunay.to_networkx()

            pos = dict(zip(delaunay_graph.nodes, coordinates))
            for node, value in pos.items():
                delaunay_graph.nodes[node]["pos"] = value

            _assert_matches_quadratic(delaunay_graph, include_node_crossings=False)


@pytest.mark.slow
class TestStressLegacyRandomGraphs(object):
    """
    Random-graph regression scenarios that originally lived inline in
    TestComplexCrossingScenarios (test_crossings.py). Moved here and chunked 
    like the scenarios above so they run on demand rather than on every
    default test run, and so progress is visible while they execute.
    """

    _random_graph_chunks = _chunks(10, _chunk_size(2))

    @pytest.mark.parametrize(
        "chunk", _random_graph_chunks, ids=_chunk_ids(_random_graph_chunks)
    )
    def test_random_graph(self, chunk):
        chunk_index, start, end = chunk
        random.seed(9018098129039 + chunk_index)
        for flat_index in range(start, end):
            i = 20 + flat_index // 2
            random_graph = nx.fast_gnp_random_graph(
                i, random.uniform(0.1, 0.5), random.randint(1, 10000000)
            )
            random_embedding = {
                n: [random.randint(-1000, 1000), random.randint(-1000, 1000)]
                for n in range(0, i + 1)
            }
            nx.set_node_attributes(random_graph, random_embedding, "pos")
            _assert_matches_quadratic(random_graph, include_node_crossings=True)

    _random_graph_2_chunks = _chunks(10, _chunk_size(2))

    @pytest.mark.parametrize(
        "chunk", _random_graph_2_chunks, ids=_chunk_ids(_random_graph_2_chunks)
    )
    def test_random_graph_2(self, chunk):
        chunk_index, start, end = chunk
        random.seed(9018098129039 + chunk_index)
        for flat_index in range(start, end):
            i = 20 + flat_index // 2
            random_graph = nx.fast_gnp_random_graph(
                i, random.uniform(0.1, 0.5), random.randint(1, 10000000)
            )
            random_embedding = {
                n: [random.randint(-1000, 1000), random.randint(-1000, 1000)]
                for n in range(0, i + 1)
            }
            nx.set_node_attributes(random_graph, random_embedding, "pos")
            _assert_matches_quadratic(random_graph)

    _random_line_graph_chunks = _chunks(100, _chunk_size(10))

    @pytest.mark.parametrize(
        "chunk",
        _random_line_graph_chunks,
        ids=_chunk_ids(_random_line_graph_chunks),
    )
    def test_random_line_graph(self, chunk):
        # Random graph that should be in normal position
        chunk_index, start, end = chunk
        random.seed(38528349829348 + chunk_index)
        for flat_index in range(start, end):
            i = flat_index // 2
            j = flat_index % 2
            random_graph = nx.Graph()

            for _node in range(i):
                random_graph.add_nodes_from([f"{i}a", f"{j}b"])
                random_graph.add_edge(f"{i}a", f"{j}b")

            random_embedding = {
                node: [random.randint(-1000, 1000), random.randint(-1000, 1000)]
                for node in random_graph.nodes()
            }
            nx.set_node_attributes(random_graph, random_embedding, "pos")

            _assert_matches_quadratic(random_graph, include_node_crossings=True)

    _random_graph_small_grid_chunks = _chunks(25, _chunk_size(5))

    @pytest.mark.parametrize(
        "chunk",
        _random_graph_small_grid_chunks,
        ids=_chunk_ids(_random_graph_small_grid_chunks),
    )
    def test_random_graph_small_grid(self, chunk):
        """
        Due to the smaller area, we expect much more edge cases such as:
            - Multiple crossings on the same point
            - Horizontal edges
            - Vertices on edges (we count those as crossings as well)
        """
        chunk_index, start, end = chunk
        random.seed(19031023901923 + chunk_index)
        for i in range(start, end):
            random_graph = nx.fast_gnp_random_graph(
                i, random.uniform(0.1, 1), random.randint(1, 1000000)
            )
            random_embedding = {
                n: [random.randint(-1, 1), random.randint(-1, 1)]
                for n in range(0, i + 1)
            }
            nx.set_node_attributes(random_graph, random_embedding, "pos")
            _assert_matches_quadratic(random_graph, include_node_crossings=True)

    _random_graph_small_grid_2_chunks = _chunks(25, _chunk_size(5))

    @pytest.mark.parametrize(
        "chunk",
        _random_graph_small_grid_2_chunks,
        ids=_chunk_ids(_random_graph_small_grid_2_chunks),
    )
    def test_random_graph_small_grid_2(self, chunk):
        """
        Due to the smaller area, we expect much more edge cases such as:
            - Multiple crossings on the same point
            - Horizontal edges
            - Vertices on edges (we count those as crossings as well)
        """
        chunk_index, start, end = chunk
        random.seed(19031023901923 + chunk_index)
        for i in range(start, end):
            random_graph = nx.fast_gnp_random_graph(
                i, random.uniform(0.1, 1), random.randint(1, 1000000)
            )
            random_embedding = {
                n: [random.randint(-1, 1), random.randint(-1, 1)]
                for n in range(0, i + 1)
            }
            nx.set_node_attributes(random_graph, random_embedding, "pos")
            _assert_matches_quadratic(random_graph)

    _random_planar_graphs_chunks = _chunks(20, _chunk_size(4))

    @pytest.mark.parametrize(
        "chunk",
        _random_planar_graphs_chunks,
        ids=_chunk_ids(_random_planar_graphs_chunks),
    )
    def test_random_planar_graphs(self, chunk):
        from libpysal import weights
        from libpysal.cg import voronoi_frames

        chunk_index, start, end = chunk
        random.seed(271828133742 + chunk_index)
        for flat_index in range(start, end):
            i = 20 + flat_index
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

            # Delaunay triangulations are planar by construction, so the sweep
            # line must not report any crossing on them.
            crossing_test_helper.assert_crossing_equality(
                delaunay_graph, [], crossings.get_crossings
            )
