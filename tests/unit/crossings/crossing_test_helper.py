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
Contains a couple of helper function for testing the crossing detection
"""

import inspect
import math

import matplotlib.pyplot as plt
import networkx as nx

import gdMetriX.common
from gdMetriX import crossings


def _rotate_point(point, angle):
    if isinstance(point, crossings.CrossingLine):
        return crossings.CrossingLine(
            _rotate_point(point.start, angle),
            _rotate_point(point.end, angle),
        )
    if isinstance(point, crossings.CrossingPoint):
        return crossings.CrossingPoint(
            _rotate_point((point.x, point.y), angle)[0],
            _rotate_point((point.x, point.y), angle)[1],
        )
    rad = math.radians(angle % 360)
    return (
        point[0] * math.cos(rad) - point[1] * math.sin(rad),
        point[0] * math.sin(rad) + point[1] * math.cos(rad),
    )


def _rotate_graph(g, angle):
    for node, position in nx.get_node_attributes(g, "pos").items():
        g.nodes[node]["pos"] = _rotate_point(position, angle)


def _rotate_crossings(crossing_list, angle):
    return [
        crossings.Crossing(_rotate_point(crossing.pos, angle), crossing.involved_edges)
        for crossing in crossing_list
    ]


def _draw_graph(g: nx.Graph, title: str, crossings_a, crossings_b):
    ax = plt.gca()
    ax.set_title(title)

    pos = gdMetriX.common.get_node_positions(g)

    nx.draw_networkx_edges(g, pos, ax=ax)
    nx.draw_networkx_nodes(g, pos, ax=ax, node_size=20)
    ax.tick_params(left=True, bottom=True, labelleft=True, labelbottom=True)
    plt.axis("on")

    # Points
    points_a = list(
        filter(
            lambda cr: type(cr.pos)
            is gdMetriX.crossings.crossing_data_types.CrossingPoint,
            crossings_a,
        )
    )
    points_b = list(
        filter(
            lambda cr: type(cr.pos)
            is gdMetriX.crossings.crossing_data_types.CrossingPoint,
            crossings_b,
        )
    )

    x_values = [point.pos[0] for point in points_a]
    y_values = [point.pos[1] for point in points_a]
    plt.plot(x_values, y_values, "rX", markersize=12)

    x_values = [point.pos[0] for point in points_b]
    y_values = [point.pos[1] for point in points_b]
    plt.plot(x_values, y_values, "gX", markersize=9)

    plt.show()


def _equal_crossings(crossings_a, crossings_b, g, title):
    crossings_a_sorted = sorted(crossings_a)
    crossings_b_sorted = sorted(crossings_b)
    print("Expected {}".format(crossings_b_sorted))
    print("Actual   {}".format(crossings_a_sorted))

    if crossings_a_sorted != crossings_b_sorted:
        _draw_graph(g, title, crossings_a, crossings_b)

    assert crossings_a_sorted == crossings_b_sorted


def assert_crossing_equality(
    g,
    crossing_list,
    crossing_function,
    include_rotation: bool = False,
    include_node_crossings: bool = False,
    title=None,
):
    """

    :param g:
    :type g:
    :param crossing_list:
    :type crossing_list:
    :param crossing_function:
    :type crossing_function:
    :param include_rotation:
    :type include_rotation:
    :param include_node_crossings:
    :type include_node_crossings:
    """
    if title is None:
        title = inspect.getouterframes(inspect.currentframe(), 2)[1][3]
    _equal_crossings(
        crossing_function(g, include_node_crossings=include_node_crossings),
        crossing_list,
        g,
        title,
    )
    angle_resolution = 10
    if include_rotation:
        for i in range(0, int(360 / angle_resolution)):
            _rotate_graph(g, angle_resolution)
            crossing_list = _rotate_crossings(crossing_list, 10)
            print(nx.get_node_attributes(g, "pos"))
            _equal_crossings(
                crossing_function(g, include_node_crossings=include_node_crossings),
                crossing_list,
                g,
                title,
            )
