# gdMetriX
#
# Copyright (C) 2025  Martin Nöllenburg, Sebastian Röder, Markus Wallinger
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
Collects helper functions for obtaining different values in relation the the orientation of edges.
"""

import math
from typing import List, Tuple, Union

from gdMetriX.common import Numeric, Vector, Angle


def order_clockwise(
    nodes: List, origin: Tuple[Numeric, Numeric], pos: Union[str, dict, None]
) -> List:
    """
    Returns the list of nodes in clockwise order from the perspective of the given origin.
    :param nodes: List of nodes to be sorted
    :type nodes: List
    :param origin: Viewpoint for defining the clockwise order
    :type origin: Tuple[Numeric, Numeric]
    :param pos: Dictionary of all node positions
    :type pos: Union[str, dict, None]
    :return: Sorted list of nodes
    :rtype: List
    """
    def _get_angle_between_nodes(pos_a, pos_b) -> float:
        vector = Vector.from_point(pos_b) - Vector.from_point(pos_a)
        return Vector(0, 1).angle(vector)

    return sorted(nodes, key=lambda nb: _get_angle_between_nodes(origin, pos[nb]))


def edge_angles(
    nodes: List,
    origin: Tuple[Numeric, Numeric],
    pos: Union[str, dict, None],
    deg: bool = False,
) -> List:
    """
    Returns a list of all angles between the given set of edges in clockwise order.
    All edges are assumed to start at the given origin and go to the nodes in the node list.
    :param nodes: List of nodes which define the endpoint of the edges
    :type nodes: List
    :param origin: Start point of all edges
    :type origin: Tuple[Numeric, Numeric]
    :param pos: Dictionary of node positions
    :type pos: Union[str, dict, None]
    :param deg: If true, the angles are returned as degrees in the range of (0,360). Otherwise, the angles are returned
        as radians.
    :type deg: bool
    :return:
    :rtype:
    """
    ordered_nodes = order_clockwise(nodes, origin, pos)

    angles = []
    origin = Vector.from_point(origin)

    if len(ordered_nodes) <= 1:
        angles.append(Angle(math.pi * 2))
    else:
        for i, node in enumerate(ordered_nodes):
            p_nb_a = Vector.from_point(pos[node])
            p_nb_b = Vector.from_point(pos[ordered_nodes[(i + 1) % len(ordered_nodes)]])
            vector_nb_a = p_nb_a - origin
            vector_nb_b = p_nb_b - origin
            angle = vector_nb_a.angle(vector_nb_b)
            angles.append(angle)

    return [angle.deg() if deg else angle.rad() for angle in angles]
