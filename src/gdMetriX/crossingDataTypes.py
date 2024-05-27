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
from collections import namedtuple
from enum import Enum
from typing import List, Optional, Iterable

from gdMetriX.common import numeric

__precision = 1e-09


def set_precision(precision: float) -> None:
    """
        Sets the global precision used for all calculation. Any two numbers with a difference smaller than `precision`
         are considered as equal
    :param precision: Precision
    :type precision: float
    """
    global __precision
    __precision = precision


def _get_precision() -> float:
    global __precision
    return __precision


CrossingPoint = namedtuple("CrossingPoint", "x y")
CrossingLine = namedtuple("CrossingLine", "point_a point_b")


def __greater_than__(a: float, b: float) -> bool:
    if __numeric_eq__(a, b):
        return False

    return a > b


def __numeric_eq__(a: numeric, b: numeric) -> bool:
    return math.isclose(a, b, abs_tol=__precision)


def __points_equal__(crossing_a, crossing_b):
    def __point_to_crossing(line):
        return CrossingPoint(line[0], line[1])

    if isinstance(crossing_a, CrossingLine) or isinstance(crossing_b, CrossingLine):
        if not (isinstance(crossing_a, CrossingLine) and isinstance(crossing_b, CrossingLine)):
            return False
        return (
                __points_equal__(__point_to_crossing(crossing_a.point_a), __point_to_crossing(crossing_b.point_a)) and
                __points_equal__(__point_to_crossing(crossing_a.point_a), __point_to_crossing(crossing_b.point_a))
        ) or (
                __points_equal__(__point_to_crossing(crossing_a.point_a), __point_to_crossing(crossing_b.point_b)) and
                __points_equal__(__point_to_crossing(crossing_a.point_b), __point_to_crossing(crossing_b.point_a))
        )

    return __numeric_eq__(crossing_a[0], crossing_b[0]) and __numeric_eq__(crossing_a[1], crossing_b[1])


def _less_than(point1, point2):
    """
    Defines the order of the event points
    """
    return __greater_than__(point1[1], point2[1]) or (
            __numeric_eq__(point1[1], point2[1]) and __greater_than__(point2[0], point1[0]))


class Crossing:
    """
        Represents a single crossing point
    """

    def __init__(self, pos, involved_edges):
        self.pos = pos
        self.involved_edges = involved_edges

    def __str__(self):
        return "[{}, edges: {}]".format(self.pos, sorted(self.involved_edges))

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        if isinstance(other, Crossing):
            return __points_equal__(self.pos, other.pos) and len(self.involved_edges) == len(
                other.involved_edges) and sorted(
                self.involved_edges) == sorted(other.involved_edges)
        return False

    def __lt__(self, other):
        if type(self.pos) is CrossingPoint:
            if type(other.pos) is CrossingPoint:
                return _less_than(self.pos, other.pos)
            else:
                return True
        if type(self.pos) is CrossingLine:
            if type(other.pos) is CrossingLine:
                self_start = self.pos[0] if _less_than(self.pos[0], self.pos[1]) else self.pos[1]
                other_start = other.pos[0] if _less_than(other.pos[0], other.pos[1]) else other.pos[1]
                return _less_than(self_start, other_start)
            else:
                return False


class EventType(Enum):
    """ Simple enum for distinguishing in which scenario an edge is introduced """
    START = 1
    END = 2
    CROSSING = 3
    HORIZONTAL = 4


# region AVL tree

class SortableObject:
    """ Represents an object to be inserted in the ParameterizedBalancedBinarySearchTree.
        The item is comparable with a parameter. The comparison does not have to build a total order.
    """

    def less_than(self, other, key_parameter: numeric) -> bool:
        """
            Returns true iff the object is strictly less than the other one.
        :param other: The object to compare too
        :type other: SortableObject
        :param key_parameter: Parameter for comparison
        :type key_parameter: numeric
        """
        pass

    def less_than_key(self, key: numeric, key_parameter: numeric) -> bool:
        """
            Returns true iff the object is strictly less than the other one.
        :param key: The key of the object to compare too
        :type key: numeric
        :param key_parameter: Parameter for comparison
        :type key_parameter: numeric
        """
        pass

    def greater_than_key(self, key: numeric, key_parameter: numeric) -> bool:
        """
            Returns true iff the object is strictly greater than the other one.
        :param key: The key of the object to compare too
        :type key: numeric
        :param key_parameter: Parameter for comparison
        :type key_parameter: numeric
        """
        pass

    def get_key(self, key_parameter: numeric) -> numeric:
        """
            Returns the key under the given parameter
        :param key_parameter:
        :type key_parameter:
        :return:
        :rtype:
        """
        pass


class BBTNode(object):
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
        self.__length__ = 0

    def __update_height__(self, root):
        root.height = 1 + max(self.__get_height__(root.left), self.__get_height__(root.right))

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

        def __insert__(root: BBTNode) -> BBTNode:

            if root is None:
                root = BBTNode(item)
                return root

            if root.content.less_than(item, key_parameter):
                root.right = __insert__(root.right)
            else:
                root.left = __insert__(root.left)

            self.__update_height__(root)

            balance = self.__get_balance__(root)
            if balance > 1:
                # Tree is unbalanced with longer side on the left

                if not root.left.content.less_than(item, key_parameter):
                    return self.__right_rotate__(root)
                else:
                    root.left = self.__left_rotate__(root.left)
                    return self.__right_rotate__(root)
            elif balance < -1:
                # Tree is unbalanced with longer side on the right

                if root.right.content.less_than(item, key_parameter):
                    return self.__left_rotate__(root)
                else:
                    root.right = self.__right_rotate__(root.right)
                    return self.__left_rotate__(root)

            return root

        self.root = __insert__(self.root)
        self.__length__ += 1

    def __left_rotate__(self, node: BBTNode) -> BBTNode:
        old_right = node.right
        old_left = old_right.left

        # Rotate
        old_right.left = node
        node.right = old_left

        # Update changed heights
        node.height = 1 + max(self.__get_height__(node.left), self.__get_height__(node.right))
        old_right.height = 1 + max(self.__get_height__(old_right.left), self.__get_height__(old_right.right))

        return old_right

    def __right_rotate__(self, node: BBTNode) -> BBTNode:
        old_left = node.left
        old_right = old_left.right

        # Rotate
        old_left.right = node
        node.left = old_right

        # Update changed heights
        node.height = 1 + max(self.__get_height__(node.left), self.__get_height__(node.right))
        old_left.height = 1 + max(self.__get_height__(old_left.left), self.__get_height__(old_left.right))

        return old_left

    @staticmethod
    def __get_height__(root):
        if root is None:
            return 0
        return root.height

    def __get_balance__(self, root):
        if root is None:
            return 0
        return self.__get_height__(root.left) - self.__get_height__(root.right)

    def get_left(self, key_value: numeric, key_parameter: object) -> Optional[SortableObject]:
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

        def __get_left__(root) -> Optional[BBTNode]:

            if root is None:
                return None

            # Get candidate from children
            if root.content.less_than_key(key_value, key_parameter):
                candidate = __get_left__(root.right)
            else:
                candidate = __get_left__(root.left)

            # Check if current root is a better candidate
            if root.content.less_than_key(key_value, key_parameter):
                if candidate is None or candidate.content.less_than(root.content, key_parameter):
                    return root

            return candidate

        left_node = __get_left__(self.root)
        return None if left_node is None else left_node.content

    def get_right(self, key_value: numeric, key_parameter: object) -> Optional[SortableObject]:
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

        def __get_right__(root: BBTNode) -> Optional[BBTNode]:

            if root is None:
                return None

            # Get candidate from children
            if not root.content.greater_than_key(key_value, key_parameter):
                candidate = __get_right__(root.right)
            else:
                candidate = __get_right__(root.left)

            # Check if current root is a better candidate
            if root.content.greater_than_key(key_value, key_parameter):
                if candidate is None or root.content.less_than(candidate.content, key_parameter):
                    return root

            return candidate

        right_node = __get_right__(self.root)
        return None if right_node is None else right_node.content

    def __get_min__(self, root: BBTNode) -> Optional[BBTNode]:
        if root is None or root.left is None:
            return root
        return self.__get_min__(root.left)

    def get_min(self) -> Optional[SortableObject]:
        """
            Finds the minimum element present.
        :return: The minimum element.
        :rtype: Optional[SortableObject]
        """

        min_element = self.__get_min__(self.root)
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

        def __remove__(root: BBTNode, value: object) -> Optional[BBTNode]:
            nonlocal found_item

            if root is None:
                return None

            if value == root.content:
                # We have found the actual root that should be deleted
                found_item = True

                # If either the left or right is None, we can simply move the node one up
                if root.left is None:
                    return root.right
                elif root.right is None:
                    return root.left

                # Move min up and delete min down the road
                temp = self.__get_min__(root.right)
                root.content = temp.content
                root.right = __remove__(root.right, temp.content)
            else:
                if not root.content.less_than(value, key_parameter):
                    root.left = __remove__(root.left, value)
                else:
                    root.right = __remove__(root.right, value)

            self.__update_height__(root)

            # Rebalancing
            balance = self.__get_balance__(root)

            if balance > 1:
                if self.__get_balance__(root.left) >= 0:
                    return self.__right_rotate__(root)
                else:
                    root.left = self.__left_rotate__(root.left)
                    return self.__right_rotate__(root)
            elif balance < -1:
                if self.__get_balance__(root.right) <= 0:
                    return self.__left_rotate__(root)
                else:
                    root.right = self.__right_rotate__(root.right)
                    return self.__left_rotate__(root)

            return root

        if found_item:
            self.__length__ -= 1

        self.root = __remove__(self.root, item)

    def __len__(self) -> int:
        return self.__length__

    def __iter__(self):
        def __list__(root):
            if root is None:
                return

            yield from __list__(root.left)
            yield root.content
            yield from __list__(root.right)

        yield from __list__(self.root)

    def find(self, item: SortableObject, key_parameter: object) -> Optional[SortableObject]:
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

        def __find__(root):

            if root is None:
                return None

            if root.content == item:
                return root
            elif root.content.less_than(item, key_parameter):
                return __find__(root.right)
            else:
                return __find__(root.left)

        found_item = __find__(self.root)
        return None if found_item is None else found_item.content

    def get_range(self, start_key: numeric, end_key: numeric, key_parameter: object) -> Iterable[SortableObject]:
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
            if __greater_than__(current_start, current_end):
                return False
            return (not __greater_than__(start_key, current_end) and
                    not __greater_than__(current_start, end_key))

        def __get_range__(root: BBTNode, current_start, current_end) -> Iterable[SortableObject]:
            if root is None:
                return

            root_key = root.content.get_key(key_parameter)

            if root.left is not None:
                new_start = current_start
                new_end = min(current_end, root_key)

                if _range_overlaps(new_start, new_end):
                    yield from __get_range__(root.left, new_start, new_end)

            if (not root.content.less_than_key(start_key, key_parameter)
                    and not root.content.greater_than_key(end_key, key_parameter)):
                yield root.content

            if root.right is not None:
                new_start = max(current_start, root_key)
                new_end = current_end

                if _range_overlaps(new_start, new_end):
                    yield from __get_range__(root.right, new_start, new_end)

        yield from __get_range__(self.root, start_key, end_key)

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

    def __init__(
            self,
            edge: (numeric, numeric),
            position_a: (numeric, numeric),
            position_b: (numeric, numeric),
    ):
        self.edge = edge

        if _less_than(position_a, position_b):
            self.start_position = position_a
            self.end_position = position_b
        else:
            self.start_position = position_b
            self.end_position = position_a

    # region Implementation of SortableObject

    def less_than(self, other, key_parameter: numeric):
        x_self = __get_x_at_y__(self, key_parameter)
        x_other = __get_x_at_y__(other, key_parameter)

        if __numeric_eq__(x_self, x_other):
            lower_end = min(self.end_position[1], other.end_position[1])
            key_parameter = min(key_parameter - _get_precision(), lower_end)

            x_self = __get_x_at_y__(self, key_parameter)
            x_other = __get_x_at_y__(other, key_parameter)

        return __greater_than__(x_other, x_self)

    def less_than_key(self, key: numeric, y: numeric):
        x_self = __get_x_at_y__(self, y)

        return __greater_than__(key, x_self)

    def greater_than_key(self, key: numeric, y: numeric):
        x_self = __get_x_at_y__(self, y)
        return __greater_than__(x_self, key)

    def get_key(self, key_parameter: numeric) -> numeric:
        return __get_x_at_y__(self, key_parameter)

    # endregion

    def __str__(self):
        return "[{}, start: {}, end: {}]".format(self.edge, self.start_position, self.end_position)

    def __repr__(self):
        return self.__str__()

    def is_horizontal(self):
        """
            Returns true if and only if the edge is considered to be horizontal
        :return:
        :rtype:
        """
        return __numeric_eq__(self.start_position[1], self.end_position[1])


class SweepLinePoint(SortableObject):
    """
    Represents a point on the event queue
    """

    def __init__(self, x, y):
        self.end_list = set()
        self.start_list = set()
        self.interior_list = set()
        self.horizontal_list = set()
        self.x = x
        self.y = y
        self.is_crossing = False

    def __str__(self):
        return "(" + str(self.x) + ", " + str(self.y) + ")"

    def __eq__(self, other):
        if other is None:
            return False
        return __points_equal__((self.x, self.y), (other.x, other.y))

    def __lt__(self, other):
        return _less_than((self.x, self.y), (other.x, other.y))

    # region Implementation of SortableObject

    def less_than(self, other, _):
        return self.__lt__(other)

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
        self.__add(
            edge_info.start_position[0],
            edge_info.start_position[1],
            edge_info,
            EventType.HORIZONTAL if edge_info.is_horizontal() else EventType.START,
        )
        self.__add(
            edge_info.end_position[0],
            edge_info.end_position[1],
            edge_info,
            EventType.HORIZONTAL if edge_info.is_horizontal() else EventType.END,
        )

    def add_crossing(self, crossing: CrossingPoint, edge_list: List[SweepLineEdgeInfo]) -> None:
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
            if not (__points_equal__(edge.start_position, crossing) or __points_equal__(edge.end_position, crossing)):
                self.__add(crossing.x, crossing.y, edge, EventType.CROSSING)

    def __add(self, x: int, y, edge_info: SweepLineEdgeInfo, event_type: EventType) -> None:
        sweep_line_point = self.sorted_list.find(SweepLinePoint(x, y), None)
        if sweep_line_point is None:
            sweep_line_point = SweepLinePoint(x, y)
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


def __get_x_at_y__(edge_info: SweepLineEdgeInfo, y: numeric):
    x1, y1 = edge_info.start_position
    x2, y2 = edge_info.end_position

    if x2 == x1:
        return x1
    if y2 - y1 == 0:
        raise ValueError("Horizontal line, TODO")
    m = (y2 - y1) / (x2 - x1)
    b = y1 - m * x1
    x = (y - b) / m

    return x


class SweepLineStatus:
    """
        Stores all edges in order from left to right as they intersect the sweep line.
        Note that when the height changes, edges with changing order have to be explicitly deleted and reinserted.
    """

    def __init__(self):
        self.sortedList = ParameterizedBalancedBinarySearchTree()

    def __str__(self):
        return [edge.edge for edge in self.sortedList].__str__()

    def add(self, y_value: numeric, edge_info: SweepLineEdgeInfo) -> None:
        """Adds a new edge to the sweep line. It will be added next to its neighboring edges at height y_value.
        :param y_value: Height of the sweep line
        :type y_value:
        :param edge_info:
        :type edge_info:
        """
        self.sortedList.insert(edge_info, y_value)

    def remove(self, y_value: numeric, edge_info: SweepLineEdgeInfo):
        """
        Removes an edge from the sweep line.
        :param y_value:
        :type y_value:
        :param edge_info: Edge that should be removed
        :type edge_info: :class:`SweepLineEdgeInfo`
        """
        self.sortedList.remove(edge_info, y_value)

    def get_left(self, point: SweepLinePoint) -> Optional[SweepLineEdgeInfo]:
        """
        Returns the edge left of the given edge. If no such edge exists, none is returned
        :param point: Query point
        :type point: SweepLinePoint
        :return: Edge left of the given edge
        :rtype: SweepLineEdgeInfo
        """
        return self.sortedList.get_left(point.x, point.y)

    def get_right(self, point: SweepLinePoint) -> Optional[SweepLineEdgeInfo]:
        """
        Returns the edge right of the given edge. If no such edge exists, none is returned
        :return: Edge right of the given edge
        :rtype: SweepLineEdgeInfo
        """
        return self.sortedList.get_right(point.x, point.y)

    def get_range(self, y: numeric, left_x: numeric, right_x: numeric) -> Iterable[SweepLineEdgeInfo]:
        """
            Returns all matching edges in range [left_x, right_x]
        :param y:
        :type y:
        :param left_x:
        :type left_x:
        :param right_x:
        :type right_x:
        """
        return self.sortedList.get_range(left_x, right_x, y)

# endregion
