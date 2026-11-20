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
This module provides functions for dealing with crossings, including obtaining crossing angles.

Usage
-----

Get a quality metric based on the number of crossings using :func:`crossing_density()`:

.. code-block:: python

    >>> g = nx.random_geometric_graph(20, 0.5)
    >>> quality = crossing_density(g)

To obtain a list of all crossings, simply call :func:`get_crossings()`:

.. code-block:: python

    >>> crossing_list = get_crossings(g)

To planarize a graph, call :func:`planarize()`:

.. code-block:: python

    >>> planarize(g)

This will replace all crossings with new nodes at the same positions.

Methods
-------

"""
import math
from typing import List, Union

import networkx as nx

from gdMetriX import common
from gdMetriX.crossings._quadratic import crossings_quadratic
from gdMetriX.crossings._sweep import CrossingSweep
from gdMetriX.crossings.data_types import Crossing
from gdMetriX.utils.edge_orientations import edge_angles
from gdMetriX.utils.sweep_line import CrossingLine, CrossingPoint

class OverlappingEdgesError(ValueError):
    """Raised when an operation cannot handle overlapping (collinear) edges.

    Two edges that overlap along a shared segment intersect in a
    :class:`~gdMetriX.utils.sweep_line.CrossingLine` (a line segment) rather
    than in a single :class:`~gdMetriX.utils.sweep_line.CrossingPoint`. Some
    operations (e.g. :func:`planarize`) have no well-defined behavior for such
    crossings and raise this error instead of failing with an obscure
    ``TypeError``.

    It subclasses :class:`ValueError`, so existing ``except ValueError``
    handlers keep working.
    """


def _get_crossings_agnostic(
    g: nx.Graph,
    pos: Union[str, dict, None],
    include_node_crossings: bool,
    use_quadratic_algorithm: bool,
    precision: float,
    crossing_list: List[Crossing],
):
    if crossing_list is None:
        if use_quadratic_algorithm:
            crossing_list = get_crossings_quadratic(
                g, pos, include_node_crossings, precision=precision
            )
        else:
            crossing_list = get_crossings(
                g, pos, include_node_crossings, precision=precision
            )
    return crossing_list


@common.resolve_pos
def get_crossings_quadratic(
    g: nx.Graph,
    pos: Union[str, dict, None] = None,
    include_node_crossings: bool = False,
    consider_singletons: bool = False,
    precision: float = 1e-09,
) -> List[Crossing]:
    r"""
    This alternative crossing detection function is in general slower, but in certain worst-cases might outperform
    the :func:`get_crossings()` method. Use this method if you have problems with precision using the
    :func:`get_crossings()` method.


    The :func:`get_crossings()` method has an asymptotic runtime of :math:`O((n+k) \text{log} n)`, where :math:`k`
    is the number of crossings. This method runs in :math:`O(n^2)` time, which might outperform the optimized
    function slightly when the number of crossing is :math:`\Theta(n^2)`.

    :param g: A networkX graph
    :type g: nx.Graph
    :param pos: Optional node position dictionary. If not supplied, node positions are read from the graph directly.
        If given as a string, the property under the given name in the networkX graph is used.
    :type pos: Union[str, dict, None]
    :param include_node_crossings: Indicate whether crossings involving vertices should be returned as well. A
        crossing involves a vertex if an endpoint of an edge lies on another edge without actually crossing it.
        Singletons will never be considered, even if the vertex lies exactly on another edge.
    :type include_node_crossings: bool
    :param consider_singletons: If true, singletons that lie on an edge or other vertices will be reported as well.
    :type consider_singletons: bool
    :param precision: Sets the absolute numeric precision. Usually, it should not be necessary to adjust the default.
    :type precision: float
    :return: A list of crossings, with a list of involved edges per crossing.
    :rtype: List[Crossing]
    """

    if g is None:
        raise ValueError(g)
    if isinstance(g, (nx.MultiGraph, nx.MultiDiGraph)):
        raise ValueError("Multi graphs are not supported")

    if consider_singletons and not include_node_crossings:
        raise ValueError(
            f"Invalid parameter combinations: cannot consider singletons if node crossings are disabled as behaviour is undefined."
        )

    return crossings_quadratic(
        g, pos, include_node_crossings, consider_singletons, precision
    )


@common.resolve_pos
def get_crossings(
    g: nx.Graph,
    pos: Union[str, dict, None] = None,
    include_node_crossings: bool = False,
    consider_singletons: bool = False,
    precision: float = 1e-09,
) -> List[Crossing]:
    r"""
    Calculates all crossings occurring in the graph. This uses the Bentley-Ottmann
    algorithm :footcite:p:`bentley_algorithms_1979` - adapted to handle degenerate cases - and runs in
    :math:`O((n+k) \log (n+k))` time and space, where :math:`k` is the number of reported crossings.

    The sweepline approach is susceptible to precision errors. Set the precision parameter to a value big enough but
    smaller than the smallest distance expected between two crossings. In case of issues, use
    :func:`get_crossings_quadratic` instead.

    :param g: A networkX graph
    :type g: nx.Graph
    :param pos: Optional node position dictionary. If not supplied, node positions are read from the graph directly.
        If given as a string, the property under the given name in the networkX graph is used.
    :type pos: Union[str, dict, None]
    :param include_node_crossings: Indicate whether crossings involving vertices should be returned as well. A
        crossing involves a vertex if an endpoint of an edge lies on another edge without actually crossing it.
        Singletons will never be considered, even if the vertex lies exactly on another edge.
    :type include_node_crossings: bool
    :param consider_singletons: If true, singletons that lie on an edge or other vertices will be reported as well.
    :type consider_singletons: bool
    :param precision: Sets the absolute numeric precision. Usually, it should not be necessary to adjust the default.
    :type precision: float
    :return: A list of crossings, with a list of involved edges per crossing.
    :rtype: List[Crossing]
    """

    if g is None:
        raise ValueError(g)
    if isinstance(g, (nx.MultiGraph, nx.MultiDiGraph)):
        raise ValueError("Multi graphs are not supported")

    return CrossingSweep(
        g, pos, include_node_crossings, consider_singletons, precision
    ).run()


@common.resolve_pos
def planarize(
    g: nx.Graph,
    pos: Union[str, dict, None] = None,
    include_node_crossings: bool = False,
    use_quadratic_algorithm: bool = False,
    precision: float = 1e-09,
    crossing_list: List[Crossing] = None,
) -> None:
    """
    Planarizes the graph by replacing all crossings with nodes.

    :param g: A networkX graph
    :type g: nx.Graph
    :param pos: Optional node position dictionary. If not supplied, node positions are read from the graph directly.
        If given as a string, the property under the given name in the networkX graph is used.
    :type pos: Union[str, dict, None]
    :param include_node_crossings: Indicate whether crossings involving vertices should be considered as well. A
        crossing involves a vertex if an endpoint of an edge lies on another edge without actually crossing it.
        Singletons will never be considered, even if the vertex lies exactly on another edge.
    :type include_node_crossings: bool
    :param use_quadratic_algorithm: If set to true, the slower quadratic time algorithm is used to obtain crossings.
        Use this method if you have problems with precision using the default method.
        See :func:`get_crossings_quadratic()` for details.
    :type use_quadratic_algorithm: bool
    :param precision: Sets the absolute numeric precision. Usually, it should not be necessary to adjust the default.
    :type precision: float
    :param crossing_list: If supplied, these crossings are used to obtain the crossing angles.
    :type crossing_list: List[Crossings]
    """

    crossings = _get_crossings_agnostic(
        g,
        pos,
        include_node_crossings,
        use_quadratic_algorithm,
        precision,
        crossing_list,
    )

    # Obtain a list of crossing per edge
    involved_edges = {}
    for crossing in crossings:
        if isinstance(crossing.pos, CrossingLine):
            raise OverlappingEdgesError(
                "Cannot planarize a drawing with overlapping (collinear) edges: "
                f"the edges {list(crossing.involved_edges)} overlap along a "
                "line segment rather than crossing in a single point. Remove or "
                "perturb the overlapping edges before calling planarize()."
            )
        for edge in crossing.involved_edges:
            if edge in involved_edges:
                involved_edges[edge].append(crossing)
            else:
                involved_edges[edge] = [crossing]

    i = 0
    for edge, crossings in involved_edges.items():
        crossings = sorted(
            crossings, key=lambda cr: common.euclidean_distance(cr.pos, pos[edge[0]])
        )

        g.remove_edge(edge[0], edge[1])

        last_node = edge[0]
        for crossing in crossings:
            if not hasattr(crossing, "node_id"):
                crossing.node_id = "crossing" + str(i)
                new_pos = (crossing.pos.x, crossing.pos.y)
                g.add_node(crossing.node_id, pos=new_pos, is_elevated_crossing=True)
                pos[crossing.node_id] = new_pos
                i += 1

            if crossing.pos == CrossingPoint.from_point(pos[last_node]):
                if last_node == edge[0]:
                    if g.degree(last_node) == 0:
                        g.remove_node(last_node)
                last_node = crossing.node_id
                continue

            g.add_edge(last_node, crossing.node_id)

            last_node = crossing.node_id

        g.add_edge(last_node, edge[1])


def crossing_angles(
    crossing: Crossing, pos: Union[str, dict, None], deg: bool = False
) -> List[float]:
    """
    Returns a list of angles in clockwise order formed by the edges at the crossing point.

    :param crossing: A crossing point
    :type crossing: gdMetriX.Crossing
    :param pos: Optional node position dictionary. If not supplied, node positions are read from the graph directly.
        If given as a string, the property under the given name in the networkX graph is used.
    :type pos: Union[str, dict, None]
    :param deg: If true, the angles are returned as degrees in the range of (0,360). Otherwise, the angles are returned
        as radians.
    :type deg: bool
    :return: A list of angles at that crossing in clockwise order
    :rtype: List[float]
    """

    if isinstance(crossing.pos, CrossingLine):
        return (
            [0.0] * (len(crossing.involved_edges) - 1)
            + [180.0]
            + [0.0] * (len(crossing.involved_edges) - 1)
            + [180.0]
        )
    else:
        involved_nodes = {node for edge in crossing.involved_edges for node in edge}
        crossing_point: CrossingPoint = crossing.pos

        # Filter out nodes that are at the crossing itself
        involved_nodes = list(
            filter(
                lambda node: not CrossingPoint.from_point(pos[node]) == crossing_point,
                involved_nodes,
            )
        )

        return edge_angles(involved_nodes, crossing_point, pos, deg)


@common.resolve_pos
def crossing_angular_resolution(
    g: nx.Graph,
    pos: Union[str, dict, None] = None,
    include_node_crossings: bool = False,
    use_quadratic_algorithm: bool = False,
    precision: float = 1e-09,
    crossing_list: List[Crossing] = None,
) -> float:
    """
    Returns the deviation from the optimal angle between two edges at crossing points similar to
    :func:`edge_directions.angular_resolution`.

    :param g: A networkX graph
    :type g: nx.Graph
    :param pos: Optional node position dictionary. If not supplied, node positions are read from the graph directly.
        If given as a string, the property under the given name in the networkX graph is used.
    :type pos: Union[str, dict, None]
    :param include_node_crossings: Indicate whether crossings involving vertices should be considered as well. A
        crossing involves a vertex if an endpoint of an edge lies on another edge without actually crossing it.
        Singletons will never be considered, even if the vertex lies exactly on another edge.
    :type include_node_crossings: bool
    :param use_quadratic_algorithm: If set to true, the slower quadratic time algorithm is used to obtain crossings.
        Use this method if you have problems with precision using the default method.
        See :func:`get_crossings_quadratic()` for details.
    :type use_quadratic_algorithm: bool
    :param precision: Sets the absolute numeric precision. Usually, it should not be necessary to adjust the default.
    :type precision: float
    :param crossing_list: If supplied, these crossings are used to obtain the crossing angles.
    :type crossing_list: List[Crossings]
    :return: The average deviation from the optimal angle between two edges in any of the crossings
    :rtype: float
    """
    deviation_sum = 0
    crossing_list = _get_crossings_agnostic(
        g,
        pos,
        include_node_crossings,
        use_quadratic_algorithm,
        precision,
        crossing_list,
    )

    if len(crossing_list) == 0:
        return 0

    for crossing in crossing_list:
        optimal_angle = math.pi / len(crossing.involved_edges)
        minimum_angle = min(crossing_angles(crossing, pos))

        deviation_sum += abs(((optimal_angle - minimum_angle) / optimal_angle))

    return 1 - deviation_sum / len(crossing_list)


def _c_max(g: nx.Graph, include_mooney_cases: bool):
    def _n_choose_2(n: int):
        return (n * (n - 1)) // 2

    if g.is_directed():
        g = g.to_undirected()

    c_deg = sum(_n_choose_2(g.degree[i]) for i in g.nodes())

    c_4cyc = 0
    c_tri = 0

    if include_mooney_cases:
        num_triangles = 0
        triangle_nodes = set()
        for cycle in nx.simple_cycles(g, 4):
            if len(cycle) == 4:
                c_4cyc += 1
            elif len(cycle) == 3:
                triangle_nodes.update(cycle)
                num_triangles += 1

        # Count the number of crossing not possible due to triangles, which are not already contained in c_deg
        triangle_graph = g.subgraph(triangle_nodes)

        # Triangle edges not adjacent to any other triangle, a.k.a degree 2 nodes
        degree_2_nodes = [
            node for node, degree in triangle_graph.degree() if degree == 2
        ]
        c_tri += triangle_graph.subgraph(degree_2_nodes).number_of_edges()

        # Shared nodes between pairs of nodes
        shared_nodes = 3 * num_triangles - triangle_graph.order()
        c_tri += _n_choose_2(num_triangles) * 3 - shared_nodes

    m = g.number_of_edges()
    return _n_choose_2(m) - c_deg - c_tri - c_4cyc


@common.resolve_pos
def number_of_crossings(
    g: nx.Graph,
    pos: Union[str, dict, None] = None,
    include_node_crossings: bool = False,
    use_quadratic_algorithm: bool = False,
    precision: float = 1e-09,
    crossing_list: List[Crossing] = None,
) -> int:
    """
    Counts the total number of crossings in the given embedding.

    Crossings involving more than 2 edges are counted for each pair of involved edges separately. Two edges crossing
    in a line are counted as a single crossing as if they would cross in a point only.

    :param g: A networkX graph
    :type g: nx.Graph
    :param pos: Optional node position dictionary. If not supplied, node positions are read from the graph directly.
        If given as a string, the property under the given name in the networkX graph is used.
    :type pos: Union[str, dict, None]
    :param include_node_crossings: Indicate whether crossings involving vertices should be considered as well. A
        crossing involves a vertex if an endpoint of an edge lies on another edge without actually crossing it.
        Singletons will never be considered, even if the vertex lies exactly on another edge.
    :type include_node_crossings: bool
    :param use_quadratic_algorithm: If set to true, the slower quadratic time algorithm is used to obtain crossings.
        Use this method if you have problems with precision using the default method.
        See :func:`get_crossings_quadratic()` for details.
    :type use_quadratic_algorithm: bool
    :param precision: Sets the absolute numeric precision. Usually, it should not be necessary to adjust the default.
    :type precision: float
    :param crossing_list: If supplied, these crossings are used to obtain the crossing angles.
    :type crossing_list: List[Crossings]
    :return: Number of crossings
    :rtype: int
    """
    crossing_list = _get_crossings_agnostic(
        g,
        pos,
        include_node_crossings,
        use_quadratic_algorithm,
        precision,
        crossing_list,
    )
    total = 0

    for crossing in crossing_list:
        involved_edges = len(crossing.involved_edges)
        total += involved_edges * (involved_edges - 1) // 2

    return total


@common.resolve_pos
def crossing_density(
    g: nx.Graph,
    pos: Union[str, dict, None] = None,
    tighter_bound: bool = False,
    include_node_crossings: bool = False,
    use_quadratic_algorithm: bool = False,
    precision: float = 1e-09,
    crossing_list: List[Crossing] = None,
) -> float:
    """
    Weighs the number of crossings in the embedding against the estimated maximum number of potential crossings.

    The estimated maximum number of potential crossings is implemented
    as defined by :footcite:t:`purchase_landscape`.

    :param g: A networkX graph
    :type g: nx.Graph
    :param pos: Optional node position dictionary. If not supplied, node positions are read from the graph directly.
        If given as a string, the property under the given name in the networkX graph is used.
    :type pos: Union[str, dict, None]
    :param tighter_bound: If set to true, a tighter bound on the maximum number of potential crossings is calculated,
        which might however lie below the actual maximum number of crossings. See :footcite:t:`purchase_landscape` for
        details. If set to false, the original estimate by :footcite:t:`purchase_metrics_2002` is used.
    :type tighter_bound: bool
    :param include_node_crossings: Indicate whether crossings involving vertices should be considered as well. A
        crossing involves a vertex if an endpoint of an edge lies on another edge without actually crossing it.
        Singletons will never be considered, even if the vertex lies exactly on another edge.
    :type include_node_crossings: bool
    :param use_quadratic_algorithm: If set to true, the slower quadratic time algorithm is used to obtain crossings.
        Use this method if you have problems with precision using the default method.
        See :func:`get_crossings_quadratic()` for details.
    :type use_quadratic_algorithm: bool
    :param precision: Sets the absolute numeric precision. Usually, it should not be necessary to adjust the default.
    :type precision: float
    :param crossing_list: If supplied, these crossings are used to obtain the crossing angles.
    :type crossing_list: List[Crossings]
    :return: A crossing quality metric between 0 and 1
    :rtype: float
    """
    c_max = max(_c_max(g, tighter_bound), 1)
    estimate = (
        1
        - number_of_crossings(
            g,
            pos,
            include_node_crossings,
            use_quadratic_algorithm,
            precision,
            crossing_list,
        )
        / c_max
    )
    return max(min(estimate, 1), 0)
