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
The Bentley-Ottmann sweep behind :func:`gdMetriX.crossings.get_crossings`, adapted to handle
degenerate drawings: crossings of more than two edges, nodes lying on edges, horizontal edges and
edges overlapping along a line.
"""

import itertools
import sys
from bisect import bisect_left
from typing import Dict, List, Optional, Set, Tuple, Union

import networkx as nx

from gdMetriX import boundary
from gdMetriX.common import Numeric
from gdMetriX.crossings.data_types import Crossing, convert_to_crossing_points
from gdMetriX.crossings.intersections import check_lines
from gdMetriX.utils import numeric
from gdMetriX.utils.numeric import numeric_eq
from gdMetriX.utils.sweep_line import (
    CrossingLine,
    CrossingPoint,
    EventQueue,
    SweepLineAlgorithm,
    SweepLineEdgeInfo,
    SweepLinePoint,
    SweepLineStatus,
    get_x_at_y,
)


def build_event_queue(
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


class CrossingSweep(SweepLineAlgorithm[SweepLinePoint, List[Crossing]]):
    """
    Implements the Bentley-Ottmann sweep used by :func:`get_crossings`.
    """

    def __init__(
        self,
        g: nx.Graph,
        pos: Union[str, dict, None],
        include_node_crossings: bool,
        consider_singletons: bool,
        precision: float,
    ):
        super().__init__()

        self.g = g
        self.include_node_crossings = include_node_crossings
        self.consider_singletons = consider_singletons

        numeric.set_precision(precision)

        self.node_positions = convert_to_crossing_points(g, pos)
        self.height = boundary.height(g, pos)

        self.crossings: List[Crossing] = []
        self.crossing_lines: List[Crossing] = []

        self.previous_y = None
        self.horizontal_edges = (
            []
        )  # Contains all horizontal edges at the current event point

        self.queue: Optional[EventQueue] = None

    # region SweepLineAlgorithm implementation

    def _build_events(self) -> None:
        self.queue = build_event_queue(
            self.g, self.node_positions, self.consider_singletons
        )

    def _pop_event(self) -> Optional[SweepLinePoint]:
        return self.queue.pop()

    def _finalize(self) -> List[Crossing]:
        # Join crossing lines with completely identical regions
        crossing_lines = sorted(self.crossing_lines)

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
        for cr in self.crossings:
            cr.prune(self.node_positions, self.include_node_crossings)
            if len(cr) > 1:
                crossing_points_consolidated.append(cr)

        return crossing_points_consolidated + crossing_lines_consolidated

    # endregion

    # region Crossing-specific helper methods

    def _insert_crossing_directly(self, c: Crossing) -> None:
        c.prune(self.node_positions, self.include_node_crossings)
        if len(c) <= 1:
            return

        index = bisect_left(self.crossings, c)

        if index < len(self.crossings):
            if self.crossings[index].pos == c.pos:
                self.crossings[index].involved_edges |= c.involved_edges
                self.crossings[index].involved_singletons |= c.involved_singletons
                return
            if self.crossings[index - 1].pos == c.pos:
                self.crossings[index - 1].involved_edges |= c.involved_edges
                self.crossings[index - 1].involved_singletons |= c.involved_singletons
                return

        self.crossings.insert(index, c)

    @staticmethod
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

    @staticmethod
    def _get_tied_group(
        edges: Set[SweepLineEdgeInfo], representative: SweepLineEdgeInfo, y: Numeric
    ) -> List[SweepLineEdgeInfo]:
        # Several edges can be exactly tied at the probe height used by
        # _get_extreme_edges - most commonly several collinear (e.g. vertical)
        # edges, whose x doesn't depend on y at all. _get_extreme_edges only ever
        # returns one of them; if that one happens to have a finite extent that
        # doesn't actually reach the point where the outer edge crosses the group
        # (while a tied sibling's extent does), testing only the chosen
        # representative misses the crossing entirely. So every exact tie needs to
        # be tried, not just whichever one was picked.
        representative_x = get_x_at_y(representative, y)
        return [e for e in edges if numeric_eq(get_x_at_y(e, y), representative_x)]

    @staticmethod
    def _get_ties(
        sweep_line_status: SweepLineStatus,
        edge: Optional[SweepLineEdgeInfo],
        current_event_point: SweepLinePoint,
    ) -> Optional[Set[SweepLineEdgeInfo]]:
        if edge is None:
            return None
        x = get_x_at_y(edge, current_event_point.position.y)
        return set(sweep_line_status.get_range(current_event_point.position.y, x, x))

    def _append_crossing_to_queue(
        self,
        e1: SweepLineEdgeInfo,
        e2: SweepLineEdgeInfo,
        current_event_point: SweepLinePoint,
        edges_involved_at_current_event_point: List[SweepLineEdgeInfo],
    ) -> None:
        potential_crossing_point = check_lines(e1, e2)
        if potential_crossing_point is not None and not isinstance(
            potential_crossing_point, CrossingLine
        ):
            # Crossing lines (i.e. overlapping edges) are checked separately,
            # which is why we skip them here

            if current_event_point.position < potential_crossing_point:
                # Add to the queue to process later.
                self.queue.add_crossing(potential_crossing_point, [e1, e2])

            elif current_event_point.position == potential_crossing_point:
                # This can only be the case if this is a crossing involving a vertex (i.e. check via bool flag)
                # We add the involved edges to the current crossing instead of adding a new event point
                if self.include_node_crossings:
                    edges_involved_at_current_event_point.append(e1)
                    edges_involved_at_current_event_point.append(e2)

            elif e1.is_horizontal() or e2.is_horizontal():
                # Horizontal edges are inserted right away
                self._insert_crossing_directly(
                    Crossing(potential_crossing_point, {e1.edge, e2.edge})
                )
            else:
                # In case the crossing came before, we assume it is already discovered
                pass

    # endregion

    def _handle_event(self, event: SweepLinePoint) -> None:
        current_event_point = event
        sweep_line_status = self.status

        # Reset horizontal edges at current event point if we go to a new point
        if self.previous_y is not None and not numeric_eq(
            current_event_point.position.y, self.previous_y
        ):
            self.horizontal_edges = []

        # In some cases (for example if an edge is horizontal or if the vertex itself is involved in the crossing)
        # we only discover crossings at the current point.
        # We save those here to add at the end
        edges_discovered_at_current_event_point = []

        # Start by removing all ends from the sweep line status
        for edge_info in current_event_point.end_list:
            sl_size_before = len(sweep_line_status)
            sweep_line_status.remove(self.previous_y, edge_info)

            # TODO Investigate why the normal remove sometimes does not catch the edge
            if len(sweep_line_status) == sl_size_before:
                sweep_line_status.force_remove(edge_info)

        # reverse the order of interior edges
        for edge in current_event_point.interior_list:
            sl_size_before = len(sweep_line_status)

            sweep_line_status.remove(self.previous_y, edge)

            # TODO Investigate why the normal remove sometimes does not catch the edge
            if len(sweep_line_status) == sl_size_before:
                sweep_line_status.remove(current_event_point.position.y, edge)
                if len(sweep_line_status) == sl_size_before:
                    sweep_line_status.force_remove(edge)

        for edge in current_event_point.interior_list:
            sweep_line_status.add(
                current_event_point.position.y - numeric.get_precision(), edge
            )

        left_edge = sweep_line_status.get_left(current_event_point)
        right_edge = sweep_line_status.get_right(current_event_point)

        # Get the edges just to the left/right of the current event point
        # Can be multiple ones if they overlap at the current y
        left_candidates = (
            self._get_ties(sweep_line_status, left_edge, current_event_point) or set()
        )
        right_candidates = (
            self._get_ties(sweep_line_status, right_edge, current_event_point) or set()
        )

        if (
            len(current_event_point.start_list) == 0
            and len(current_event_point.interior_list) == 0
        ):
            # Nothing comes below that is connected to the current event point
            # So we check the above and below neighbour for crossings
            for left_candidate in left_candidates or {None}:
                for right_candidate in right_candidates or {None}:
                    self._append_crossing_to_queue(
                        left_candidate,
                        right_candidate,
                        current_event_point,
                        edges_discovered_at_current_event_point,
                    )
        else:
            union = current_event_point.interior_list | current_event_point.start_list

            # Zero-length edges have no meaningful direction at the probe height
            # used below (their x is constant, equal to their single point,
            # regardless of y) - so they can spuriously look "more extreme" than a
            # genuinely sloped edge that's actually the one which needs testing
            # against the outer neighbour. They're never inserted into the sweep
            # line status itself (see the start_list insertion loop further down),
            # so exclude them here and fall back to the full union only if nothing
            # else qualifies.
            directional_union = {
                e for e in union if e.start_position != e.end_position
            } or union

            probe_y = current_event_point.position.y - 100 * numeric.get_precision()
            leftmost, rightmost = self._get_extreme_edges(directional_union, probe_y)

            # Several members of the union can likewise be exactly tied at the
            # probe height (e.g. several collinear/vertical edges) -
            # _get_extreme_edges only ever returns one of them, but a tied sibling
            # can have a different finite extent that's actually the one reaching
            # the outer edge, so every exact tie has to be tried too. Trying every
            # combination of outer candidate x tied union member (rather than
            # picking one representative of each and only conditionally expanding
            # afterwards) is what actually guarantees a genuine crossing isn't
            # missed just because the first pair tried happens to fall outside one
            # of the two edges' finite extent.
            left_group = (
                self._get_tied_group(directional_union, leftmost, probe_y)
                if leftmost is not None
                else [None]
            )
            right_group = (
                self._get_tied_group(directional_union, rightmost, probe_y)
                if rightmost is not None
                else [None]
            )

            for left_candidate in left_candidates or {None}:
                for member in left_group:
                    self._append_crossing_to_queue(
                        left_candidate,
                        member,
                        current_event_point,
                        edges_discovered_at_current_event_point,
                    )
            for right_candidate in right_candidates or {None}:
                for member in right_group:
                    self._append_crossing_to_queue(
                        right_candidate,
                        member,
                        current_event_point,
                        edges_discovered_at_current_event_point,
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
        if self.include_node_crossings:
            involved_edges |= (
                current_event_point.start_list
                | current_event_point.end_list
                | current_event_point.horizontal_list
            )

        involved_singletons = set()
        if self.consider_singletons:
            involved_singletons |= current_event_point.singletons

        if len(involved_edges) + len(involved_singletons) > 0:
            involved_edges |= set(self.horizontal_edges)
            crossing = Crossing(
                current_event_point.position,
                {edge.edge for edge in involved_edges},
                involved_singletons,
            )
            self._insert_crossing_directly(crossing)

        # endregion

        # region Check for crossing lines
        if len(current_event_point.start_list) > 0:
            # Check every pair of edges touching this point (whether starting here
            # or already passing through) for an overlap.
            overlap_candidates = list(edges_from_sweepline) + list(
                current_event_point.start_list
            )

            for a, b in itertools.combinations(overlap_candidates, 2):
                crossing = check_lines(a, b)
                if isinstance(crossing, CrossingLine):
                    self.crossing_lines.append(Crossing(crossing, {a.edge, b.edge}))

        # endregion

        # Check horizontal edges for line intersection
        for horizontal in current_event_point.horizontal_list:
            for edge_info in sweep_line_status.get_range(
                current_event_point.position.y,
                horizontal.start_position[0],
                horizontal.end_position[0],
            ):
                self._append_crossing_to_queue(
                    horizontal,
                    edge_info,
                    current_event_point,
                    edges_discovered_at_current_event_point,
                )

            if horizontal.start_position == current_event_point.position:
                for edge_info in self.horizontal_edges:
                    crossing_line = check_lines(edge_info, horizontal)
                    # It might be the case that this returns just a point
                    # => This is tested in the region called "Check all edges at the current point for intersection"
                    # We can thus safely ignore crossing points here
                    if isinstance(crossing_line, CrossingLine):
                        self.crossing_lines.append(
                            Crossing(crossing_line, {edge_info.edge, horizontal.edge})
                        )
                self.horizontal_edges.append(horizontal)
            elif horizontal.end_position == current_event_point.position:
                self.horizontal_edges.remove(horizontal)

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

            if self.include_node_crossings:
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
            self._insert_crossing_directly(new_crossing)
        else:
            pass

        self.previous_y = current_event_point.position.y
