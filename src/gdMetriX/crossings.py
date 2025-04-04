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
import itertools
import math
import sys
from typing import List, Optional, Tuple, Union, Set, Dict

import networkx as nx
from bisect import bisect_left

from gdMetriX import common, boundary
from gdMetriX.utils import crossing_data_types
from gdMetriX.common import Numeric
from gdMetriX.utils.crossing_data_types import (
    Crossing,
)
from gdMetriX.utils import numeric
from gdMetriX.utils.edge_orientations import edge_angles
from gdMetriX.utils.intersections import check_lines, check_point_and_line
from gdMetriX.utils.numeric import numeric_eq
from gdMetriX.utils.sweep_line import (
    get_x_at_y,
    CrossingPoint,
    EventQueue,
    SweepLineEdgeInfo,
    SweepLineStatus,
    CrossingLine,
)

# region Common helper functions


def _convert_to_crossing_points(
    g: nx.Graph, pos: Union[List, dict, None]
) -> Dict[object, CrossingPoint]:
    pos = common.get_node_positions(g, pos)
    return {key: CrossingPoint.from_point(position) for key, position in pos.items()}


def _build_event_queue(
    g, node_positions: Dict[object, CrossingPoint], consider_singletons: bool
):
    queue = EventQueue()
    for e in g.edges():
        edge_info = SweepLineEdgeInfo(
            e,
            node_positions[e[0]],
            node_positions[e[1]],
        )
        queue.add_edge(edge_info)

    if consider_singletons:
        for node in nx.isolates(g):
            queue.add_singleton(node_positions[node], node)

    return queue


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


# endregion


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
    :type pos: Union[str, dic, None]
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

    numeric.set_precision(precision)
    node_positions = _convert_to_crossing_points(g, pos)
    crossings = []

    for edge1, edge2 in itertools.combinations(g.edges(), 2):
        crossing_point = check_lines(
            crossing_data_types.SweepLineEdgeInfo.from_edge(edge1, node_positions),
            crossing_data_types.SweepLineEdgeInfo.from_edge(edge2, node_positions),
        )

        if crossing_point is not None:
            crossings.append(Crossing(crossing_point, {edge1, edge2}))

    if consider_singletons:
        singletons = list(sorted(nx.isolates(g), key=lambda x: node_positions[x]))

        previous_singleton = None
        prev_pos = None

        for singleton in singletons:
            current_pos = node_positions[singleton]

            if current_pos == prev_pos:
                crossings.append(
                    Crossing(current_pos, set(), {singleton, previous_singleton})
                )
            else:
                # Check all edges for overlap
                for edge in g.edges():
                    crossing_point = check_point_and_line(
                        current_pos,
                        crossing_data_types.SweepLineEdgeInfo.from_edge(
                            edge, node_positions
                        ),
                    )

                    if crossing_point is not None:
                        crossings.append(Crossing(current_pos, {edge}, {singleton}))
                        break

            print(f"Singleton: {singleton}")

            previous_singleton = singleton
            prev_pos = node_positions[previous_singleton]

    crossings.sort()

    # Group together crossings
    previous_crossing = None

    i = 0
    while i < len(crossings):
        crossing = crossings[i]
        if previous_crossing is not None and previous_crossing.pos == crossing.pos:
            previous_crossing.involved_edges.update(crossing.involved_edges)
            previous_crossing.involved_singletons.update(crossing.involved_singletons)
            crossings.pop(i)
        else:
            i += 1
            previous_crossing = crossing

    def _filter_node_crossings(cr: Crossing):
        if isinstance(cr.pos, CrossingPoint):
            cr.prune(node_positions, include_node_crossings)
        return len(cr) > 1

    return list(filter(_filter_node_crossings, crossings))


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
    :type pos: Union[str, dic, None]
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

    numeric.set_precision(precision)

    node_positions = _convert_to_crossing_points(g, pos)

    height = boundary.height(g, pos)

    crossings: List[Crossing] = []
    crossing_lines = []
    sweep_line_status = SweepLineStatus()

    # Initialize event points
    queue = _build_event_queue(g, node_positions, consider_singletons)

    def _insert_crossing_directly(c: Crossing) -> None:
        c.prune(node_positions, include_node_crossings)
        if len(c) <= 1:
            return

        index = bisect_left(crossings, c)

        if index < len(crossings):
            if crossings[index].pos == c.pos:
                crossings[index].involved_edges |= c.involved_edges
                crossings[index].involved_singletons |= c.involved_singletons
                return
            if crossings[index - 1].pos == c.pos:
                crossings[index - 1].involved_edges |= c.involved_edges
                crossings[index - 1].involved_singletons |= c.involved_singletons
                return

        crossings.insert(index, c)

    def _get_extreme_edges(
        edges: Set[SweepLineEdgeInfo], y: Numeric
    ) -> Tuple[Optional[SweepLineEdgeInfo], Optional[SweepLineEdgeInfo]]:
        smallest_x = sys.maxsize
        smallest_edge = None
        biggest_x = (sys.maxsize - 1) * -1
        biggest_edge = None

        for e in edges:
            x = get_x_at_y(e, y)
            if x <= smallest_x:
                smallest_x = x
                smallest_edge = e
            if x > biggest_x:
                biggest_x = x
                biggest_edge = e
        return smallest_edge, biggest_edge

    def _append_crossing_to_queue(
        e1: SweepLineEdgeInfo,
        e2: SweepLineEdgeInfo,
        edges_involved_at_current_event_point: List[SweepLineEdgeInfo],
    ) -> None:
        potential_crossing_point = check_lines(e1, e2)
        if potential_crossing_point is not None and not isinstance(
            potential_crossing_point, crossing_data_types.CrossingLine
        ):
            # Crossing lines (i.e. overlapping edges) are checked separately,
            # which is why we skip them here

            if current_event_point.position < potential_crossing_point:
                # Add to the queue to process later
                queue.add_crossing(potential_crossing_point, [e1, e2])

            elif current_event_point.position == potential_crossing_point:
                # This can only be the case if this is a crossing involving a vertex (i.e. check via bool flag)
                # We add the involved edges to the current crossing instead of adding a new event point
                if include_node_crossings:
                    edges_involved_at_current_event_point.append(e1)
                    edges_involved_at_current_event_point.append(e2)

            elif e1.is_horizontal() or e2.is_horizontal():
                # Horizontal edges are inserted right away
                _insert_crossing_directly(
                    Crossing(potential_crossing_point, {e1.edge, e2.edge})
                )
            else:
                # In case the crossing came before, we assume it is already discovered
                pass

    previous_y = None

    horizontal_edges = []  # Contains all horizontal edges at the current event point

    while (current_event_point := queue.pop()) is not None:

        # Reset horizontal edges at current event point if we go to a new point
        if previous_y is not None and not numeric_eq(
            current_event_point.position.y, previous_y
        ):
            horizontal_edges = []

        # In some cases (for example if an edge is horizontal or if the vertex itself is involved in the crossing)
        # we only discover crossings at the current point.
        # We save those here to add at the end
        edges_discovered_at_current_event_point = []

        # Start by removing all ends from the sweep line status
        for edge_info in current_event_point.end_list:
            sl_size_before = len(sweep_line_status)
            sweep_line_status.remove(previous_y, edge_info)

            # TODO Investigate why the normal remove sometimes does not catch the edge
            if len(sweep_line_status) == sl_size_before:
                sweep_line_status.force_remove(edge_info)

        # reverse the order of interior edges
        for edge in current_event_point.interior_list:
            sl_size_before = len(sweep_line_status)

            sweep_line_status.remove(previous_y, edge)

            # TODO Investigate why the normal remove sometimes does not catch the edge
            if len(sweep_line_status) == sl_size_before:
                sweep_line_status.remove(current_event_point.position.y, edge)
                if len(sweep_line_status) == sl_size_before:
                    sweep_line_status.force_remove(edge)

            sweep_line_status.add(
                current_event_point.position.y - numeric.get_precision(), edge
            )

        left_edge = sweep_line_status.get_left(current_event_point)
        right_edge = sweep_line_status.get_right(current_event_point)

        if (
            len(current_event_point.start_list) == 0
            and len(current_event_point.interior_list) == 0
        ):
            # Nothing comes below that is connected to the current event point
            # So we check the above and below neighbour for crossings
            _append_crossing_to_queue(
                left_edge, right_edge, edges_discovered_at_current_event_point
            )
        else:
            union = current_event_point.interior_list | current_event_point.start_list

            leftmost, rightmost = _get_extreme_edges(
                union,
                current_event_point.position.y - 100 * numeric.get_precision(),
            )

            _append_crossing_to_queue(
                left_edge, leftmost, edges_discovered_at_current_event_point
            )
            _append_crossing_to_queue(
                right_edge, rightmost, edges_discovered_at_current_event_point
            )

        # region Check all edges at the current point for intersection

        involved_edges = set()

        # Check edges at the actual crossing (this is necessary for covering edge cases not in general position)
        edges_from_sweepline = set(
            sweep_line_status.get_range(
                current_event_point.position.y,
                current_event_point.position.x,
                current_event_point.position.x,
            )
        )
        involved_edges |= edges_from_sweepline

        # Potential candidates for node-edge crossings
        if include_node_crossings:
            involved_edges |= (
                current_event_point.start_list
                | current_event_point.end_list
                | current_event_point.horizontal_list
            )

        involved_singletons = set()
        if consider_singletons:
            involved_singletons |= current_event_point.singletons

        if len(involved_edges) + len(involved_singletons) > 0:
            involved_edges |= set(horizontal_edges)
            crossing = Crossing(
                current_event_point.position,
                {edge.edge for edge in involved_edges},
                involved_singletons,
            )
            _insert_crossing_directly(crossing)

        # endregion

        # region Check for crossing lines
        if len(current_event_point.start_list) > 0:
            candidates_sorted = sorted(
                edges_from_sweepline,
                key=lambda e: get_x_at_y(e, current_event_point.position.y - height),
            )
            start_sorted = sorted(
                current_event_point.start_list,
                key=lambda e: get_x_at_y(e, current_event_point.position.y - height),
            )

            index_candidate = index_start = 0
            start_group = []
            candidate_group = []
            while index_start < len(start_sorted) or index_candidate < len(
                candidates_sorted
            ):
                overlap_starts = (
                    check_lines(
                        start_sorted[index_start], start_sorted[index_start + 1]
                    )
                    if index_start < len(start_sorted) - 1
                    else None
                )
                overlap_candidate = (
                    check_lines(
                        start_sorted[index_start], candidates_sorted[index_candidate]
                    )
                    if index_candidate < len(candidates_sorted)
                    and index_start < len(start_sorted)
                    else None
                )

                if isinstance(overlap_starts, CrossingLine):
                    start_group.append(start_sorted[index_start])
                    start_group.append(start_sorted[index_start + 1])
                    index_start += 1
                elif isinstance(overlap_candidate, CrossingLine):
                    start_group.append(start_sorted[index_start])
                    candidate_group.append(candidates_sorted[index_candidate])
                    index_candidate += 1
                else:
                    # Report group pairwise as line crossings
                    for a, b in itertools.combinations(start_group, 2):
                        if a == b:
                            continue

                        crossing = check_lines(a, b)

                        if isinstance(crossing, CrossingLine):
                            crossing_lines.append(Crossing(crossing, {a.edge, b.edge}))

                    for a in start_group:
                        for b in candidate_group:

                            crossing = check_lines(a, b)
                            if isinstance(crossing, CrossingLine):
                                crossing_lines.append(
                                    Crossing(crossing, {a.edge, b.edge})
                                )

                    start_group = []
                    candidate_group = []

                    if index_start == len(start_sorted):
                        index_candidate += 1
                    elif index_candidate == len(candidates_sorted):
                        index_start += 1
                    elif get_x_at_y(
                        start_sorted[index_start], current_event_point.position.y - 1000
                    ) < get_x_at_y(
                        candidates_sorted[index_candidate],
                        current_event_point.position.y - 1000,
                    ):
                        index_start += 1
                    else:
                        index_candidate += 1

        # endregion

        # Check horizontal edges for line intersection
        for horizontal in current_event_point.horizontal_list:
            for edge_info in sweep_line_status.get_range(
                current_event_point.position.y,
                horizontal.start_position[0],
                horizontal.end_position[0],
            ):
                _append_crossing_to_queue(
                    horizontal, edge_info, edges_discovered_at_current_event_point
                )

            if horizontal.start_position == current_event_point.position:
                for edge_info in horizontal_edges:
                    crossing_line = check_lines(edge_info, horizontal)
                    # It might be the case that this returns just a point
                    # => This is tested in the region called "Check all edges at the current point for intersection"
                    # We can thus safely ignore crossing points here
                    if isinstance(crossing_line, CrossingLine):
                        crossing_lines.append(
                            Crossing(crossing_line, {edge_info.edge, horizontal.edge})
                        )
                horizontal_edges.append(horizontal)
            elif horizontal.end_position == current_event_point.position:
                horizontal_edges.remove(horizontal)

        # Insert start points
        for edge_info in current_event_point.start_list:
            # In case the edge both starts and ends at the same point, we dont want to have
            # it in the sweepline further down
            if not edge_info.start_position == edge_info.end_position:
                sweep_line_status.add(
                    current_event_point.position.y - numeric.get_precision(),
                    edge_info,
                )

        # In order to report all crossings in order, we report it only after encountering it on the sweepline
        if (
            current_event_point.is_crossing
            or len(edges_discovered_at_current_event_point) != 0
        ):
            relevant_edges = current_event_point.interior_list

            if include_node_crossings:
                relevant_edges |= (
                    current_event_point.start_list
                    | current_event_point.end_list
                    | current_event_point.horizontal_list
                    | set(edges_discovered_at_current_event_point)
                )

            new_crossing = Crossing(
                current_event_point.position,
                set(list(map(lambda x: x.edge, relevant_edges))),
                current_event_point.singletons,
            )
            _insert_crossing_directly(new_crossing)
        else:
            pass

        previous_y = current_event_point.position.y

    # Join crossing lines with completely identical regions
    crossing_lines = sorted(crossing_lines)

    crossing_lines_consolidated = []
    for i in range(0, len(crossing_lines) - 1):
        if crossing_lines[i].pos == crossing_lines[i + 1].pos:
            crossing_lines[i + 1].involved_edges |= crossing_lines[i].involved_edges
        else:
            crossing_lines_consolidated.append(crossing_lines[i])
    if len(crossing_lines) > 0:
        crossing_lines_consolidated.append(crossing_lines[len(crossing_lines) - 1])

    # Remove false positives
    crossing_points_consolidated = []
    for cr in crossings:
        cr.prune(node_positions, include_node_crossings)
        if len(cr) > 1:
            crossing_points_consolidated.append(cr)

    return crossing_points_consolidated + crossing_lines_consolidated


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
    :type pos: Union[str, dic, None]
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

    pos = common.get_node_positions(g, pos)

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
    :type pos: Union[str, dic, None]
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
    :type pos: Union[str, dic, None]
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
    pos = common.get_node_positions(g, pos)
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
    :type pos: Union[str, dic, None]
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
    :type pos: Union[str, dic, None]
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
