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
This module collects some metrics on the distribution of nodes.

Methods
-------
"""
import math
import random
from enum import Enum
from typing import Union, List, Tuple, Optional, Iterable

import networkx as nx
import numpy as np
from scipy.spatial import KDTree

from gdMetriX import common, boundary, crossings
from gdMetriX.common import Numeric, Vector, circle_from_two_points, circle_from_three_points
from gdMetriX.utils import numeric
from gdMetriX.utils.sweep_line import SweepLineAlgorithm


@common.resolve_pos
def center_of_mass(
    g: nx.Graph,
    pos: Union[str, dict, None] = None,
    weight: Union[str, dict, None] = None,
) -> Optional[Vector]:
    """
    Calculates the center of mass of all vertices (i.e. the average vertex position). Edges are not considered.

    :param g: A networkX graph
    :type g: nx.Graph
    :param pos: Optional node position dictionary. If not supplied, node positions are read from the graph directly.
        If given as a string, the property under the given name in the networkX graph is used.
    :type pos: Union[str, dict, None]
    :param weight: An optional weight dictionary. If given as a string, the property under the given name in the
        networkX graph is used.
    :type weight: Union[str, dict, None]
    :return: A vector representing the position of the center of mass. If the graph is empty, None is returned.
    :rtype: Optional[Vector]
    """
    if len(pos) == 0:
        return None

    if isinstance(weight, str):
        weight = nx.get_node_attributes(g, weight)

    total_sum = Vector(0.0, 0.0)

    for node, position in pos.items():
        node_position = Vector.from_point(position)
        if weight is not None:
            node_position *= weight[node]
        total_sum += node_position

    if weight is not None:
        total_weight = sum(weight.values())
    else:
        total_weight = g.number_of_nodes()

    total_sum /= total_weight

    return total_sum


def _get_grid_distribution(
    g: nx.Graph,
    pos: Union[str, dict, None],
    grid_size: int,
    bounding_box: Tuple[Numeric, Numeric, Numeric, Numeric] = None,
):
    return heatmap(g, pos, None, grid_size, bounding_box, False)


@common.resolve_pos
def heatmap(
    g: nx.Graph,
    pos: Union[dict, list, None] = None,
    values: Optional[list] = None,
    grid_size: int = 10,
    bounding_box: Tuple[Numeric, Numeric, Numeric, Numeric] = None,
    average: bool = True,
) -> np.ndarray:
    """
    Calculates a heatmap for all the values in `values` at the positions `pos`. The values and positions are expected
    to be of the same length and in the same order.

    :param g: A networkX graph
    :type g: nx.Graph
    :param pos: A dictionary or list of tuples of x and y positions. If not supplied, node positions are read from
        the graph directly. If given as a string, the property under the given name in the networkX graph is used.
    :type pos: Union[dict, list, None]
    :param values: A list of values. If None, `1` is assumed for each position.
    :type values: Optional[list]
    :param grid_size: Number of grid cells per dimension. A grid size of 5 would lead to 5x5 = 25 individual cells.
    :type grid_size: int
    :param bounding_box: The bounding box of the heatmap. If None, the minimum sized bounding box containing the whole
        graph is assumed.
    :type bounding_box: Tuple[numeric, numeric, numeric, numeric]
    :param average: If true, each the sum of each cell is divided by the number of values falling into it.
    :type average: bool
    :return: A two dimensional array with all grid cell values.
    :rtype: np.ndarray
    """
    if grid_size <= 0:
        raise ValueError("grid_size must be a positive integer")

    def _get_grid_cell(min_bound, max_bound, v):
        return int(
            min(((v - min_bound) / (max_bound - min_bound)) * grid_size, grid_size - 1)
        )

    if values is None:
        values = np.ones(len(pos))

    if bounding_box is None:
        x_min, y_min, x_max, y_max = boundary.bounding_box(g, pos)
    else:
        x_min, y_min, x_max, y_max = bounding_box

    grid = np.zeros((grid_size, grid_size))
    count = np.zeros((grid_size, grid_size))

    if isinstance(pos, dict):
        x_positions = [point[0] for point in pos.values()]
        y_positions = [point[1] for point in pos.values()]
    else:
        x_positions = [point[0] for point in pos]
        y_positions = [point[1] for point in pos]

    # Iterate through the values, x positions, and y positions
    for value, x, y in zip(values, x_positions, y_positions):
        # Determine grid indices
        grid_x = _get_grid_cell(x_min, x_max, x)
        grid_y = _get_grid_cell(y_min, y_max, y)

        # Add value to grid cell
        grid[grid_y, grid_x] += value
        count[grid_y, grid_x] += 1

    if average:
        grid = np.divide(grid, count, out=np.zeros_like(grid), where=count != 0)

    return grid


def _balance(
    g: nx.Graph,
    pos: Union[str, dict, None],
    use_relative_coordinates: bool,
    index_offset: int,
) -> float:
    pos = common.get_node_positions(g, pos)

    if len(pos) == 0:
        return 0

    if use_relative_coordinates:
        box = boundary.bounding_box(g, pos)
        cutoff = box[index_offset] + (box[index_offset + 2] - box[index_offset]) / 2
    else:
        cutoff = 0

    upper_count = 0
    lower_count = 0

    for _, point in pos.items():
        if point[index_offset] > cutoff:
            upper_count += 1
        elif point[index_offset] < cutoff:
            lower_count += 1
        else:
            upper_count += 0.5
            lower_count += 0.5

    return (
        0
        if lower_count + upper_count == 0
        else (upper_count - lower_count) / (lower_count + upper_count)
    )


@common.resolve_pos
def horizontal_balance(
    g: nx.Graph,
    pos: Union[str, dict, None] = None,
    use_relative_coordinates: bool = True,
) -> float:
    """
    Returns a value between -1 and 1 indicating the horizontal balance.

    A value of 0 means a perfectly even balance between the upper and lower half.
    A value of -1 means that all nodes lie on the lower half, a value of 1 means that all nodes lie on the upper
    half.

    :param g: A networkX graph
    :type g: nx.Graph
    :param pos: Optional node position dictionary. If not supplied, node positions are read from the graph directly.
        If given as a string, the property under the given name in the networkX graph is used.
    :type pos: Union[str, dict, None]
    :param use_relative_coordinates: Indicates whether to use the absolute zero points or relative coordinates.
        If use_relative_coordinates is true, the horizontal split line will be at the center between the lowest and
        the highest node in the graph. If use_relative_coordinates is false, the horizontal split line is put at y=0.
    :type use_relative_coordinates: bool
    :return: A value between -1 and 1.
    :rtype: float
    """

    return _balance(g, pos, use_relative_coordinates, 1)


@common.resolve_pos
def vertical_balance(
    g: nx.Graph,
    pos: Union[str, dict, None] = None,
    use_relative_coordinates: bool = True,
) -> float:
    """
    Returns a value between -1 and 1 indicating the vertical balance.

    A value of 0 means a perfectly even balance between the left and right half.
    A value of -1 means that all nodes lie on the left half, a value of 1 means that all nodes lie on the right
    half.

    :param g: A networkX graph
    :type g: nx.Graph
    :param pos: Optional node position dictionary. If not supplied, node positions are read from the graph directly.
        If given as a string, the property under the given name in the networkX graph is used.
    :type pos: Union[str, dict, None]
    :param use_relative_coordinates: Indicates whether to use the absolute zero points or relative coordinates.
        If use_relative_coordinates is true, the vertical split line will be at the center between the leftmost and the
        rightmost node in the graph. If use_relative_coordinates is false, the vertical split line is put at x=0.
    :type use_relative_coordinates: bool
    :return: A value between -1 and 1.
    :rtype: float
    """

    return _balance(g, pos, use_relative_coordinates, 0)


@common.resolve_pos
def homogeneity(g: nx.Graph, pos: Union[str, dict, None] = None) -> float:
    """
    Calculates how evenly the nodes are distributed among the four quadrants.

    The measure was first defined by :footcite:t:`taylor_applying_2005`.

    :param g: A networkX graph
    :type g: nx.Graph
    :param pos: Optional node position dictionary. If not supplied, node positions are read from the graph directly.
        If given as a string, the property under the given name in the networkX graph is used.
    :type pos: Union[str, dict, None]
    :return: A value between 0 and 1. A value of 0 indicates an even distribution among the quadrants, and 1 the worst
        case distribution.
    :rtype: float
    """
    if g.order() <= 1:
        return 0

    # Necessary variables
    n = g.order()
    n_avg = math.floor(n / 4)
    
    # Sum up the number of nodes in each quadrant
    quadrants = _get_grid_distribution(g, pos, 2)
    multiply = []
    divide = []
    for n_quadrant in quadrants.flatten():
        n_quadrant = int(n_quadrant)
        if n_quadrant < n_avg:
            multiply += list(range(n_quadrant + 1, n_avg + 1))
        elif n_quadrant > n_avg:
            divide += list(range(n_avg + 1, n_quadrant + 1))

    # Calculate the logarithmic sum of the numerator and denominator
    numerator = sum(math.log(x) for x in multiply)
    denominator = sum(math.log(x) for x in divide)

    # Calculate the fraction using the exponential function
    fraction = math.exp(numerator - denominator)

    return 1 - fraction


@common.resolve_pos
def concentration(
    g: nx.Graph,
    pos: Union[str, dict, None] = None,
    grid_size: Numeric = 0,
    bounding_box: Tuple[Numeric, Numeric, Numeric, Numeric] = None,
) -> float:
    """
    Calculates the concentration of the given networkX graph g.
    The concentration is a density measure counting the number of nodes in each cell of a sqrt(n) * sqrt(n) grid,
    where n is the number of nodes in the graph. The counts for each cell are then summed up and divided by n-1.

    A concentration of 1 means that all nodes are within a single grid cell, and a concentration of 0 means that
    all nodes are evenly spaced between the cells.

    The measure was first defined by :footcite:t:`taylor_applying_2005`.

    :param g: A networkX graph
    :type g: nx.Graph
    :param pos: Optional node position dictionary. If not supplied, node positions are read from the graph directly.
        If given as a string, the property under the given name in the networkX graph is used.
    :type pos: Union[str, dict, None]
    :param grid_size: For large graphs, where the calculation might be time sensitive, set a bigger grid size to improve
        performance. A higher grid size reduces the precision of the metric. In most cases, leaving the
        default value should be sufficient.
    :type grid_size: numeric
    :param bounding_box: The bounding box in the form of (x_min, y_min, x_max, y_max) of the graph.
        If not specified, a tight bounding box is used. All nodes must be contained within the bounding box.
    :type bounding_box: Tuple[numeric, numeric, numeric, numeric]
    :return: The concentration of the graph between 0 and 1
    :rtype: float
    """
    if g.order() <= 1:
        return 0

    if grid_size == 0:
        grid_size = int(math.ceil(math.sqrt(g.order())))
        expected_per_cell = 1
    elif grid_size < 0:
        raise ValueError("grid_size")
    elif grid_size > int(math.ceil(math.sqrt(g.order()))):
        raise ValueError(
            "The cell size is to small for the given graph. There can be at most one grid cell per node "
            "in the graph"
        )
    else:
        expected_per_cell = g.order() / math.pow(grid_size, 2)

    grid = _get_grid_distribution(g, pos, grid_size, bounding_box)
    return (np.sum(np.maximum(grid - expected_per_cell, 0))) / (g.order() - 1)


@common.resolve_pos
def closest_pair_of_points(g: nx.Graph, pos: Union[str, dict, None] = None):
    """
    Returns the two closest points a, b together with their euclidean distance in the form (a,b, distance)

    :param g: A networkX graph
    :type g: nx.Graph
    :param pos: Optional node position dictionary. If not supplied, node positions are read from the graph directly.
        If given as a string, the property under the given name in the networkX graph is used.
    :type pos: Union[str, dict, None]
    :return: The keys of the two involved nodes as well as their distance
    :rtype: (object, object, float)
    """
    if g.order() <= 1:
        return None, None, None

    points = [(key, pos[key][0], pos[key][1]) for key in pos]

    x_sorted = sorted(points, key=lambda p: p[1])
    y_sorted = sorted(points, key=lambda p: p[2])

    p, q, d_sq = _cpop_recursion(x_sorted, y_sorted)
    return p[0], q[0], d_sq ** 0.5


def _sq_dist(p, q):
    dx = p[1] - q[1]
    dy = p[2] - q[2]
    return dx * dx + dy * dy


def _cpop_brute_force(points):
    mi = _sq_dist(points[0], points[1])
    pair = (points[0], points[1])
    n = len(points)
    if n == 2:
        return pair[0], pair[1], mi
    for i in range(n - 1):
        for j in range(i + 1, n):
            d = _sq_dist(points[i], points[j])
            if d < mi:
                mi = d
                pair = (points[i], points[j])
    return pair[0], pair[1], mi


def _cpop_closest_split_pair(x_sorted_list, y_sorted_list, delta_sq, best_pair):
    mid_x = x_sorted_list[len(x_sorted_list) // 2][1]

    # Only points within delta in x
    strip = [p for p in y_sorted_list if (mid_x - p[1]) ** 2 < delta_sq]

    n = len(strip)
    for i in range(n - 1):
        for j in range(i + 1, min(i + 7, n)):
            d = _sq_dist(strip[i], strip[j])
            if d < delta_sq:
                delta_sq = d
                best_pair = (strip[i], strip[j])
    return best_pair[0], best_pair[1], delta_sq


def _cpop_recursion(x_sorted, y_sorted):
    if len(x_sorted) <= 3:
        return _cpop_brute_force(x_sorted)

    mid = len(x_sorted) // 2
    left_x = x_sorted[:mid]
    right_x = x_sorted[mid:]

    mid_x = x_sorted[mid][1]

    left_y = [p for p in y_sorted if p[1] <= mid_x]
    right_y = [p for p in y_sorted if p[1] > mid_x]

    p_l, q_l, d_l = _cpop_recursion(left_x, left_y)
    p_r, q_r, d_r = _cpop_recursion(right_x, right_y)

    if d_l <= d_r:
        min_total = d_l
        min_pair = (p_l, q_l)
    else:
        min_total = d_r
        min_pair = (p_r, q_r)

    # check split
    p_s, q_s, d_s = _cpop_closest_split_pair(x_sorted, y_sorted, min_total, min_pair)

    if min_total <= d_s:
        return min_pair[0], min_pair[1], min_total
    return p_s, q_s, d_s


class _ClosestPairSweep(SweepLineAlgorithm):
    """
    Finds the closest node-to-edge pair using a left-to-right sweep over the x-axis, reusing the generic
    driving loop from :class:`SweepLineAlgorithm` (the same base class used by the crossing detection sweep,
    see :class:`gdMetriX.crossings._CrossingSweep`).

    Unlike the crossing detection sweep, this does *not* reuse the AVL-backed SweepLineStatus for its active
    set. A single "position at the current sweep coordinate" key (such as x-at-y, or its mirror y-at-x) is only
    a sound proxy for an *exact* intersection test - for a "closest within distance d" query it is unsound for
    steep segments, since the vertical gap to a steep line can be arbitrarily larger than the true perpendicular
    distance to it. Active edges are therefore kept in a plain list, windowed by x with a safety margin (see
    :meth:`_build_events`/:meth:`_evict_expired`), and matched against each node via an exact bounding-box
    overlap check (sound for any slope) before falling back to the precise point-to-segment distance formula.

    The closest node-to-node pair is assumed to already be known (from :func:`closest_pair_of_points`) and is
    used as the initial best distance; only node-to-edge improvements are searched for.
    """

    _ADD_EDGE = 0
    _QUERY_NODE = 1

    def __init__(
        self,
        g: nx.Graph,
        pos: dict,
        element_a: object,
        element_b: object,
        min_distance: Optional[float],
    ):
        super().__init__()

        self.g = g
        self.pos = pos

        self.element_a = element_a
        self.element_b = element_b
        self.min_distance = min_distance
        self._initial_distance = min_distance

        self._events: List[Tuple[Numeric, int, object]] = []
        self._event_index = 0

        # Active edges: list of (x_max, y_min, y_max, edge)
        self._active: List[Tuple[Numeric, Numeric, Numeric, Tuple[object, object]]] = (
            []
        )

    def _build_events(self) -> None:
        if self.min_distance is None:
            # Fewer than two nodes - closest_pair_of_points already returned (None, None, None)
            # and there can be no edge to compare against
            return

        for edge in self.g.edges():
            x0, y0 = self.pos[edge[0]]
            x1, y1 = self.pos[edge[1]]
            x_min, x_max = min(x0, x1), max(x0, x1)
            y_min, y_max = min(y0, y1), max(y0, y1)

            # An edge can only be the closest match for a node whose true distance to it is below the initial
            # (upper bound) distance. By the standard coordinate-projection argument, such a node's x cannot be
            # smaller than x_min - initial_distance, so adding the edge there is always early enough.
            add_x = x_min - self._initial_distance
            self._events.append(
                (add_x, self._ADD_EDGE, (x_max, y_min, y_max, edge))
            )

        for node in self.g.nodes():
            self._events.append((self.pos[node][0], self._QUERY_NODE, node))

        self._events.sort(key=lambda e: (e[0], e[1]))

    def _pop_event(self) -> Optional[Tuple[Numeric, int, object]]:
        if self._event_index >= len(self._events):
            return None
        event = self._events[self._event_index]
        self._event_index += 1
        return event

    def _evict_expired(self, current_x: Numeric) -> None:
        # An edge whose x_max already lies more than the current best distance behind the sweep position can
        # no longer be closer than min_distance to any node still to come (same projection argument as above).
        self._active = [
            entry for entry in self._active if entry[0] >= current_x - self.min_distance
        ]

    def _distance_to_edge(self, node: object, edge: Tuple[object, object]) -> float:
        return common.LineSegment(
            Vector.from_point(self.pos[edge[0]]), Vector.from_point(self.pos[edge[1]])
        ).distance_to_point(Vector.from_point(self.pos[node]))

    def _handle_event(self, event: Tuple[Numeric, int, object]) -> None:
        x, kind, payload = event

        self._evict_expired(x)

        if kind == self._ADD_EDGE:
            self._active.append(payload)
            return

        node = payload
        y = self.pos[node][1]
        d = self.min_distance

        for x_max, y_min, y_max, edge in self._active:
            if node in edge:
                continue
            # Sound overlap check: any point within distance d of the edge has a y-coordinate within d of the
            # edge's y-range, regardless of the edge's slope
            if y_min - d > y or y_max + d < y:
                continue

            distance = self._distance_to_edge(node, edge)
            if distance < self.min_distance:
                self.min_distance = distance
                self.element_a, self.element_b = node, edge
                d = self.min_distance

    def _finalize(self) -> Tuple[object, object, Optional[float]]:
        return self.element_a, self.element_b, self.min_distance


@common.resolve_pos
def closest_pair_of_elements(
    g: nx.Graph, pos: Union[str, dict, None] = None, consider_crossings=False
):
    """
    Returns the two graph elements (i.e. nodes and edges) with minimum distance between between them.

    :param g: A networkX graph
    :type g: nx.Graph
    :param pos: Optional node position dictionary. If not supplied, node positions are read from the graph directly.
        If given as a string, the property under the given name in the networkX graph is used.
    :type pos: Union[str, dict, None]
    :param consider_crossings: Whether or not to consider crossings as well. If a crossing exists, the closest pair of
        elements consists of two crossing edges.
    :type consider_crossings:
    :return: The keys of the two closest graph elements as well as their distance
    :rtype: (object, object, float)
    """
    if consider_crossings:
        crossing_list = crossings.get_crossings(g, pos)
        if len(crossing_list) > 0:
            first_crossing = crossing_list[0]
            return (
                first_crossing.involved_edges.pop(),
                first_crossing.involved_edges.pop(),
                0.0,
            )

    element_a, element_b, min_distance = closest_pair_of_points(g, pos)

    return _ClosestPairSweep(g, pos, element_a, element_b, min_distance).run()


@common.resolve_pos
def node_orthogonality(
    g: nx.Graph,
    pos: Union[str, dict, None] = None,
    width: int = None,
    height: int = None,
) -> float:
    """
    Calculates the node orthogonality of a graph, defined by how densely packed nodes are on the grid. More precisely,
    the metric is defined by the number of nodes devided by the number of grid cells.

    :param g: A networkX graph
    :type g: nx.Graph
    :param pos: Optional node position dictionary. If not supplied, node positions are read from the graph directly.
        If given as a string, the property under the given name in the networkX graph is used.
    :type pos: Union[str, dict, None]
    :param width: Total number of horizontal grid cells. If not supplied, a minimal integer grid fitting g is assumed.
    :type width: int
    :param height: Total number of vertical grid cells. If not supplied, a minimal integer grid fitting g is assumed.
    :type height: int
    :return: A metric of node orthogonality between 0 and 1
    :rtype: float
    """

    if width is None:
        width = math.ceil(boundary.width(g, pos)) + 1
    if height is None:
        height = math.ceil(boundary.height(g, pos)) + 1

    return g.order() / (width * height)


@common.resolve_pos
def gabriel_ratio(g: nx.Graph, pos: Union[str, dict, None] = None) -> float:
    """
    The Gabriel ratio is the ratio of the number of nodes falling within a minimum circle covering an edge for any edge.

    This measure was first defined by :footcite:t:`purchase_landscape`.

    :param g: A networkX graph
    :type g: nx.Graph
    :param pos: Optional node position dictionary. If not supplied, node positions are read from the graph directly.
        If given as a string, the property under the given name in the networkX graph is used.
    :type pos: Union[str, dict, None]
    :return: The Gabriel ratio between 0 and 1
    :rtype: float
    """
    nodes = list(g.nodes())
    edges = list(g.edges())
    n = g.order()

    if len(edges) == 0 or len(nodes) <= 2:
        return 1.0

    # Neighbors for each node to count candidates
    neighbors = {v: set(g.neighbors(v)) for v in nodes}

    # KD tree to find violations faster
    vecs = {v: Vector.from_point(pos[v]) for v in nodes}
    points = [(vecs[v].x, vecs[v].y) for v in nodes]
    tree = KDTree(points)

    # Pre-convert to vectors
    vecs = {v: Vector.from_point(pos[v]) for v in nodes}

    total_candidates = 0
    total_violations = 0

    for u, v in edges:
        if u == v:
            continue

        u_pos = vecs[u]
        v_pos = vecs[v]

        midpoint = u_pos.mid(v_pos)
        radius = midpoint.distance(u_pos)

        # eligible nodes for this edge
        violations = 0

        # ---- Count candidates ----
        neighbors_u = neighbors[u] - {u, v}
        neighbors_v = neighbors[v] - {u, v}

        both = len(neighbors_u & neighbors_v)
        one = len(neighbors_u) + len(neighbors_v) - 2 * both
        none = n - 2 - one - both

        # Weighted counting (scaled by 6)
        total_candidates += 6 * none + 3 * one + 2 * both

        # ---- Count violations ----
        indices = tree.query_ball_point((midpoint.x, midpoint.y), radius)

        for idx in indices:
            w = nodes[idx]
            if w == u or w == v:
                continue

            # Strict interior test
            if numeric.greater_than(
                    radius, midpoint.distance(vecs[w])
            ):
                total_violations += 1

    # We counted every violation times 6 to keep everything integer
    total_candidates /= 6

    if total_candidates == 0 or total_violations == 0:
        return 1.0

    return 1.0 - (total_violations / total_candidates)


def _smallest_enclosing_circle_iteratively(points: List[Vector]) -> common.Circle:
    class _SecStages(Enum):
        """Stages between all recursive calls"""

        FIRST_CALL = 0
        SECOND_CALL = 1
        TRAIL = 2

    stack = [(_SecStages.FIRST_CALL, None)]
    results = []
    point_boundary: List[Vector] = []

    while stack:
        stage, point = stack.pop()

        if stage == _SecStages.FIRST_CALL:
            if not points or len(point_boundary) == 3:
                # Trivial cases
                if len(point_boundary) == 0:
                    circle = Vector(0, 0), 0.0
                elif len(point_boundary) == 1:
                    circle = point_boundary[0], 0.0
                elif len(point_boundary) == 2:
                    circle = circle_from_two_points(point_boundary[0], point_boundary[1])
                elif len(point_boundary) == 3:
                    circle = circle_from_three_points(
                        point_boundary[0], point_boundary[1], point_boundary[2]
                    )
                else:
                    raise ValueError()
                results.append(circle)
            else:
                p = points.pop()
                stack.append((_SecStages.SECOND_CALL, p))
                stack.append((_SecStages.FIRST_CALL, None))

        elif stage == _SecStages.SECOND_CALL:
            center, radius = results.pop()

            if point.distance(center) <= radius:
                points.append(point)
                results.append((center, radius))
            else:
                point_boundary.append(point)
                stack.append((_SecStages.TRAIL, point))
                stack.append((_SecStages.FIRST_CALL, None))

        elif stage == _SecStages.TRAIL:
            circle = results.pop()
            point_boundary.pop()
            points.append(point)
            results.append(circle)

    return results.pop()


def smallest_enclosing_circle_from_point_set(points: Iterable) -> common.Circle:
    """
    Implementation of Welzl's algorithm to find the smallest enclosing circle of a point set.

    :param points: List of points
    :type points: Iterable
    :return: The centre and radius of the smallest circle containing all points in the list.
    :rtype:  gdMetriX.Circle
    """
    points = [common.Vector(p[0], p[1]) for p in points]

    if len(points) == 0:
        return Vector(0, 0), 0

    random.shuffle(points)

    # Find extremes to fast-charge the algorithm
    left_most, left_most_index = None, None
    right_most, right_most_index = None, None
    top_most, top_most_index = None, None
    bottom_most, bottom_most_index = None, None
    for index, point in enumerate(points):
        if left_most is None or left_most > point.x:
            left_most = point.x
            left_most_index = index

        if right_most is None or right_most < point.x:
            right_most = point.x
            right_most_index = index

        if top_most is None or top_most < point.y:
            top_most = point.y
            top_most_index = index

        if bottom_most is None or bottom_most > point.y:
            bottom_most = point.y
            bottom_most_index = index

    indices = {left_most_index, right_most_index, top_most_index, bottom_most_index}
    elements = [points[i] for i in indices]
    indices_sorted = sorted(indices, reverse=True)

    for i in indices_sorted:
        points.pop(i)
    for point in elements:
        points.insert(0, point)

    return _smallest_enclosing_circle_iteratively(points)


@common.resolve_pos
def smallest_enclosing_circle(
    g: nx.Graph, pos: Union[str, dict, None] = None
) -> common.Circle:
    """
    Implementation of Welzl's algorithm to find the smallest enclosing circle of a graph.

    :param g: A networkX graph
    :type g: nx.Graph
    :param pos: Optional node position dictionary. If not supplied, node positions are read from the graph directly.
        If given as a string, the property under the given name in the networkX graph is used.
    :type pos: Union[str, dict, None]
    :return: The centre and radius of the smallest circle containing all nodes in g.
    :rtype:  gdMetriX.Circle
    """
    return smallest_enclosing_circle_from_point_set(pos.values())
