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
Unittests for bend_support.py
"""

import functools
import inspect
import pathlib
import re
import unittest

import networkx as nx

# noinspection PyUnresolvedReferences
import pytest

# noinspection PyUnresolvedReferences
import pytest_socket

import gdMetriX
from gdMetriX import bend_support as bend_support_module
from gdMetriX import common
from gdMetriX.bend_support import (
    BendSupport,
    BendsNotSupportedError,
    bend_support,
    bend_support_of,
    _ADMONITIONS,
    _REGISTRY,
    _validated_graphs,
)


def _drawing(bends=False, attribute="bends"):
    """A triangle, optionally with geometry on one of its edges."""
    g = nx.Graph()
    g.add_node(0, pos=(0, 0))
    g.add_node(1, pos=(1, 1))
    g.add_node(2, pos=(2, 0))
    g.add_edge(0, 1)
    g.add_edge(1, 2)

    if bends:
        g.edges[0, 1][attribute] = [(0.5, 0.9)]

    return g


class TestBendSupportDecorator(unittest.TestCase):

    def test_classification_is_recorded(self):
        @bend_support(BendSupport.SUPPORTED)
        def metric():
            """Some metric."""

        assert bend_support_of(metric) == BendSupport.SUPPORTED

    def test_function_is_not_wrapped(self):
        def metric(a, b):
            """Some metric."""
            return a + b

        decorated = bend_support(BendSupport.GEOMETRY_INDEPENDENT)(metric)

        assert decorated is metric
        assert decorated(1, 2) == 3

    def test_all_classifications_are_accepted(self):
        for support in BendSupport:

            @bend_support(support)
            def metric():
                """Some metric."""

            assert bend_support_of(metric) == support

    def test_non_classification_is_rejected(self):
        with pytest.raises(TypeError):
            bend_support("supported")

    def test_registry_contains_annotated_metric(self):
        @bend_support(BendSupport.STRAIGHT_LINE_ONLY)
        def metric():
            """Some metric."""

        key = f"{metric.__module__}.{metric.__qualname__}"

        assert _REGISTRY[key] == BendSupport.STRAIGHT_LINE_ONLY


class TestDocumentation(unittest.TestCase):

    def test_admonition_is_appended(self):
        @bend_support(BendSupport.SUPPORTED)
        def metric():
            """Some metric."""

        assert metric.__doc__.startswith("Some metric.")
        assert metric.__doc__.endswith(_ADMONITIONS[BendSupport.SUPPORTED])

    def test_docstring_is_dedented(self):
        @bend_support(BendSupport.SUPPORTED)
        def metric():
            """Some metric.

            :param g: A networkX graph
            :type g: nx.Graph
            """

        # The appended admonition carries no indentation of its own, so the indentation of the
        # original docstring has to go - a mixture of the two is not valid reStructuredText.
        assert "\n:param g: A networkX graph\n" in metric.__doc__
        assert "\n:type g: nx.Graph\n" in metric.__doc__

    def test_missing_docstring(self):
        @bend_support(BendSupport.STRAIGHT_LINE_ONLY)
        def metric():
            pass

        assert metric.__doc__ == _ADMONITIONS[BendSupport.STRAIGHT_LINE_ONLY]

    def test_geometry_independent_leaves_the_docstring_untouched(self):
        def metric():
            """Some metric.

            :param g: A networkX graph
            :type g: nx.Graph
            """

        original = metric.__doc__
        bend_support(BendSupport.GEOMETRY_INDEPENDENT)(metric)

        # There is nothing for the reader to act on, so the docstring stays exactly as written -
        # not even its indentation is touched.
        assert metric.__doc__ == original
        assert "admonition" not in metric.__doc__

    def test_geometry_independent_without_a_docstring(self):
        @bend_support(BendSupport.GEOMETRY_INDEPENDENT)
        def metric():
            pass

        assert metric.__doc__ is None

    def test_every_classification_needing_an_admonition_has_one(self):
        for support in BendSupport:
            if support is BendSupport.GEOMETRY_INDEPENDENT:
                assert support not in _ADMONITIONS
            else:
                assert support in _ADMONITIONS

    def test_admonitions_differ(self):
        assert len(set(_ADMONITIONS.values())) == len(_ADMONITIONS)


class TestBendSupportOf(unittest.TestCase):

    def test_unannotated_function_raises(self):
        def metric():
            """Some metric."""

        with pytest.raises(ValueError):
            bend_support_of(metric)

    def test_classification_survives_wrapping(self):
        @bend_support(BendSupport.SUPPORTED)
        def metric(g, pos=None):
            """Some metric."""
            return pos

        @functools.wraps(metric)
        def wrapper(*args, **kwargs):
            return metric(*args, **kwargs)

        assert bend_support_of(wrapper) == BendSupport.SUPPORTED

    def test_classification_is_found_through_a_wrapper(self):
        @bend_support(BendSupport.SUPPORTED)
        def metric(g, pos=None):
            """Some metric."""
            return pos

        def wrapper(*args, **kwargs):
            return metric(*args, **kwargs)

        # Unlike functools.wraps, this wrapper does not copy over the attributes of the wrapped
        # function, so the classification has to be found by unwrapping.
        wrapper.__wrapped__ = metric

        assert bend_support_of(wrapper) == BendSupport.SUPPORTED

    def test_classification_survives_resolve_pos(self):
        @common.resolve_pos
        @bend_support(BendSupport.GEOMETRY_INDEPENDENT)
        def metric(g, pos=None):
            """Some metric."""
            return pos

        g = nx.Graph()
        g.add_node(0, pos=(1, 2))

        assert bend_support_of(metric) == BendSupport.GEOMETRY_INDEPENDENT
        assert metric(g) == {0: (1, 2)}


class TestGuard(unittest.TestCase):

    def test_straight_line_only_is_wrapped(self):
        def metric(g):
            """Some metric."""

        assert bend_support(BendSupport.STRAIGHT_LINE_ONLY)(metric) is not metric

    def test_raises_on_a_drawing_with_bends(self):
        with pytest.raises(BendsNotSupportedError):
            gdMetriX.area(_drawing(bends=True))

    def test_raises_on_a_drawing_with_a_geometry_attribute(self):
        with pytest.raises(BendsNotSupportedError):
            gdMetriX.area(_drawing(bends=True, attribute="geometry"))

    def test_does_not_raise_on_a_straight_line_drawing(self):
        assert gdMetriX.area(_drawing()) == 2

    def test_geometry_independent_metric_still_runs(self):
        bent = _drawing(bends=True)

        assert gdMetriX.center_of_mass(bent) == gdMetriX.center_of_mass(_drawing())

    def test_raises_when_the_graph_is_passed_as_a_keyword(self):
        with pytest.raises(BendsNotSupportedError):
            gdMetriX.area(g=_drawing(bends=True))

    def test_error_is_a_value_error(self):
        # Mirrors OverlappingEdgesError, so that existing `except ValueError` handlers keep working.
        with pytest.raises(ValueError):
            gdMetriX.area(_drawing(bends=True))

    def test_function_without_a_graph_is_not_guarded(self):
        # crossing_angles takes a Crossing rather than a graph - there is nothing to inspect.
        def metric(crossing, pos=None):
            """Some metric."""

        assert bend_support(BendSupport.STRAIGHT_LINE_ONLY)(metric) is metric

    def test_the_graph_is_scanned_once_per_outermost_call(self):
        scanned = []
        original = bend_support_module._has_edge_geometry

        @bend_support(BendSupport.STRAIGHT_LINE_ONLY)
        def inner(g):
            return 1

        @bend_support(BendSupport.STRAIGHT_LINE_ONLY)
        def outer(g):
            return sum(inner(g) for _ in range(5))

        bend_support_module._has_edge_geometry = lambda g: (
            scanned.append(g) or original(g)
        )
        try:
            assert outer(_drawing()) == 5
        finally:
            bend_support_module._has_edge_geometry = original

        assert len(scanned) == 1

    def test_a_nested_call_on_a_different_graph_is_still_checked(self):
        bent = _drawing(bends=True)

        @bend_support(BendSupport.STRAIGHT_LINE_ONLY)
        def inner(g):
            return 1

        @bend_support(BendSupport.STRAIGHT_LINE_ONLY)
        def outer(g):
            return inner(bent)

        with pytest.raises(BendsNotSupportedError):
            outer(_drawing())

    def test_bookkeeping_is_cleaned_up(self):
        gdMetriX.area(_drawing())

        assert _validated_graphs() == {}

    def test_bookkeeping_is_cleaned_up_when_the_metric_raises(self):
        @bend_support(BendSupport.STRAIGHT_LINE_ONLY)
        def metric(g):
            raise RuntimeError("boom")

        with pytest.raises(RuntimeError):
            metric(_drawing())

        assert _validated_graphs() == {}


class TestMetricsTable(unittest.TestCase):
    """The 'Bends' column of the documentation tables is derived from the registry.

    The column is generated, but nothing regenerates it on a doc build - these tests are what
    keeps it from drifting away from the classifications in the code.
    """

    DOCUMENTS = ("metrics.rst", "additional_features.rst")

    @staticmethod
    def _documented_rows():
        doc = pathlib.Path(__file__).resolve().parents[2] / "doc"
        rows = []

        for name in TestMetricsTable.DOCUMENTS:
            for line in (doc / name).read_text(encoding="utf-8").splitlines():
                if not line.startswith("|"):
                    continue

                references = re.findall(r":func:`([a-zA-Z_.]+)`", line)
                if not references:
                    # The header row of a table.
                    continue

                cells = [cell.strip() for cell in line.strip("|").split("|")]
                rows.append((references[0], cells[-1]))

        return rows

    @staticmethod
    def _annotated_rows():
        """The documented rows referring to an annotated function, with their expected value.

        Rows referring to something else - the dataset table lists :func:`iterate_dataset`, which
        loads drawings rather than measuring them - carry no classification and no column.
        """
        by_reference = {
            key[len("gdMetriX.") :]: value.value for key, value in _REGISTRY.items()
        }

        return [
            (reference, cell, by_reference[reference])
            for reference, cell in TestMetricsTable._documented_rows()
            if reference in by_reference
        ]

    def test_the_tables_are_parsed(self):
        # Guards the test below against silently passing on tables it failed to read.
        assert len(self._annotated_rows()) > 20

    def test_the_column_matches_the_registry(self):
        drifted = [
            (reference, documented, expected)
            for reference, documented, expected in self._annotated_rows()
            if documented != expected
        ]

        assert drifted == []


class TestPublicApi(unittest.TestCase):

    def test_the_error_is_exported(self):
        # The one name of this module that users need: metrics raise it at them, so they have to
        # be able to catch it without reaching into a submodule.
        assert gdMetriX.BendsNotSupportedError is BendsNotSupportedError

    def test_the_classification_machinery_is_not_exported(self):
        # `bend_support_of` only becomes worth exporting once a metric is classified SUPPORTED -
        # until then it answers nothing that calling the metric does not already reveal, and a
        # public name is far easier to add later than to take away.
        assert not hasattr(gdMetriX, "bend_support_of")
        assert not hasattr(gdMetriX, "BendSupport")

        assert gdMetriX.bend_support.bend_support_of is bend_support_of

    def test_every_public_function_taking_a_graph_is_annotated(self):
        unannotated = []

        for name in dir(gdMetriX):
            if name.startswith("_"):
                continue

            function = getattr(gdMetriX, name)
            if not inspect.isfunction(function):
                continue
            if "g" not in inspect.signature(function).parameters:
                continue

            try:
                bend_support_of(function)
            except ValueError:
                unannotated.append(name)

        assert unannotated == []

    def test_module_is_not_shadowed_by_the_decorator(self):
        # `from gdMetriX.bend_support import bend_support` in __init__.py would rebind the
        # submodule attribute to the decorator - the decorator is therefore not re-exported.
        assert gdMetriX.bend_support.BendSupport is BendSupport
