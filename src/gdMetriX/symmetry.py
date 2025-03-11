# gdMetriX
#
# Copyright (C) 2013  Roman Klapaukh (for edge_based_symmetry)
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
This module defines some symmetry metrics.

Methods
-------

"""
from __future__ import annotations

import math
from enum import Enum
from typing import Union, Tuple

from matplotlib.backends.backend_agg import FigureCanvasAgg
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
from scipy import ndimage
from scipy.spatial import ConvexHull, QhullError, KDTree

from gdMetriX import crossings, common, boundary
from gdMetriX.common import Numeric, Vector
from gdMetriX.distribution import smallest_enclosing_circle_from_point_set


def _flip_point_around_axis(p: np.array, a: np.array, b: np.array) -> np.array:
    m = (a + b) / 2
    v_ab = b - a
    v_mp = p - m

    # Obtain the perpendicular bisector
    v_ab_rot = np.asarray((v_ab[1], v_ab[0] * -1))
    v_ab_rot_norm = v_ab_rot / np.linalg.norm(v_ab_rot)

    projection = m + v_mp.dot(v_ab_rot_norm) * v_ab_rot_norm

    v_pl = projection - p
    return p + 2 * v_pl


def reflective_symmetry(
    g: nx.Graph,
    pos: Union[str, dict, None] = None,
    threshold: int = 2,
    tolerance: float = 1e-2,
    fraction: float = 1,
) -> float:
    r"""
    Computes a metric for axial symmetry between 0 and 1 as defined by :footcite:t:`purchase_metrics_2002`.

    The metric sums up the symmetry for all axes defined by pairs of points. For each such axis, a symmetry value
    is calculated for all subgraphs with sufficiently many reflected nodes. The symmetry values for each subgraph
    are weighted by the area of the subgraph and summed up.

    Note that, with a worst-case runtime of :math:`O(n^7)` and a best-case runtime of :math:`O(n^5)`,
    the metric is computationally very expensive.

    :param g: A networkX graph
    :type g: nx.Graph
    :param pos: Optional node position dictionary. If not supplied, node positions are read from the graph directly.
            If given as a string, the property under the given name in the networkX graph is used.
    :type pos: Union[str, dic, None]
    :param threshold: The minimum number of edges a subgraph needs in order to be considered to be symmetric
    :type threshold: int
    :param tolerance: The tolerance for when two points should be considered to be at the same position.
    :type tolerance: float
    :param fraction: A weighing of how much crossings and endpoints should be distinguished between 0 and 1. 1 means
            that we do not care about whether a point is a crossing or an endpoint regarding detecting symmetry and the
            two are treated equally.
    :type fraction:
    :return: Axial symmetry estimate between 0 and 1
    :rtype: float
    """

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
            factor_1 = (
                fraction
                if _is_crossing_node(pair_1[0]) != _is_crossing_node(pair_1[1])
                else 1
            )
            factor_2 = (
                fraction
                if _is_crossing_node(pair_2[0]) != _is_crossing_node(pair_2[1])
                else 1
            )

            total += factor_1 * factor_2

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
                pos[node_a][0] == pos[node_b][0] and pos[node_a][1] == pos[node_b][1]
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

            # Build a subgraph of symmetric nodes
            symmetric_subgraph = g.subgraph(mirrored_nodes)
            subgraph_edges = list(symmetric_subgraph.edges)

            if len(subgraph_edges) <= threshold:
                continue

            if fraction == 1:
                sub_sym = 1
            else:

                # Obtain all mirrored edges
                subgraph_edge_pairs = []

                for edge in subgraph_edges:
                    a = edge[0]
                    b = edge[1]

                    for mirror_of_a in mirrored_node_pairs[a]:
                        mirror_of_a = node_list[mirror_of_a]
                        for mirror_of_b in mirrored_node_pairs[b]:
                            mirror_of_b = node_list[mirror_of_b]
                            if g.has_edge(mirror_of_a, mirror_of_b) or g.has_edge(
                                mirror_of_b, mirror_of_a
                            ):
                                subgraph_edge_pairs.append(
                                    ((a, b), (mirror_of_a, mirror_of_b))
                                )

                sub_sym = _subgraph_symmetry(subgraph_edge_pairs)

            sub_area = _subgraph_area(symmetric_subgraph.nodes)
            total_symmetry += sub_sym * sub_area
            total_area += sub_area

    return total_symmetry / max(total_area, convex_hull_area)


class SymmetryType(Enum):
    """Type of symmetry used for :func:`edge_based_symmetry`"""

    REFLECTIVE = 0
    ROTATIONAL = 1
    TRANSLATIONAL = 2


class _SIFTFeature:

    def __init__(self, edge: Tuple[Numeric, Numeric], edge_pos, score):

        point_a = common.Vector.from_point(edge_pos[0])
        point_b = common.Vector.from_point(edge_pos[1])

        self.mid = (point_a + point_b) / 2
        self.length = common.euclidean_distance(edge_pos[0], edge_pos[1])
        self.angle = (
            (
                common.Vector.from_point(edge_pos[1])
                - (common.Vector.from_point(edge_pos[0]))
            )
            .upward_and_forward_direction()
            .rad()
        )
        self.edge = edge
        self.score = score

    def compare_scale(self, other: _SIFTFeature, sigma_scale: float) -> float:
        """Scale similarity"""
        top = -abs(self.length - other.length)
        bottom = sigma_scale * (self.length + other.length)

        if bottom == 0:
            return 0

        return math.exp(top / bottom) ** 2

    def compare_distance(
        self, other: _SIFTFeature, sigma_distance: float, is_distance_bound: bool
    ):
        """Distance similarity"""
        if not is_distance_bound:
            return 1
        dist = self.mid.distance(other.mid)
        return math.exp(-(dist**2) / (2 * sigma_distance * sigma_distance))

    def compare_rotation(self, other: _SIFTFeature, theta: float = None):
        """Rotation similarity"""
        if theta is None:
            return abs(math.cos(self.angle - other.angle))
        return abs(math.cos(self.angle + other.angle - 2 * theta))


class _Axis:

    def __init__(self, pos, edge_a, edge_b, score):
        self.pos = pos
        self.edge_a = edge_a
        self.edge_b = edge_b
        self.score = score

    def __str__(self):
        return f"_Vote({self.pos}, {self.edge_a}, {self.edge_b}, {self.score})"


class _AxesSystem:

    def __init__(
        self,
        pos: dict,
        sigma_scale: float,
        distance_bound: bool,
        sigma_distance: float,
        num_features: int,
        angle_merge: float,
        pixel_merge: float,
        x_min: float,
        y_min: float,
    ):
        self.pos = pos
        self.y_min = y_min
        self.x_min = x_min
        self.y_merge = pixel_merge
        self.x_merge = angle_merge
        self.num_features = num_features
        self.sigma_distance = sigma_distance
        self.is_distance_bound = distance_bound
        self.sigma_scale = sigma_scale
        self.votes = []

    def add_rotational_vote(self, feature):
        """Add rotational axis to voting"""
        self.votes.append(_Axis(feature.mid, feature.edge, feature.edge, 1))

    def add_rotational_vote_from_two(self, feature_a, feature_b):
        """Add rotational axis to voting created from two edges"""
        sca = feature_a.compare_scale(feature_b, self.sigma_scale)
        dis = feature_a.compare_distance(
            feature_b, self.sigma_distance, self.is_distance_bound
        )
        score = sca * dis

        mid = feature_a.mid.mid(feature_b.mid)
        mid_diff = feature_b.mid - feature_a.mid
        theta_ij = math.atan2(mid_diff.y, mid_diff.x) + math.pi / 2

        delta_dist = feature_a.mid.distance(feature_b.mid) / 2
        delta_angl = abs(feature_b.angle - feature_a.angle) / 2

        if math.tan(delta_angl) == 0:
            # The two edges are parallel -> rotation equals 0° -> skip
            return

        radius = delta_dist / math.tan(delta_angl)

        if (
            abs(radius) < 0.001
            or abs(delta_angl) < 0.5
            or abs(delta_angl - math.pi) < 0.05
        ):
            # The rotational symmetry is centered at the mid itself
            vote = _Axis(mid, feature_a.edge, feature_b.edge, score)
            self.votes.append(vote)
        else:
            # Otherwise, find rotation points on boundary of radius (two opposite points)

            direction = common.Vector(1, 0).rotate(common.Angle(theta_ij))

            scaled_direction = direction * radius

            center_a = mid + scaled_direction
            center_b = mid - scaled_direction

            theta_diff = feature_b.angle - feature_a.angle

            test_a = (feature_a.mid - center_a).rotate(theta_diff) + center_a
            test_b = (feature_a.mid - center_b).rotate(theta_diff) + center_b

            if test_a.distance(feature_b.mid) < 0.0001:
                center = center_a
                factor = -1
            elif test_b.distance(feature_b.mid) < 0.0001:
                center = center_b
                factor = 1
            else:
                # Should never by the case
                return

            vote = _Axis(center, feature_a.edge, feature_b.edge, score)
            self.votes.append(vote)

            # Opposite point
            if radius > 0:
                delta_angl_flipped = (math.pi - delta_angl * 2) / 2
                radius_2 = delta_dist / math.tan(delta_angl_flipped)

                scaled_direction = direction * radius_2 * factor
                center = mid + scaled_direction

                vote = _Axis(center, feature_a.edge, feature_b.edge, score)
                self.votes.append(vote)

    @staticmethod
    def _parse_reflective_vote(
        angle: common.Angle, radius: float, score: float, edge_a, edge_b
    ) -> _Axis:
        while angle.rad() < 0:
            angle += math.pi

        if radius < 0:
            radius = abs(radius)
            angle += math.pi
            while angle > math.pi * 2:
                angle -= math.pi

        return _Axis(common.Vector(angle.deg(), radius), edge_a, edge_b, score)

    def add_reflective_vote(self, feature):
        """Add reflective axis to voting"""

        mid = feature.mid

        edge_pos_a = common.Vector.from_point(self.pos[feature.edge[0]])
        edge_pos_b = common.Vector.from_point(self.pos[feature.edge[1]])

        theta_ij = common.Angle((edge_pos_a - edge_pos_b).rad() % math.pi)
        theta_ij_bisector = common.Angle(theta_ij + math.pi / 2)

        # Symmetry axis along perpendicular bisector
        r_ij = mid.x * math.cos(theta_ij_bisector.rad()) + mid.y * math.sin(
            theta_ij_bisector.rad()
        )
        self.votes.append(
            self._parse_reflective_vote(
                theta_ij_bisector, r_ij, 1, feature.edge, feature.edge
            )
        )

        # Symmetry axis along edge itself
        r_ij = mid.x * math.cos(theta_ij.rad()) + mid.y * math.sin(theta_ij.rad())
        self.votes.append(
            self._parse_reflective_vote(theta_ij, r_ij, 1, feature.edge, feature.edge)
        )

    def add_reflective_vote_from_two(self, feature_a, feature_b):
        """Add reflective axis to voting created from two edges"""

        theta_ij = (feature_a.mid - feature_b.mid).rad() % math.pi
        mid = feature_a.mid.mid(feature_b.mid)
        r_ij = mid.x * math.cos(theta_ij) + mid.y * math.sin(theta_ij)

        rot = feature_a.compare_rotation(feature_b, theta_ij)
        sca = feature_a.compare_scale(feature_b, self.sigma_scale)
        dis = feature_a.compare_distance(
            feature_b, self.sigma_distance, self.is_distance_bound
        )
        score = rot * sca * dis

        self.votes.append(
            self._parse_reflective_vote(
                theta_ij, r_ij, score, feature_a.edge, feature_b.edge
            )
        )

    def add_translative_vote(self, feature_a, feature_b):
        """Add translative axis to voting"""

        rot = feature_a.compare_rotation(feature_b)
        sca = feature_a.compare_scale(feature_b, self.sigma_scale)
        dis = feature_a.compare_distance(
            feature_b, self.sigma_distance, self.is_distance_bound
        )

        delta = feature_a.mid - feature_b.mid

        if delta.y < 0:
            delta *= -1

        score = rot * sca * dis
        vote = _Axis(delta, feature_a.edge, feature_b.edge, score)
        self.votes.append(vote)

    def _points_too_close(self, pos_a, pos_b):
        return (
            abs(pos_a.x - pos_b.x) < self.x_min and abs(pos_a.y - pos_b.y) < self.y_min
        )

    def _find_maxima(self):
        def _merge_close_point(value: float, merge_span: float):
            return (int(value / merge_span)) * merge_span

        voting_dic = {}

        # Group together close points
        for vote in self.votes:
            x_merged = _merge_close_point(vote.pos.x, self.x_merge)
            y_merged = _merge_close_point(vote.pos.y, self.y_merge)

            key = Vector(x_merged, y_merged)

            if vote.score <= 0:
                continue

            if key in voting_dic:
                voting_dic[key] += vote.score
            else:
                voting_dic[key] = vote.score

        # Find max-scoring points
        sorted_axes = list(
            sorted(voting_dic.keys(), key=lambda x: voting_dic[x], reverse=True)
        )

        # Remove double-entries that are too close
        for i in range(min(self.num_features, len(sorted_axes))):
            j = i + 1
            while j < len(sorted_axes):
                if self._points_too_close(sorted_axes[i], sorted_axes[j]):
                    sorted_axes.pop(j)
                else:
                    j += 1

        return sorted_axes[: min(self.num_features, len(sorted_axes))]

    def conclude_voting(self, g: nx.Graph) -> float:
        """Takes the top axes and counts the percentage of edges voting for at least one of them"""
        top_features = self._find_maxima()

        if len(top_features) == 0:
            return 0

        matching_edge_dic = set()

        for vote in self.votes:
            matched = False

            for feature in top_features:
                if self._points_too_close(vote.pos, feature):
                    matched = True
                    break

            if matched:
                matching_edge_dic.add(vote.edge_a)
                matching_edge_dic.add(vote.edge_b)

        return len(matching_edge_dic) / float(len(top_features) * len(g.edges()))


def edge_based_symmetry(
    g: nx.Graph,
    symmetry_type: SymmetryType,
    pos: Union[str, dict, None] = None,
    axes_count: int = 1,
    sigma_scale: float = 0.1,
    sigma_distance: float = 2,
    is_distance_bound: bool = False,
    angle_merge: float = 5,
    pixel_merge: float = 5,
    x_min: float = 10,
    y_min: float = 10,
) -> float:
    """
    This calculates the symmetry metric proposed by :footcite:t:`chapman_symmetry_2018`. It is
    capable of estimating either translational, reflective or rotational symmetry.

    The implementation follows the `Java implementation
    <https://github.com/klapaukh/GraphAnalyser/blob/master/src/analysis/symmetry/Image.java>`_ by the original authors.

    :param g: A networkX graph
    :type g: nx.Graph
    :param symmetry_type: The type of symmetry that should be evaluated.
    :type symmetry_type: gdMetriX.SymmetryType
    :param pos: Optional node position dictionary. If not supplied, node positions are read from the graph directly.
            If given as a string, the property under the given name in the networkX graph is used.
    :type pos: Union[str, dic, None]
    :param axes_count: Only the top `axes_count` axes are selected and evaluated.
    :type axes_count: int
    :param sigma_scale: The tolerance for when two features are considered to have the same scale.
    :type sigma_scale: float
    :param sigma_distance: The tolerance for when two features are considered to have the same position.
    :type sigma_distance: float
    :param is_distance_bound: Whether to bound the distance
    :type is_distance_bound: bool
    :param angle_merge: The tolerance between angles for merging two axes.
    :type angle_merge: float
    :param pixel_merge: The tolerance between positions for merging two axes.
    :type pixel_merge: float
    :param x_min: Tolerance in the x direction for when two points are considered equal.
    :type x_min: float
    :param y_min: Tolerance in the y direction for when two points are considered equal.
    :type y_min: float
    :return: A symmetry estimate
    :rtype: float
    """
    pos = common.get_node_positions(g, pos)

    if len(g.edges()) == 0:
        return 1

    votes = _AxesSystem(
        pos,
        sigma_scale,
        is_distance_bound,
        sigma_distance,
        axes_count,
        angle_merge,
        pixel_merge,
        x_min,
        y_min,
    )
    sift_features = [_SIFTFeature(e, (pos[e[0]], pos[e[1]]), 1) for e in g.edges()]

    for a, feature_a in enumerate(sift_features):
        for _, feature_b in enumerate(sift_features[a + 1 :], start=a + 1):
            if symmetry_type == SymmetryType.REFLECTIVE:
                votes.add_reflective_vote_from_two(feature_a, feature_b)
            elif symmetry_type == SymmetryType.ROTATIONAL:
                votes.add_rotational_vote_from_two(feature_a, feature_b)
            elif symmetry_type == SymmetryType.TRANSLATIONAL:
                votes.add_translative_vote(feature_a, feature_b)

        if symmetry_type == SymmetryType.REFLECTIVE:
            votes.add_reflective_vote(feature_a)
        elif symmetry_type == SymmetryType.ROTATIONAL:
            votes.add_rotational_vote(feature_a)

    return votes.conclude_voting(g)


def visual_symmetry(
    g: nx.Graph,
    pos: Union[str, dict, None] = None,
    resolution: int = 100,
    sigma: float = 2,
    rotational: bool = True,
    reflective: bool = True,
    dihedral: bool = True,
) -> float:
    """
    Tries to estimate the perceived symmetry of the drawing by visually testing reflective, rotational and dihedral
    symmetry.

    :param g: graph
    :type g: nx.Graph
    :param pos: Dictionary of node positions. If not supplied, it is expected that the positions are included in g.
    :type pos: dic
    :param resolution: Width and height of the image the graph is drawn to. The higher the resolution, the more
        sensitive the measure is to local details.
    :type resolution: int
    :param sigma: Sigma of the Gaussian blur applied to the drawing of g. The higher the value, the more the symmetry
        reflects just the general shape of the graph instead of local details.
    :type sigma: float
    :param rotational: If true, rotational symmetry is measured and considered for the final symmetry value.
    :type rotational: bool
    :param reflective: If true, reflective symmetry is measured and considered for the final symmetry value.
    :type reflective: bool
    :param dihedral: If true, dihedral symmetry is measured and considered for the final symmetry value.
    :type dihedral: bool
    :return: A value in [0,1] estimating the perceived symmetry.
    :rtype: float
    """

    pos = common.get_node_positions(g, pos)

    if len(pos) <= 1:
        return 1

    pos = boundary.normalize_positions(g, pos)

    def _build_canvas():
        fig = plt.figure(1, figsize=(1, 1), dpi=resolution)
        ax = plt.axes([0.0, 0.0, 1.0, 1.0], frameon=False, xticks=[], yticks=[])
        ax.set_xlim(-0.8, 0.8)
        ax.set_ylim(-0.8, 0.8)
        ax.set_facecolor((0, 0, 0))
        fig.patch.set_facecolor((0, 0, 0))
        canvas = FigureCanvasAgg(fig)
        return canvas, fig, ax

    def _draw_to_array(canvas: FigureCanvasAgg):
        return np.array(canvas.buffer_rgba())[:, :, :3]

    def _get_edge_image():
        canvas, fig, ax = _build_canvas()
        nx.draw_networkx_edges(g, pos, edge_color="#f00", ax=ax)
        canvas.draw()
        image = _draw_to_array(canvas)
        fig.clf()
        return image

    def _get_node_image():
        canvas, fig, ax = _build_canvas()
        nx.draw_networkx_nodes(g, pos, node_size=0.1, node_color="#0f0", ax=ax)
        canvas.draw()
        image = _draw_to_array(canvas)
        fig.clf()
        return image

    def _normalize_array(img):
        min_val = np.min(img)
        max_val = np.max(img)
        if min_val == max_val:
            return np.zeros_like(img)
        return (img - min_val) / (max_val - min_val)

    edge_image = _normalize_array(_get_edge_image()[:, :, 0])
    node_image = _normalize_array(_get_node_image()[:, :, 1])
    graph_image = edge_image + node_image

    # Translate to centroid
    centroid = ndimage.center_of_mass(graph_image)
    shape = graph_image.shape
    graph_image = ndimage.shift(
        graph_image, np.array([shape[0] / 2 - centroid[0], shape[1] / 2 - centroid[1]])
    )

    # Blur
    graph_image = ndimage.gaussian_filter(graph_image, sigma=sigma)

    original_sum = np.sum(graph_image)
    rotational_estimate = 0 if rotational else float("inf")
    reflective_estimate = 0 if reflective else float("inf")
    dihedral_estimate = 0 if dihedral else float("inf")

    def _get_axis_weight(degree) -> float:
        if degree % 180 == 0:
            # Vertical
            return 0.5
        if degree % 90 == 0:
            # Horizontal
            return 0.3
        if degree % 45 == 0:
            # In between
            return 0.1
        return 0

    for i in range(0, 360, 45):
        # Rotate image
        rotated_image = ndimage.rotate(graph_image, i, reshape=False)
        flipped_and_rotated = np.flip(rotated_image, 0)

        # Rotational symmetry
        if rotational and 0 < i <= 180:
            rotational_difference_image = graph_image - rotated_image
            rotational_difference = np.sum(np.abs(rotational_difference_image))
            rotational_estimate += _get_axis_weight(i) * rotational_difference

        # Reflective symmetry
        if reflective and i < 180:
            reflective_difference_image = rotated_image - flipped_and_rotated
            reflective_difference = np.sum(np.abs(reflective_difference_image))
            reflective_estimate += _get_axis_weight(i) * reflective_difference

        # Dihedral symmetry
        if dihedral:
            dihedral_difference_image = flipped_and_rotated - graph_image
            dihedral_difference = np.sum(np.abs(dihedral_difference_image))
            dihedral_estimate += _get_axis_weight(i) * dihedral_difference

    rotational_estimate /= 1 * original_sum
    reflective_estimate /= original_sum
    dihedral_estimate /= 1.9 * original_sum

    minimum = min(rotational_estimate, reflective_estimate, dihedral_estimate, 1)
    return 1 - math.pow(minimum, 2)


def stress(
    g: nx.Graph, pos: Union[str, dict, None] = None, scale_minimization: bool = True
) -> float:
    r"""
    Estimates symmetry by utilizing the stress of the graph embedding as proposed by :footcite:t:`welch_measuring_2017`.

    The stress of a graph :math:`G=(V,E)` is defined as :math:`\sum{i,j \in V} (||p_j - p_j|| - d_{ij})^2`, where :math:`||p_i - p_j||` denotes
    the Euclidean distance between two vertices and $d_{ij}$ the length of the shortest path between :math:`i`
    and :math:`j`.

    :param g: A networkX graph
    :type g: nx.Graph
    :param pos: Optional node position dictionary. If not supplied, node positions are read from the graph directly.
            If given as a string, the property under the given name in the networkX graph is used.
    :type pos: Union[str, dic, None]
    :param scale_minimization: If true, the scale of the drawing is adjusted to minimize the stress. To be precise,
            a parameter :math:`s` is calculated using a binary search, minimizing the following function:
            :math:`\sum{i,j \in V} (s \cdot ||p_j - p_j|| - d_{ij})^2`
    :type scale_minimization:
    :return: Stress of the graph embedding
    :rtype: float
    """

    pos = common.get_node_positions(g, pos)
    shortest_path_distances = dict(nx.all_pairs_shortest_path_length(g))

    def _get_stress(scale):
        stress_value = 0

        for i, p_i_key in enumerate(pos):
            p_i = pos[p_i_key]
            for j, p_j_key in enumerate(pos):
                p_j = pos[p_j_key]
                if i < j and p_j_key in shortest_path_distances[p_i_key]:
                    d_ij = shortest_path_distances[p_i_key][p_j_key]
                    euclidean_distance = common.euclidean_distance(p_i, p_j)
                    stress_value += (euclidean_distance * scale - d_ij) ** 2 / (d_ij**2)

        return stress_value

    def _binary_search_optimize(s_min, s_max, epsilon=1e-4):

        while s_max - s_min > epsilon:
            s_mid1 = s_min + (s_max - s_min) / 3
            s_mid2 = s_max - (s_max - s_min) / 3

            stress_mid1 = _get_stress(s_mid1)
            stress_mid2 = _get_stress(s_mid2)

            if stress_mid1 < stress_mid2:
                s_max = s_mid2
            else:
                s_min = s_mid1

        return (s_min + s_max) / 2

    optimal_scale = (
        _binary_search_optimize(0.00000025, 4000000) if scale_minimization else 1
    )
    return _get_stress(optimal_scale)


def even_neighborhood_distribution(
    g: nx.Graph, pos: Union[str, dict, None] = None
) -> float:
    r"""
    Estimates symmetry by calculating how central each node is within its neighborhood as proposed by
    :footcite:t:`xu_force-directed_2018`.

    Let :math:`N_v` be defined as the neighborhood of a node :math:`v \in V` and :math:`W_v := N_v \cup \{v\}`. Let
    :math:`C(W_v)` be the smallest enclosing circle of :math:`W_v` and :math:`\text{bary}(W_v)` its barycenter.
    The symmetry metric :math:`\sigma_v` for a node :math:`v \in V` is defined as the distance between the barycenter
    :math:`\text{bary}(W_v)` and the center of :math:`\text{center}(C(W_v))`, scaled by the radius of :math:`C(W_v)`,
    i.e., :math:`\frac{|\text{bary}(W_v) - \text{center}(C(W_v))}{\text{radius}(C(W_v))}`.

    The final metric is defined by the average over all nodes, i.e., :math:`\frac{1}{n} \sum_{v \in V} \sigma_v`.

    :param g: A networkX graph
    :type g: nx.Graph
    :param pos: Optional node position dictionary. If not supplied, node positions are read from the graph directly.
            If given as a string, the property under the given name in the networkX graph is used.
    :type pos: Union[str, dic, None]
    :return: The symmetry metric defined by the neighborhood distribution.
    :rtype: float
    """
    pos = common.get_node_positions(g, pos)

    if g.order() <= 2:
        return 1

    total_distance = 0
    total_nodes = 0
    for i in g.nodes():
        w_i = [pos[neighbor] for neighbor in g[i]]
        w_i.append(pos[i])

        if len(w_i) <= 2:
            continue

        total_nodes += 1

        center, radius = smallest_enclosing_circle_from_point_set(w_i)
        barycenter = common.barycenter(w_i)
        total_distance += center.distance(barycenter) / radius

    if total_nodes == 0:
        return 1

    return 1 - (total_distance / total_nodes)
