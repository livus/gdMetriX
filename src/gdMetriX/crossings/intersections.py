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

from gdMetriX.common import segment_distance_squared
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

    # If two edges share a node, they are not considered to be crossing - unless one of them has
    # no length. Only an overlap can then still be reported, so there is no point in computing
    # where they meet.
    adjacent = (
        line_a.share_endpoint(line_b)
        and not _is_zero_length(line_a)
        and not _is_zero_length(line_b)
    )

    result = _intersect(line_a, line_b, adjacent)

    if adjacent and isinstance(result, CrossingPoint):
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
    line_a: SweepLineEdgeInfo, line_b: SweepLineEdgeInfo, overlap_only: bool = False
) -> Union[CrossingPoint, CrossingLine, None]:
    """
    Intersects the two segments. With overlap_only, a result that could only be a single point is
    not computed - None is returned in its place - as the caller discards it anyway.
    """
    p1, p2 = line_a.start_position, line_a.end_position
    p3, p4 = line_b.start_position, line_b.end_position
    x1, y1, x2, y2 = p1.x, p1.y, p2.x, p2.y
    x3, y3, x4, y4 = p3.x, p3.y, p4.x, p4.y

    d1x = x2 - x1
    d1y = y2 - y1
    d2x = x4 - x3
    d2y = y4 - y3
    len1_sq = d1x * d1x + d1y * d1y
    len2_sq = d2x * d2x + d2y * d2y

    precision = numeric.PRECISION
    precision_sq = precision * precision

    if len1_sq == 0 or len2_sq == 0:
        if overlap_only:
            # A segment without length can only ever touch in a single point
            return None
        return _intersect_degenerate(
            x1, y1, x2, y2, len1_sq, x3, y3, x4, y4, len2_sq, precision_sq
        )

    # Decide whether the two segments are collinear within precision - i.e.
    # every point of one lies within precision of the other's infinite line -
    # using whichever segment is longer as the reference line.
    if len1_sq >= len2_sq:
        is_collinear = (
            _perpendicular_distance_squared(x3, y3, x1, y1, d1x, d1y, len1_sq)
            <= precision_sq
            and _perpendicular_distance_squared(x4, y4, x1, y1, d1x, d1y, len1_sq)
            <= precision_sq
        )
    else:
        is_collinear = (
            _perpendicular_distance_squared(x1, y1, x3, y3, d2x, d2y, len2_sq)
            <= precision_sq
            and _perpendicular_distance_squared(x2, y2, x3, y3, d2x, d2y, len2_sq)
            <= precision_sq
        )

    if is_collinear:
        return _collinear_overlap(x1, y1, d1x, d1y, len1_sq, x3, y3, x4, y4, precision)

    if overlap_only:
        return None

    return _crossing_point(
        x1, y1, x2, y2, d1x, d1y, x3, y3, x4, y4, d2x, d2y, precision_sq
    )


def _intersect_degenerate(
    x1, y1, x2, y2, len1_sq, x3, y3, x4, y4, len2_sq, precision_sq
) -> Union[CrossingPoint, None]:
    # At least one side has zero length (its "segment" is really just a
    # point) - the only possible result is a single touching point, never an
    # overlapping CrossingLine.
    if len1_sq == 0 and len2_sq == 0:
        diff_x = x1 - x3
        diff_y = y1 - y3
        distance_sq = diff_x * diff_x + diff_y * diff_y
        point_x, point_y = x1, y1
    elif len1_sq == 0:
        distance_sq = segment_distance_squared(x3, y3, x4, y4, x1, y1)
        point_x, point_y = x1, y1
    else:
        distance_sq = segment_distance_squared(x1, y1, x2, y2, x3, y3)
        point_x, point_y = x3, y3

    if distance_sq <= precision_sq:
        return CrossingPoint(point_x, point_y)
    return None


def _perpendicular_distance_squared(
    point_x, point_y, origin_x, origin_y, direction_x, direction_y, direction_len_sq
) -> float:
    """Squared distance from the point to the infinite line through the origin along the direction."""
    cross = direction_x * (point_y - origin_y) - direction_y * (point_x - origin_x)
    return (cross * cross) / direction_len_sq


def _crossing_point(
    x1, y1, x2, y2, d1x, d1y, x3, y3, x4, y4, d2x, d2y, precision_sq
) -> Union[CrossingPoint, None]:
    denom = d1x * d2y - d1y * d2x
    if denom == 0:
        # Exactly parallel - and, since _intersect already ruled out being
        # collinear within precision, genuinely offset - so no intersection
        # point exists at all.
        return None

    t = ((x3 - x1) * d2y - (y3 - y1) * d2x) / denom
    point_x = x1 + d1x * t
    point_y = y1 + d1y * t

    if (
        segment_distance_squared(x1, y1, x2, y2, point_x, point_y) <= precision_sq
        and segment_distance_squared(x3, y3, x4, y4, point_x, point_y) <= precision_sq
    ):
        return CrossingPoint(point_x, point_y)
    return None


def _collinear_overlap(
    x1, y1, d1x, d1y, len1_sq, x3, y3, x4, y4, precision
) -> Union[CrossingLine, CrossingPoint, None]:
    # Line a and line b are collinear within precision - find the overlap of
    # their extents by projecting b's endpoints onto a's direction. Working in
    # actual length units (rather than a normalized [0, 1] parameter) keeps
    # the overlap-length comparison against `precision` a plain distance
    # check, regardless of how long line a happens to be.
    length1 = math.sqrt(len1_sq)

    t3 = (d1x * (x3 - x1) + d1y * (y3 - y1)) / length1
    t4 = (d1x * (x4 - x1) + d1y * (y4 - y1)) / length1
    lo_b, hi_b = (t3, t4) if t3 <= t4 else (t4, t3)

    lo = max(0.0, lo_b)
    hi = min(length1, hi_b)
    overlap = hi - lo

    if overlap > precision:
        start = lo / length1
        end = hi / length1
        return CrossingLine(
            CrossingPoint(x1 + d1x * start, y1 + d1y * start),
            CrossingPoint(x1 + d1x * end, y1 + d1y * end),
        )

    if overlap >= -precision:
        # Touching tip-to-tip (or separated by less than precision) rather
        # than genuinely overlapping - report it as a single point.
        mid = ((lo + hi) / 2) / length1
        return CrossingPoint(x1 + d1x * mid, y1 + d1y * mid)

    return None
