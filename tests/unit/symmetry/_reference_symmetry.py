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
Reference (naive) implementation of the Purchase 2002 axial-symmetry metric.

This is the original, straightforward :math:`O(n^7)` implementation of
``reflective_symmetry``. It has been moved out of the shipped package (it is
not part of the PyPI distribution) and lives here purely as the oracle for the
regression tests that pin the optimized in-package ``reflective_symmetry``
against it. Do not use this for anything other than testing - it is slow by
design and kept only as a byte-for-byte trustworthy reference.
"""
from __future__ import annotations

import math
from typing import Union

import networkx as nx
import numpy as np
from scipy.spatial import ConvexHull, QhullError, KDTree

from gdMetriX import crossings, common, boundary
from gdMetriX.utils.numeric import numeric_eq
from gdMetriX.symmetry import _flip_point_around_axis


def reflective_symmetry(
    g: nx.Graph,
    pos: Union[str, dict, None] = None,
    threshold: int = 2,
    tolerance: float = 1e-2,
    fraction: float = 0.5,
) -> float:
    r"""
    Original naive reference implementation of the Purchase axial-symmetry
    metric. See :func:`gdMetriX.symmetry.reflective_symmetry` for the public,
    optimized version and full parameter documentation.
    """

    if threshold < 1:
        raise ValueError("threshold must be a positive integer")
    if tolerance <= 0:
        raise ValueError("tolerance must be positive")

    def _subgraph_area(nodes) -> float:
        try:
            ch = ConvexHull(list([[pos[node][0], pos[node][1]] for node in nodes]))
            return ch.volume
        except QhullError:
            return 0

    def _is_crossing_node(node):
        node = g.nodes[node]
        return "is_elevated_crossing" in node and node["is_elevated_crossing"]

    def _subgraph_symmetry(edge_pairs) -> float:

        if fraction == 1 or len(edge_pairs) == 0:
            return 1

        total = 0

        for pair_1, pair_2 in edge_pairs:
            factor_p = (
                fraction
                if _is_crossing_node(pair_1[0]) != _is_crossing_node(pair_2[0])
                else 1
            )
            factor_q = (
                fraction
                if _is_crossing_node(pair_1[1]) != _is_crossing_node(pair_2[1])
                else 1
            )

            total += factor_p * factor_q

        return total / len(edge_pairs)

    def _find_mirrored_nodes(pos_a, pos_b):

        node_positions = np.array([pos[node] for node in node_list])
        node_positions_mirrored = np.array(
            [_flip_point_around_axis(pos[node], pos_a, pos_b) for node in node_list]
        )

        kdtree = KDTree(node_positions)
        kdtree_mirrored = KDTree(node_positions_mirrored)

        matching_pairs = list(kdtree.query_ball_tree(kdtree_mirrored, r=tolerance))

        mirrored_nodes = []
        matching_pairs_dic = {}

        for i in range(len(matching_pairs)):
            if len(matching_pairs[i]) > 0:
                mirrored_nodes.append(node_list[i])

            matching_pairs_dic[node_list[i]] = matching_pairs[i]

        return mirrored_nodes, matching_pairs_dic

    if g.order() <= 1:
        return 1

    convex_hull_area = boundary.area_tight(g, pos)
    if convex_hull_area <= 0:
        return 1

    # Get node positions
    g = nx.edge_subgraph(g, g.edges()).copy()

    pos = common.get_node_positions(g, pos)
    nx.set_node_attributes(g, pos, "pos")

    # Planarize by replacing crossings with nodes
    crossings.planarize(g)
    pos = common.get_node_positions(g)
    n = len(g.nodes())

    total_area = 0.0
    total_symmetry = 0.0

    node_list = list(g.nodes())

    for i_a, node_a in enumerate(node_list):
        for i_b in range(i_a, n):
            node_b = node_list[i_b]

            if node_a == node_b or (
                numeric_eq(pos[node_a][0], pos[node_b][0])
                and numeric_eq(pos[node_a][1], pos[node_b][1])
            ):
                continue

            # Iterate over all node pairs

            pos_a = np.asarray(pos[node_a])
            pos_b = np.asarray(pos[node_b])

            mirrored_nodes, mirrored_node_pairs = _find_mirrored_nodes(pos_a, pos_b)

            if len(mirrored_nodes) <= math.floor(math.sqrt(threshold)):
                # In this case there cannot even be enough reflected edges
                # Abort before we even build the subgraph G_alpha
                continue

            # Edge-centric: collect only edges that have a mirrored counterpart.
            # Track unique pairs to avoid double-counting: iterating (u,v) and
            # then (mu,mv) would add both ((u,v),(mu,mv)) and ((mu,mv),(u,v)).
            # Threshold is compared against the number of *mirrored edges*
            # (Purchase 2002): a genuine pair contributes 2 (both edges have a
            # mirror), a self-symmetric edge contributes 1.
            seen_pairs: set = set()
            subgraph_edge_pairs = []
            subgraph_nodes = set()
            num_mirrored_edges = 0

            for u, v in g.edges():
                for mu_idx in mirrored_node_pairs[u]:
                    mu = node_list[mu_idx]
                    for mv_idx in mirrored_node_pairs[v]:
                        mv = node_list[mv_idx]
                        if g.has_edge(mu, mv) or g.has_edge(mv, mu):
                            key = frozenset(
                                {frozenset({u, v}), frozenset({mu, mv})}
                            )
                            if key in seen_pairs:
                                continue
                            seen_pairs.add(key)
                            subgraph_edge_pairs.append(((u, v), (mu, mv)))
                            subgraph_nodes.update([u, v, mu, mv])
                            if frozenset({u, v}) == frozenset({mu, mv}):
                                num_mirrored_edges += 1  # self-symmetric edge
                            else:
                                num_mirrored_edges += 2  # genuine mirror pair

            if num_mirrored_edges < threshold:
                continue

            sub_sym = _subgraph_symmetry(subgraph_edge_pairs)
            sub_area = _subgraph_area(subgraph_nodes)
            total_symmetry += sub_sym * sub_area
            total_area += sub_area

    return total_symmetry / max(total_area, convex_hull_area)
