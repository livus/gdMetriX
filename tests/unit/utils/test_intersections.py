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
Unit tests for `gdMetriX.utils.intersections.check_lines` and `check_point_and_line`.

Both are a custom (non-shapely) implementation that is precision-aware
throughout, built on `numeric.get_precision()`: two segments that come within
precision of crossing, touching or overlapping are treated as if they did
exactly - not just when floating point happens to agree to the last bit.
"""

import contextlib
import itertools
import math

# noinspection PyUnresolvedReferences
import pytest

from gdMetriX.utils import numeric
from gdMetriX.utils.intersections import check_lines, check_point_and_line
from gdMetriX.utils.sweep_line import CrossingLine, CrossingPoint, SweepLineEdgeInfo

_edge_id_counter = itertools.count()


def _edge(point_a, point_b, edge_id=None):
    """
    Builds a SweepLineEdgeInfo for the given coordinates.

    Unless an explicit edge_id is given, a fresh, globally unique pair of node
    ids is used, so that unrelated edges never accidentally `share_endpoint()`
    just because two tests happen to reuse the same coordinates.
    """
    if edge_id is None:
        n = next(_edge_id_counter)
        edge_id = (f"n{n}a", f"n{n}b")
    return SweepLineEdgeInfo(edge_id, CrossingPoint(*point_a), CrossingPoint(*point_b))


@contextlib.contextmanager
def _precision(value):
    previous = numeric.get_precision()
    numeric.set_precision(value)
    try:
        yield
    finally:
        numeric.set_precision(previous)


def _rotate_point(point, degrees):
    """Rotates a coordinate tuple counter-clockwise around the origin."""
    rad = math.radians(degrees)
    cos_a, sin_a = math.cos(rad), math.sin(rad)
    x, y = point
    return (x * cos_a - y * sin_a, x * sin_a + y * cos_a)


def _rotated_overlap_scenario(a_points, b_points, expected_points, degrees):
    """
    Rebuilds an (a, b, expected_overlap) scenario, rotated by `degrees` around
    the origin - so the same instance can be re-checked repeatedly at many
    orientations instead of just whatever single (typically axis-aligned)
    orientation it was originally written in.

    Rotation preserves distances and angles exactly (up to floating point
    noise far smaller than the precision-scale offsets these scenarios rely
    on), so a configuration that's only "almost collinear" along the x-axis is
    still only "almost collinear" by the same margin at any other angle -
    overlap detection driven by *precision* should behave identically
    regardless of orientation, not just happen to work for axis-aligned
    inputs.
    """
    a = _edge(_rotate_point(a_points[0], degrees), _rotate_point(a_points[1], degrees))
    b = _edge(_rotate_point(b_points[0], degrees), _rotate_point(b_points[1], degrees))
    expected = CrossingLine(
        CrossingPoint(*_rotate_point(expected_points[0], degrees)),
        CrossingPoint(*_rotate_point(expected_points[1], degrees)),
    )
    return a, b, expected


# A deliberately uneven spread - includes the axis-aligned angles (0/90/180/270)
# the scenarios were originally written in, but also plenty of off-axis ones,
# so a fix that only happens to special-case horizontal/vertical lines
# wouldn't be mistaken for a real fix.
_ROTATION_ANGLES = [0, 15, 30, 45, 60, 90, 123, 180, 200, 270, 315, 350, 359]


class TestNormalCrossings:
    """Ordinary, unambiguous crossings between two non-collinear segments."""

    def test_simple_x_crossing(self):
        a = _edge((-1, 0), (1, 0))
        b = _edge((0, -1), (0, 1))

        assert check_lines(a, b) == CrossingPoint(0, 0)

    def test_crossing_away_from_origin(self):
        a = _edge((-2, 0), (4, 2))
        b = _edge((0, 3), (2, -1))

        assert check_lines(a, b) == CrossingPoint(1, 1)

    def test_crossing_is_symmetric_in_argument_order(self):
        a = _edge((-2, 0), (4, 2))
        b = _edge((0, 3), (2, -1))

        assert check_lines(a, b) == check_lines(b, a)

    def test_grazing_shallow_angle_crossing(self):
        # Line b's slope (0.0001) differs only slightly from line a's (0), so the
        # two segments cross at a very sharp/shallow angle.
        a = _edge((-10, 0), (10, 0))
        b = _edge((-10, -0.001), (10, 0.001))

        assert check_lines(a, b) == CrossingPoint(0, 0)

    @pytest.mark.parametrize("degrees", [1, 5, 15, 45, 60, 90, 120, 150, 179])
    def test_crossing_at_various_angles(self, degrees):
        rad = math.radians(degrees)
        dx, dy = math.cos(rad), math.sin(rad)

        a = _edge((-5, 0), (5, 0))
        # Constructed as exact opposites of each other, so the segment passes
        # through the origin exactly even with floating point cos/sin.
        b = _edge((-5 * dx, -5 * dy), (5 * dx, 5 * dy))

        assert check_lines(a, b) == CrossingPoint(0, 0)


class TestEndpointOnEdgeInterior:
    """'T'-shaped intersections: one segment's endpoint lands on the interior of the other."""

    @pytest.mark.parametrize("fraction", [0.1, 0.3, 0.5, 0.7, 0.9])
    def test_endpoint_lands_on_interior(self, fraction):
        a = _edge((0, 0), (10, 0))
        touch_point = (10 * fraction, 0)
        b = _edge(touch_point, (touch_point[0], 5))

        assert check_lines(a, b) == CrossingPoint(*touch_point)

    def test_point_on_the_extension_beyond_the_segment_is_not_a_crossing(self):
        a = _edge((0, 0), (10, 0))
        # (15, 0) lies on a's infinite line, but past its actual extent.
        b = _edge((15, 0), (15, 5))

        assert check_lines(a, b) is None

    def test_both_endpoints_touching_each_others_interior(self):
        # Two segments that cross each other's interior in the middle of both -
        # contrast with the T-shape above where only one endpoint touches.
        a = _edge((-5, 0), (5, 0))
        b = _edge((0, -5), (0, 5))

        result = check_lines(a, b)

        assert isinstance(result, CrossingPoint)
        assert result == CrossingPoint(0, 0)


class TestSharedEndpoints:
    """Edges that meet exactly at a vertex should not be reported as crossing/touching."""

    def test_adjacent_edges_sharing_a_node_are_not_reported(self):
        a = _edge((0, 0), (5, 5), edge_id=(1, 2))
        b = _edge((5, 5), (10, 0), edge_id=(2, 3))

        assert check_lines(a, b) is None

    def test_collinear_edges_sharing_a_node_tip_to_tip_are_not_reported(self):
        a = _edge((0, 0), (5, 0), edge_id=(1, 2))
        b = _edge((5, 0), (10, 0), edge_id=(2, 3))

        assert check_lines(a, b) is None

    def test_coincident_position_without_a_shared_node_is_reported(self):
        # Same physical location, but the two edges don't actually reference a
        # common node id - share_endpoint() is identity-based, not position-based.
        a = _edge((0, 0), (5, 5))
        b = _edge((5, 5), (10, 0))

        assert check_lines(a, b) == CrossingPoint(5, 5)

    def test_collinear_tip_to_tip_without_a_shared_node_is_reported(self):
        a = _edge((0, 0), (5, 0))
        b = _edge((5, 0), (10, 0))

        assert check_lines(a, b) == CrossingPoint(5, 0)


class TestZeroLengthEdges:
    """Degenerate edges whose start and end coincide."""

    def test_zero_length_edge_on_interior_of_another_edge(self):
        a = _edge((0, 0), (10, 0))
        b = _edge((5, 0), (5, 0))

        assert check_lines(a, b) == CrossingPoint(5, 0)

    def test_zero_length_edge_off_the_line_is_not_reported(self):
        a = _edge((0, 0), (10, 0))
        b = _edge((5, 1), (5, 1))

        assert check_lines(a, b) is None

    def test_two_coincident_zero_length_edges_without_shared_node(self):
        a = _edge((5, 5), (5, 5))
        b = _edge((5, 5), (5, 5))

        assert check_lines(a, b) == CrossingPoint(5, 5)

    def test_two_coincident_zero_length_edges_sharing_a_node_is_still_reported(self):
        # Unlike two *ordinary* (non-zero-length) edges sharing a node - which
        # is just normal graph adjacency and never a crossing - a zero-length
        # edge stands in for a node-like point rather than a real edge.
        # share_endpoint() is deliberately not applied here: whether this
        # counts as a crossing is the include_node_crossings/prune()
        # machinery's call to make (see crossing_data_types.Crossing.prune,
        # which keeps exactly this case), not check_lines'.
        a = _edge((5, 5), (5, 5), edge_id=(1, 2))
        b = _edge((5, 5), (5, 5), edge_id=(2, 3))

        assert check_lines(a, b) == CrossingPoint(5, 5)

    def test_zero_length_edge_sharing_a_node_with_a_normal_edge_is_still_reported(self):
        a = _edge((5, 5), (5, 5), edge_id=(1, 2))
        b = _edge((5, 5), (10, 0), edge_id=(2, 3))

        assert check_lines(a, b) == CrossingPoint(5, 5)


class TestNoCrossing:
    """Segments that genuinely do not interact at all."""

    def test_disjoint_segments_far_apart(self):
        a = _edge((0, 0), (1, 1))
        b = _edge((100, 100), (101, 101))

        assert check_lines(a, b) is None

    def test_parallel_non_collinear_segments(self):
        a = _edge((0, 0), (10, 0))
        b = _edge((0, 5), (10, 5))

        assert check_lines(a, b) is None

    def test_collinear_but_disjoint_segments(self):
        a = _edge((0, 0), (4, 0))
        b = _edge((5, 0), (10, 0))

        assert check_lines(a, b) is None

    def test_none_is_returned_if_either_line_is_none(self):
        a = _edge((0, 0), (1, 1))

        assert check_lines(a, None) is None
        assert check_lines(None, a) is None
        assert check_lines(None, None) is None


class TestCollinearOverlaps:
    """Two collinear segments that overlap over a sub-range should yield a CrossingLine."""

    def test_full_identical_overlap(self):
        a = _edge((0, 0), (10, 0))
        b = _edge((0, 0), (10, 0))

        assert check_lines(a, b) == CrossingLine(CrossingPoint(0, 0), CrossingPoint(10, 0))

    def test_one_segment_fully_contained_in_the_other(self):
        a = _edge((0, 0), (10, 0))
        b = _edge((3, 0), (7, 0))

        assert check_lines(a, b) == CrossingLine(CrossingPoint(3, 0), CrossingPoint(7, 0))

    def test_partial_overlap(self):
        a = _edge((0, 0), (6, 0))
        b = _edge((3, 0), (9, 0))

        assert check_lines(a, b) == CrossingLine(CrossingPoint(3, 0), CrossingPoint(6, 0))

    def test_overlap_is_independent_of_endpoint_order(self):
        a_forward = _edge((0, 0), (10, 0))
        a_reversed = _edge((10, 0), (0, 0))
        b_forward = _edge((2, 0), (8, 0))
        b_reversed = _edge((8, 0), (2, 0))

        expected = CrossingLine(CrossingPoint(2, 0), CrossingPoint(8, 0))

        assert check_lines(a_forward, b_forward) == expected
        assert check_lines(a_forward, b_reversed) == expected
        assert check_lines(a_reversed, b_forward) == expected
        assert check_lines(a_reversed, b_reversed) == expected

    def test_diagonal_overlap(self):
        a = _edge((0, 0), (10, 10))
        b = _edge((4, 4), (14, 14))

        assert check_lines(a, b) == CrossingLine(CrossingPoint(4, 4), CrossingPoint(10, 10))


class TestPointToLinePrecision:
    """Direct tests of `check_point_and_line`'s use of `numeric.numeric_eq`."""

    def test_point_well_within_default_precision_is_on_the_line(self):
        line = _edge((0, 0), (10, 0))
        point = CrossingPoint(5, 5e-10)  # default PRECISION is 1e-09

        assert check_point_and_line(point, line) == CrossingPoint(5, 5e-10)

    def test_point_well_outside_default_precision_is_not_on_the_line(self):
        line = _edge((0, 0), (10, 0))
        point = CrossingPoint(5, 5e-9)

        assert check_point_and_line(point, line) is None

    def test_point_just_outside_default_precision_is_not_on_the_line(self):
        # Unlike the "well outside" case above (5x the precision), this is
        # genuinely "almost touching" - the gap is only 1.5x the precision
        # radius, not orders of magnitude past it.
        line = _edge((0, 0), (10, 0))
        point = CrossingPoint(5, numeric.get_precision() * 1.5)

        assert check_point_and_line(point, line) is None

    def test_point_just_inside_default_precision_is_on_the_line(self):
        line = _edge((0, 0), (10, 0))
        point = CrossingPoint(5, numeric.get_precision() * 0.9)

        assert check_point_and_line(point, line) == point

    def test_point_exactly_at_the_precision_boundary_is_on_the_line(self):
        # numeric_eq()/math.isclose()'s abs_tol comparison is inclusive (<=),
        # so a distance exactly equal to the configured precision still
        # counts as touching, not just strictly-less-than it.
        line = _edge((0, 0), (10, 0))
        point = CrossingPoint(5, numeric.get_precision())

        assert check_point_and_line(point, line) == point

    def test_point_well_outside_the_segments_extent_is_not_on_the_line(self):
        line = _edge((0, 0), (10, 0))
        point = CrossingPoint(-1e-10, 0)

        # (-1e-10, 0) is within precision of the infinite line y=0, but past the
        # segment's actual start - distance_to_point() correctly measures the
        # distance to the nearest endpoint (1e-10), which is still within
        # precision here, so it *is* reported as touching.
        assert check_point_and_line(point, line) == CrossingPoint(-1e-10, 0)

    @pytest.mark.parametrize("distance", [1e-3, 1e-4, 1e-5])
    def test_custom_precision_changes_whether_a_point_counts_as_touching(self, distance):
        line = _edge((0, 0), (10, 0))
        point = CrossingPoint(5, distance)

        with _precision(1e-9):
            assert check_point_and_line(point, line) is None

        with _precision(distance * 10):
            assert check_point_and_line(point, line) == CrossingPoint(5, distance)


class TestCheckLinesPrecisionFallback:
    """
    `check_lines` falls back to `check_point_and_line` (which is precision-aware)
    whenever shapely itself reports no intersection - so near misses where an
    endpoint of one segment falls just short of actually reaching the other are
    already handled correctly today.
    """

    def test_near_coincident_endpoints_within_precision_are_reported(self):
        a = _edge((0, 0), (5, 5))
        b = _edge((5, 5 + 4e-10), (10, 0))

        result = check_lines(a, b)

        assert result == CrossingPoint(5, 5)

    def test_near_coincident_endpoints_outside_precision_are_not_reported(self):
        a = _edge((0, 0), (5, 5))
        b = _edge((5, 5 + 4e-8), (10, 0))

        assert check_lines(a, b) is None

    def test_near_coincident_endpoints_just_outside_precision_are_not_reported(self):
        # Same shape as the "well outside" case above, but the gap is only
        # 1.5x the precision radius rather than orders of magnitude past it -
        # i.e. genuinely "almost touching", not just "far away".
        a = _edge((0, 0), (5, 5))
        b = _edge((5, 5 + numeric.get_precision() * 1.5), (10, 0))

        assert check_lines(a, b) is None

    def test_near_coincident_endpoints_just_inside_precision_are_reported(self):
        a = _edge((0, 0), (5, 5))
        b = _edge((5, 5 + numeric.get_precision() * 0.9), (10, 0))

        assert check_lines(a, b) == CrossingPoint(5, 5)

    def test_t_intersection_within_precision_of_edge_interior_is_reported(self):
        a = _edge((0, 0), (10, 0))
        b = _edge((5, 5e-10), (5, 5))

        assert check_lines(a, b) == CrossingPoint(5, 0)

    def test_t_intersection_outside_precision_of_edge_interior_is_not_reported(self):
        a = _edge((0, 0), (10, 0))
        b = _edge((5, 5e-8), (5, 5))

        assert check_lines(a, b) is None

    def test_t_intersection_just_outside_precision_of_edge_interior_is_not_reported(self):
        a = _edge((0, 0), (10, 0))
        b = _edge((5, numeric.get_precision() * 1.5), (5, 5))

        assert check_lines(a, b) is None

    def test_t_intersection_just_inside_precision_of_edge_interior_is_reported(self):
        a = _edge((0, 0), (10, 0))
        b = _edge((5, numeric.get_precision() * 0.9), (5, 5))

        assert check_lines(a, b) == CrossingPoint(5, 0)

    def test_t_intersection_exactly_at_precision_boundary_is_reported(self):
        a = _edge((0, 0), (10, 0))
        b = _edge((5, numeric.get_precision()), (5, 5))

        assert check_lines(a, b) == CrossingPoint(5, 0)

    @pytest.mark.parametrize("precision_value", [1e-9, 1e-6, 1e-3])
    def test_precision_value_is_actually_threaded_through(self, precision_value):
        gap = precision_value * 0.1
        a = _edge((0, 0), (10, 0))
        b = _edge((5, gap), (5, 5))

        with _precision(precision_value):
            assert check_lines(a, b) == CrossingPoint(5, 0)


class TestNearCollinearOverlaps:
    """
    Two segments where every point of one is within precision of the other's
    infinite line, but the two aren't *exactly* collinear, should still be
    reported as an overlapping `CrossingLine` - the same as if they were
    exactly collinear. This was a known gap in the old shapely-based
    `check_lines` (shapely's exact computation has no notion of this
    tolerance, so it returned a single Point - or, in the second case, only
    one of the two touching endpoints - instead of the full overlap range);
    the precision-aware rewrite handles it directly via `_collinear_overlap`.

    Each case is checked at many different orientations (`_ROTATION_ANGLES`),
    not just the axis-aligned way it was originally found, via
    `_rotated_overlap_scenario` - this shouldn't depend on which way the
    segments happen to point.
    """

    @pytest.mark.parametrize("degrees", _ROTATION_ANGLES)
    def test_segment_tilted_within_precision_of_collinear_is_reported_as_overlap(
        self, degrees
    ):
        a, b, expected = _rotated_overlap_scenario(
            [(0, 0), (10, 0)], [(2, 6e-10), (8, -6e-10)], [(2, 0), (8, 0)], degrees
        )

        assert check_lines(a, b) == expected

    @pytest.mark.parametrize("degrees", _ROTATION_ANGLES)
    def test_segment_shifted_within_precision_of_collinear_is_reported_as_overlap(
        self, degrees
    ):
        a, b, expected = _rotated_overlap_scenario(
            [(0, 0), (10, 0)], [(2, 5e-10), (8, 5e-10)], [(2, 0), (8, 0)], degrees
        )

        assert check_lines(a, b) == expected
