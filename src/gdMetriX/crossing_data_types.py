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
Supporting module for the crossings module containing some datastructures.
"""

import math
from enum import Enum
from typing import (
    List,
    Optional,
    Iterable,
    Union,
    Self,
    Tuple,
    SupportsIndex,
    Set,
    Dict,
)

from gdMetriX.common import Numeric, Vector, LineSegment
from gdMetriX.utils.avl_tree import (
    SortableObject,
    ParameterizedBalancedBinarySearchTree,
)

PRECISION = 1e-09


def set_precision(precision: float) -> None:
    """
        Sets the global precision used for all calculation. Any two numbers with a difference smaller than `precision`
         are considered as equal
    :param precision: Precision
    :type precision: float
    """
    global PRECISION
    PRECISION = precision


def _get_precision() -> float:
    global PRECISION
    return PRECISION


class CrossingPoint(Vector):
    """
    Represents a point used during the crossing detection algorithm, not necessarely an actuall crossing.
    Supports total ordering according to sweep line direction.
    """

    def __eq__(self, other: Vector):
        if other is None or not isinstance(other, CrossingPoint):
            return False
        return _numeric_eq(self.distance(other), 0)

    @staticmethod
    def from_point(pos: Tuple[Numeric, Numeric]) -> Self:
        vec = Vector.from_point(pos)
        return CrossingPoint(vec.x, vec.y)

    def __lt__(self, other):
        if isinstance(other, CrossingPoint):
            return _greater_than(self.y, other.y) or (
                _numeric_eq(self.y, other.y) and _greater_than(other.x, self.x)
            )
        if isinstance(other, CrossingLine):
            return True
        raise TypeError(other)

    def __hash__(self):
        return hash(
            (
                self.x,
                self.y,
            )
        )


class CrossingLine(LineSegment):
    """
    Represents a line segment used during the crossing detection algorithm.
    Supports total ordering according to sweep line direction.
    """

    start: CrossingPoint
    end: CrossingPoint

    def __init__(self, point_a: CrossingPoint, point_b: CrossingPoint):
        self.start, self.end = sorted([point_a, point_b])
        super().__init__(self.start, self.end)

    def __lt__(self, other):
        if isinstance(other, CrossingLine):
            return self.start < other.start or self.end < other.end
        if isinstance(other, CrossingPoint):
            return False
        raise TypeError(other)

    def __eq__(self, other):
        return self.start == other.start and self.end == other.end

    def __str__(self):
        return f"Line({self.start}, {self.end})"


def _greater_than(a: float, b: float) -> bool:
    if _numeric_eq(a, b):
        return False

    return a > b


def _numeric_eq(a: Numeric, b: Numeric) -> bool:
    return math.isclose(a, b, abs_tol=PRECISION)


class Crossing:
    """
    Represents a single crossing point
    """

    def __init__(self, pos: Union[CrossingPoint, CrossingLine], involved_edges: set):
        self.pos = pos
        self.involved_edges = involved_edges

    def __str__(self):
        return f"[{self.pos}, edges: {sorted(self.involved_edges)}]"

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        if isinstance(other, Crossing):
            return self.pos == other.pos and self.involved_edges == other.involved_edges
        return False

    def __lt__(self, other):
        # Comparison purely based on CrPoint/CrLineSegment
        return self.pos < other.pos


class EventType(Enum):
    """Simple enum for distinguishing in which scenario an edge is introduced"""

    START = 1
    END = 2
    CROSSING = 3
    HORIZONTAL = 4


# region Edge and point classes for insertion into AVL tree


class SweepLineEdgeInfo(SortableObject):
    """
    Represents an edge within the sweep line. Supports basic properties for comparison
    """

    start_position: CrossingPoint
    end_position: CrossingPoint

    def __init__(
        self,
        edge: (object, object),
        position_a: CrossingPoint,
        position_b: CrossingPoint,
    ):
        self.edge = edge
        self.crossing_line = CrossingLine(position_a, position_b)
        self.start_position = self.crossing_line.start
        self.end_position = self.crossing_line.end

    @staticmethod
    def from_edge(
        edge: Tuple[SupportsIndex, SupportsIndex], pos: Dict[object, CrossingPoint]
    ) -> Self:
        point_a = pos[edge[0]]
        point_b = pos[edge[1]]

        return SweepLineEdgeInfo(
            edge,
            CrossingPoint(point_a[0], point_a[1]),
            CrossingPoint(point_b[0], point_b[1]),
        )

    # region Implementation of SortableObject

    def less_than(self, other: Self, key_parameter: Numeric):
        x_self = _get_x_at_y(self, key_parameter)
        x_other = _get_x_at_y(other, key_parameter)

        if _numeric_eq(x_self, x_other):
            lower_end = min(self.end_position.y, other.end_position.y)
            key_parameter = min(key_parameter - _get_precision(), lower_end)

            x_self = _get_x_at_y(self, key_parameter)
            x_other = _get_x_at_y(other, key_parameter)

        return _greater_than(x_other, x_self)

    def less_than_key(self, key: Numeric, y: Numeric):
        x_self = _get_x_at_y(self, y)

        return _greater_than(key, x_self)

    def greater_than_key(self, key: Numeric, y: Numeric):
        x_self = _get_x_at_y(self, y)
        return _greater_than(x_self, key)

    def get_key(self, key_parameter: Numeric) -> Numeric:
        return _get_x_at_y(self, key_parameter)

    # endregion

    def __str__(self):
        return f"[{self.edge}, start: {self.start_position}, end: {self.end_position}]"

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        if other is None or not isinstance(other, SweepLineEdgeInfo):
            return False
        return (
            self.edge == other.edge
            and self.start_position == other.start_position
            and self.end_position == other.end_position
        )

    def __hash__(self):
        return hash((self.edge, self.start_position, self.end_position))

    def is_horizontal(self) -> bool:
        """
            Returns true if and only if the edge is considered to be horizontal
        :return:
        :rtype:
        """
        return _numeric_eq(
            self.start_position.y, self.end_position.y
        ) and not _numeric_eq(self.start_position.x, self.end_position.x)

    def share_endpoint(self, other) -> bool:
        """
            Checks if the two edges have at least one node in common
        :param other: The second edge
        :type other: gdMetriX.SweepLineEdgeInfo
        :return: Returns true if and only if one ore more nodes are shared between the edges
        :rtype: bool
        """
        return (
            self.edge[0] == other.edge[0]
            or self.edge[0] == other.edge[1]
            or self.edge[1] == other.edge[0]
            or self.edge[1] == other.edge[1]
        )


class SweepLinePoint(SortableObject):
    """
    Represents a point on the event queue
    """

    def __init__(self, position: CrossingPoint):
        self.end_list: Set[SweepLineEdgeInfo] = set()
        self.start_list: Set[SweepLineEdgeInfo] = set()
        self.interior_list: Set[SweepLineEdgeInfo] = set()
        self.horizontal_list: Set[SweepLineEdgeInfo] = set()
        self.position: CrossingPoint = position
        self.is_crossing: bool = False

    def __str__(self):
        return self.position.__str__()

    def __eq__(self, other):
        if other is None:
            return False
        return self.position == other.position

    def __lt__(self, other):
        return self.position < other.position

    # region Implementation of SortableObject

    def less_than(self, other: Self, _):
        return self < other

    # endregion


# endregion


# region Event queue and sweep line status


class EventQueue:
    """
    An event queue ordering SweepLinePoints by their total order.
    For each point, a list of edges added to that point can be stored.
    """

    def __init__(self) -> None:
        self.sorted_list = ParameterizedBalancedBinarySearchTree(_greater_than)

    def __len__(self) -> int:
        return len(self.sorted_list)

    def add_edge(self, edge_info: SweepLineEdgeInfo) -> None:
        """
        Adds a new event Point to the queue.
        :param edge_info:
        :type edge_info:
        """
        self._add(
            edge_info.start_position,
            edge_info,
            EventType.HORIZONTAL if edge_info.is_horizontal() else EventType.START,
        )
        self._add(
            edge_info.end_position,
            edge_info,
            EventType.HORIZONTAL if edge_info.is_horizontal() else EventType.END,
        )

    def add_crossing(
        self, crossing: CrossingPoint, edge_list: List[SweepLineEdgeInfo]
    ) -> None:
        """
        Adds a new event point to the queue. If there is already an event point with the same position,
        the new event point will be added to the existing event point.
        :param crossing:
        :type crossing:
        :param edge_list: List of edges involved in the crossing
        :type edge_list: List[SweepLineEdgeInfo]
        :return: None
        :rtype: None
        """
        assert len(edge_list) >= 2

        for edge in edge_list:
            # If the edge only crosses in an endpoint, it will not be added as an "interior point"
            if crossing not in (edge.start_position, edge.end_position):
                if edge.is_horizontal():
                    self._add(crossing, edge, EventType.HORIZONTAL)
                else:
                    self._add(crossing, edge, EventType.CROSSING)

    def _add(
        self, point: CrossingPoint, edge_info: SweepLineEdgeInfo, event_type: EventType
    ) -> None:

        new_point_to_add = SweepLinePoint(point)

        sweep_line_point = self.sorted_list.find(new_point_to_add, None)
        if sweep_line_point is None:
            sweep_line_point = new_point_to_add
            self.sorted_list.insert(sweep_line_point, None)

        list_to_add_to = None
        if event_type == EventType.START:
            list_to_add_to = sweep_line_point.start_list
        elif event_type == EventType.END:
            list_to_add_to = sweep_line_point.end_list
        elif event_type == EventType.CROSSING:
            list_to_add_to = sweep_line_point.interior_list
            sweep_line_point.is_crossing = True
        elif event_type == EventType.HORIZONTAL:
            list_to_add_to = sweep_line_point.horizontal_list

        list_to_add_to.add(edge_info)

    def pop(self) -> Optional[SweepLinePoint]:
        """
            Removes the next element in the queue
        :return: Either the next element or none
        :rtype:
        """
        return self.sorted_list.pop()


def _get_x_at_y(edge_info: SweepLineEdgeInfo, y: Numeric):
    start = edge_info.start_position
    end = edge_info.end_position

    if _numeric_eq(start.x, end.x):
        return start.x
    if _numeric_eq(end.y - start.y, 0):
        return min(start.x, end.x)

    m = (end.y - start.y) / (end.x - start.x)
    b = start.y - m * start.x

    return (y - b) / m


class SweepLineStatus:
    """
    Stores all edges in order from left to right as they intersect the sweep line.
    Note that when the height changes, edges with changing order have to be explicitly deleted and reinserted.
    """

    def __init__(self):
        self.sorted_list = ParameterizedBalancedBinarySearchTree(_greater_than)

    def __str__(self):
        return [edge.edge for edge in self.sorted_list].__str__()

    def add(self, y_value: Numeric, edge_info: SweepLineEdgeInfo) -> None:
        """Adds a new edge to the sweep line. It will be added next to its neighboring edges at height y_value.
        :param y_value: Current height of the sweep line
        :type y_value:
        :param edge_info:
        :type edge_info:
        """
        self.sorted_list.insert(edge_info, y_value)

    def remove(self, y_value: Numeric, edge_info: SweepLineEdgeInfo):
        """
        Removes an edge from the sweep line.
        :param y_value:
        :type y_value:
        :param edge_info: Edge that should be removed
        :type edge_info: :class:`SweepLineEdgeInfo`
        """
        self.sorted_list.remove(edge_info, y_value)

    def get_left(self, point: SweepLinePoint) -> Optional[SweepLineEdgeInfo]:
        """
        Returns the edge left of the given edge. If no such edge exists, none is returned
        :param point: Query point
        :type point: SweepLinePoint
        :return: Edge left of the given edge
        :rtype: SweepLineEdgeInfo
        """
        return self.sorted_list.get_left(point.position.x, point.position.y)

    def get_right(self, point: SweepLinePoint) -> Optional[SweepLineEdgeInfo]:
        """
        Returns the edge right of the given edge. If no such edge exists, none is returned
        :return: Edge right of the given edge
        :rtype: SweepLineEdgeInfo
        """
        return self.sorted_list.get_right(point.position.x, point.position.y)

    def get_range(
        self, y: Numeric, left_x: Numeric, right_x: Numeric
    ) -> Iterable[SweepLineEdgeInfo]:
        """
            Returns all matching edges in range [left_x, right_x]
        :param y:
        :type y:
        :param left_x:
        :type left_x:
        :param right_x:
        :type right_x:
        """
        return self.sorted_list.get_range(left_x, right_x, y)


# endregion
