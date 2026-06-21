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
Unit tests for the generic AVL tree (ParameterizedBalancedBinarySearchTree) underlying the sweep line
status structure. Deliberately uses a plain integer SortableObject instead of crossing-specific geometry,
since this data structure is meant to be a reusable, domain-agnostic building block - its correctness should
not depend on (or be obscured by) crossing-specific comparison logic.
"""

import random
import unittest

from gdMetriX.utils.avl_tree import ParameterizedBalancedBinarySearchTree, SortableObject


def _greater_than(a, b):
    return a > b


class IntItem(SortableObject):
    """ Simple SortableObject wrapping an int, ignoring key_parameter (fixed total order). """

    def __init__(self, value, tag=None):
        self.value = value
        # Distinguishes structurally-different objects that should still compare equal,
        # for duplicate-handling tests. Two IntItems are == whenever their tags match.
        self.tag = tag if tag is not None else value

    def less_than(self, other, key_parameter):
        return self.value < other.value

    def less_than_key(self, key, key_parameter):
        return key > self.value

    def greater_than_key(self, key, key_parameter):
        return key < self.value

    def get_key(self, key_parameter):
        return self.value

    def __eq__(self, other):
        return isinstance(other, IntItem) and self.tag == other.tag

    def __hash__(self):
        return hash(self.tag)

    def __repr__(self):
        return f"IntItem({self.value}, tag={self.tag})"


def _assert_avl_balanced(testcase, tree):
    """ Verifies the AVL height-balance invariant holds at every node. """

    def _check(node):
        if node is None:
            return 0
        left_height = _check(node.left)
        right_height = _check(node.right)
        balance = left_height - right_height
        testcase.assertTrue(
            -1 <= balance <= 1,
            f"AVL balance invariant violated at node {node.content}: balance={balance}",
        )
        expected_height = 1 + max(left_height, right_height)
        testcase.assertEqual(
            node.height, expected_height,
            f"Stored height at node {node.content} is wrong: stored={node.height}, actual={expected_height}",
        )
        return expected_height

    _check(tree.root)


def _assert_bst_ordered(testcase, tree):
    """ Verifies an in-order traversal yields values in non-decreasing order. """
    values = [item.value for item in tree]
    testcase.assertEqual(values, sorted(values))


class TestInsertOrdering(unittest.TestCase):

    def test_empty_tree(self):
        tree = ParameterizedBalancedBinarySearchTree(_greater_than)
        self.assertEqual(len(list(tree)), 0)
        self.assertIsNone(tree.get_min())
        self.assertTrue(tree.empty())

    def test_single_insert(self):
        tree = ParameterizedBalancedBinarySearchTree(_greater_than)
        tree.insert(IntItem(5), None)
        self.assertEqual([i.value for i in tree], [5])
        _assert_avl_balanced(self, tree)

    def test_in_order_traversal_matches_sorted(self):
        values = [5, 3, 8, 1, 4, 7, 9, 2, 6, 0]
        tree = ParameterizedBalancedBinarySearchTree(_greater_than)
        for v in values:
            tree.insert(IntItem(v), None)
        _assert_bst_ordered(self, tree)
        _assert_avl_balanced(self, tree)

    def test_ascending_insert_stays_balanced(self):
        # Naive unbalanced BST insertion would degenerate into a linked list here
        tree = ParameterizedBalancedBinarySearchTree(_greater_than)
        for v in range(200):
            tree.insert(IntItem(v), None)
        _assert_avl_balanced(self, tree)
        _assert_bst_ordered(self, tree)
        # A balanced tree of 200 nodes should have height around log2(200) =~ 7-8, not 200
        self.assertLess(tree.root.height, 20)

    def test_descending_insert_stays_balanced(self):
        tree = ParameterizedBalancedBinarySearchTree(_greater_than)
        for v in reversed(range(200)):
            tree.insert(IntItem(v), None)
        _assert_avl_balanced(self, tree)
        _assert_bst_ordered(self, tree)
        self.assertLess(tree.root.height, 20)

    def test_duplicate_values_both_kept(self):
        tree = ParameterizedBalancedBinarySearchTree(_greater_than)
        tree.insert(IntItem(5, tag="a"), None)
        tree.insert(IntItem(5, tag="b"), None)
        self.assertEqual(len(list(tree)), 2)
        _assert_avl_balanced(self, tree)


class TestLength(unittest.TestCase):
    """
    __len__ is relied upon by gdMetriX.crossings to detect whether a `remove()` call actually removed
    something (`sl_size_before = len(status); status.remove(...); if len(status) == sl_size_before: ...`).
    """

    def test_len_after_inserts(self):
        tree = ParameterizedBalancedBinarySearchTree(_greater_than)
        for i, v in enumerate([5, 3, 8, 1, 4]):
            tree.insert(IntItem(v), None)
            self.assertEqual(len(tree), i + 1)

    def test_len_decreases_after_successful_remove(self):
        tree = ParameterizedBalancedBinarySearchTree(_greater_than)
        for v in [5, 3, 8, 1, 4, 7, 9]:
            tree.insert(IntItem(v), None)
        self.assertEqual(len(tree), 7)

        tree.remove(IntItem(3), None)

        # BUG: __len__ does not actually reflect the tree content. `remove()` checks
        # `if found_item: self._length -= 1` *before* calling `_remove_recursive` (which is the only
        # place `found_item` is ever set), so the decrement can never fire - len(tree) is permanently
        # stuck at the highest count ever inserted, no matter how many successful removes happen.
        # This directly explains why crossings.py's `if len(sweep_line_status) == sl_size_before:
        # force_remove(...)` fallback always fires, even when the preceding `remove()` already
        # succeeded: the size never appears to change, successful or not.
        self.assertEqual(
            len(tree), 6,
            "len(tree) should decrease after a successful remove(), but the length bookkeeping in "
            "remove()/force_remove() checks `found_item` before the recursive removal runs, so it "
            "never decrements (see avl_tree.py around the 'if found_item: self._length -= 1' lines)",
        )
        self.assertEqual(len(list(tree)), 6)  # the tree's actual content is correct regardless

    def test_len_after_force_remove(self):
        tree = ParameterizedBalancedBinarySearchTree(_greater_than)
        for v in [5, 3, 8, 1, 4]:
            tree.insert(IntItem(v), None)

        tree.force_remove(IntItem(3))

        self.assertEqual(
            len(tree), 4,
            "Same bookkeeping bug as test_len_decreases_after_successful_remove, but in force_remove()",
        )

    def test_len_matches_iteration_count_after_mixed_operations(self):
        # General sanity check: regardless of the specific bug above, len() should never silently
        # drift from the tree's actual content over a longer sequence of operations.
        tree = ParameterizedBalancedBinarySearchTree(_greater_than)
        present = []  # list of (tag, value)
        next_tag = 0
        random.seed(1)
        for _ in range(50):
            if not present or random.random() < 0.6:
                v = random.randint(0, 1000)
                tag = next_tag
                next_tag += 1
                tree.insert(IntItem(v, tag=tag), None)
                present.append((tag, v))
            else:
                idx = random.randrange(len(present))
                tag, v = present.pop(idx)
                tree.remove(IntItem(v, tag=tag), None)

        self.assertEqual(len(tree), len(list(tree)))


class TestRemove(unittest.TestCase):

    def test_remove_existing_leaf(self):
        tree = ParameterizedBalancedBinarySearchTree(_greater_than)
        for v in [5, 3, 8]:
            tree.insert(IntItem(v), None)
        tree.remove(IntItem(3), None)
        self.assertEqual(sorted(i.value for i in tree), [5, 8])
        _assert_avl_balanced(self, tree)
        _assert_bst_ordered(self, tree)

    def test_remove_root_with_two_children(self):
        tree = ParameterizedBalancedBinarySearchTree(_greater_than)
        for v in [5, 3, 8, 1, 4, 7, 9]:
            tree.insert(IntItem(v), None)
        tree.remove(IntItem(5), None)
        self.assertEqual(sorted(i.value for i in tree), [1, 3, 4, 7, 8, 9])
        _assert_avl_balanced(self, tree)
        _assert_bst_ordered(self, tree)

    def test_remove_nonexistent_is_safe_noop(self):
        tree = ParameterizedBalancedBinarySearchTree(_greater_than)
        for v in [5, 3, 8]:
            tree.insert(IntItem(v), None)
        tree.remove(IntItem(999), None)
        self.assertEqual(sorted(i.value for i in tree), [3, 5, 8])

    def test_remove_from_empty_tree_is_safe(self):
        tree = ParameterizedBalancedBinarySearchTree(_greater_than)
        tree.remove(IntItem(1), None)  # must not raise
        self.assertEqual(list(tree), [])

    def test_remove_fails_for_tied_value_relocated_by_rotation(self):
        """
        BUG (found via TestRandomizedStress, shrunk from a 2000-step failure to this 5-insert
        reproduction): when two distinct items compare *equal* under less_than (same .value, here
        with different tags so they are still != via __eq__), the insert-time tie-breaking
        convention is "ties go left". But the very insertion that creates the tie can also trigger
        an AVL rotation (here: an RL double rotation, because inserting the second -588 makes the
        first -588's subtree right-heavy) whose case-selection logic *also* uses the tied
        less_than() comparison and ends up placing the tied node on the right instead.

        remove()'s navigation always evaluates the same "ties go left" rule, so it never looks on
        the right for a tied value - and dead-ends without ever finding a node that is structurally
        present in the tree. This is very plausibly the actual mechanism behind
        gdMetriX.crossings's "the normal remove sometimes does not catch the edge" TODOs: multiple
        edges sharing the exact same x-at-y position (e.g. several edges meeting at one event
        point) are exactly the kind of tied keys this reproduces.
        """
        tree = ParameterizedBalancedBinarySearchTree(_greater_than)
        for v, tag in [(-821, 183), (181, 186), (434, 187), (-588, 204), (-588, 220)]:
            tree.insert(IntItem(v, tag=tag), None)

        tree.remove(IntItem(-588, tag=204), None)

        remaining_tags = {i.tag for i in tree}
        self.assertNotIn(
            204, remaining_tags,
            "remove() failed to find and remove a tied-value item relocated by a rotation - "
            "it is still structurally present in the tree (see docstring for the exact mechanism)",
        )

    def test_remove_all_elements_one_by_one(self):
        values = list(range(50))
        random.seed(2)
        random.shuffle(values)
        tree = ParameterizedBalancedBinarySearchTree(_greater_than)
        for v in values:
            tree.insert(IntItem(v), None)

        random.shuffle(values)
        for v in values:
            tree.remove(IntItem(v), None)
            _assert_avl_balanced(self, tree)
            _assert_bst_ordered(self, tree)

        self.assertEqual(list(tree), [])


class TestForceRemove(unittest.TestCase):

    def test_force_remove_existing(self):
        tree = ParameterizedBalancedBinarySearchTree(_greater_than)
        for v in [5, 3, 8]:
            tree.insert(IntItem(v), None)
        tree.force_remove(IntItem(3))
        self.assertEqual(sorted(i.value for i in tree), [5, 8])
        _assert_avl_balanced(self, tree)

    def test_force_remove_nonexistent_is_safe_noop(self):
        tree = ParameterizedBalancedBinarySearchTree(_greater_than)
        for v in [5, 3, 8]:
            tree.insert(IntItem(v), None)
        tree.force_remove(IntItem(999))
        self.assertEqual(sorted(i.value for i in tree), [3, 5, 8])

    def test_force_remove_removes_all_duplicates(self):
        """
        BUG: force_remove's docstring promises to "remove all that are equal to the given item", but
        when a duplicate ends up positioned as the lone child of another node that also matches (so
        it's spliced out by the "node has at most one child" shortcut instead of via the
        "move successor up" path), it is never visited again and survives the call.
        """
        tree = ParameterizedBalancedBinarySearchTree(_greater_than)
        # Constructed so that IntItem(6, tag="X") ends up as the sole right child of
        # IntItem(5, tag="X") - both compare equal via the shared tag.
        tree.insert(IntItem(5, tag="X"), None)
        tree.insert(IntItem(6, tag="X"), None)

        tree.force_remove(IntItem(0, tag="X"))

        self.assertEqual(
            list(tree), [],
            "force_remove should remove every item equal to the given one, but a duplicate "
            "positioned as the lone child of another match survives (see force_remove's "
            "'if root.left is None: return root.right' shortcut, which never re-checks the "
            "spliced-in child against the value being removed)",
        )

    def test_force_remove_with_duplicates_among_unrelated_values(self):
        tree = ParameterizedBalancedBinarySearchTree(_greater_than)
        for v, tag in [(1, "a"), (2, "dup"), (3, "b"), (4, "dup"), (5, "c"), (6, "dup")]:
            tree.insert(IntItem(v, tag=tag), None)

        tree.force_remove(IntItem(0, tag="dup"))

        self.assertEqual(sorted(i.tag for i in tree), ["a", "b", "c"])


class TestGetLeftRight(unittest.TestCase):

    def _build(self, values):
        tree = ParameterizedBalancedBinarySearchTree(_greater_than)
        for v in values:
            tree.insert(IntItem(v), None)
        return tree

    def test_get_left_basic(self):
        tree = self._build([10, 20, 30, 40])

        self.assertIsNone(tree.get_left(5, None))
        self.assertEqual(tree.get_left(10, None), None)  # strictly left of 10: nothing
        self.assertEqual(tree.get_left(15, None).value, 10)
        self.assertEqual(tree.get_left(25, None).value, 20)
        self.assertEqual(tree.get_left(1000, None).value, 40)

    def test_get_right_basic(self):
        tree = self._build([10, 20, 30, 40])

        self.assertEqual(tree.get_right(5, None).value, 10)
        self.assertEqual(tree.get_right(15, None).value, 20)
        self.assertIsNone(tree.get_right(40, None))
        self.assertIsNone(tree.get_right(1000, None))

    def test_get_left_right_against_brute_force(self):
        random.seed(3)
        values = random.sample(range(-500, 500), 80)
        tree = self._build(values)
        sorted_values = sorted(values)

        for query in range(-600, 600, 17):
            left_candidates = [v for v in sorted_values if v < query]
            right_candidates = [v for v in sorted_values if v > query]

            expected_left = max(left_candidates) if left_candidates else None
            expected_right = min(right_candidates) if right_candidates else None

            left = tree.get_left(query, None)
            right = tree.get_right(query, None)

            self.assertEqual(left.value if left else None, expected_left)
            self.assertEqual(right.value if right else None, expected_right)


class TestGetRange(unittest.TestCase):

    def test_get_range_basic(self):
        tree = ParameterizedBalancedBinarySearchTree(_greater_than)
        for v in [10, 20, 30, 40, 50]:
            tree.insert(IntItem(v), None)

        result = sorted(i.value for i in tree.get_range(15, 45, None))
        self.assertEqual(result, [20, 30, 40])

    def test_get_range_inclusive_bounds(self):
        tree = ParameterizedBalancedBinarySearchTree(_greater_than)
        for v in [10, 20, 30]:
            tree.insert(IntItem(v), None)

        result = sorted(i.value for i in tree.get_range(10, 30, None))
        self.assertEqual(result, [10, 20, 30])

    def test_get_range_empty_result(self):
        tree = ParameterizedBalancedBinarySearchTree(_greater_than)
        for v in [10, 20, 30]:
            tree.insert(IntItem(v), None)

        self.assertEqual(list(tree.get_range(100, 200, None)), [])

    def test_get_range_against_brute_force(self):
        random.seed(4)
        values = random.sample(range(-500, 500), 80)
        tree = ParameterizedBalancedBinarySearchTree(_greater_than)
        for v in values:
            tree.insert(IntItem(v), None)

        for _ in range(50):
            a, b = sorted(random.sample(range(-600, 600), 2))
            expected = sorted(v for v in values if a <= v <= b)
            actual = sorted(i.value for i in tree.get_range(a, b, None))
            self.assertEqual(actual, expected, f"range [{a},{b}]")


class TestFindAndPop(unittest.TestCase):

    def test_find_existing(self):
        tree = ParameterizedBalancedBinarySearchTree(_greater_than)
        for v in [5, 3, 8]:
            tree.insert(IntItem(v), None)
        found = tree.find(IntItem(3), None)
        self.assertIsNotNone(found)
        self.assertEqual(found.value, 3)

    def test_find_nonexistent(self):
        tree = ParameterizedBalancedBinarySearchTree(_greater_than)
        for v in [5, 3, 8]:
            tree.insert(IntItem(v), None)
        self.assertIsNone(tree.find(IntItem(999), None))

    def test_pop_returns_ascending_order(self):
        values = [5, 3, 8, 1, 4, 7, 9, 2, 6, 0]
        tree = ParameterizedBalancedBinarySearchTree(_greater_than)
        for v in values:
            tree.insert(IntItem(v), None)

        popped = []
        item = tree.pop()
        while item is not None:
            popped.append(item.value)
            item = tree.pop()

        self.assertEqual(popped, sorted(values))
        self.assertEqual(list(tree), [])

    def test_pop_empty_tree(self):
        tree = ParameterizedBalancedBinarySearchTree(_greater_than)
        self.assertIsNone(tree.pop())


class TestRandomizedStress(unittest.TestCase):
    """
    Cross-checks a long, randomized sequence of inserts/removes against a plain Python list used as
    a trusted reference, re-verifying the AVL balance invariant and sorted-content correctness after
    every single operation - not just at the end.
    """

    def test_mixed_operations_stay_correct_and_balanced(self):
        random.seed(5)
        tree = ParameterizedBalancedBinarySearchTree(_greater_than)
        reference = []  # list of (tag, value), mirrors what's logically "in" the tree
        next_tag = 0

        for step in range(2000):
            if not reference or random.random() < 0.55:
                value = random.randint(-1000, 1000)
                tag = next_tag
                next_tag += 1
                tree.insert(IntItem(value, tag=tag), None)
                reference.append((tag, value))
            else:
                idx = random.randrange(len(reference))
                tag, value = reference.pop(idx)
                tree.remove(IntItem(value, tag=tag), None)

            _assert_avl_balanced(self, tree)
            actual_values = sorted(i.value for i in tree)
            expected_values = sorted(v for _, v in reference)
            self.assertEqual(
                actual_values, expected_values,
                f"Mismatch after step {step} ({len(reference)} items expected)",
            )
