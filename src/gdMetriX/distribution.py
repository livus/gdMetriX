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
from dataclasses import dataclass
import math
import random
from enum import Enum
from typing import Union, List, Tuple, Optional, Iterable

import networkx as nx
import numpy as np

from gdMetriX import common, boundary, crossings
from gdMetriX.common import Numeric, Vector


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
    :type pos: Union[str, dic, None]
    :param weight: An optional weight dictionary. If given as a string, the property under the given name in the
        networkX graph is used.
    :type weight: Union[str, dict, None]
    :return: A vector representing the position of the center of mass. If the graph is empty, None is returned.
    :rtype: Optional[Vector]
    """
    pos = common.get_node_positions(g, pos)

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


def heatmap(
    g: nx.Graph,
    pos: Union[dict, list],
    values: Optional[list],
    grid_size: int,
    bounding_box: Tuple[Numeric, Numeric, Numeric, Numeric] = None,
    average: bool = True,
) -> np.ndarray:
    """
    Calculates a heatmap for all the values in `values` at the positions `pos`. The values and positions are expected
    to be of the same length and in the same order.

    :param g: A networkX graph
    :type g: nx.Graph
    :param pos: A dictionary or list of tuples of x and y positions
    :type pos: pos: Optional[dict, list]
    :param values: A list of values. If None, `1` is assumed for each position.
    :type values: Optional[list, None]
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
    :type pos: Union[str, dic, None]
    :param use_relative_coordinates: Indicates whether to use the absolute zero points or relative coordinates.
        If use_relative_coordinates is true, the horizontal split line will be at the center between the lowest and
        the highest node in the graph. If use_relative_coordinates is false, the horizontal split line is put at y=0.
    :type use_relative_coordinates: bool
    :return: A value between -1 and 1.
    :rtype: float
    """

    return _balance(g, pos, use_relative_coordinates, 1)


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
    :type pos: Union[str, dic, None]
    :param use_relative_coordinates: Indicates whether to use the absolute zero points or relative coordinates.
        If use_relative_coordinates is true, the vertical split line will be at the center between the leftmost and the
        rightmost node in the graph. If use_relative_coordinates is false, the vertical split line is put at x=0.
    :type use_relative_coordinates: bool
    :return: A value between -1 and 1.
    :rtype: float
    """

    return _balance(g, pos, use_relative_coordinates, 0)


def homogeneity(g: nx.Graph, pos: Union[str, dict, None] = None) -> float:
    """
    Calculates how evenly the nodes are distributed among the four quadrants.

    The measure was first defined by :footcite:t:`taylor_applying_2005`.

    :param g: A networkX graph
    :type g: nx.Graph
    :param pos: Optional node position dictionary. If not supplied, node positions are read from the graph directly.
        If given as a string, the property under the given name in the networkX graph is used.
    :type pos: Union[str, dic, None]
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
    pos = common.get_node_positions(g, pos)

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
    :type pos: Union[str, dic, None]
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
    pos = common.get_node_positions(g, pos)

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


@dataclass
class _EmbeddedPoint:
    """Represents a vertex with position"""

    key: object
    vec: Vector

    def __str__(self):
        return f"[{self.key}, {self.vec}]"


def closest_pair_of_points(g: nx.Graph, pos: Union[str, dict, None] = None):
    """
    Returns the two closest points a, b together with their euclidean distance in the form (a,b, distance)

    :param g: A networkX graph
    :type g: nx.Graph
    :param pos: Optional node position dictionary. If not supplied, node positions are read from the graph directly.
        If given as a string, the property under the given name in the networkX graph is used.
    :type pos: Union[str, dic, None]
    :return: The keys of the two involved nodes as well as their distance
    :rtype: (object, object, float)
    """
    if g.order() <= 1:
        return None, None, None
    pos = common.get_node_positions(g, pos)

    p_list = list(_EmbeddedPoint(p, Vector.from_point(pos[p])) for p in pos)

    x_sorted = sorted(p_list, key=lambda p: p.vec.x)
    y_sorted = sorted(p_list, key=lambda p: p.vec.y)

    a, b, distance = _closest_pair_recursion(x_sorted, y_sorted)

    return a.key, b.key, distance


def _closest_pair_recursion(x_sorted, y_sorted):
    def _bruteforce_distance(
        points: List[_EmbeddedPoint],
    ) -> Tuple[_EmbeddedPoint, _EmbeddedPoint, float]:
        mi = points[0].vec.distance(points[1].vec)
        p1 = points[0]
        p2 = points[1]
        ln_ax = len(points)
        if ln_ax == 2:
            return p1, p2, mi
        for i in range(ln_ax - 1):
            for j in range(i + 1, ln_ax):
                if i != 0 and j != 1:
                    d = points[i].vec.distance(points[j].vec)
                    if d < mi:  # Update min_dist and points
                        mi = d
                        p1, p2 = points[i], points[j]
        return p1, p2, mi

    def _closest_split_pair(
        x_sorted_list: List[_EmbeddedPoint],
        y_sorted_list: List[_EmbeddedPoint],
        old_min: float,
        old_min_pair: Tuple[_EmbeddedPoint, _EmbeddedPoint],
    ) -> Tuple[_EmbeddedPoint, _EmbeddedPoint, float]:
        x_med = x_sorted_list[len(x_sorted_list) // 2].vec.x

        close_y = [
            p for p in y_sorted_list if x_med - old_min <= p.vec.x <= x_med + old_min
        ]
        new_min = old_min
        for i in range(len(close_y) - 1):
            for j in range(i + 1, min(i + 7, len(close_y))):
                p, q = close_y[i], close_y[j]
                dst = p.vec.distance(q.vec)
                if dst < new_min:
                    old_min_pair = p, q
                    new_min = dst
        return old_min_pair[0], old_min_pair[1], new_min

    if len(x_sorted) <= 3:
        return _bruteforce_distance(x_sorted)

    mid = len(x_sorted) // 2
    x_median = x_sorted[mid].vec.x
    # Split by x into two even halves
    left_x = x_sorted[:mid]
    right_x = x_sorted[mid:]

    left_y, right_y = [], []

    # Do the same for y
    for point in y_sorted:
        if point.vec.x <= x_median:
            left_y.append(point)
        else:
            right_y.append(point)

    (p_left, q_left, min_left) = _closest_pair_recursion(left_x, left_y)
    (p_right, q_right, min_right) = _closest_pair_recursion(right_x, right_y)

    # Combine the two halves
    if min_left <= min_right:
        min_total = min_left
        min_pair = (p_left, q_left)
    else:
        min_total = min_left
        min_pair = (p_right, q_right)

    (p_split, q_split, min_split) = _closest_split_pair(
        x_sorted, y_sorted, min_total, min_pair
    )

    if min_total <= min_split:
        return min_pair[0], min_pair[1], min_total
    return p_split, q_split, min_split


def _edge_node_distance(edge: Tuple[object, object], node: object, pos) -> float:
    return common.LineSegment(
        Vector.from_point(pos[edge[0]]), Vector.from_point(pos[edge[1]])
    ).distance_to_point(Vector.from_point(pos[node]))


def closest_pair_of_elements(
    g: nx.Graph, pos: Union[str, dict, None] = None, consider_crossings=False
):
    """
    Returns the two graph elements (i.e. nodes and edges) with minimum distance between between them.

    :param g: A networkX graph
    :type g: nx.Graph
    :param pos: Optional node position dictionary. If not supplied, node positions are read from the graph directly.
        If given as a string, the property under the given name in the networkX graph is used.
    :type pos: Union[str, dic, None]
    :param consider_crossings: Whether or not to consider crossings as well. If a crossing exists, the closest pair of
        elements consists of two crossing edges.
    :type consider_crossings:
    :return: The keys of the two closest graph elements as well as their distance
    :rtype: (object, object, float)
    """
    pos = common.get_node_positions(g, pos)
    element_a, element_b, min_distance = closest_pair_of_points(g, pos)

    if consider_crossings:
        crossing_list = crossings.get_crossings_quadratic(g, pos)
        if len(crossing_list) > 0:
            first_crossing = crossing_list[0]
            return (
                first_crossing.involved_edges.pop(),
                first_crossing.involved_edges.pop(),
                0.0,
            )

    # TODO implement sweep line approach
    for edge in g.edges():
        for node in g.nodes():
            if node in edge:
                continue

            distance = _edge_node_distance(edge, node, pos)

            if distance < min_distance:
                element_a, element_b, min_distance = node, edge, distance

    return element_a, element_b, min_distance


def node_orthogonality(
    g: nx.Graph,
    pos: Union[dict, list, None] = None,
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
    :type pos: Union[str, dic, None]
    :param width: Total number of horizontal grid cells. If not supplied, a minimal integer grid fitting g is assumed.
    :type width: int
    :param height: Total number of vertical grid cells. If not supplied, a minimal integer grid fitting g is assumed.
    :type height: int
    :return: A metric of node orthogonality between 0 and 1
    :rtype: float
    """

    pos = common.get_node_positions(g, pos)

    if width is None:
        width = math.ceil(boundary.width(g, pos)) + 1
    if height is None:
        height = math.ceil(boundary.height(g, pos)) + 1

    return g.order() / (width * height)


def gabriel_ratio(g: nx.Graph, pos: Union[str, dict, None] = None) -> float:
    """
    The Gabriel ratio is the ratio of all number of nodes falling within a minimum circle covering an edge for any edge.

    This measure was first defined by :footcite:t:`purchase_landscape`.

    :param g: A networkX graph
    :type g: nx.Graph
    :param pos: Optional node position dictionary. If not supplied, node positions are read from the graph directly.
        If given as a string, the property under the given name in the networkX graph is used.
    :type pos: Union[str, dic, None]
    :return: The Gabriel ratio between 0 and 1
    :rtype: float
    """

    def _within_circle(v, e):
        a_pos, b_pos = Vector.from_point(pos[e[0]]), Vector.from_point(pos[e[1]])
        n_pos = Vector.from_point(pos[v])

        mid_point = a_pos.mid(b_pos)

        edge_radius = mid_point.distance(a_pos)
        mid_distance = mid_point.distance(n_pos)

        return mid_distance < edge_radius

    pos = common.get_node_positions(g, pos)

    max_estimate = (g.order() - 2) * (len(g.edges()))
    if max_estimate <= 0:
        return 1

    violations = 0

    for node in g.nodes():
        for edge in g.edges():
            if node in edge:
                continue

            if _within_circle(node, edge):
                if g.has_edge(node, edge[0]):
                    max_estimate -= 1
                if g.has_edge(node, edge[1]):
                    max_estimate -= 1
                violations += 1

    if max_estimate <= 0:
        return 1

    return 1 - (violations / max_estimate)


def _smallest_enclosing_circle_iteratively(
    points: List[common.Vector],
) -> common.Circle:
    class _SecStages(Enum):
        """Stages between all recursive calls"""

        FIRST_CALL = 0
        SECOND_CALL = 1
        TRAIL = 2

    stack = [(_SecStages.FIRST_CALL, None)]
    results = []
    point_boundary = []

    while len(stack) > 0:
        stage, point = stack.pop()

        if stage == _SecStages.FIRST_CALL:
            if len(points) == 0 or len(point_boundary) == 3:
                # Trivial cases
                if len(point_boundary) == 0:
                    circle = common.Vector(0, 0), 0
                elif len(point_boundary) == 1:
                    circle = point_boundary[0], 0
                elif len(point_boundary) == 2:
                    circle = common.circle_from_two_points(
                        point_boundary[0], point_boundary[1]
                    )
                elif len(point_boundary) == 3:
                    circle = common.circle_from_three_points(
                        point_boundary[0], point_boundary[1], point_boundary[2]
                    )
                else:
                    raise ValueError()
                results.append(circle)
            else:
                point = points.pop()
                stack.append((_SecStages.SECOND_CALL, point))
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
            result = results.pop()
            point_boundary.pop()
            points.append(point)
            results.append(result)

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


def smallest_enclosing_circle(
    g: nx.Graph, pos: Union[str, dict, None] = None
) -> common.Circle:
    """
    Implementation of Welzl's algorithm to find the smallest enclosing circle of a graph.

    :param g: A networkX graph
    :type g: nx.Graph
    :param pos: Optional node position dictionary. If not supplied, node positions are read from the graph directly.
        If given as a string, the property under the given name in the networkX graph is used.
    :type pos: Union[str, dic, None]
    :return: The centre and radius of the smallest circle containing all nodes in g.
    :rtype:  gdMetriX.Circle
    """
    pos = common.get_node_positions(g, pos)
    return smallest_enclosing_circle_from_point_set(pos.values())
