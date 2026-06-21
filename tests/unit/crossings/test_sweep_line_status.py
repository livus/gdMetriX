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
Unit tests for the sweep line data structure used in the crossing detection algorithm.
"""

import random
import unittest

from gdMetriX.utils import numeric
from gdMetriX.utils.numeric import greater_than
from gdMetriX.utils.sweep_line import (
    SweepLineEdgeInfo,
    CrossingPoint,
    SweepLineStatus,
    SweepLinePoint,
)


class TestSweepLineStatus(unittest.TestCase):
    def test_initialization(self):
        SweepLineStatus()

    def test_adding_single_edge(self):
        s = SweepLineStatus()
        s.add(10, SweepLineEdgeInfo((0, 1), CrossingPoint(0, 0), CrossingPoint(10, 10)))

    def test_adding_multiple_edges(self):
        s = SweepLineStatus()
        s.add(10, SweepLineEdgeInfo((0, 1), CrossingPoint(0, 0), CrossingPoint(10, 10)))
        s.add(10, SweepLineEdgeInfo((2, 3), CrossingPoint(0, 0), CrossingPoint(10, 10)))

    def test_adding_multiple_edges_with_same_start(self):
        s = SweepLineStatus()
        s.add(10, SweepLineEdgeInfo((0, 1), CrossingPoint(0, 0), CrossingPoint(4, 10)))
        s.add(10, SweepLineEdgeInfo((2, 3), CrossingPoint(0, 0), CrossingPoint(7, 10)))
        s.add(10, SweepLineEdgeInfo((4, 5), CrossingPoint(0, 10), CrossingPoint(1, 0)))
        s.add(10, SweepLineEdgeInfo((6, 7), CrossingPoint(0, 10), CrossingPoint(2, 0)))

    def test_get_right_neighbor(self):
        s = SweepLineStatus()
        edge1 = SweepLineEdgeInfo((0, 1), CrossingPoint(0, 0), CrossingPoint(1, 10))
        edge2 = SweepLineEdgeInfo((2, 3), CrossingPoint(1, 0), CrossingPoint(2, 10))
        edge3 = SweepLineEdgeInfo((4, 5), CrossingPoint(2, 0), CrossingPoint(3, 10))
        edge4 = SweepLineEdgeInfo((6, 7), CrossingPoint(3, 0), CrossingPoint(4, 10))

        s.add(6, edge1)
        s.add(6, edge2)
        s.add(6, edge3)
        s.add(6, edge4)

        self.assertEqual(s.get_right(SweepLinePoint(CrossingPoint(0, 1))), edge1)
        self.assertEqual(s.get_right(SweepLinePoint(CrossingPoint(0, 2))), edge1)
        self.assertEqual(s.get_right(SweepLinePoint(CrossingPoint(0, 3))), edge1)
        self.assertEqual(s.get_right(SweepLinePoint(CrossingPoint(0, 4))), edge1)
        self.assertEqual(s.get_right(SweepLinePoint(CrossingPoint(0, 5))), edge1)
        self.assertEqual(s.get_right(SweepLinePoint(CrossingPoint(0, 6))), edge1)
        self.assertEqual(s.get_right(SweepLinePoint(CrossingPoint(0, 7))), edge1)
        self.assertEqual(s.get_right(SweepLinePoint(CrossingPoint(1, 1))), edge2)
        self.assertEqual(s.get_right(SweepLinePoint(CrossingPoint(1, 2))), edge2)
        self.assertEqual(s.get_right(SweepLinePoint(CrossingPoint(1, 3))), edge2)
        self.assertEqual(s.get_right(SweepLinePoint(CrossingPoint(1, 4))), edge2)
        self.assertEqual(s.get_right(SweepLinePoint(CrossingPoint(1, 5))), edge2)
        self.assertEqual(s.get_right(SweepLinePoint(CrossingPoint(1, 6))), edge2)
        self.assertEqual(s.get_right(SweepLinePoint(CrossingPoint(1, 7))), edge2)
        self.assertEqual(s.get_right(SweepLinePoint(CrossingPoint(2, 1))), edge3)
        self.assertEqual(s.get_right(SweepLinePoint(CrossingPoint(2, 2))), edge3)
        self.assertEqual(s.get_right(SweepLinePoint(CrossingPoint(2, 3))), edge3)
        self.assertEqual(s.get_right(SweepLinePoint(CrossingPoint(2, 4))), edge3)
        self.assertEqual(s.get_right(SweepLinePoint(CrossingPoint(2, 5))), edge3)
        self.assertEqual(s.get_right(SweepLinePoint(CrossingPoint(2, 6))), edge3)
        self.assertEqual(s.get_right(SweepLinePoint(CrossingPoint(2, 7))), edge3)
        self.assertEqual(s.get_right(SweepLinePoint(CrossingPoint(3, 1))), edge4)
        self.assertEqual(s.get_right(SweepLinePoint(CrossingPoint(3, 2))), edge4)
        self.assertEqual(s.get_right(SweepLinePoint(CrossingPoint(3, 3))), edge4)
        self.assertEqual(s.get_right(SweepLinePoint(CrossingPoint(3, 4))), edge4)
        self.assertEqual(s.get_right(SweepLinePoint(CrossingPoint(3, 5))), edge4)
        self.assertEqual(s.get_right(SweepLinePoint(CrossingPoint(3, 6))), edge4)
        self.assertEqual(s.get_right(SweepLinePoint(CrossingPoint(3, 7))), edge4)
        self.assertEqual(s.get_right(SweepLinePoint(CrossingPoint(4, 1))), None)
        self.assertEqual(s.get_right(SweepLinePoint(CrossingPoint(4, 2))), None)
        self.assertEqual(s.get_right(SweepLinePoint(CrossingPoint(4, 3))), None)
        self.assertEqual(s.get_right(SweepLinePoint(CrossingPoint(4, 4))), None)
        self.assertEqual(s.get_right(SweepLinePoint(CrossingPoint(4, 5))), None)
        self.assertEqual(s.get_right(SweepLinePoint(CrossingPoint(4, 6))), None)
        self.assertEqual(s.get_right(SweepLinePoint(CrossingPoint(4, 7))), None)

    def test_get_left_neighbor(self):
        s = SweepLineStatus()
        edge1 = SweepLineEdgeInfo((0, 1), CrossingPoint(0, 0), CrossingPoint(1, 10))
        edge2 = SweepLineEdgeInfo((2, 3), CrossingPoint(1, 0), CrossingPoint(2, 10))
        edge3 = SweepLineEdgeInfo((4, 5), CrossingPoint(2, 0), CrossingPoint(3, 10))
        edge4 = SweepLineEdgeInfo((6, 7), CrossingPoint(3, 0), CrossingPoint(4, 10))

        s.add(10, edge1)
        s.add(10, edge2)
        s.add(10, edge3)
        s.add(10, edge4)

        self.assertEqual(s.get_left(SweepLinePoint(CrossingPoint(0, 1))), None)
        self.assertEqual(s.get_left(SweepLinePoint(CrossingPoint(0, 2))), None)
        self.assertEqual(s.get_left(SweepLinePoint(CrossingPoint(0, 3))), None)
        self.assertEqual(s.get_left(SweepLinePoint(CrossingPoint(0, 4))), None)
        self.assertEqual(s.get_left(SweepLinePoint(CrossingPoint(0, 5))), None)
        self.assertEqual(s.get_left(SweepLinePoint(CrossingPoint(0, 6))), None)
        self.assertEqual(s.get_left(SweepLinePoint(CrossingPoint(0, 7))), None)
        self.assertEqual(s.get_left(SweepLinePoint(CrossingPoint(1, 1))), edge1)
        self.assertEqual(s.get_left(SweepLinePoint(CrossingPoint(1, 2))), edge1)
        self.assertEqual(s.get_left(SweepLinePoint(CrossingPoint(1, 3))), edge1)
        self.assertEqual(s.get_left(SweepLinePoint(CrossingPoint(1, 4))), edge1)
        self.assertEqual(s.get_left(SweepLinePoint(CrossingPoint(1, 5))), edge1)
        self.assertEqual(s.get_left(SweepLinePoint(CrossingPoint(1, 6))), edge1)
        self.assertEqual(s.get_left(SweepLinePoint(CrossingPoint(1, 7))), edge1)
        self.assertEqual(s.get_left(SweepLinePoint(CrossingPoint(2, 1))), edge2)
        self.assertEqual(s.get_left(SweepLinePoint(CrossingPoint(2, 2))), edge2)
        self.assertEqual(s.get_left(SweepLinePoint(CrossingPoint(2, 3))), edge2)
        self.assertEqual(s.get_left(SweepLinePoint(CrossingPoint(2, 4))), edge2)
        self.assertEqual(s.get_left(SweepLinePoint(CrossingPoint(2, 5))), edge2)
        self.assertEqual(s.get_left(SweepLinePoint(CrossingPoint(2, 6))), edge2)
        self.assertEqual(s.get_left(SweepLinePoint(CrossingPoint(2, 7))), edge2)
        self.assertEqual(s.get_left(SweepLinePoint(CrossingPoint(3, 1))), edge3)
        self.assertEqual(s.get_left(SweepLinePoint(CrossingPoint(3, 2))), edge3)
        self.assertEqual(s.get_left(SweepLinePoint(CrossingPoint(3, 3))), edge3)
        self.assertEqual(s.get_left(SweepLinePoint(CrossingPoint(3, 4))), edge3)
        self.assertEqual(s.get_left(SweepLinePoint(CrossingPoint(3, 5))), edge3)
        self.assertEqual(s.get_left(SweepLinePoint(CrossingPoint(3, 6))), edge3)
        self.assertEqual(s.get_left(SweepLinePoint(CrossingPoint(3, 7))), edge3)
        self.assertEqual(s.get_left(SweepLinePoint(CrossingPoint(4, 1))), edge4)
        self.assertEqual(s.get_left(SweepLinePoint(CrossingPoint(4, 2))), edge4)
        self.assertEqual(s.get_left(SweepLinePoint(CrossingPoint(4, 3))), edge4)
        self.assertEqual(s.get_left(SweepLinePoint(CrossingPoint(4, 4))), edge4)
        self.assertEqual(s.get_left(SweepLinePoint(CrossingPoint(4, 5))), edge4)
        self.assertEqual(s.get_left(SweepLinePoint(CrossingPoint(4, 6))), edge4)
        self.assertEqual(s.get_left(SweepLinePoint(CrossingPoint(4, 7))), edge4)

    def test_removing_edge(self):
        s = SweepLineStatus()
        edge1 = SweepLineEdgeInfo((0, 1), CrossingPoint(0, 0), CrossingPoint(0, 10))
        edge2 = SweepLineEdgeInfo((2, 3), CrossingPoint(1, 0), CrossingPoint(1, 10))
        edge3 = SweepLineEdgeInfo((4, 5), CrossingPoint(2, 0), CrossingPoint(2, 10))

        s.add(5, edge1)
        s.add(5, edge2)
        s.add(5, edge3)

        s.remove(5, edge2)

        items_left = list(s.sorted_list)
        assert len(items_left) == 2
        assert items_left[0] == edge1
        assert items_left[1] == edge3

    def test_removing_edge_2(self):
        random.seed(3949023845)
        s = SweepLineStatus()
        edge_list = []

        total_size = 1000

        for i in range(total_size):
            pos_a = CrossingPoint(random.uniform(-1, 1), random.uniform(-1, 1))
            pos_b = CrossingPoint(random.uniform(-1, 1), random.uniform(-1, 1))
            edge = SweepLineEdgeInfo((i * 2, i * 2 + 1), pos_a, pos_b)
            s.add(0.5, edge)
            edge_list.append(edge)

        assert len(list(s.sorted_list)) == total_size

        for edge in edge_list:
            total_size -= 1
            s.remove(0.5, edge)
            assert len(list(s.sorted_list)) == total_size

    def test_removing_edge_3(self):
        random.seed(3949023845)
        s = SweepLineStatus()
        edge_list = []

        total_size = 1000

        for i in range(total_size):
            pos_a = CrossingPoint(random.randint(-5, 5), random.uniform(-5, 5))
            pos_b = CrossingPoint(random.uniform(-5, 5), random.uniform(-5, 5))
            edge = SweepLineEdgeInfo((i * 2, i * 2 + 1), pos_a, pos_b)
            s.add(0.5, edge)
            edge_list.append(edge)

        assert len(list(s.sorted_list)) == total_size

        for edge in edge_list:
            total_size -= 1
            s.remove(0.5, edge)
            assert len(list(s.sorted_list)) == total_size

    def test_same_x_position_inserted_in_correct_order(self):
        s = SweepLineStatus()
        edge1 = SweepLineEdgeInfo((4, 1), CrossingPoint(0, 1), CrossingPoint(0, 0))
        edge2 = SweepLineEdgeInfo((4, 2), CrossingPoint(0, 1), CrossingPoint(1, 0))
        edge3 = SweepLineEdgeInfo((4, 3), CrossingPoint(0, 1), CrossingPoint(2, 0))
        s.add(1, edge1)
        s.add(1, edge2)
        s.add(1, edge3)

        ordered_list = list(s.sorted_list)
        assert len(ordered_list) == 3
        assert ordered_list[0] == edge1
        assert ordered_list[1] == edge2
        assert ordered_list[2] == edge3

    def test_same_x_position_inserted_in_correct_order_2(self):
        s = SweepLineStatus()
        edge1 = SweepLineEdgeInfo((4, 1), CrossingPoint(0, 1), CrossingPoint(0, 0))
        edge2 = SweepLineEdgeInfo((4, 2), CrossingPoint(0, 1), CrossingPoint(1, 0))
        edge3 = SweepLineEdgeInfo((4, 3), CrossingPoint(0, 1), CrossingPoint(2, 0))
        s.add(1, edge3)
        s.add(1, edge2)
        s.add(1, edge1)

        ordered_list = list(s.sorted_list)
        assert len(ordered_list) == 3
        assert ordered_list[0] == edge1
        assert ordered_list[1] == edge2
        assert ordered_list[2] == edge3

    def test_edges_with_same_startpoint_left(self):
        s = SweepLineStatus()
        edge1 = SweepLineEdgeInfo((4, 1), CrossingPoint(0, 1), CrossingPoint(0, 0))
        edge2 = SweepLineEdgeInfo((4, 2), CrossingPoint(0, 1), CrossingPoint(1, 0))
        edge3 = SweepLineEdgeInfo((4, 3), CrossingPoint(0, 1), CrossingPoint(2, 0))
        s.add(1, edge1)
        s.add(1, edge2)
        s.add(1, edge3)

        self.assertEqual(s.get_left(SweepLinePoint(CrossingPoint(1, 1))), edge3)

    def test_edges_with_same_startpoint_left_reversed(self):
        s = SweepLineStatus()
        edge1 = SweepLineEdgeInfo((4, 1), CrossingPoint(0, 1), CrossingPoint(0, 0))
        edge2 = SweepLineEdgeInfo((4, 2), CrossingPoint(0, 1), CrossingPoint(1, 0))
        edge3 = SweepLineEdgeInfo((4, 3), CrossingPoint(0, 1), CrossingPoint(2, 0))
        s.add(1, edge3)
        s.add(1, edge2)
        s.add(1, edge1)

        self.assertEqual(s.get_left(SweepLinePoint(CrossingPoint(1, 1))), edge3)

    def test_edges_with_same_startpoint_right(self):
        s = SweepLineStatus()
        edge1 = SweepLineEdgeInfo((4, 1), CrossingPoint(0, 1), CrossingPoint(0, 0))
        edge2 = SweepLineEdgeInfo((4, 2), CrossingPoint(0, 1), CrossingPoint(1, 0))
        edge3 = SweepLineEdgeInfo((4, 3), CrossingPoint(0, 1), CrossingPoint(2, 0))
        s.add(1, edge1)
        s.add(1, edge2)
        s.add(1, edge3)

        self.assertEqual(s.get_right(SweepLinePoint(CrossingPoint(-2, 1))), edge1)

    def test_edges_with_same_startpoint_right_reversed(self):
        s = SweepLineStatus()
        edge1 = SweepLineEdgeInfo((4, 1), CrossingPoint(0, 1), CrossingPoint(0, 0))
        edge2 = SweepLineEdgeInfo((4, 2), CrossingPoint(0, 1), CrossingPoint(1, 0))
        edge3 = SweepLineEdgeInfo((4, 3), CrossingPoint(0, 1), CrossingPoint(2, 0))
        s.add(1, edge3)
        s.add(1, edge2)
        s.add(1, edge1)

        self.assertEqual(s.get_right(SweepLinePoint(CrossingPoint(-2, 1))), edge1)

    def test_get_range_whole_spectrum(self):
        s = SweepLineStatus()
        edge1 = SweepLineEdgeInfo((1, 5), CrossingPoint(0, 2), CrossingPoint(0, 0))
        edge2 = SweepLineEdgeInfo((2, 5), CrossingPoint(1, 2), CrossingPoint(1, 0))
        edge3 = SweepLineEdgeInfo((2, 7), CrossingPoint(2, 0), CrossingPoint(2, 2))
        edge4 = SweepLineEdgeInfo((3, 6), CrossingPoint(3, 0), CrossingPoint(3, 2))

        s.add(1, edge1)
        s.add(1, edge2)
        s.add(1, edge3)
        s.add(1, edge4)

        result = list(s.get_range(1, 0, 3))

        assert len(result) == 4
        assert result[0] == edge1
        assert result[1] == edge2
        assert result[2] == edge3
        assert result[3] == edge4

    def test_get_range_whole_spectrum_2(self):
        s = SweepLineStatus()
        edge1 = SweepLineEdgeInfo((1, 2), CrossingPoint(0, 2), CrossingPoint(0, 0))
        edge2 = SweepLineEdgeInfo((3, 4), CrossingPoint(1, 2), CrossingPoint(1, 0))
        edge3 = SweepLineEdgeInfo((5, 6), CrossingPoint(2, 0), CrossingPoint(2, 2))
        edge4 = SweepLineEdgeInfo((7, 8), CrossingPoint(3, 0), CrossingPoint(3, 2))

        s.add(0, edge1)
        s.add(0, edge2)
        s.add(0, edge3)
        s.add(0, edge4)

        result = list(s.get_range(0, 0, 3))

        assert len(result) == 4
        assert result[0] == edge1
        assert result[1] == edge2
        assert result[2] == edge3
        assert result[3] == edge4

    def test_get_range_whole_spectrum_3(self):
        s = SweepLineStatus()
        edge1 = SweepLineEdgeInfo((1, 2), CrossingPoint(0, 2), CrossingPoint(0, 0))
        edge2 = SweepLineEdgeInfo((3, 4), CrossingPoint(1, 2), CrossingPoint(1, 0))
        edge3 = SweepLineEdgeInfo((5, 6), CrossingPoint(2, 0), CrossingPoint(2, 2))
        edge4 = SweepLineEdgeInfo((7, 8), CrossingPoint(3, 0), CrossingPoint(3, 2))

        s.add(2, edge1)
        s.add(2, edge2)
        s.add(2, edge3)
        s.add(2, edge4)

        result = list(s.get_range(2, 0, 3))

        assert len(result) == 4
        assert result[0] == edge1
        assert result[1] == edge2
        assert result[2] == edge3
        assert result[3] == edge4

    def test_get_range_partial(self):
        s = SweepLineStatus()
        edge1 = SweepLineEdgeInfo((1, 2), CrossingPoint(0, 2), CrossingPoint(0, 0))
        edge2 = SweepLineEdgeInfo((3, 4), CrossingPoint(1, 2), CrossingPoint(1, 0))
        edge3 = SweepLineEdgeInfo((5, 6), CrossingPoint(2, 0), CrossingPoint(2, 2))
        edge4 = SweepLineEdgeInfo((7, 8), CrossingPoint(3, 0), CrossingPoint(3, 2))

        s.add(2, edge1)
        s.add(2, edge2)
        s.add(2, edge3)
        s.add(2, edge4)

        result = list(s.get_range(2, 0.01, 2.99))

        assert len(result) == 2
        assert result[0] == edge2
        assert result[1] == edge3

    def test_get_range_stress_test(self):
        random.seed(9023854908239405)

        s = SweepLineStatus()

        range_query = (-102.5, 0.539)

        count = 0

        for i in range(0, 5000):
            x = random.uniform(-1000, 1000)

            edge = SweepLineEdgeInfo(
                (i * 2, (i * 2) + 1), CrossingPoint(x, -1), CrossingPoint(x, 1)
            )
            s.add(0, edge)

            if not greater_than(range_query[0], x) and not greater_than(
                x, range_query[1]
            ):
                count += 1

        result = list(s.get_range(0, range_query[0], range_query[1]))
        assert len(result) == count

    def test_get_range_stress_test_2(self):
        random.seed(9023854908239405)

        s = SweepLineStatus()

        range_query = (-102.5, 0.539)

        count = 0

        for i in range(0, 5000):
            x = random.randint(-150, 150)

            edge = SweepLineEdgeInfo(
                (i * 2, (i * 2) + 1), CrossingPoint(x, -1), CrossingPoint(x, 1)
            )
            s.add(0, edge)

            if not greater_than(range_query[0], x) and not greater_than(
                x, range_query[1]
            ):
                count += 1

        result = list(s.get_range(0, range_query[0], range_query[1]))
        assert len(result) == count

    def test_get_left_independent_on_insert_order(self):
        random.seed(983490890)

        edge1 = SweepLineEdgeInfo((0, 1), CrossingPoint(0, 0), CrossingPoint(1, 10))
        edge2 = SweepLineEdgeInfo((2, 3), CrossingPoint(1, 0), CrossingPoint(2, 10))
        edge3 = SweepLineEdgeInfo((4, 5), CrossingPoint(2, 0), CrossingPoint(3, 10))
        edge4 = SweepLineEdgeInfo((6, 7), CrossingPoint(3, 0), CrossingPoint(4, 10))

        edges = [edge1, edge2, edge3, edge4]

        for i in range(0, 50):
            random.shuffle(edges)

            s = SweepLineStatus()
            for edge in edges:
                s.add(10, edge)

            self.assertEqual(s.get_left(SweepLinePoint(CrossingPoint(0, 7))), None)
            self.assertEqual(s.get_left(SweepLinePoint(CrossingPoint(1, 7))), edge1)
            self.assertEqual(s.get_left(SweepLinePoint(CrossingPoint(2, 7))), edge2)
            self.assertEqual(s.get_left(SweepLinePoint(CrossingPoint(3, 7))), edge3)
            self.assertEqual(s.get_left(SweepLinePoint(CrossingPoint(4, 7))), edge4)

    def test_get_right_independent_on_insert_order(self):
        random.seed(9890384095)

        edge1 = SweepLineEdgeInfo((0, 1), CrossingPoint(0, 0), CrossingPoint(1, 10))
        edge2 = SweepLineEdgeInfo((2, 3), CrossingPoint(1, 0), CrossingPoint(2, 10))
        edge3 = SweepLineEdgeInfo((4, 5), CrossingPoint(2, 0), CrossingPoint(3, 10))
        edge4 = SweepLineEdgeInfo((6, 7), CrossingPoint(3, 0), CrossingPoint(4, 10))

        edges = [edge1, edge2, edge3, edge4]

        for i in range(0, 50):
            random.shuffle(edges)

            s = SweepLineStatus()
            for edge in edges:
                s.add(10, edge)

            self.assertEqual(s.get_right(SweepLinePoint(CrossingPoint(0, 7))), edge1)
            self.assertEqual(s.get_right(SweepLinePoint(CrossingPoint(1, 7))), edge2)
            self.assertEqual(s.get_right(SweepLinePoint(CrossingPoint(2, 7))), edge3)
            self.assertEqual(s.get_right(SweepLinePoint(CrossingPoint(3, 7))), edge4)
            self.assertEqual(s.get_right(SweepLinePoint(CrossingPoint(4, 7))), None)

    def test_get_left_independent_on_insert_order_2(self):
        random.seed(983490890)

        edge1 = SweepLineEdgeInfo((0, 1), CrossingPoint(0, 0), CrossingPoint(1, 10))
        edge2 = SweepLineEdgeInfo((2, 3), CrossingPoint(1, 0), CrossingPoint(2, 10))
        edge3 = SweepLineEdgeInfo((4, 5), CrossingPoint(2, 0), CrossingPoint(3, 10))
        edge4 = SweepLineEdgeInfo((6, 7), CrossingPoint(3, 0), CrossingPoint(4, 10))

        edges = [edge1, edge2, edge3, edge4]

        junk_edges = [
            SweepLineEdgeInfo(
                ((i * 2) + 8, (i + 2) + 9),
                CrossingPoint(random.uniform(-100, 100), random.uniform(-100, 100)),
                CrossingPoint(random.uniform(-100, 100), random.uniform(-100, 100)),
            )
            for i in range(0, 100)
        ]

        both = junk_edges + edges

        for i in range(0, 10):
            random.shuffle(both)

            s = SweepLineStatus()
            for edge in both:
                s.add(10, edge)

            random.shuffle(junk_edges)

            for edge in junk_edges:
                s.remove(10, edge)

            self.assertEqual(s.get_left(SweepLinePoint(CrossingPoint(0, 7))), None)
            self.assertEqual(s.get_left(SweepLinePoint(CrossingPoint(1, 7))), edge1)
            self.assertEqual(s.get_left(SweepLinePoint(CrossingPoint(2, 7))), edge2)
            self.assertEqual(s.get_left(SweepLinePoint(CrossingPoint(3, 7))), edge3)
            self.assertEqual(s.get_left(SweepLinePoint(CrossingPoint(4, 7))), edge4)

    def test_get_right_independent_on_insert_order_2(self):
        random.seed(985943890)

        edge1 = SweepLineEdgeInfo((0, 1), CrossingPoint(0, 0), CrossingPoint(1, 10))
        edge2 = SweepLineEdgeInfo((2, 3), CrossingPoint(1, 0), CrossingPoint(2, 10))
        edge3 = SweepLineEdgeInfo((4, 5), CrossingPoint(2, 0), CrossingPoint(3, 10))
        edge4 = SweepLineEdgeInfo((6, 7), CrossingPoint(3, 0), CrossingPoint(4, 10))

        edges = [edge1, edge2, edge3, edge4]

        junk_edges = [
            SweepLineEdgeInfo(
                ((i * 2) + 8, (i + 2) + 9),
                CrossingPoint(random.uniform(-100, 100), random.uniform(-100, 100)),
                CrossingPoint(random.uniform(-100, 100), random.uniform(-100, 100)),
            )
            for i in range(0, 100)
        ]

        both = junk_edges + edges

        for i in range(0, 10):
            random.shuffle(both)

            s = SweepLineStatus()
            for edge in both:
                s.add(10, edge)

            random.shuffle(junk_edges)

            for edge in junk_edges:
                s.remove(10, edge)

            self.assertEqual(s.get_right(SweepLinePoint(CrossingPoint(0, 7))), edge1)
            self.assertEqual(s.get_right(SweepLinePoint(CrossingPoint(1, 7))), edge2)
            self.assertEqual(s.get_right(SweepLinePoint(CrossingPoint(2, 7))), edge3)
            self.assertEqual(s.get_right(SweepLinePoint(CrossingPoint(3, 7))), edge4)
            self.assertEqual(s.get_right(SweepLinePoint(CrossingPoint(4, 7))), None)

    def test_get_right_with_multiple_edges(self):
        edge1 = SweepLineEdgeInfo((0, 1), CrossingPoint(1, 1), CrossingPoint(1, -1))
        edge2 = SweepLineEdgeInfo((2, 3), CrossingPoint(2, 1), CrossingPoint(0, -1))
        edge3 = SweepLineEdgeInfo((4, 5), CrossingPoint(0, 1), CrossingPoint(2, -1))
        edge4 = SweepLineEdgeInfo((6, 7), CrossingPoint(0, 1), CrossingPoint(0, -1))

        s = SweepLineStatus()
        s.add(0, edge1)
        s.add(0, edge2)
        s.add(0, edge3)
        s.add(0, edge4)

        assert s.get_right(SweepLinePoint(CrossingPoint(0, 0))) == edge2

    def test_get_left_with_multiple_edges(self):
        edge1 = SweepLineEdgeInfo((0, 1), CrossingPoint(1, 1), CrossingPoint(1, -1))
        edge2 = SweepLineEdgeInfo((2, 3), CrossingPoint(2, 1), CrossingPoint(0, -1))
        edge3 = SweepLineEdgeInfo((4, 5), CrossingPoint(0, 1), CrossingPoint(2, -1))
        edge4 = SweepLineEdgeInfo((6, 7), CrossingPoint(2, 1), CrossingPoint(2, -1))

        s = SweepLineStatus()
        s.add(0, edge1)
        s.add(0, edge2)
        s.add(0, edge3)
        s.add(0, edge4)

        assert s.get_left(SweepLinePoint(CrossingPoint(2, 0))) == edge3

    # region Edges sharing an endpoint (regression tests for the less_than() tie-break)
    #
    # SweepLineEdgeInfo.less_than() has to disambiguate two edges that compare equal at the
    # queried height by looking slightly off that height. Two straight, non-identical edges
    # only ever tie at a single height: either the height where they actually cross, or a
    # shared endpoint where neither line "crosses" the other but they still happen to meet.
    # In the latter case, both edges may end exactly at the queried height, leaving no valid
    # spot below to probe - probing there anyway extrapolates past where the edges end and
    # can report the wrong order (see test_less_than_at_shared_endpoint_is_consistent below).

    def test_less_than_at_shared_endpoint_is_consistent(self):
        # A approaches (0, -1) from the left, B is the vertical line through x=0. Both end
        # at exactly the same point, so comparing them there ties and needs disambiguation.
        a = SweepLineEdgeInfo((0, 1), CrossingPoint(-1, 0), CrossingPoint(0, -1))
        b = SweepLineEdgeInfo((2, 3), CrossingPoint(0, 1), CrossingPoint(0, -1))

        self.assertTrue(a.less_than(b, -1))
        self.assertFalse(b.less_than(a, -1))

    def test_less_than_at_shared_endpoint_is_consistent_reversed(self):
        # Same as above, but with A approaching from the right instead.
        a = SweepLineEdgeInfo((0, 1), CrossingPoint(1, 0), CrossingPoint(0, -1))
        b = SweepLineEdgeInfo((2, 3), CrossingPoint(0, 1), CrossingPoint(0, -1))

        self.assertFalse(a.less_than(b, -1))
        self.assertTrue(b.less_than(a, -1))

    def test_less_than_never_mutually_true(self):
        random.seed(31415926535)

        for _ in range(0, 2000):
            a = SweepLineEdgeInfo(
                (0, 1),
                CrossingPoint(random.uniform(-10, 10), random.uniform(-10, 10)),
                CrossingPoint(random.uniform(-10, 10), random.uniform(-10, 10)),
            )
            b = SweepLineEdgeInfo(
                (2, 3),
                CrossingPoint(random.uniform(-10, 10), random.uniform(-10, 10)),
                CrossingPoint(random.uniform(-10, 10), random.uniform(-10, 10)),
            )
            y = random.uniform(-10, 10)

            self.assertFalse(
                a.less_than(b, y) and b.less_than(a, y),
                f"a={a}, b={b}, y={y} were reported as mutually less than each other",
            )

    def test_less_than_never_mutually_true_shared_endpoint(self):
        # Same as above, but every pair is forced to share its lower endpoint, which is
        # exactly the scenario that triggers the problematic tie-break.
        random.seed(271828182)

        shared_end = CrossingPoint(0, -1)
        for _ in range(0, 2000):
            a = SweepLineEdgeInfo(
                (0, 1),
                CrossingPoint(random.uniform(-10, 10), random.uniform(0, 10)),
                shared_end,
            )
            b = SweepLineEdgeInfo(
                (2, 3),
                CrossingPoint(random.uniform(-10, 10), random.uniform(0, 10)),
                shared_end,
            )

            self.assertFalse(
                a.less_than(b, -1) and b.less_than(a, -1),
                f"a={a}, b={b} were reported as mutually less than each other at the shared endpoint",
            )

    def test_remove_edges_sharing_endpoint_no_force_remove_needed(self):
        # A "fan" of edges all converging on the same point from various angles - a common
        # situation at the bottom of a sweep when several edges end at the same node.
        # Removing each of them exactly at that shared endpoint must always succeed without
        # falling back to force_remove.
        shared_end = CrossingPoint(0, -1)
        edges = [
            SweepLineEdgeInfo((i, i + 1), CrossingPoint(x, 1), shared_end)
            for i, x in enumerate([-5, -2, -1, -0.5, 0, 0.5, 1, 2, 5])
        ]

        s = SweepLineStatus()
        for edge in edges:
            s.add(1, edge)

        random.seed(112358132134)
        random.shuffle(edges)

        for edge in edges:
            size_before = len(s)
            s.remove(-1, edge)
            self.assertEqual(
                len(s),
                size_before - 1,
                f"remove() failed to find {edge} sharing the endpoint with its siblings",
            )

    def test_remove_edges_sharing_endpoint_stress(self):
        random.seed(998244353)

        for _ in range(0, 50):
            shared_end = CrossingPoint(
                random.uniform(-10, 10), random.uniform(-10, 10)
            )
            fan_size = random.randint(2, 20)
            edges = [
                SweepLineEdgeInfo(
                    (i, i + fan_size),
                    CrossingPoint(
                        random.uniform(-10, 10), shared_end.y + random.uniform(0, 10)
                    ),
                    shared_end,
                )
                for i in range(fan_size)
            ]

            s = SweepLineStatus()
            for edge in edges:
                s.add(shared_end.y + 1, edge)

            random.shuffle(edges)

            for edge in edges:
                size_before = len(s)
                s.remove(shared_end.y, edge)
                self.assertEqual(
                    len(s),
                    size_before - 1,
                    f"remove() failed for {edge} in a fan of size {fan_size} "
                    f"converging at {shared_end}",
                )

    # endregion

    def test_minimal_repro_no_force_remove_needed(self):
        # Regression test distilled from a real Bentley-Ottmann run (8-node graph with
        # several coincident nodes) where SweepLineStatus.remove() silently failed to find
        # edges that were genuinely still present, requiring force_remove as a workaround.
        # The root cause was the less_than() tie-break extrapolating past a shared endpoint
        # (see test_less_than_at_shared_endpoint_is_consistent): (2, 5) and (5, 7) end at the
        # exact same point, and the original tie-break gave their order incorrectly once the
        # sweep reached that point. This replays the add()/remove() calls observed during
        # that run, with every edge reordered at each crossing it takes part in (the caller's
        # responsibility per the SweepLineStatus contract - a separate, still-open gap in
        # crossings.py currently only reorders one edge per crossing, which is not exercised
        # here).
        edge_defs = {
            (0, 4): (0, 1, -1, -1),
            (0, 6): (0, 1, -1, -1),
            (0, 3): (0, 1, -1, -1),
            (0, 7): (0, 1, 0, -1),
            (0, 2): (0, 1, 0, -1),
            (2, 5): (-1, 0, 0, -1),
            (5, 7): (-1, 0, 0, -1),
            (4, 5): (-1, 0, -1, -1),
            (5, 6): (-1, 0, -1, -1),
            (1, 6): (0, 0, -1, -1),
            (1, 4): (0, 0, -1, -1),
            (1, 2): (0, 0, 0, -1),
            (1, 3): (0, 0, -1, -1),
            (1, 7): (0, 0, 0, -1),
        }
        ops = [
            ("add", 0.999999999, (0, 4)),
            ("add", 0.999999999, (0, 6)),
            ("add", 0.999999999, (0, 3)),
            ("add", 0.999999999, (0, 7)),
            ("add", 0.999999999, (0, 2)),
            ("add", -1e-09, (2, 5)),
            ("add", -1e-09, (5, 7)),
            ("add", -1e-09, (4, 5)),
            ("add", -1e-09, (5, 6)),
            ("remove", 0, (0, 4)),
            ("add", -1e-09, (0, 4)),
            ("remove", 0, (0, 6)),
            ("add", -1e-09, (0, 6)),
            ("remove", 0, (0, 3)),
            ("add", -1e-09, (0, 3)),
            ("remove", 0.0, (0, 7)),
            ("add", -1e-09, (0, 7)),
            ("remove", 0.0, (0, 2)),
            ("add", -1e-09, (0, 2)),
            ("add", -1e-09, (1, 6)),
            ("add", -1e-09, (1, 4)),
            ("add", -1e-09, (1, 2)),
            ("add", -1e-09, (1, 3)),
            ("add", -1e-09, (1, 7)),
            # Crossing at y=-1/3 between the (0,3)/(0,4)/(0,6) and (2,5)/(5,7) line groups -
            # every member on both sides has to be reordered.
            ("remove", 0, (2, 5)),
            ("remove", 0, (5, 7)),
            ("remove", 0, (0, 3)),
            ("remove", 0, (0, 4)),
            ("remove", 0, (0, 6)),
            ("add", -0.33333333433333334, (2, 5)),
            ("add", -0.33333333433333334, (5, 7)),
            ("add", -0.33333333433333334, (0, 3)),
            ("add", -0.33333333433333334, (0, 4)),
            ("add", -0.33333333433333334, (0, 6)),
            # Crossing at y=-0.5 between the (1,3)/(1,4)/(1,6) and (2,5)/(5,7) line groups.
            ("remove", -0.3333333333333333, (2, 5)),
            ("remove", -0.3333333333333333, (5, 7)),
            ("remove", -0.3333333333333333, (1, 3)),
            ("remove", -0.3333333333333333, (1, 4)),
            ("remove", -0.3333333333333333, (1, 6)),
            ("add", -0.500000001, (2, 5)),
            ("add", -0.500000001, (5, 7)),
            ("add", -0.500000001, (1, 3)),
            ("add", -0.500000001, (1, 4)),
            ("add", -0.500000001, (1, 6)),
            # Final endpoint removals.
            ("remove", -0.5, (1, 6)),
            ("remove", -0.5, (1, 4)),
            ("remove", -0.5, (0, 4)),
            ("remove", -0.5, (0, 6)),
            ("remove", -0.5, (0, 3)),
            ("remove", -0.5, (5, 6)),
            ("remove", -0.5, (4, 5)),
            ("remove", -0.5, (1, 3)),
            ("remove", -1, (0, 2)),
            ("remove", -1, (2, 5)),
            ("remove", -1, (1, 2)),
            ("remove", -1, (5, 7)),
            ("remove", -1, (0, 7)),
            ("remove", -1, (1, 7)),
        ]

        previous_precision = numeric.get_precision()
        numeric.set_precision(1e-09)
        try:
            edges = {
                key: SweepLineEdgeInfo(
                    key, CrossingPoint(ax, ay), CrossingPoint(bx, by)
                )
                for key, (ax, ay, bx, by) in edge_defs.items()
            }

            s = SweepLineStatus()
            for op, y, key in ops:
                if op == "add":
                    s.add(y, edges[key])
                else:
                    size_before = len(s)
                    s.remove(y, edges[key])
                    self.assertEqual(
                        len(s),
                        size_before - 1,
                        f"remove({y}, {key}) needed force_remove",
                    )

            self.assertEqual(len(s), 0)
        finally:
            numeric.set_precision(previous_precision)
