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
)

from gdMetriX.utils import numeric
from gdMetriX.utils.intersections import check_lines
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
        self, pos: Dict[object, CrossingPoint], include_node_crossings: bool
    ) -> None:
        """
        Removes all elements of the crossing, which are false positives, i.e. which do not take part in the crossing.
        :return: None
        :rtype: None
        """
        if isinstance(self.pos, CrossingPoint):
            self._prune_crossing_point(pos, include_node_crossings)
        elif isinstance(self.pos, CrossingLine):
            self.involved_singletons = set()
            if len(self.involved_edges) == 1:
                self.involved_edges = set()

    def _prune_crossing_point(
        self, pos: Dict[object, CrossingPoint], include_node_crossings: bool
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

        # It might be the case that we have removed all actual crossings and what remains are just crossing lines
        # Crossing lines however are captured separately
        if len(self.involved_edges) > 1:
            just_lines = True
            edge_list = list(self.involved_edges)
            for index in range(1, len(edge_list)):
                if not isinstance(
                    check_lines(
                        SweepLineEdgeInfo.from_edge(edge_list[0], pos),
                        SweepLineEdgeInfo.from_edge(edge_list[index], pos),
                    ),
                    CrossingLine,
                ):
                    just_lines = False
                    break

            if just_lines:
                self.involved_edges = set()
                return


def _share_common_endpoint(edges: set) -> bool:
    if edges is None or len(edges) <= 1:
        return False

    common_elements = set(next(iter(edges)))

    for edge in edges:
        common_elements &= set(edge)

    return len(common_elements) > 0
