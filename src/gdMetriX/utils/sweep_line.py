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
from abc import ABC, abstractmethod
from enum import Enum
from typing import (
    Tuple,
    Self,
    Set,
    SupportsIndex,
    Dict,
    List,
    Optional,
    Iterable,
    Generic,
    TypeVar,
)

from gdMetriX.common import Vector, Numeric, LineSegment
from gdMetriX.utils.avl_tree import (
    SortableObject,
    ParameterizedBalancedBinarySearchTree,
)
from gdMetriX.utils import numeric
from gdMetriX.utils.numeric import numeric_eq, greater_than


class CrossingPoint(Vector):
    # TODO make this also a tuple type or provide cast method
    """
    Represents a point used during the crossing detection algorithm, not necessarily an actual crossing.
    Supports total ordering according to sweep line direction.
    """

    def __eq__(self, other: Vector):
        if other is None or not isinstance(other, CrossingPoint):
            return False
        # Inlined implementation as numeric_eq(distance, 0)
        diff_x = self.x - other.x
        diff_y = self.y - other.y
        return math.sqrt(diff_x**2 + diff_y**2) <= numeric.PRECISION

    @staticmethod
    def from_point(pos: Tuple[Numeric, Numeric]) -> Self:
        vec = Vector.from_point(pos)
        return CrossingPoint(vec.x, vec.y)

    def __lt__(self, other):
        if isinstance(other, CrossingPoint):
            precision = numeric.PRECISION
            if not math.isclose(self.y, other.y, abs_tol=precision):
                return self.y > other.y
            return (
                not math.isclose(other.x, self.x, abs_tol=precision)
                and other.x > self.x
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
            return self.start < other.start or (
                self.start == other.start and self.end < other.end
            )
        if isinstance(other, CrossingPoint):
            return False
        raise TypeError(other)

    def __eq__(self, other):
        return self.start == other.start and self.end == other.end

    def __str__(self):
        return f"Line({self.start}, {self.end})"


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
        # The line through the edge as used by get_x_at_y, with the precision it was computed
        # for: (precision, x if vertical or horizontal else None, slope, intercept)
        self._line = None

    @staticmethod
    def from_edge(
        edge: Tuple[SupportsIndex, SupportsIndex], pos: Dict[object, CrossingPoint]
    ) -> Self:
        """
        Builds the SweepLineEdgeInfo from the given edge tuple
        :param edge: Edge from the graph
        :type edge: Tuple[SupportsIndex, SupportsIndex]
        :param pos: Node position dictionary to look up the endpoints of the edge
        :type pos: Dict[object, CrossingPoint]
        :return: The SweepLineEdgeInfo build from the given edge
        :rtype: SweepLineEdgeInfo
        """
        point_a = pos[edge[0]]
        point_b = pos[edge[1]]

        return SweepLineEdgeInfo(
            edge,
            CrossingPoint(point_a[0], point_a[1]),
            CrossingPoint(point_b[0], point_b[1]),
        )

    # region Implementation of SortableObject

    # The comparisons below run millions of times while sweeping, so they inline numeric_eq and
    # greater_than rather than calling them. They decide exactly as those do.

    def less_than(self, other: Self, key_parameter: Numeric):
        x_self = get_x_at_y(self, key_parameter)
        x_other = get_x_at_y(other, key_parameter)
        precision = numeric.PRECISION

        if math.isclose(x_self, x_other, abs_tol=precision):
            # Break the tie by looking at the order slightly off key_parameter. For two
            # straight, non-identical lines the sign of (x_self - x_other) is constant on
            # either side of their unique intersection, so jumping all the way down to
            # the shorter of the two segment ends is a safe (and numerically robust) way
            # to escape the tie - as long as that point still lies on or below both lines.
            # If both lines already end at (or before) key_parameter - e.g. two edges
            # sharing an endpoint, compared exactly at that shared point - there is no
            # valid spot below to probe, so look slightly above instead, where both lines
            # are guaranteed to still exist.
            lower_end = min(self.end_position.y, other.end_position.y)

            if (
                not math.isclose(key_parameter, lower_end, abs_tol=precision)
                and key_parameter > lower_end
            ):
                probe = lower_end
            else:
                probe = key_parameter + 100 * precision

            x_self = get_x_at_y(self, probe)
            x_other = get_x_at_y(other, probe)

        # greater_than(x_other, x_self)
        return not math.isclose(x_other, x_self, abs_tol=precision) and x_other > x_self

    def less_than_key(self, key: Numeric, y: Numeric):
        x_self = get_x_at_y(self, y)
        # greater_than(key, x_self)
        return not math.isclose(key, x_self, abs_tol=numeric.PRECISION) and key > x_self

    def greater_than_key(self, key: Numeric, y: Numeric):
        x_self = get_x_at_y(self, y)
        # greater_than(x_self, key)
        return not math.isclose(x_self, key, abs_tol=numeric.PRECISION) and x_self > key

    def get_key(self, key_parameter: Numeric) -> Numeric:
        return get_x_at_y(self, key_parameter)

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
        return numeric_eq(
            self.start_position.y, self.end_position.y
        ) and not numeric_eq(self.start_position.x, self.end_position.x)

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
        self.singletons: Set[object] = set()
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
        return self.position < other.position

    # endregion


# endregion


# region Event queue and sweep line status


class _EventType(Enum):
    """Simple enum for distinguishing in which scenario an edge is introduced"""

    START = 1
    END = 2
    CROSSING = 3
    HORIZONTAL = 4


class EventQueue:
    """
    An event queue ordering SweepLinePoints by their total order.
    For each point, a list of edges added to that point can be stored.
    """

    def __init__(self) -> None:
        self.sorted_list = ParameterizedBalancedBinarySearchTree(greater_than)

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
            _EventType.HORIZONTAL if edge_info.is_horizontal() else _EventType.START,
        )
        self._add(
            edge_info.end_position,
            edge_info,
            _EventType.HORIZONTAL if edge_info.is_horizontal() else _EventType.END,
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
                    self._add(crossing, edge, _EventType.HORIZONTAL)
                else:
                    self._add(crossing, edge, _EventType.CROSSING)

    def add_singleton(self, point: CrossingPoint, node: object) -> None:
        """
        Adds a singleton to the queue. If there is already an event point with the same position,
        the new event point will be added to the existing event point.
        :param point: Position of the singleton
        :type point: CrossingPoint
        :param node: Index of the node of the networkX graph
        :type node: object
        :return: None
        :rtype: None
        """
        sweep_line_point = self._find(point)
        if sweep_line_point is None:
            sweep_line_point = SweepLinePoint(point)
            self.sorted_list.insert(sweep_line_point, None)
        sweep_line_point.singletons.add(node)

    def _find(self, position: CrossingPoint) -> Optional[SweepLinePoint]:
        """
        Returns the event point at the given position, or None if there is none.

        This is ParameterizedBalancedBinarySearchTree.find for event points, with
        SweepLinePoint.__eq__ / less_than - and the CrossingPoint comparisons behind them -
        inlined: it visits the same nodes and decides exactly as they do. Adding an event looks
        its position up first, which makes this one of the hottest paths of the sweep.
        """
        precision = numeric.PRECISION
        isclose = math.isclose
        sqrt = math.sqrt
        px = position.x
        py = position.y

        def _find_recursive(node):
            while node is not None:
                r = node.content.position
                rx = r.x
                ry = r.y

                # node.content == item: CrossingPoint.__eq__(r, position)
                diff_x = rx - px
                diff_y = ry - py
                if sqrt(diff_x**2 + diff_y**2) <= precision:
                    return node

                # node.content.less_than(item) and item.less_than(node.content):
                # CrossingPoint.__lt__ both ways. isclose is symmetric, so it is evaluated once.
                if not isclose(ry, py, abs_tol=precision):
                    node_less = ry > py
                    item_less = py > ry
                else:
                    x_close = isclose(px, rx, abs_tol=precision)
                    node_less = not x_close and px > rx
                    item_less = not x_close and rx > px

                if node_less and not item_less:
                    node = node.right
                elif item_less and not node_less:
                    node = node.left
                else:
                    # Tied, see ParameterizedBalancedBinarySearchTree.find
                    found = _find_recursive(node.left)
                    if found is not None:
                        return found
                    node = node.right
            return None

        found_node = _find_recursive(self.sorted_list.root)
        return None if found_node is None else found_node.content

    def _add(
        self, point: CrossingPoint, edge_info: SweepLineEdgeInfo, event_type: _EventType
    ) -> None:

        sweep_line_point = self._find(point)
        if sweep_line_point is None:
            sweep_line_point = SweepLinePoint(point)
            self.sorted_list.insert(sweep_line_point, None)

        list_to_add_to = None
        if event_type == _EventType.START:
            list_to_add_to = sweep_line_point.start_list
        elif event_type == _EventType.END:
            list_to_add_to = sweep_line_point.end_list
        elif event_type == _EventType.CROSSING:
            list_to_add_to = sweep_line_point.interior_list
            sweep_line_point.is_crossing = True
        elif event_type == _EventType.HORIZONTAL:
            list_to_add_to = sweep_line_point.horizontal_list

        list_to_add_to.add(edge_info)

    def pop(self) -> Optional[SweepLinePoint]:
        """
            Removes the next element in the queue
        :return: Either the next element or none
        :rtype:
        """
        return self.sorted_list.pop()

    def __str__(self) -> str:
        return f"Queue[{','.join(map(str, self.sorted_list))}]"

    def __repr__(self) -> str:
        return self.__str__()


class SweepLineStatus:
    """
    Stores all edges in order from left to right as they intersect the sweep line.
    Note that when the height changes, edges with changing order have to be explicitly deleted and reinserted.
    """

    def __init__(self):
        self.sorted_list = ParameterizedBalancedBinarySearchTree(greater_than)

    def __str__(self):
        return [edge.edge for edge in self.sorted_list].__str__()

    def __len__(self):
        return len(self.sorted_list)

    def add(self, y_value: Numeric, edge_info: SweepLineEdgeInfo) -> None:
        """Adds a new edge to the sweep line. It will be added next to its neighboring edges at height y_value.
        :param y_value: Current height of the sweep line
        :type y_value:
        :param edge_info:
        :type edge_info:
        """
        self.sorted_list.insert(edge_info, y_value)

    def remove(self, y_value: Numeric, edge_info: SweepLineEdgeInfo) -> None:
        """
        Removes an edge from the sweep line.
        :param y_value:
        :type y_value:
        :param edge_info: Edge that should be removed
        :type edge_info: :class:`SweepLineEdgeInfo`
        """
        self.sorted_list.remove(edge_info, y_value)

    def force_remove(self, edge_info: SweepLineEdgeInfo) -> None:
        """
        Remove all instances of the given edge from the sweep line.
        :param edge_info: Edge that should be removed
        :type edge_info: :class:`SweepLineEdgeInfo`
        """
        self.sorted_list.force_remove(edge_info)

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
        # ParameterizedBalancedBinarySearchTree.get_range for edges, with get_key, less_than_key,
        # greater_than_key and the tree's greater_than inlined: it visits the same nodes and
        # decides exactly as they do. Every event queries the status, often several times.
        precision = numeric.PRECISION
        isclose = math.isclose
        start_key = left_x
        end_key = right_x
        result: List[SweepLineEdgeInfo] = []

        def _overlaps(current_start, current_end) -> bool:
            # _range_overlaps, with greater_than(a, b) = not isclose(a, b) and a > b
            if (
                not isclose(current_start, current_end, abs_tol=precision)
                and current_start > current_end
            ):
                return False
            return not (
                not isclose(start_key, current_end, abs_tol=precision)
                and start_key > current_end
            ) and not (
                not isclose(current_start, end_key, abs_tol=precision)
                and current_start > end_key
            )

        def _get_range_recursive(node, current_start, current_end) -> None:
            content = node.content
            root_key = get_x_at_y(content, y)

            if node.left is not None:
                new_end = min(current_end, root_key)
                if _overlaps(current_start, new_end):
                    _get_range_recursive(node.left, current_start, new_end)

            # not less_than_key(start_key) and not greater_than_key(end_key), where
            # less_than_key(k) = greater_than(k, x) and greater_than_key(k) = greater_than(x, k)
            # for x = get_x_at_y(content, y) = root_key
            x = root_key
            if not (
                not isclose(start_key, x, abs_tol=precision) and start_key > x
            ) and not (not isclose(x, end_key, abs_tol=precision) and x > end_key):
                result.append(content)

            if node.right is not None:
                new_start = max(current_start, root_key)
                if _overlaps(new_start, current_end):
                    _get_range_recursive(node.right, new_start, current_end)

        if self.sorted_list.root is not None:
            _get_range_recursive(self.sorted_list.root, start_key, end_key)

        return result


# endregion


# region Generic sweep line algorithm runner


TEvent = TypeVar("TEvent")
TResult = TypeVar("TResult")


class SweepLineAlgorithm(Generic[TEvent, TResult], ABC):
    """
    Base class for sweep line algorithms.

    Encapsulates the part that is genuinely shared between sweep line algorithms:
    a :class:`SweepLineStatus` holding the elements currently intersecting the
    sweep line, and the driving loop that repeatedly pops the next event and
    hands it to the subclass.

    Subclasses are deliberately free to choose their own event source (e.g. a
    dynamic :class:`EventQueue` for algorithms that discover new events while
    running, or a simple pre-sorted sequence for algorithms whose events are
    all known upfront) - only ``status`` and the loop itself are shared.
    """

    def __init__(self):
        self.status = SweepLineStatus()

    def run(self) -> TResult:
        """
            Runs the sweep line algorithm to completion and returns its result.
        :return: The result of the algorithm, as produced by :meth:`_finalize`.
        :rtype: TResult
        """
        self._build_events()

        event = self._pop_event()
        while event is not None:
            self._handle_event(event)
            event = self._pop_event()

        return self._finalize()

    @abstractmethod
    def _build_events(self) -> None:
        """Populates the initial event source."""

    @abstractmethod
    def _pop_event(self) -> Optional[TEvent]:
        """
            Returns and removes the next event in sweep order.
        :return: The next event, or None if no events remain.
        :rtype: Optional[TEvent]
        """

    @abstractmethod
    def _handle_event(self, event: TEvent) -> None:
        """Processes a single event against ``self.status``."""

    def _finalize(self) -> TResult:
        """Returns the final result once all events have been processed."""
        return None


# endregion


def get_x_at_y(edge_info: SweepLineEdgeInfo, y: Numeric) -> Numeric:
    """
    Returns the x value at the specified y value for the line build from the edge_info.
    :param edge_info: Edge that defines the line.
    :type edge_info: SweepLineEdgeInfo
    :param y: Height to measure the x value at
    :type y: Numeric
    :return: X value
    :rtype: Numeric
    """
    precision = numeric.PRECISION
    line = edge_info._line

    # The line only depends on the edge and the precision, so it is computed once per edge
    # rather than on every call - with the exact same arithmetic, so the results are the same.
    if line is None or line[0] != precision:
        start = edge_info.start_position
        end = edge_info.end_position

        if math.isclose(start.x, end.x, abs_tol=precision):
            line = (precision, start.x, None, None)
        elif math.isclose(end.y - start.y, 0, abs_tol=precision):
            line = (precision, min(start.x, end.x), None, None)
        else:
            m = (end.y - start.y) / (end.x - start.x)
            b = start.y - m * start.x
            line = (precision, None, m, b)

        edge_info._line = line

    if line[1] is not None:
        return line[1]

    return (y - line[3]) / line[2]
