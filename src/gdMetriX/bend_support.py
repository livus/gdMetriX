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
Classifies how each metric responds to edge geometry, i.e. to drawings whose edges are drawn as
polylines or curves rather than as straight lines.

Every function taking a graph is annotated with a `BendSupport` value through the `bend_support`
decorator, which records the classification, appends it to the docstring of the function and, for
`STRAIGHT_LINE_ONLY`, guards the call so that a drawing carrying edge geometry raises instead of
being measured as if its edges were straight.
"""

import functools
import inspect
import threading
from enum import Enum
from typing import Any, Callable, Dict, Optional


class BendsNotSupportedError(ValueError):
    """Raised when a metric assuming straight-line edges is applied to a drawing with geometry."""


class BendSupport(Enum):
    """Describes how a metric responds to edge geometry, i.e. to bends and curves."""

    SUPPORTED = "supported"
    """The metric reads the edge geometry and respects it."""

    GEOMETRY_INDEPENDENT = "node-based"
    """The metric is defined over node positions alone, so edge geometry is irrelevant."""

    STRAIGHT_LINE_ONLY = "straight-line"
    """The metric assumes straight edges and raises BendsNotSupportedError on graphs with edge bends."""


# GEOMETRY_INDEPENDENT has no admonition on purpose: such a metric is valid for a drawing with
# bends as it stands, so there is nothing for the reader to act on.
_ADMONITIONS = {
    BendSupport.SUPPORTED: """.. admonition:: Bend support: supported
   :class: note

   This function reads the geometry of the edges and respects it. For a drawing without bends the
   returned value is identical to the value returned before bend support was added.""",
    BendSupport.STRAIGHT_LINE_ONLY: """.. admonition:: Bend support: straight-line drawings only
   :class: warning

   This function assumes that all edges are drawn as straight lines. Applied to a drawing with
   bent or curved edges it would measure something other than what is drawn, so it refuses to run
   on one rather than return a wrong value.""",
}

_REGISTRY: Dict[str, BendSupport] = {}
"""Qualified name of every annotated function to its classification.

Feeds the 'Bends' column of the documentation tables and the test that no function is left
unannotated. To ask about a single function, use `bend_support_of`.
"""


def _registry_key(func: Callable) -> str:
    return f"{func.__module__}.{func.__qualname__}"


def _has_edge_geometry(g: Any) -> bool:
    """Whether any edge of the given graph carries bend or curve information.

    ``bends`` holds a list of (x, y) coordinate pairs, ``geometry`` an explicit edge geometry.
    """
    if g is None or not hasattr(g, "edges"):
        return False

    return any(
        "bends" in data or "geometry" in data for _, _, data in g.edges(data=True)
    )


_VALIDATED = threading.local()
"""Graphs that an enclosing guarded call has already scanned, per thread."""


def _validated_graphs() -> Dict[int, int]:
    graphs = getattr(_VALIDATED, "graphs", None)

    if graphs is None:
        graphs = {}
        _VALIDATED.graphs = graphs

    return graphs


def _guard(func: Callable) -> Callable:
    """Wraps a straight-line-only function so that it refuses to run on a drawing with geometry."""
    params = list(inspect.signature(func).parameters)

    if "g" not in params:
        return func

    g_index = params.index("g")

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        g = args[g_index] if g_index < len(args) else kwargs.get("g")

        validated = _validated_graphs()
        key = id(g)

        if key not in validated and _has_edge_geometry(g):
            raise BendsNotSupportedError(
                f"'{func.__name__}' is only defined for straight-line drawings, but the given "
                "graph carries edge geometry. Computing it would measure the straight-line "
                "drawing spanned by the node positions rather than the drawing described by the "
                "graph."
            )

        validated[key] = validated.get(key, 0) + 1
        try:
            return func(*args, **kwargs)
        finally:
            if validated[key] > 1:
                validated[key] -= 1
            else:
                del validated[key]

    return wrapper


def _annotate_docstring(doc: Optional[str], support: BendSupport) -> Optional[str]:
    admonition = _ADMONITIONS.get(support)

    if admonition is None:
        return doc

    if doc is None or doc.strip() == "":
        return admonition

    # cleandoc() strips the indentation of the existing docstring. The admonition carries none, and
    # a mixture of the two is not valid reStructuredText.
    return f"{inspect.cleandoc(doc)}\n\n{admonition}"


def bend_support(support: BendSupport):
    """Decorator declaring how the decorated function responds to edge geometry."""
    if not isinstance(support, BendSupport):
        raise TypeError(f"Expected a BendSupport value, got {support!r}")

    def decorator(func: Callable) -> Callable:
        func.__bend_support__ = support
        func.__doc__ = _annotate_docstring(func.__doc__, support)
        _REGISTRY[_registry_key(func)] = support

        # The guard closes over the classification made here rather than consulting the registry.
        if support is BendSupport.STRAIGHT_LINE_ONLY:
            return _guard(func)

        return func

    return decorator


def bend_support_of(func: Callable) -> BendSupport:
    """The classification of the given function; raises ValueError if it carries none."""
    support = getattr(func, "__bend_support__", None)

    if support is None:
        # functools.wraps copies the attribute onto the wrapper; this covers wrappers that do not.
        support = getattr(inspect.unwrap(func), "__bend_support__", None)

    if support is None:
        name = getattr(func, "__qualname__", repr(func))
        raise ValueError(
            f"'{name}' is not annotated with a bend support classification"
        )

    return support
