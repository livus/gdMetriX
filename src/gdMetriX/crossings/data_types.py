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

from typing import (
    Union,
    Dict,
    List,
    Optional,
)

import networkx as nx

from gdMetriX import common
from gdMetriX.utils import numeric
from gdMetriX.crossings.intersections import check_lines
from gdMetriX.utils.sweep_line import (
    CrossingPoint,
    CrossingLine,
    SweepLineEdgeInfo,
)


class Crossing:
    """
    Represents a single crossing point
    """

    def __init__(
        self,
        pos: Union[CrossingPoint, CrossingLine],
        involved_edges: set,
        involved_singletons: set = None,
    ):
        if involved_singletons is None:
            involved_singletons = set()

        self.pos = pos
        self.involved_edges = involved_edges
        self.involved_singletons = involved_singletons

    def __str__(self):
        return f"[{self.pos}, edges: {sorted(self.involved_edges)}, singletons: {sorted(self.involved_singletons)}]"

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        if isinstance(other, Crossing):
            return (
                self.pos == other.pos
                and self.involved_edges == other.involved_edges
                and self.involved_singletons == other.involved_singletons
            )
        return False

    def __lt__(self, other):
        # Comparison purely based on CrPoint/CrLineSegment
        return self.pos < other.pos

    def __len__(self):
        return len(self.involved_edges) + len(self.involved_singletons)

    def prune(
        self,
        pos: Dict[object, CrossingPoint],
        include_node_crossings: bool,
        edge_infos: Optional[Dict[object, SweepLineEdgeInfo]] = None,
        known_relations: Optional[Dict[tuple, object]] = None,
    ) -> None:
        """
        Removes all elements of the crossing, which are false positives, i.e. which do not take part in the crossing.
        :param pos: Node positions
        :param include_node_crossings: Whether crossings involving vertices are kept
        :param edge_infos: Optionally, the already built SweepLineEdgeInfo of the edges, keyed by
            edge, so that they need not be built again for every crossing
        :param known_relations: Optionally, a cache of `check_lines` results keyed by the ordered
            pair of edges, computed from those same edge infos. It is used and extended in place.
        :return: None
        :rtype: None
        """
        if isinstance(self.pos, CrossingPoint):
            self._prune_crossing_point(
                pos, include_node_crossings, edge_infos, known_relations
            )
        elif isinstance(self.pos, CrossingLine):
            self.involved_singletons = set()
            if len(self.involved_edges) == 1:
                self.involved_edges = set()

    def _prune_crossing_point(
        self,
        pos: Dict[object, CrossingPoint],
        include_node_crossings: bool,
        known_edge_infos: Optional[Dict[object, SweepLineEdgeInfo]],
        known_relations: Optional[Dict[tuple, object]] = None,
    ) -> None:
        if not include_node_crossings:
            # Only add those edges which actually cross and not those just ending in that point
            edges = []
            for edge in self.involved_edges:
                if self.pos not in (pos[edge[0]], pos[edge[1]]):
                    edges.append(edge)

            self.involved_edges = set(edges)

        # Check if all edges share a common endpoint => not actually a crossing
        if len(self.involved_singletons) == 0 and _share_common_endpoint(
            self.involved_edges
        ):

            # If there are edges with length 0 (i.e. the second endpoint is still in the crossing point)
            # we actually still consider this a crossing
            if not any(
                edge[0] != edge[1]
                and numeric.numeric_eq(pos[edge[0]].distance(pos[edge[1]]), 0)
                for edge in self.involved_edges
            ):
                self.involved_edges = set()
                return

        # If only one element is left, this is not actually a crossing
        if len(self.involved_edges) + len(self.involved_singletons) <= 1:
            self.involved_edges = set()
            self.involved_singletons = set()
            return

        if len(self.involved_edges) > 1:
            edge_list = list(self.involved_edges)
            if known_edge_infos is None:
                known_edge_infos = {}
            edge_infos = {
                edge: (
                    known_edge_infos[edge]
                    if edge in known_edge_infos
                    else SweepLineEdgeInfo.from_edge(edge, pos)
                )
                for edge in edge_list
            }
            relation_cache: Dict[tuple, object] = (
                {} if known_relations is None else known_relations
            )

            def relation(a, b):
                key = (a, b)
                if key not in relation_cache:
                    relation_cache[key] = check_lines(edge_infos[a], edge_infos[b])
                return relation_cache[key]

            # It might be the case that we have removed all actual crossings and
            # what remains are just crossing lines. Crossing lines however are
            # captured separately.
            just_lines = all(
                isinstance(relation(edge_list[0], other), CrossingLine)
                for other in edge_list[1:]
            )
            if just_lines:
                self.involved_edges = set()
                return

            # An edge might still be in the bundle only incidentally - e.g. it merely
            # shares a node with another involved edge, or it is collinear with one of
            # them (already reported separately as a CrossingLine) - without actually
            # taking part in a crossing at this exact point itself. Such edges have no
            # genuine CrossingPoint relation (via check_lines) to any other edge in the
            # bundle and must be dropped, or they get reported as part of a crossing
            # they don't belong to.
            survivors = set()
            for edge in edge_list:
                for other in edge_list:
                    if other == edge:
                        continue
                    rel = relation(edge, other)
                    if isinstance(rel, CrossingPoint) and rel == self.pos:
                        survivors.add(edge)
                        break
            self.involved_edges = survivors

            if len(self.involved_edges) + len(self.involved_singletons) <= 1:
                self.involved_edges = set()
                self.involved_singletons = set()
                return


def _share_common_endpoint(edges: set) -> bool:
    if edges is None or len(edges) <= 1:
        return False

    common_elements = set(next(iter(edges)))

    for edge in edges:
        common_elements &= set(edge)

    return len(common_elements) > 0


def convert_to_crossing_points(
    g: nx.Graph, pos: Union[List, dict, None]
) -> Dict[object, CrossingPoint]:
    """Returns the node positions of the drawing as crossing points."""
    pos = common.get_node_positions(g, pos)
    return {key: CrossingPoint.from_point(position) for key, position in pos.items()}
