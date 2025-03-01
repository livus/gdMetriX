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
This module provides some basic functionality for obtaining the bounding box and aspect ratio of an embedded graph.

Usage
-----

To obtain the aspect ratio of an embedded graph simply call :func:`aspect_ratio()`:

.. code-block:: python

    >>> g = nx.random_geometric_graph(20, 0.5)
    >>> crossing_list = aspect_ratio(g)

To scale the graph into a defined rectangle, call :func:`normalize_positions()`:

.. code-block:: python

    >>> pos = normalize_positions(g, box=(0,0,1,1))
    >>> nx.set_node_attributes(g, pos)

This preserves the original aspect ratio of the graph. To deform the graph to fit the bounding box perfectly call
:func:`normalize_positions()` with :code:`preserve_aspect_ratio = False`:


.. code-block:: python

    >>> pos = normalize_positions(g, box=(0,0,1,1), preserve_aspect_ratio = False)

Methods
-------

"""

from typing import Union, Tuple, Optional

import networkx as nx
import scipy.spatial
from scipy.spatial import ConvexHull

from gdMetriX import common
from gdMetriX.common import Numeric


def area(g: nx.Graph, pos: Union[str, dict, None] = None) -> float:
    """
    Calculates the area of the smallest axis-aligned bounding box containing all nodes.

    :param g: A networkX graph
    :type g: nx.Graph
    :param pos: Optional node position dictionary. If not supplied, node positions are read from the graph directly.
        If given as a string, the property under the given name in the networkX graph is used.
    :type pos: Union[str, dic, None]
    :return: Area of the bounding box of g
    :rtype: float
    """
    return height(g, pos) * width(g, pos)


def area_tight(g: nx.Graph, pos: Union[str, dict, None] = None) -> float:
    """
    Returns the area of the convex hull of the given networkx graph g.

    :param g: A networkX graph
    :type g: nx.Graph
    :param pos: Optional node position dictionary. If not supplied, node positions are read from the graph directly.
        If given as a string, the property under the given name in the networkX graph is used.
    :type pos: Union[str, dic, None]
    :return: Area of the convex hull of g
    :rtype: float
    """
    pos = common.get_node_positions(g, pos)

    if len(pos) <= 1:
        return 0.0

    try:
        ch = ConvexHull(list(pos.values()))
        return ch.volume
    except scipy.spatial.QhullError:
        return 0.0


def bounding_box(
    g: nx.Graph, pos: Union[str, dict, None] = None
) -> Optional[Tuple[Numeric, Numeric, Numeric, Numeric]]:
    """
    Returns the tight bounding box around the given graph.

    :param g: A networkX graph
    :type g: nx.Graph
    :param pos: Optional node position dictionary. If not supplied, node positions are read from the graph directly.
                If given as a string, the property under the given name in the networkX graph is used.
    :type pos: Union[str, dic, None]
    :return: Bounding box in the form (min_x, min_y, max_x, max_y)
    :rtype: Optional[Tuple[numeric, numeric, numeric, numeric]]
    """
    if g.order() == 0:
        return None

    pos = common.get_node_positions(g, pos)

    min_x, max_x, min_y, max_y = (None, None, None, None)

    for node in g.nodes():
        node_pos = pos[node]

        if min_x is None or node_pos[0] < min_x:
            min_x = node_pos[0]
        if max_x is None or node_pos[0] > max_x:
            max_x = node_pos[0]
        if min_y is None or node_pos[1] < min_y:
            min_y = node_pos[1]
        if max_y is None or node_pos[1] > max_y:
            max_y = node_pos[1]

    return min_x, min_y, max_x, max_y


def height(g: nx.Graph, pos: Union[str, dict, None] = None) -> Numeric:
    """
    Returns the height of the graph, which is defined as the vertical distance between the lowest and the highest node.

    :param g: A networkX graph
    :type g: nx.Graph
    :param pos: Optional node position dictionary. If not supplied, node positions are read from the graph directly.
        If given as a string, the property under the given name in the networkX graph is used.
    :type pos: Union[str, dic, None]
    :return: The height of the graph
    :rtype: numeric
    """
    if g.order() == 0:
        return 0
    (_, min_y, _, max_y) = bounding_box(g, pos)
    return max_y - min_y


def width(g: nx.Graph, pos: Union[str, dict, None] = None) -> Numeric:
    """
    Returns the width of the graph, which is defined as the horizontal distance between the left-most and the right-most
    node.

    :param g: A networkX graph
    :type g: nx.Graph
    :param pos: Optional node position dictionary. If not supplied, node positions are read from the graph directly.
        If given as a string, the property under the given name in the networkX graph is used.
    :type pos: Union[str, dic, None]
    :return: The width of the graph
    :rtype: numeric
    """
    if g.order() == 0:
        return 0
    (min_x, _, max_x, _) = bounding_box(g, pos)
    return max_x - min_x


def aspect_ratio(g: nx.Graph, pos: Union[str, dict, None] = None) -> Optional[float]:
    """
    Calculates the aspect ratio of the given graph. The aspect ratio is defined as the ratio of the bigger side over the
    smaller side.

    :param g: A networkX graph
    :type g: nx.Graph
    :param pos: Optional node position dictionary. If not supplied, node positions are read from the graph directly.
        If given as a string, the property under the given name in the networkX graph is used.
    :type pos: Union[str, dic, None]
    :return: The aspect ratio of the graph (None in case the graph is empty).
    :rtype: Optional[float]
    """
    if g.order() == 0:
        return None

    h, w = height(g, pos), width(g, pos)

    bigger = max(h, w)
    smaller = min(h, w)

    if bigger == 0 and smaller == 0:
        return 1

    return smaller / bigger


def normalize_positions(
    g: nx.Graph,
    pos: Union[str, dict, None] = None,
    box: Tuple[Numeric, Numeric, Numeric, Numeric] = (-0.5, -0.5, 0.5, 0.5),
    preserve_aspect_ratio: bool = True,
) -> dict:
    """
    Normalizes the positions of the graph to fit within a given bounding box.

    :param g: A networkX graph
    :type g: nx.Graph
    :param pos: Optional node position dictionary. If not supplied, node positions are read from the graph directly.
        If given as a string, the property under the given name in the networkX graph is used.
    :type pos: Union[str, dic, None]
    :param box: The bounding box b = (min_x, min_y, max_x, max_y) to fit the graph into. By default, the bounding box is
        equal to (-0.5, -0.5, 0.5, 0.5)
    :type box: Tuple[numeric, numeric, numeric, numeric]
    :param preserve_aspect_ratio: Whether or not to preserve the aspect ratio. If false, the graph is distorted to fill
        the bounding box exactly.
    :type preserve_aspect_ratio: bool
    :return: The new node positions
    :rtype: dict
    """
    pos = common.get_node_positions(g, pos).copy()

    if pos is None or len(pos) == 0:
        return {}

    (min_x, min_y, max_x, max_y) = bounding_box(g, pos)
    h = max_y - min_y
    w = max_x - min_x

    box_height = max(box[1], box[3]) - min(box[1], box[3])
    box_width = max(box[0], box[2]) - min(box[0], box[2])

    if preserve_aspect_ratio:
        if w == 0 or box_width == 0 or h == 0 or box_height == 0:
            target_width = 0 if w == 0 or box_width == 0 else box_width
            target_height = 0 if h == 0 or box_height == 0 else box_height
        else:
            if w / h <= (box_width / box_height):
                target_height = box_height
                target_width = w * (target_height / h)
            else:
                target_width = box_width
                target_height = h * (target_width / w)

        start_x = box[0] + (box_width - target_width) / 2
        start_y = box[1] + (box_height - target_height) / 2

    else:
        target_height = box_height
        target_width = box_width
        start_x = box[0]
        start_y = box[1]

    for key, value in pos.items():
        x, y = value

        percentage_x = 0.5 if w == 0 else (x - min_x) / w
        percentage_y = 0.5 if h == 0 else (y - min_y) / h

        pos[key] = (
            start_x + percentage_x * target_width,
            start_y + percentage_y * target_height,
        )

    return pos
