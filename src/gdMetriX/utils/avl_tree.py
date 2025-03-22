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

"""
Custom AVL tree implementation
"""

from typing import (
    List,
    Optional,
    Iterable,
    Callable,
)

from gdMetriX.common import Numeric


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

    def __init__(self, greater_than: Callable[[Numeric, Numeric], bool]):
        self.root = None
        self._length = 0
        self._greater_than = greater_than

    def _update_height(self, root):
        root.height = 1 + max(self._get_height(root.left), self._get_height(root.right))

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
        node.height = 1 + max(self._get_height(node.left), self._get_height(node.right))
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
        node.height = 1 + max(self._get_height(node.left), self._get_height(node.right))
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

    def force_remove(self, item: SortableObject) -> None:
        """
        Iterates over all objects in the tree and removes all that are equal to the given item.
        :param item: Item that shall be deleted
        :type item: SortableObject
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
                root.left = _remove_recursive(root.left, value)
                root.right = _remove_recursive(root.right, value)

            self._update_height(root)

            # Re-balancing
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

            # Re-balancing
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
            if self._greater_than(current_start, current_end):
                return False
            return not self._greater_than(
                start_key, current_end
            ) and not self._greater_than(current_start, end_key)

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
