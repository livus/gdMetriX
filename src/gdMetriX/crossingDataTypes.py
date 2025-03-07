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


# TODO move AVL tree to new file

# region AVL tree


class SortableObject:
    """Represents an object to be inserted in the ParameterizedBalancedBinarySearchTree.
    The item is comparable with a parameter. The comparison does not have to build a total order.
    """

    def less_than(self, other, key_parameter: Numeric) -> bool:
        """
            Returns true iff the object is strictly less than the other one.
        :param other: The object to compare too
        :type other: SortableObject
        :param key_parameter: Parameter for comparison
        :type key_parameter: numeric
        """

    def less_than_key(self, key: Numeric, key_parameter: Numeric) -> bool:
        """
            Returns true iff the object is strictly less than the other one.
        :param key: The key of the object to compare too
        :type key: numeric
        :param key_parameter: Parameter for comparison
        :type key_parameter: numeric
        """

    def greater_than_key(self, key: Numeric, key_parameter: Numeric) -> bool:
        """
            Returns true iff the object is strictly greater than the other one.
        :param key: The key of the object to compare too
        :type key: numeric
        :param key_parameter: Parameter for comparison
        :type key_parameter: numeric
        """

    def get_key(self, key_parameter: Numeric) -> Numeric:
        """
            Returns the key under the given parameter
        :param key_parameter:
        :type key_parameter:
        :return:
        :rtype:
        """


class BBTNode:
    """
    Node for the ParameterizedBalancedBinarySearchTree
    """

    def __init__(self, content):
        self.content = content
        self.left = None
        self.right = None
        self.height = 1


class ParameterizedBalancedBinarySearchTree:
    """
    An AVL tree, where the key can be parameterized (i.e. the keys of the inserted elements depend on an parameter).
    Note that, even though the parameter for the keys might change throughout, whenever the order might change with
    a change in the parameter, all objects with a change in order will have to be deleted and reinserted to be
    placed into their correct spot.
    """

    def __init__(self):
        self.root = None
        self._length = 0

    def _update_height(self, root):
        root.height = 1 + max(
            self._get_height(root.left), self._get_height(root.right)
        )

    def insert(self, item: SortableObject, key_parameter: object) -> None:
        """
            Inserts a new item into the tree.
        :param item: Item to be inserted.
        :type item: SortableObject
        :param key_parameter: Parameter for the keys
        :type key_parameter: object
        :return: None
        :rtype: None
        """

        def _insert_recursive(root: BBTNode) -> BBTNode:

            if root is None:
                root = BBTNode(item)
                return root

            if root.content.less_than(item, key_parameter):
                root.right = _insert_recursive(root.right)
            else:
                root.left = _insert_recursive(root.left)

            self._update_height(root)

            balance = self._get_balance(root)
            if balance > 1:
                # Tree is unbalanced with longer side on the left

                if not root.left.content.less_than(item, key_parameter):
                    return self._right_rotate(root)
                root.left = self._left_rotate(root.left)
                return self._right_rotate(root)
            if balance < -1:
                # Tree is unbalanced with longer side on the right

                if root.right.content.less_than(item, key_parameter):
                    return self._left_rotate(root)
                root.right = self._right_rotate(root.right)
                return self._left_rotate(root)

            return root

        self.root = _insert_recursive(self.root)
        self._length += 1

    def _left_rotate(self, node: BBTNode) -> BBTNode:
        old_right = node.right
        old_left = old_right.left

        # Rotate
        old_right.left = node
        node.right = old_left

        # Update changed heights
        node.height = 1 + max(
            self._get_height(node.left), self._get_height(node.right)
        )
        old_right.height = 1 + max(
            self._get_height(old_right.left), self._get_height(old_right.right)
        )

        return old_right

    def _right_rotate(self, node: BBTNode) -> BBTNode:
        old_left = node.left
        old_right = old_left.right

        # Rotate
        old_left.right = node
        node.left = old_right

        # Update changed heights
        node.height = 1 + max(
            self._get_height(node.left), self._get_height(node.right)
        )
        old_left.height = 1 + max(
            self._get_height(old_left.left), self._get_height(old_left.right)
        )

        return old_left

    @staticmethod
    def _get_height(root):
        if root is None:
            return 0
        return root.height

    def _get_balance(self, root):
        if root is None:
            return 0
        return self._get_height(root.left) - self._get_height(root.right)

    def get_left(
        self, key_value: Numeric, key_parameter: object
    ) -> Optional[SortableObject]:
        """
            Returns the next element to the left of the key specified by 'key_value'. Elements having the key
            'key_value' are not considered - only elements strictly left of 'key_value'.
        :param key_value: Key to look up
        :type key_value: numeric
        :param key_parameter: Parameter for parameterized key look up
        :type key_parameter: object
        :return: The element directly left of the given key. None if there is no such element.
        :rtype: Optional[object]
        """

        def _get_left_recursive(root) -> Optional[BBTNode]:

            if root is None:
                return None

            # Get candidate from children
            if root.content.less_than_key(key_value, key_parameter):
                candidate = _get_left_recursive(root.right)
            else:
                candidate = _get_left_recursive(root.left)

            # Check if current root is a better candidate
            if root.content.less_than_key(key_value, key_parameter):
                if candidate is None or candidate.content.less_than(
                    root.content, key_parameter
                ):
                    return root

            return candidate

        left_node = _get_left_recursive(self.root)
        return None if left_node is None else left_node.content

    def get_right(
        self, key_value: Numeric, key_parameter: object
    ) -> Optional[SortableObject]:
        """
            Returns the next element to the right of the key specified by 'key_value'. Elements having the key
            'key_value' are not considered - only elements strictly right of 'key_value'.
        :param key_value: Key to look up
        :type key_value: numeric
        :param key_parameter: Parameter for parameterized key look up
        :type key_parameter: object
        :return: The element directly right of the given key. None if there is no such element.
        :rtype: Optional[object]
        """

        def _get_right_recursive(root: BBTNode) -> Optional[BBTNode]:

            if root is None:
                return None

            # Get candidate from children
            if not root.content.greater_than_key(key_value, key_parameter):
                candidate = _get_right_recursive(root.right)
            else:
                candidate = _get_right_recursive(root.left)

            # Check if current root is a better candidate
            if root.content.greater_than_key(key_value, key_parameter):
                if candidate is None or root.content.less_than(
                    candidate.content, key_parameter
                ):
                    return root

            return candidate

        right_node = _get_right_recursive(self.root)
        return None if right_node is None else right_node.content

    def _get_min(self, root: BBTNode) -> Optional[BBTNode]:
        if root is None or root.left is None:
            return root
        return self._get_min(root.left)

    def get_min(self) -> Optional[SortableObject]:
        """
            Finds the minimum element present.
        :return: The minimum element.
        :rtype: Optional[SortableObject]
        """

        min_element = self._get_min(self.root)
        if min_element is None:
            return None
        return min_element.content

    def remove(self, item: SortableObject, key_parameter: object) -> None:
        """
            Removes the item from the tree - if it is present.
        :param item: Item to be removed
        :type item: SortableObject
        :param key_parameter: Parameter for the keys
        :type key_parameter: object
        :return: None
        :rtype: None
        """
        found_item = False

        def _remove_recursive(root: BBTNode, value: object) -> Optional[BBTNode]:
            nonlocal found_item

            if root is None:
                return None

            if value == root.content:
                # We have found the actual root that should be deleted
                found_item = True

                # If either the left or right is None, we can simply move the node one up
                if root.left is None:
                    return root.right
                if root.right is None:
                    return root.left

                # Move min up and delete min down the road
                temp = self._get_min(root.right)
                root.content = temp.content
                root.right = _remove_recursive(root.right, temp.content)
            else:
                if not root.content.less_than(value, key_parameter):
                    root.left = _remove_recursive(root.left, value)
                else:
                    root.right = _remove_recursive(root.right, value)

            self._update_height(root)

            # Rebalancing
            balance = self._get_balance(root)

            if balance > 1:
                if self._get_balance(root.left) >= 0:
                    return self._right_rotate(root)
                root.left = self._left_rotate(root.left)
                return self._right_rotate(root)
            if balance < -1:
                if self._get_balance(root.right) <= 0:
                    return self._left_rotate(root)
                root.right = self._right_rotate(root.right)
                return self._left_rotate(root)

            return root

        if found_item:
            self._length -= 1

        self.root = _remove_recursive(self.root, item)

    def __len__(self) -> int:
        return self._length

    def __iter__(self):
        def _list_recursive(root):
            if root is None:
                return

            yield from _list_recursive(root.left)
            yield root.content
            yield from _list_recursive(root.right)

        yield from _list_recursive(self.root)

    def find(
        self, item: SortableObject, key_parameter: object
    ) -> Optional[SortableObject]:
        """
        Tries to find an item in the tree that is equivalent to the supplied item. If none is found,
        None is returned.
        :param item: Item to be found
        :type item: SortableObject
        :param key_parameter: Parameter for the keys
        :type key_parameter: object
        :return: The first item in the tree, that is equivalent to the supplied item. None if there is no such item.
        :rtype: Optional[SortableObject]
        """

        def _find_recursive(root):

            if root is None:
                return None

            if root.content == item:
                return root
            if root.content.less_than(item, key_parameter):
                return _find_recursive(root.right)
            return _find_recursive(root.left)

        found_item = _find_recursive(self.root)
        return None if found_item is None else found_item.content

    def get_range(
        self, start_key: Numeric, end_key: Numeric, key_parameter: object
    ) -> Iterable[SortableObject]:
        """
            Returns all items in the range of [start_key, end_key] (including elements on the bounds)
        :param start_key: Start key
        :type start_key: numeric
        :param end_key: End key
        :type end_key: numeric
        :param key_parameter: Parameter for the keys
        :type key_parameter: object
        :return: List of matching elements
        :rtype: List[SortableObject]
        """

        def _range_overlaps(current_start, current_end) -> bool:
            if _greater_than(current_start, current_end):
                return False
            return not _greater_than(
                start_key, current_end
            ) and not _greater_than(current_start, end_key)

        def _get_range_recursive(
            root: BBTNode, current_start, current_end
        ) -> Iterable[SortableObject]:
            if root is None:
                return

            root_key = root.content.get_key(key_parameter)

            if root.left is not None:
                new_start = current_start
                new_end = min(current_end, root_key)

                if _range_overlaps(new_start, new_end):
                    yield from _get_range_recursive(root.left, new_start, new_end)

            if not root.content.less_than_key(
                start_key, key_parameter
            ) and not root.content.greater_than_key(end_key, key_parameter):
                yield root.content

            if root.right is not None:
                new_start = max(current_start, root_key)
                new_end = current_end

                if _range_overlaps(new_start, new_end):
                    yield from _get_range_recursive(root.right, new_start, new_end)

        yield from _get_range_recursive(self.root, start_key, end_key)

    def empty(self):
        """
            Returns true if and only if the tree is empty
        :return:
        :rtype:
        """
        return self.root is None

    def pop(self) -> Optional[SortableObject]:
        """
            Removes the minimal item from the tree and returns it
        :return: The minimal item present in the tree. None if the tree is empty.
        :rtype: Optional[SortableObject]
        """
        min_element = self.get_min()
        if min_element is None:
            return None

        self.remove(min_element, None)

        return min_element


# endregion


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
        position_b: CrossingPoint,  # TODO why is this not a CrossingLine
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
        self.sorted_list = ParameterizedBalancedBinarySearchTree()

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
        self.sorted_list = ParameterizedBalancedBinarySearchTree()

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
