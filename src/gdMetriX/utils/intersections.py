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

import math
from typing import Union

from gdMetriX.utils import numeric
from gdMetriX.utils.sweep_line import CrossingLine, CrossingPoint, SweepLineEdgeInfo


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
    if line_a is None or line_b is None:
        return None

    result = _intersect(line_a, line_b)

    if (
        isinstance(result, CrossingPoint)
        and line_a.share_endpoint(line_b)
        and not _is_zero_length(line_a)
        and not _is_zero_length(line_b)
    ):
        # If two edges share a node, they are not
        # considered to be crossing.
        return None

    return result


def _is_zero_length(line: SweepLineEdgeInfo) -> bool:
    return line.start_position == line.end_position


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
    precision = numeric.get_precision()

    if line.crossing_line.distance_squared_to_point(point) <= precision * precision:
        return CrossingPoint(point.x, point.y)
    return None


def _intersect(
    line_a: SweepLineEdgeInfo, line_b: SweepLineEdgeInfo
) -> Union[CrossingPoint, CrossingLine, None]:
    p1, p2 = line_a.start_position, line_a.end_position
    p3, p4 = line_b.start_position, line_b.end_position

    d1 = p2 - p1
    d2 = p4 - p3
    len1_sq = d1.dot(d1)
    len2_sq = d2.dot(d2)

    precision = numeric.get_precision()
    precision_sq = precision * precision

    if len1_sq == 0 or len2_sq == 0:
        return _intersect_degenerate(
            p1, len1_sq, p3, len2_sq, line_a, line_b, precision_sq
        )

    # Decide whether the two segments are collinear within precision - i.e.
    # every point of one lies within precision of the other's infinite line -
    # using whichever segment is longer as the reference line.
    if len1_sq >= len2_sq:
        is_collinear = (
            _perpendicular_distance_squared(p3, p1, d1, len1_sq) <= precision_sq
            and _perpendicular_distance_squared(p4, p1, d1, len1_sq) <= precision_sq
        )
    else:
        is_collinear = (
            _perpendicular_distance_squared(p1, p3, d2, len2_sq) <= precision_sq
            and _perpendicular_distance_squared(p2, p3, d2, len2_sq) <= precision_sq
        )

    if is_collinear:
        return _collinear_overlap(p1, d1, len1_sq, p3, p4, precision)

    return _crossing_point(p1, d1, p3, d2, line_a, line_b, precision_sq)


def _intersect_degenerate(
    p1: CrossingPoint,
    len1_sq: float,
    p3: CrossingPoint,
    len2_sq: float,
    line_a: SweepLineEdgeInfo,
    line_b: SweepLineEdgeInfo,
    precision_sq: float,
) -> Union[CrossingPoint, None]:
    # At least one side has zero length (its "segment" is really just a
    # point) - the only possible result is a single touching point, never an
    # overlapping CrossingLine.
    if len1_sq == 0 and len2_sq == 0:
        diff = p1 - p3
        distance_sq = diff.dot(diff)
        point = p1
    elif len1_sq == 0:
        distance_sq = line_b.crossing_line.distance_squared_to_point(p1)
        point = p1
    else:
        distance_sq = line_a.crossing_line.distance_squared_to_point(p3)
        point = p3

    if distance_sq <= precision_sq:
        return CrossingPoint(point.x, point.y)
    return None


def _perpendicular_distance_squared(
    point, origin, direction, direction_len_sq
) -> float:
    """Squared distance from `point` to the infinite line through `origin` along `direction`."""
    cross = direction.cross(point - origin)
    return (cross * cross) / direction_len_sq


def _crossing_point(
    p1: CrossingPoint,
    d1,
    p3: CrossingPoint,
    d2,
    line_a: SweepLineEdgeInfo,
    line_b: SweepLineEdgeInfo,
    precision_sq: float,
) -> Union[CrossingPoint, None]:
    denom = d1.cross(d2)
    if denom == 0:
        # Exactly parallel - and, since _intersect already ruled out being
        # collinear within precision, genuinely offset - so no intersection
        # point exists at all.
        return None

    t = (p3 - p1).cross(d2) / denom
    point = p1 + d1 * t

    if (
        line_a.crossing_line.distance_squared_to_point(point) <= precision_sq
        and line_b.crossing_line.distance_squared_to_point(point) <= precision_sq
    ):
        return CrossingPoint(point.x, point.y)
    return None


def _collinear_overlap(
    p1: CrossingPoint,
    d1,
    len1_sq: float,
    p3: CrossingPoint,
    p4: CrossingPoint,
    precision: float,
) -> Union[CrossingLine, CrossingPoint, None]:
    # Line a and line b are collinear within precision - find the overlap of
    # their extents by projecting b's endpoints onto a's direction. Working in
    # actual length units (rather than a normalized [0, 1] parameter) keeps
    # the overlap-length comparison against `precision` a plain distance
    # check, regardless of how long line a happens to be.
    length1 = math.sqrt(len1_sq)

    t3 = d1.dot(p3 - p1) / length1
    t4 = d1.dot(p4 - p1) / length1
    lo_b, hi_b = (t3, t4) if t3 <= t4 else (t4, t3)

    lo = max(0.0, lo_b)
    hi = min(length1, hi_b)
    overlap = hi - lo

    if overlap > precision:
        start = p1 + d1 * (lo / length1)
        end = p1 + d1 * (hi / length1)
        return CrossingLine(
            CrossingPoint(start.x, start.y), CrossingPoint(end.x, end.y)
        )

    if overlap >= -precision:
        # Touching tip-to-tip (or separated by less than precision) rather
        # than genuinely overlapping - report it as a single point.
        mid_point = p1 + d1 * (((lo + hi) / 2) / length1)
        return CrossingPoint(mid_point.x, mid_point.y)

    return None
