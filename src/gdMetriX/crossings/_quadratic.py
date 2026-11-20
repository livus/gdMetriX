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
The quadratic crossing detection behind :func:`gdMetriX.crossings.get_crossings_quadratic`: every
pair of edges is checked, after a broad phase has ruled out the pairs that cannot intersect.

It is also the reference the sweep line algorithm is tested against, so it must stay simple
enough to be obviously right - and fast enough to check many drawings.
"""

import itertools
from typing import Dict, List, Union

import networkx as nx
import numpy as np

from gdMetriX.crossings.data_types import Crossing, convert_to_crossing_points
from gdMetriX.crossings.intersections import check_lines, check_point_and_line
from gdMetriX.utils import numeric
from gdMetriX.utils.sweep_line import CrossingPoint, SweepLineEdgeInfo

# region Broad phase

# Below this many edges, numpy's per-call overhead outweighs the pairs it rules out.
BROAD_PHASE_MIN_EDGES = 48


def candidate_pairs(edge_infos: List[SweepLineEdgeInfo], precision: float):
    """
    Yields the index pairs (i, j), i < j, of all edges that might intersect - in the order of
    itertools.combinations, so that the result does not depend on whether pairs were ruled out.

    A pair is only ruled out if it certainly cannot intersect within `precision`, so every pair
    check_lines would report is still yielded. See filtered_pairs.
    """
    m = len(edge_infos)
    coordinates = None

    if m >= max(BROAD_PHASE_MIN_EDGES, 2):
        try:
            coordinates = np.array(
                [
                    (
                        info.start_position.x,
                        info.start_position.y,
                        info.end_position.x,
                        info.end_position.y,
                    )
                    for info in edge_infos
                ],
                dtype=np.float64,
            )
        except (TypeError, ValueError, OverflowError):
            coordinates = None

        if coordinates is not None and not np.isfinite(coordinates).all():
            coordinates = None

    if coordinates is None:
        return itertools.combinations(range(m), 2)

    return filtered_pairs(coordinates, precision)


def filtered_pairs(coordinates: np.ndarray, precision: float):
    """
    Rules out, one edge against all later ones at a time, the pairs of edges that cannot intersect:
    those whose bounding boxes lie apart, and those where one edge lies entirely on one side of the
    other's line.

    Both tests leave a margin well beyond `precision` and beyond the rounding of the float
    arithmetic here - the coordinates may have been exact integers - so that they never rule out a
    pair check_lines would report. Edges that are not much longer than that margin are never ruled
    out: their direction says next to nothing, and check_lines' collinearity test may still pair
    them with an edge that is further away.
    """
    start_x, start_y, end_x, end_y = coordinates.T
    scale = float(np.abs(coordinates).max())

    tolerance = 10 * precision + 1e-12 * scale
    # Absolute rounding slack for the cross products below, which scale with coordinates squared
    slack = 1e-12 * scale * scale

    min_x = np.minimum(start_x, end_x) - tolerance
    max_x = np.maximum(start_x, end_x) + tolerance
    min_y = np.minimum(start_y, end_y) - tolerance
    max_y = np.maximum(start_y, end_y) + tolerance

    direction_x = end_x - start_x
    direction_y = end_y - start_y
    length = np.hypot(direction_x, direction_y)
    threshold = tolerance * length + slack
    exempt = (length > 0) & (length <= 1000 * tolerance)
    exempt_indices = np.flatnonzero(exempt)

    m = len(coordinates)
    for i in range(m - 1):
        if exempt[i]:
            yield from ((i, j) for j in range(i + 1, m))
            continue

        # The bounding boxes first, x before y: the cheapest tests, and in most drawings they
        # already rule out nearly every pair. The tests after only look at what is left.
        later = slice(i + 1, m)
        candidates = (i + 1) + np.flatnonzero(
            (min_x[later] <= max_x[i]) & (max_x[later] >= min_x[i])
        )
        candidates = candidates[
            (min_y[candidates] <= max_y[i]) & (max_y[candidates] >= min_y[i])
        ]

        # Sides of the candidates' endpoints relative to the line of edge i ...
        side_start = direction_x[i] * (start_y[candidates] - start_y[i]) - direction_y[
            i
        ] * (start_x[candidates] - start_x[i])
        side_end = direction_x[i] * (end_y[candidates] - start_y[i]) - direction_y[
            i
        ] * (end_x[candidates] - start_x[i])
        bound = threshold[i]
        apart = ((side_start > bound) & (side_end > bound)) | (
            (side_start < -bound) & (side_end < -bound)
        )

        # ... and of edge i's endpoints relative to the lines of the candidates
        side_start = direction_x[candidates] * (
            start_y[i] - start_y[candidates]
        ) - direction_y[candidates] * (start_x[i] - start_x[candidates])
        side_end = direction_x[candidates] * (
            end_y[i] - start_y[candidates]
        ) - direction_y[candidates] * (end_x[i] - start_x[candidates])
        bound = threshold[candidates]
        apart |= ((side_start > bound) & (side_end > bound)) | (
            (side_start < -bound) & (side_end < -bound)
        )

        candidates = candidates[~apart]

        # Exempt edges are always checked, wherever they lie
        later_exempt = exempt_indices[exempt_indices > i]
        if later_exempt.size:
            candidates = np.union1d(candidates, later_exempt)

        for j in candidates.tolist():
            yield i, j


# endregion


@numeric.applies_precision
def crossings_quadratic(
    g: nx.Graph,
    pos: Union[str, dict, None],
    include_node_crossings: bool,
    consider_singletons: bool,
    precision: float,
) -> List[Crossing]:
    """
    Computes all crossings of the given drawing by checking every pair of edges. The arguments are
    those of :func:`gdMetriX.crossings.get_crossings_quadratic`, already validated.
    """
    node_positions = convert_to_crossing_points(g, pos)

    # Built once per edge rather than once per pair of edges
    edges = list(g.edges())
    edge_infos = [SweepLineEdgeInfo.from_edge(edge, node_positions) for edge in edges]

    crossings = []
    # The result of every pair found to intersect, which pruning would otherwise compute again
    relations: Dict[tuple, object] = {}

    for i, j in candidate_pairs(edge_infos, precision):
        crossing_point = check_lines(edge_infos[i], edge_infos[j])

        if crossing_point is not None:
            crossings.append(Crossing(crossing_point, {edges[i], edges[j]}))
            relations[(edges[i], edges[j])] = crossing_point

    if consider_singletons:
        singletons = list(sorted(nx.isolates(g), key=lambda x: node_positions[x]))

        previous_singleton = None
        prev_pos = None

        for singleton in singletons:
            current_pos = node_positions[singleton]

            if current_pos == prev_pos:
                crossings.append(
                    Crossing(current_pos, set(), {singleton, previous_singleton})
                )
            else:
                # Check all edges for overlap
                for edge, edge_info in zip(edges, edge_infos):
                    crossing_point = check_point_and_line(current_pos, edge_info)

                    if crossing_point is not None:
                        crossings.append(Crossing(current_pos, {edge}, {singleton}))
                        break

            previous_singleton = singleton
            prev_pos = node_positions[previous_singleton]

    crossings.sort()

    # Group together crossings at the same position. Each one is compared against the first
    # crossing of the current group.
    grouped: List[Crossing] = []
    for crossing in crossings:
        if grouped and grouped[-1].pos == crossing.pos:
            grouped[-1].involved_edges.update(crossing.involved_edges)
            grouped[-1].involved_singletons.update(crossing.involved_singletons)
        else:
            grouped.append(crossing)

    edge_info_of = dict(zip(edges, edge_infos))

    def _filter_node_crossings(cr: Crossing):
        if isinstance(cr.pos, CrossingPoint):
            cr.prune(node_positions, include_node_crossings, edge_info_of, relations)
        return len(cr) > 1

    return list(filter(_filter_node_crossings, grouped))
