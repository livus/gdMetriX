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


from typing import Union

import shapely

from gdMetriX.utils import numeric
from shapely.geometry.linestring import LineString

from gdMetriX.utils.sweep_line import CrossingPoint, CrossingLine, SweepLineEdgeInfo


def check_lines(
    line_a: SweepLineEdgeInfo, line_b: SweepLineEdgeInfo
) -> Union[CrossingPoint, CrossingLine, None]:
    """
    Checks if the two given line segments intersect. If so, the intersection point/line segment is returned.
    Otherwise, None is returned.
    :param line_a: First line segment
    :type line_a: SweepLineEdgeInfo
    :param line_b: Second line segment
    :type line_b: SweepLineEdgeInfo
    :return: Intersection of the two line segments
    :rtype: Union[CrossingPoint, CrossingLine, None]
    """
    # TODO Replace with custom implementation without shapely in the future
    if line_a is None or line_b is None:
        return None

    line1 = LineString((line_a.start_position, line_a.end_position))
    line2 = LineString((line_b.start_position, line_b.end_position))

    crossing_point = line1.intersection(line2)

    if not crossing_point.is_empty:
        if isinstance(crossing_point, LineString):
            return CrossingLine(
                CrossingPoint(crossing_point.coords[0][0], crossing_point.coords[0][1]),
                CrossingPoint(crossing_point.coords[1][0], crossing_point.coords[1][1]),
            )
        if isinstance(
            crossing_point, shapely.geometry.Point
        ) and not line_a.share_endpoint(line_b):
            return CrossingPoint(crossing_point.x, crossing_point.y)
    else:
        # Check if an endpoint lies on another edge
        potential_crossing_a = check_point_and_line(line_a.start_position, line_b)
        potential_crossing_b = check_point_and_line(line_a.end_position, line_b)
        potential_crossing_c = check_point_and_line(line_b.start_position, line_a)
        potential_crossing_d = check_point_and_line(line_b.end_position, line_a)

        if potential_crossing_a is not None:
            return potential_crossing_a
        if potential_crossing_b is not None:
            return potential_crossing_b
        if potential_crossing_c is not None:
            return potential_crossing_c
        if potential_crossing_d is not None:
            return potential_crossing_d

    return None


def check_point_and_line(
    point: CrossingPoint, line: SweepLineEdgeInfo
) -> Union[CrossingPoint, None]:
    """
    Checks if the given line segment and point intersect. If so, the intersection point is returned.
    Otherwise, None is returned.
    :param point: Point to check for intersection
    :type point: CrossingPoint
    :param line: Line segment to check for intersection
    :type line: SweepLineEdgeInfo
    :return: Possible intersection point
    :rtype: Union[CrossingPoint, None]
    """
    line_seg = CrossingLine(line.start_position, line.end_position)

    if numeric.numeric_eq(line_seg.distance_to_point(point), 0.0):
        return CrossingPoint(point.x, point.y)
    return None
