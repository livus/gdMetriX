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
    Unit tests for the event queue data structure used in the crossing detection algorithm.
"""

import random
import unittest

from gdMetriX import crossingDataTypes
from gdMetriX.crossingDataTypes import EventQueue, SweepLineEdgeInfo, SweepLinePoint, CrossingPoint


class TestEventQueue(unittest.TestCase):
    def test_initialization(self):
        EventQueue()

    def test_pop_empty_queue(self):
        assert EventQueue().pop() is None

    def test_add_edge(self):
        queue = EventQueue()
        sweep_line_edge_info = SweepLineEdgeInfo((1, 2), (0, 0), (1, 1))
        queue.add_edge(sweep_line_edge_info)

    def test_add_multiple_edges_without_duplicate_points(self):
        queue = EventQueue()
        queue.add_edge(SweepLineEdgeInfo((1, 2), (0, 3), (1, 1)))
        queue.add_edge(SweepLineEdgeInfo((3, 4), (2, 123), (1023, 352)))
        queue.add_edge(SweepLineEdgeInfo((5, 6), (435, 8345), (9234, 48)))

    def test_pop_edge(self):
        queue = EventQueue()
        sweep_line_edge_info = SweepLineEdgeInfo((1, 2), (0, 0), (1, 1))
        queue.add_edge(sweep_line_edge_info)
        queue.pop()

    def test_pop_edge_check_two_inserted(self):
        queue = EventQueue()
        sweep_line_edge_info = SweepLineEdgeInfo((1, 2), (0, 0), (1, 1))
        queue.add_edge(sweep_line_edge_info)

        assert queue.pop() is not None
        assert queue.pop() is not None
        assert queue.pop() is None
        assert queue.pop() is None

    def test_pop_edge_check_correct_inserted(self):
        queue = EventQueue()
        sweep_line_edge_info = SweepLineEdgeInfo((1, 2), (0, 0), (1, 1))
        queue.add_edge(sweep_line_edge_info)

        point_a = queue.pop()
        point_b = queue.pop()

        assert point_a is not None
        assert point_b is not None
        assert point_a.start_list == {sweep_line_edge_info}
        assert point_a.end_list == set()
        assert point_a.interior_list == set()
        assert point_b.start_list == set()
        assert point_b.end_list == {sweep_line_edge_info}
        assert point_b.interior_list == set()

        assert queue.pop() is None

    def test_no_double_edge_inserts(self):
        queue = EventQueue()
        sweep_line_edge_info_a = SweepLineEdgeInfo((1, 2), (-3, 5), (12, 18))
        sweep_line_edge_info_b = SweepLineEdgeInfo((3, 4), (12, 18), (-3, 5))
        queue.add_edge(sweep_line_edge_info_a)
        queue.add_edge(sweep_line_edge_info_b)

        assert type(queue.pop()) is SweepLinePoint
        assert type(queue.pop()) is SweepLinePoint
        assert queue.pop() is None

    def test_insert_multiple_edges_at_same_point(self):
        queue = EventQueue()
        queue.add_edge(SweepLineEdgeInfo((1, 2), (0, 300), (3, 5)))
        queue.add_edge(SweepLineEdgeInfo((1, 2), (0, 300), (12, 3)))
        queue.add_edge(SweepLineEdgeInfo((1, 2), (0, 300), (7, 18)))

        first_point = queue.pop()

        assert type(first_point) is SweepLinePoint
        assert len(first_point.start_list) == 3
        assert len(first_point.end_list) == 0
        assert len(first_point.interior_list) == 0

    def test_edges_inserted_in_correct_y_order(self):
        """
        The event points should be returned in y order
        """

        queue = EventQueue()
        queue.add_edge(SweepLineEdgeInfo((1, 2), (-3, 1), (3, 5)))
        queue.add_edge(SweepLineEdgeInfo((1, 2), (19, 3), (0, 2)))
        queue.add_edge(SweepLineEdgeInfo((1, 2), (19, 0), (0, 4)))

        for i in range(6).__reversed__():
            event_point = queue.pop()
            assert event_point.y == i

    def test_edges_inserted_in_correct_x_order(self):
        """
        If two points have the same y value, they should be ordered by their x values
        """

        queue = EventQueue()
        queue.add_edge(SweepLineEdgeInfo((1, 2), (5, -123), (2, 5)))
        queue.add_edge(SweepLineEdgeInfo((1, 2), (3, -123), (1, 5)))
        queue.add_edge(SweepLineEdgeInfo((1, 2), (4, -123), (0, 5)))

        for i in range(6):
            event_point = queue.pop()
            assert event_point.x == i

    def test_add_crossing(self):
        queue = EventQueue()
        queue.add_crossing(
            CrossingPoint(3, 5),
            [
                SweepLineEdgeInfo((1, 2), (0, 0), (1, 1)),
                SweepLineEdgeInfo((1, 2), (0, 0), (1, 1)),
            ]
        )

    def test_add_multiple_crossings_without_duplicate_points(self):
        queue = EventQueue()
        queue.add_crossing(
            CrossingPoint(3, 5),
            [
                SweepLineEdgeInfo((1, 2), (0, 0), (1, 1)),
                SweepLineEdgeInfo((1, 2), (0, 0), (1, 1)),
            ]
        )
        queue.add_crossing(
            CrossingPoint(13, 5),
            [
                SweepLineEdgeInfo((1, 3), (0, 0), (1, 5)),
                SweepLineEdgeInfo((1, 3), (0, 0), (1, 5)),
            ],
        )

    def test_pop_crossing(self):
        queue = EventQueue()
        queue.add_crossing(
            CrossingPoint(3, 5),
            [
                SweepLineEdgeInfo((1, 2), (0, 0), (1, 1)),
                SweepLineEdgeInfo((1, 2), (0, 0), (1, 1)),
            ],
        )
        queue.pop()

    def test_pop_crossing_check_one_inserted(self):
        queue = EventQueue()
        queue.add_crossing(
            CrossingPoint(3, 5),
            [
                SweepLineEdgeInfo((1, 2), (0, 0), (1, 1)),
                SweepLineEdgeInfo((3, 4), (0, 0), (1, 1)),
            ],
        )

        assert queue.pop() is not None
        assert queue.pop() is None
        assert queue.pop() is None

    def test_pop_crossing_check_correct_inserted(self):
        queue = EventQueue()
        queue.add_crossing(
            CrossingPoint(3, 5),
            [
                SweepLineEdgeInfo((1, 2), (0, 0), (1, 1)),
                SweepLineEdgeInfo((3, 4), (0, 0), (1, 1)),
            ],
        )

        point_a = queue.pop()

        assert point_a.x == 3
        assert point_a.y == 5
        assert len(point_a.start_list) == 0
        assert len(point_a.end_list) == 0
        assert len(point_a.interior_list) == 2

        assert queue.pop() is None

    def test_no_double_crossing_inserts(self):
        queue = EventQueue()
        queue.add_crossing(
            CrossingPoint(3, 5),
            [
                SweepLineEdgeInfo((1, 2), (0, 0), (1, 1)),
                SweepLineEdgeInfo((3, 4), (0, 0), (1, 1)),
            ]
        )
        queue.add_crossing(
            CrossingPoint(3, 5),
            [
                SweepLineEdgeInfo((5, 6), (2, 20), (-1, 2)),
                SweepLineEdgeInfo((12, 4), (5, 76), (61, 345)),
            ],
        )

        assert type(queue.pop()) is SweepLinePoint
        assert queue.pop() is None

    def test_crossings_inserted_in_correct_y_order(self):
        """
        The event points should be returned in y order
        """
        edge_list = [
            SweepLineEdgeInfo((5, 6), (2, 20), (-1, 2)),
            SweepLineEdgeInfo((12, 4), (5, 76), (61, 345)),
        ]

        queue = EventQueue()
        queue.add_crossing(CrossingPoint(3, 5), edge_list)
        queue.add_crossing(CrossingPoint(13, 3), edge_list)
        queue.add_crossing(CrossingPoint(-1, 2), edge_list)
        queue.add_crossing(CrossingPoint(23098, 4), edge_list)
        queue.add_crossing(CrossingPoint(1, 1), edge_list)
        queue.add_crossing(CrossingPoint(5, 0), edge_list)

        assert list(range(6).__reversed__()) == [queue.pop().y for _ in range(len(queue))]

    def test_crossings_inserted_in_correct_x_order(self):
        """
        The event points should be returned in y order
        """
        edge_list = [
            SweepLineEdgeInfo((5, 6), (2, 20), (-1, 2)),
            SweepLineEdgeInfo((12, 4), (5, 76), (61, 345)),
        ]

        queue = EventQueue()
        queue.add_crossing(CrossingPoint(0, 12), edge_list)
        queue.add_crossing(CrossingPoint(1, 12), edge_list)
        queue.add_crossing(CrossingPoint(2, 12), edge_list)
        queue.add_crossing(CrossingPoint(5, 4), edge_list)
        queue.add_crossing(CrossingPoint(4, 4), edge_list)
        queue.add_crossing(CrossingPoint(3, 4), edge_list)

        assert list(range(6)) == [queue.pop().x for _ in range(len(queue))]

    def test_stress_test(self):
        random.seed(12930919203)

        width = 25
        height = 25
        depth = 5

        queue = EventQueue()

        edge_list_for_crossing = [
            SweepLineEdgeInfo((5, 6), (2, 20), (-1, 2)),
            SweepLineEdgeInfo((12, 4), (5, 76), (61, 345)),
        ]

        point_list = []
        for x in range(width):
            for y in range(height):
                for i in range(depth):
                    point_list.append((x, y))

        random.shuffle(point_list)

        for x, y in point_list:
            if random.randint(0, 1) == 0:
                queue.add_crossing(CrossingPoint(x, y), edge_list_for_crossing)
                queue.add_crossing(CrossingPoint(x + 1, y + 1), edge_list_for_crossing)
            else:
                queue.add_edge(SweepLineEdgeInfo((x, y), (x, y), (x + 1, y + 1)))

        prev_x, prev_y = None, None
        count = 0
        item = queue.pop()
        while item is not None:
            if prev_x is not None and prev_y is not None:
                assert prev_y > item.y or (prev_y == item.y and item.x >= prev_x)
            assert -1 <= queue.sorted_list.__get_balance__(queue.sorted_list.root) <= 1
            count += 1
            prev_x, prev_y = item.x, item.y
            item = queue.pop()

        assert count == (width + 1) * (height + 1) - 2

    def test_close_points_are_grouped(self):
        crossingDataTypes.set_precision(0.001)
        queue = EventQueue()

        edge_list_for_crossing = [
            SweepLineEdgeInfo((5, 6), (2, 20), (-1, 2)),
            SweepLineEdgeInfo((12, 4), (5, 76), (61, 345)),
        ]

        queue.add_crossing(CrossingPoint(1, 1.001), edge_list_for_crossing)
        queue.add_crossing(CrossingPoint(1, 1), edge_list_for_crossing)

        assert len(queue) == 1

        crossingDataTypes.set_precision(1e-09)

    def test_close_points_are_grouped_2(self):
        crossingDataTypes.set_precision(0.001)
        queue = EventQueue()

        edge_list_for_crossing = [
            SweepLineEdgeInfo((5, 6), (2, 20), (-1, 2)),
            SweepLineEdgeInfo((12, 4), (5, 76), (61, 345)),
        ]

        queue.add_crossing(CrossingPoint(1.001, 1.001), edge_list_for_crossing)
        queue.add_crossing(CrossingPoint(1, 1), edge_list_for_crossing)

        assert len(queue) == 1

        crossingDataTypes.set_precision(1e-09)

    def test_close_points_are_grouped_3(self):
        crossingDataTypes.set_precision(0.001)
        queue = EventQueue()

        queue.add_edge(SweepLineEdgeInfo((0, 1), (1, 1.001), (2, 2.001)))
        queue.add_edge(SweepLineEdgeInfo((2, 3), (1, 1), (2, 2)))

        assert len(queue) == 2

        crossingDataTypes.set_precision(1e-09)

    def test_close_points_are_grouped_4(self):
        crossingDataTypes.set_precision(0.001)
        queue = EventQueue()

        queue.add_edge(SweepLineEdgeInfo((0, 1), (1.001, 1.001), (2.001, 2.001)))
        queue.add_edge(SweepLineEdgeInfo((2, 3), (1, 1), (2, 2)))

        assert len(queue) == 2

        crossingDataTypes.set_precision(1e-09)
