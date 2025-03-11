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

This module collects metrics concerning the orientation of edges.

Methods
-------

"""

import math
from typing import Union, Tuple, Optional, List

import networkx as nx
import numpy as np

import gdMetriX.utils.edge_orientations
from gdMetriX import common
from gdMetriX.common import Numeric, Vector, Angle
from gdMetriX.utils.edge_orientations import order_clockwise


def upwards_flow(
    g: nx.DiGraph,
    pos: Union[str, dict, None] = None,
    direction_vector: Tuple[Numeric, Numeric] = (0, 1),
) -> Optional[float]:
    """
    Calculates the percentage of edges pointing in the 'upwards' direction.
    An edge points 'upwards' if the angle between the upwards vector and the edge is smaller than 90 degrees.

    The measure was first defined by :footcite:t:`purchase_metrics_2002`.

    :param g: A networkX graph
    :type g: nx.Graph
    :param pos: Optional node position dictionary. If not supplied, node positions are read from the graph directly.
        If given as a string, the property under the given name in the networkX graph is used.
    :type pos: Union[str, dic, None]
    :param direction_vector: Defines the direction of 'upwards'
    :type direction_vector: Tuple[numeric, numeric]
    :return: Percentage of edges pointing 'upwards'
    :rtype: Optional[float]
    """
    if g is None or not nx.is_directed(g) or len(g.edges()) == 0:
        return 0

    if direction_vector == (0, 0):
        return None

    pos = common.get_node_positions(g, pos)

    sum_upward_edges = 0

    for edge in g.edges():
        e_vector = np.subtract(pos[edge[1]], pos[edge[0]])
        inner_product = np.inner(e_vector, direction_vector)

        if inner_product > 0:
            sum_upward_edges += 1

    return float(sum_upward_edges) / len(g.edges())


def average_flow(
    g: nx.DiGraph, pos: Union[str, dict, None] = None
) -> Optional[Tuple[float, float]]:
    """
    Calculates the average edge direction as defined by :footcite:t:`purchase_metrics_2002`.

    :param g: A networkX graph
    :type g: nx.Graph
    :param pos: Optional node position dictionary. If not supplied, node positions are read from the graph directly.
        If given as a string, the property under the given name in the networkX graph is used.
    :type pos: Union[str, dic, None]
    :return: The average edge direction, as a normalized vector.
    :rtype: Optional[Tuple[float, float]]
    """
    if g is None or not nx.is_directed(g) or len(g.edges()) == 0:
        return None

    pos = common.get_node_positions(g, pos)
    sum_vector = np.array([0.0, 0.0])

    for edge in g.edges():
        e_vector = np.subtract(pos[edge[1]], pos[edge[0]])
        length = np.linalg.norm(e_vector)
        if length != 0:
            sum_vector += e_vector / length

    sum_length = np.linalg.norm(sum_vector)
    if sum_length != 0:
        average = sum_vector / sum_length
    else:
        average = sum_vector

    np.nan_to_num(average, False, 0)
    return float(average[0]), float(average[1])


def coherence_to_average_flow(
    g: nx.DiGraph, pos: Union[str, dict, None] = None
) -> Optional[float]:
    """
    Calculates the upwards flow along the average edge direction.
    This is equal to calling :func:`upwards_flow(g, average_flow(g))`.

    :param g: A networkX graph
    :type g: nx.Graph
    :param pos: Optional node position dictionary. If not supplied, node positions are read from the graph directly.
        If given as a string, the property under the given name in the networkX graph is used.
    :type pos: Union[str, dic, None]
    :return: The coherence to the average flow
    :rtype: Optional[float]
    """
    return upwards_flow(g, pos, average_flow(g, pos))


def ordered_neighborhood(
    g: nx.Graph, node: object, pos: Union[str, dict, None] = None
) -> List:
    """
    Returns the neighborhood of the given node in the networkX graph ordered clockwise.

    :param g: A networkX graph
    :type g: nx.Graph
    :param node: A node key present in the given networkX graph
    :type node: object
    :param pos: Optional node position dictionary. If not supplied, node positions are read from the graph directly.
        If given as a string, the property under the given name in the networkX graph is used.
    :type pos: Union[str, dic, None]
    :return: List of neighbors of 'node' ordered clockwise
    :rtype: List
    """
    pos = common.get_node_positions(g, pos)

    neighbors = [edge[0] if edge[0] != node else edge[1] for edge in g.edges(node)]
    neighbors = list(filter(lambda nb: nb != node, neighbors))
    return order_clockwise(neighbors, pos[node], pos)


def combinatorial_embedding(g: nx.Graph, pos: Union[str, dict, None] = None) -> dict:
    """
    Returns the combinatorial embedding for the given networkX graph g.

    :param g: A networkX graph
    :type g: nx.Graph
    :param pos: Optional node position dictionary. If not supplied, node positions are read from the graph directly.
        If given as a string, the property under the given name in the networkX graph is used.
    :type pos: Union[str, dic, None]
    :return: The new node positions
    :rtype: dict
    """
    pos = common.get_node_positions(g, pos)
    return {node: ordered_neighborhood(g, node, pos) for node in g.nodes()}


def edge_angles(
    g: nx.Graph, node: object, pos: Union[str, dict, None] = None, deg: bool = False
) -> List:
    """
    Returns a list of edge angles for the given node present in the networkX graph.

    :param g: A networkX graph
    :type g: nx.Graph
    :param node: A node key present in the given networkX graph
    :type node: object
    :param pos: Optional node position dictionary. If not supplied, node positions are read from the graph directly.
        If given as a string, the property under the given name in the networkX graph is used.
    :type pos: Union[str, dic, None]
    :param deg: If true, the angles are returned as degrees in the range of (0,360). Otherwise, the angles are returned
        as radians.
    :type deg: bool
    :return: List of angles between the edges in a clockwise order
    :rtype: List
    """
    pos = common.get_node_positions(g, pos)
    neighbors = ordered_neighborhood(g, node, pos)

    return gdMetriX.utils.edge_orientations.edge_angles(neighbors, pos[node], pos, deg)


def minimum_angle(
    g: nx.Graph, pos: Union[str, dict, None] = None, deg: bool = False
) -> float:
    """
    Returns the shallowest angle between any two edges sharing an endpoint.

    :param g: A networkX graph
    :type g: nx.Graph
    :param pos: Optional node position dictionary. If not supplied, node positions are read from the graph directly.
        If given as a string, the property under the given name in the networkX graph is used.
    :type pos: Union[str, dic, None]
    :param deg: If true, the angles are returned as degrees in the range of (0,360). Otherwise, the angles are returned
        as radians.
    :type deg: bool
     :return: Minimum angle between two adjacent edges
    :rtype: float
    """
    pos = common.get_node_positions(g, pos)

    minimum = 360 if deg else math.pi * 2

    for node in g.nodes():
        resolution = min(edge_angles(g, node, pos, deg))
        minimum = min(minimum, resolution)

    return minimum


def angular_resolution(
    g: nx.Graph, pos: Union[str, dict, None] = None, deg: bool = False
) -> float:
    r"""
    Returns the deviation from the optimal angle between any two edges sharing an endpoint as defined by
    :footcite:t:`purchase_metrics_2002`.

    More precisely, the deviation from the optimal angle is defined as
    :math:`\sum \lvert \frac{o_i - \theta_i}{o_i}\rvert`, where :math:`o_i` is the optimal angle
    :math:`\frac{360^\circ}{\text{deg}(i)}` of a vertex :math:`i` and :math:`\theta_i` the actual minimal
    angle formed by edges at :math:`i`.

    :param g: A networkX graph
    :type g: nx.Graph
    :param pos: Optional node position dictionary. If not supplied, node positions are read from the graph directly.
        If given as a string, the property under the given name in the networkX graph is used.
    :type pos: Union[str, dic, None]
    :param deg: If true, the angles are returned as degrees in the range of (0,360). Otherwise, the angles are returned
        as radians.
    :type deg: bool
    :return: Angular resolution between 0 and 1
    :rtype: float
    """

    pos = common.get_node_positions(g, pos)

    node_count = 0
    deviation_sum = 0

    for node in g.nodes():
        neighbours = sum(1 for _ in g.neighbors(node))

        if neighbours <= 1:
            continue

        node_count += 1

        optimal_angle = Angle(2 * math.pi) / neighbours
        min_angle = Angle(min(edge_angles(g, node, pos, deg)))

        deviation_sum += abs(((optimal_angle - min_angle) / optimal_angle))

    return deviation_sum / node_count if node_count > 0 else 0


def edge_orthogonality(g: nx.Graph, pos: Union[str, dict, None] = None) -> float:
    """
    Returns the extend to which edges are vertical or horizontal.

    The measure was first defined by :footcite:t:`purchase_metrics_2002`.

    :param g: A networkX graph
    :type g: nx.Graph
    :param pos: Optional node position dictionary. If not supplied, node positions are read from the graph directly.
        If given as a string, the property under the given name in the networkX graph is used.
    :type pos: Union[str, dic, None]
     :return: Edge orthogonality between 0 and 1
    :rtype: float
    """

    pos = common.get_node_positions(g, pos)

    total = 0
    for edge in g.edges():
        v_edge = Vector.from_point(pos[edge[1]]) - Vector.from_point(pos[edge[0]])
        angle = v_edge.angle(Vector(1, 0))
        degree_deviation = angle % (math.pi / 2)
        degree_deviation = min(degree_deviation, math.pi / 2 - degree_deviation)
        total += degree_deviation * 4 / math.pi

    return 1 - (total / len(g.edges()))


def edge_length_deviation(
    g: nx.Graph, pos: Union[str, dict, None] = None, ideal_length: float = None
) -> float:
    """
    Calculates the average edge length deviation as defined by :footcite:t:`purchase_landscape`.

    :param g: A networkX graph
    :type g: nx.Graph
    :param pos: Optional node position dictionary. If not supplied, node positions are read from the graph directly.
        If given as a string, the property under the given name in the networkX graph is used.
    :type pos: Union[str, dic, None]
    :param ideal_length: The ideal length an edge should have. If not supplied, the average edge length is assumed to be
        the ideal edge length.
    :type ideal_length: float
    :return: Edge length deviation between 0 and 1
    :rtype: float
    """

    if g.number_of_edges() < 1:
        return 0

    pos = common.get_node_positions(g, pos)

    edge_lengths = [
        common.euclidean_distance(pos[edge[0]], pos[edge[1]]) for edge in g.edges()
    ]
    average = ideal_length if ideal_length is not None else np.average(edge_lengths)
    return np.average(
        [abs(average - edge_length) / average for edge_length in edge_lengths]
    )
